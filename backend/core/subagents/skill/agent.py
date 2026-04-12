"""
Skill SubAgent - 技能发现与执行Agent
负责：技能加载、沙箱执行、结果收集、改进反馈
"""

import os
import json
import time
import logging
from typing import Dict, Any, List, Optional, Tuple

from ..base import BaseSubAgent, AgentCapability, AgentExecutionContext, AgentExecutionResult, AgentHealthCheckResult, AgentHealthStatus

logger = logging.getLogger(__name__)


class SkillSubAgent(BaseSubAgent):
    """
    技能执行Agent
    
    核心能力：
    1. 技能注册与发现（从技能库查找）
    2. 安全扫描（静态代码分析）
    3. 沙箱执行（Docker容器隔离）
    4. 结果验证与格式化
    5. 执行反馈收集
    
    技能生命周期：
    注册 → 审核 → 部署 → 安装 → 执行 → 反馈 → 改进
    """
    
    def __init__(self, config: Optional[Dict] = None):
        capability = AgentCapability(
            name="skill_execution",
            description="技能发现、加载、沙箱执行、自改进",
            version="1.0.0",
            input_schema={
                "skill_name": {"type": "string", "required": True},
                "params": {"type": "object"},
                "version": {"type": "string", "default": "latest"}
            },
            output_schema={
                "result": {"type": "object"},
                "execution_log": {"type": "array"},
                "skill_version": {"type": "string"}
            },
            supported_intents=["task_execution", "ecommerce_operation", "design_work", 
                             "finance_management", "software_development"],
            max_concurrent_tasks=5,
            estimated_latency_ms=3000
        )
        
        super().__init__("skill-agent-001", capability)
        
        self.config = config or {}
        self.skill_storage_path = config.get("skill_storage_path", "./data/skills") if config else "./data/skills"
        self.default_timeout = config.get("default_timeout", 300) if config else 300
        
        # 技能注册表（内存缓存，实际应使用数据库）
        self._skill_registry: Dict[str, Dict] = {}
        self._execution_history_detailed: List[Dict] = []
        
        # Docker配置
        self._docker_available = False
        try:
            import docker
            self._docker_client = docker.from_env()
            self._docker_available = True
            logger.info(f"[{self.agent_id}] Docker client initialized")
        except Exception as e:
            logger.warning(f"[{self.agent_id}] Docker not available: {e}. Skills will run in-process.")
    
    async def execute(self, task: Dict[str, Any], context: AgentExecutionContext) -> AgentExecutionResult:
        """执行技能"""
        start_time = time.time()
        
        skill_name = task.get("skill_name", "")
        params = task.get("params", {})
        skill_version = task.get("version", "latest")
        
        logger.info(f"[{self.agent_id}] Executing skill: {skill_name} v{skill_version}")
        
        execution_log = []
        
        # Step 1: 查找并加载技能
        skill = await self._load_skill(skill_name, skill_version)
        if not skill:
            return AgentExecutionResult(
                success=False,
                error=f"Skill '{skill_name}' (v{skill_version}) not found",
                error_type="skill_not_found",
                suggestions=[
                    f"检查技能名称是否正确: {skill_name}",
                    f"可用技能列表: {list(self._skill_registry.keys())[:10]}",
                    "尝试 /skills 命令查看已安装的技能"
                ]
            )
        
        execution_log.append({"step": "load", "status": "success", "time": time.time() - start_time})
        
        # Step 2: 参数验证
        validation_result = await self._validate_skill_params(skill, params)
        if not validation_result["valid"]:
            return AgentExecutionResult(
                success=False,
                error=f"Parameter validation failed: {validation_result['errors']}",
                error_type="invalid_params",
                metrics={"step": "validation"}
            )
        
        execution_log.append({"step": "validate", "status": "success"})
        
        # Step 3: 安全扫描
        if self.config.get("security_scan_on_upload", True):
            scan_result = await self._security_scan(skill)
            if not scan_result["safe"]:
                return AgentExecutionResult(
                    success=False,
                    error=f"Security scan failed: {scan_result['issues']}",
                    error_type="security_violation",
                    should_retry=False
                )
            
            execution_log.append({"step": "security_scan", "status": "passed"})
        
        # Step 4: 执行技能
        if self._docker_available and skill.get("runtime", {}).get("use_sandbox", True):
            result = await self._execute_in_sandbox(skill, params, context.timeout_seconds)
        else:
            result = await self._execute_in_process(skill, params)
        
        execution_log.extend(result.get("log", []))
        
        total_time = time.time() - start_time
        
        if result["success"]:
            # 记录执行历史用于后续改进
            self._record_skill_execution(skill_name, {
                "success": True,
                "duration": total_time,
                "params_hash": hash(json.dumps(params, sort_keys=True))
            })
            
            return AgentExecutionResult(
                success=True,
                data=result["data"],
                metrics={
                    "total_time_sec": total_time,
                    "skill_version": skill["version"],
                    **result.get("metrics", {})
                },
                artifacts=result.get("artifacts", []),
                suggestions=result.get("suggestions", [])
            )
        else:
            self._record_skill_execution(skill_name, {
                "success": False,
                "duration": total_time,
                "error": result.get("error", "")[:200]
            })
            
            return AgentExecutionResult(
                success=False,
                error=result.get("error", "Unknown skill execution error"),
                error_type=result.get("error_type", "skill_error"),
                should_retry=self._should_retry_skill_error(result.get("error_type", "")),
                retry_delay=2.0,
                metrics={"total_time_sec": total_time}
            )
    
    async def validate_input(self, task: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        
        if "skill_name" not in task or not task.get("skill_name"):
            errors.append("Missing required parameter: 'skill_name'")
        elif not isinstance(task["skill_name"], str):
            errors.append("'skill_name' must be a string")
        
        if "params" in task and not isinstance(task.get("params"), dict):
            errors.append("'params' must be an object/dict")
        
        return (len(errors) == 0, errors)
    
    async def health_check(self) -> AgentHealthCheckResult:
        stats = await self.get_statistics()
        
        status = AgentHealthStatus.HEALTHY
        if not self._docker_available:
            status = AgentHealthStatus.DEGRADED
        
        return AgentHealthCheckResult(
            status=status,
            agent_id=self.agent_id,
            uptime_seconds=stats["uptime_seconds"],
            tasks_completed=sum(1 for r in self._execution_history if r["success"]),
            tasks_failed=sum(1 for r in self._execution_history if not r["success"]),
            average_latency_ms=stats["avg_latency_ms"],
            queue_size=len(self._skill_registry),
            details={
                "registered_skills": len(self._skill_registry),
                "docker_available": self._docker_available,
                **stats
            }
        )
    
    def register_skill(self, manifest: Dict[str, Any], code: str) -> str:
        """
        手动注册技能
        
        Args:
            manifest: 技能元数据（符合skill_manifest.json规范）
            code: 技能代码
            
        Returns:
            skill_id
        """
        skill_id = manifest.get("skill_id")
        if not skill_id:
            raise ValueError("manifest must contain 'skill_id'")
        
        skill_data = {
            **manifest,
            "code": code,
            "registered_at": time.time(),
            "execution_count": 0,
            "last_executed": None,
            "avg_duration": 0,
            "success_rate": 1.0
        }
        
        self._skill_registry[skill_id] = skill_data
        logger.info(f"[{self.agent_id}] Registered skill: {skill_id} ({manifest.get('name', 'Unknown')})")
        
        return skill_id
    
    async def _load_skill(self, skill_name: str, version: str) -> Optional[Dict]:
        """从注册表或文件系统加载技能"""
        # 先查内存注册表
        for skill_id, skill_data in self._skill_registry.items():
            base_name = skill_id.split(".v")[0] if ".v" in skill_id else skill_id
            if base_name == skill_name or skill_id == skill_name:
                if version == "latest" or skill_data.get("version") == version:
                    return skill_data
        
        # 尝试从文件系统加载
        skill_path = os.path.join(self.skill_storage_path, f"{skill_name}")
        manifest_path = os.path.join(skill_path, "skill_manifest.json")
        
        if os.path.exists(manifest_path):
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            code_path = os.path.join(skill_path, manifest.get("entry_point", "main.py"))
            if os.path.exists(code_path):
                with open(code_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                skill_data = {**manifest, "code": code}
                self._skill_registry[f"{skill_name}.{manifest.get('version', '1.0')}"] = skill_data
                return skill_data
        
        return None
    
    async def _validate_skill_params(self, skill: Dict, params: Dict) -> Dict:
        """验证技能参数是否符合schema"""
        input_schema = skill.get("capability", {}).get("input_schema", {})
        errors = []
        
        required_fields = [k for k, v in input_schema.items() if v.get("required", False)]
        for field in required_fields:
            if field not in params:
                errors.append(f"Missing required parameter: '{field}'")
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    async def _security_scan(self, skill: Dict) -> Dict:
        """静态代码安全扫描"""
        code = skill.get("code", "")
        issues = []
        
        dangerous_patterns = [
            (r"\bos\.system\s*\(", "os.system() detected"),
            (r"\bsubprocess\.", "subprocess usage"),
            (r"\beval\s*\(", "eval() usage"),
            (r"\bexec\s*\(", "exec() usage"),
            (r"__import__\s*\(", "dynamic import"),
            (r"rm\s+-rf", "dangerous file deletion"),
        ]
        
        for pattern, description in dangerous_patterns:
            if __import__("re").search(pattern, code):
                issues.append(description)
        
        is_safe = len(issues) == 0
        
        return {"safe": is_safe, "issues": issues}
    
    async def _execute_in_sandbox(self, skill: Dict, params: Dict, timeout: float) -> Dict:
        """在Docker沙箱中执行技能"""
        runtime_config = skill.get("runtime", {})
        image = runtime_config.get("image", "python:3.11-slim")
        entry_point = runtime_config.get("entry_point", "main.py")
        memory_limit = runtime_config.get("memory_limit_mb", 512)
        
        log_entries = [{"step": "sandbox_start", "status": "pending"}]
        
        try:
            container_name = f"wukong-skill-{skill['skill_id'][:12]}-{int(time.time())}"
            
            # 准备执行脚本
            exec_script = f'''
import json
import sys

# 注入参数
params = json.loads('''{json.dumps(params)}''')

# 加载并执行技能代码
{skill.get('code', '# No code')}

# 调用主函数
if 'main' in locals():
    result = main(params)
    print(json.dumps({{"status": "success", "result": result}}))
else:
    print(json.dumps({{"status": "error", "message": "No main() function found"}}))
'''
            
            # 创建容器
            container = self._docker_client.containers.run(
                image=image,
                command=["python", "-c", exec_script],
                name=container_name,
                mem_limit=f"{memory_limit}m",
                cpu_period=100000,
                cpu_quota=100000,
                network_mode="none",  # 网络隔离
                remove=True,
                detach=True
            )
            
            log_entries[-1]["status"] = "running"
            log_entries.append({"step": "container_created", "container_id": container.id[:12]})
            
            # 等待执行完成
            result = container.wait(timeout=timeout)
            
            logs = container.logs().decode('utf-8')
            
            output = None
            for line in logs.strip().split('\n'):
                if line.startswith('{'):
                    try:
                        output = json.loads(line)
                        break
                    except:
                        pass
            
            if output and output.get("status") == "success":
                return {
                    "success": True,
                    "data": output.get("result"),
                    "metrics": {
                        "exit_code": result.get("StatusCode", 0),
                        "container_used": True
                    },
                    "log": log_entries + [{"step": "completed", "status": "success"}]
                }
            else:
                return {
                    "success": False,
                    "error": output.get("message", "Unknown error from sandbox"),
                    "error_type": "sandbox_error",
                    "log": log_entries + [{"step": "completed", "status": "failed"}]
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Sandbox execution failed: {str(e)}",
                "error_type": "sandbox_error",
                "should_retry": False,
                "log": log_entries + [{"step": "error", "error": str(e)}]
            }
    
    async def _execute_in_process(self, skill: Dict, params: Dict) -> Dict:
        """进程内执行（无Docker时降级方案）"""
        log_entries = [{"step": "in_process", "warning": "Running without sandbox isolation"}]
        
        try:
            code = skill.get("code", "")
            local_vars = {"params": params}
            
            exec(code, local_vars)
            
            if "main" in local_vars:
                result = local_vars["main"](params)
                return {
                    "success": True,
                    "data": result,
                    "metrics": {"mode": "in_process"},
                    "log": log_entries + [{"step": "completed", "status": "success"}]
                }
            else:
                return {
                    "success": False,
                    "error": "Skill code has no main() function",
                    "error_type": "invalid_skill",
                    "log": log_entries
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"In-process execution error: {str(e)}",
                "error_type": "execution_error",
                "should_retry": True,
                "log": log_entries + [{"step": "error", "error": str(e)}]
            }
    
    def _record_skill_execution(self, skill_name: str, record: Dict):
        """记录技能执行历史"""
        record["timestamp"] = time.time()
        record["skill"] = skill_name
        self._execution_history_detailed.append(record)
        
        if len(self._execution_history_detailed) > 5000:
            self._execution_history_detailed = self._execution_history_detailed[-3000:]
    
    def _should_retry_skill_error(self, error_type: str) -> bool:
        retryable = ["timeout", "sandbox_error", "execution_error"]
        return error_type in retryable
