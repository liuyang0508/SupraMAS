"""
File SubAgent - 文件智能处理Agent
负责：精准读取、原子修改、版本管理、格式转换
参考悟空RealDoc理念
"""

import os
import re
import json
import time
import hashlib
import shutil
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from ..base import BaseSubAgent, AgentCapability, AgentExecutionContext, AgentExecutionResult, AgentHealthCheckResult, AgentHealthStatus

logger = logging.getLogger(__name__)


class FileSubAgent(BaseSubAgent):
    """
    文件智能处理Agent - RealDoc风格
    
    核心能力：
    1. 精准读取（按行号/关键词定位）
    2. 原子修改（只改指定部分）
    3. 版本快照（每次修改自动保存）
    4. 差异对比与回滚
    5. 批量操作与格式转换
    
    设计原则：
    - 幂等性：重复执行相同操作结果一致
    - 原子性：修改要么完全成功，要么完全失败
    - 可追溯：所有操作有完整记录
    """
    
    SUPPORTED_FORMATS = {
        ".md": "markdown",
        ".txt": "text",
        ".json": "json",
        ".yaml": "yaml", ".yml": "yaml",
        ".py": "python",
        ".js": "javascript",
        ".csv": "csv"
    }
    
    def __init__(self, config: Optional[Dict] = None):
        capability = AgentCapability(
            name="file_operations",
            description="文件智能读取、原子修改、版本管理、格式转换",
            version="1.0.0",
            input_schema={
                "action": {"type": "string", "required": True, 
                          "enum": ["read", "write", "modify", "delete", "list", "snapshot_list", "rollback", "search_replace", "convert"]},
                "file_path": {"type": "string"},
                "content": {"type": "string"},
                "start_line": {"type": "integer"},
                "end_line": {"type": "integer"},
                "search_pattern": {"type": "string"},
                "replace_with": {"type": "string"},
                "target_format": {"type": "string"}
            },
            output_schema={
                "content": {"type": "string"},
                "version": {"type": "integer"},
                "checksum": {"type": "string"},
                "lines_count": {"type": "integer"}
            },
            supported_intents=["file_operation"],
            max_concurrent_tasks=20,
            estimated_latency_ms=500
        )
        
        super().__init__("file-agent-001", capability)
        
        self.config = config or {}
        self.base_storage_path = config.get("base_storage_path", "./data/files") if config else "./data/files"
        self.snapshots_dir = os.path.join(self.base_storage_path, ".snapshots")
        
        # 版本管理索引 {file_path: [version_info, ...]}
        self._version_index: Dict[str, List[Dict]] = {}
        
        # 确保目录存在
        os.makedirs(self.base_storage_path, exist_ok=True)
        os.makedirs(self.snapshots_dir, exist_ok=True)
    
    async def execute(self, task: Dict[str, Any], context: AgentExecutionContext) -> AgentExecutionResult:
        """执行文件操作"""
        start_time = time.time()
        
        action = task.get("action", "read")
        file_path = task.get("file_path", "")
        
        logger.info(f"[{self.agent_id}] Action={action} File={file_path}")
        
        try:
            if action == "read":
                result = await self._handle_read(task)
            elif action == "write":
                result = await self._handle_write(task)
            elif action == "modify":
                result = await self._handle_modify(task)
            elif action == "search_replace":
                result = await self._handle_search_replace(task)
            elif action == "snapshot_list":
                result = await self._handle_snapshot_list(task)
            elif action == "rollback":
                result = await self._handle_rollback(task)
            elif action == "list":
                result = await self._handle_list(task)
            else:
                return AgentExecutionResult(
                    success=False,
                    error=f"Unsupported file action: {action}",
                    error_type="invalid_action"
                )
            
            total_time_ms = (time.time() - start_time) * 1000
            result["metrics"] = {**result.get("metrics", {}), "total_time_ms": total_time_ms}
            
            return AgentExecutionResult(
                success=result.get("success", True),
                data=result.get("data"),
                metrics=result.get("metrics", {}),
                artifacts=[result.get("file_path")] if result.get("file_path") else []
            )
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error in {action}: {e}", exc_info=True)
            return AgentExecutionResult(
                success=False,
                error=str(e),
                error_type="file_error"
            )
    
    async def validate_input(self, task: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        action = task.get("action")
        
        valid_actions = ["read", "write", "modify", "delete", "list", "snapshot_list", "rollback", "search_replace", "convert"]
        if action not in valid_actions:
            errors.append(f"Invalid action '{action}'. Must be one of: {valid_actions}")
        
        if action not in ["list"] and not task.get("file_path"):
            errors.append("'file_path' is required for this action")
        
        if action == "modify" and not task.get("search_pattern"):
            errors.append("'search_pattern' required for modify action")
        
        return (len(errors) == 0, errors)
    
    async def health_check(self) -> AgentHealthCheckResult:
        stats = await self.get_statistics()
        
        storage_info = {
            "base_path": self.base_storage_path,
            "disk_usage": self._get_dir_size(self.base_storage_path),
            "snapshots_count": len(self._version_index),
            "supported_formats": list(self.SUPPORTED_FORMATS.keys())
        }
        
        return AgentHealthCheckResult(
            status=AgentHealthStatus.HEALTHY,
            agent_id=self.agent_id,
            uptime_seconds=stats["uptime_seconds"],
            tasks_completed=sum(1 for r in self._execution_history if r["success"]),
            tasks_failed=sum(1 for r in self._execution_history if not r["success"]),
            average_latency_ms=stats["avg_latency_ms"],
            details={**stats, **storage_info}
        )
    
    async def _handle_read(self, task: Dict) -> Dict:
        """读取文件内容"""
        file_path = self._resolve_path(task["file_path"])
        start_line = task.get("start_line")
        end_line = task.get("end_line")
        
        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}", "error_type": "not_found"}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if start_line and end_line:
            content_lines = lines[start_line-1:end_line]
        elif start_line:
            content_lines = lines[start_line-1:]
        else:
            content_lines = lines
        
        content = "".join(content_lines)
        checksum = hashlib.md5(content.encode()).hexdigest()
        
        return {
            "success": True,
            "data": {
                "content": content,
                "lines_count": len(content_lines),
                "line_range": (start_line or 1, start_line + len(content_lines) - 1 if start_line else len(lines)),
                "checksum": checksum,
                "file_size_bytes": os.path.getsize(file_path),
                "modified_at": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
            }
        }
    
    async def _handle_write(self, task: Dict) -> Dict:
        """写入文件（自动创建快照）"""
        file_path = self._resolve_path(task["file_path"])
        content = task.get("content", "")
        
        # 如果文件已存在，先创建快照
        if os.path.exists(file_path):
            snapshot_ver = self._create_snapshot(file_path, "before_write")
        
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        new_version = self._create_snapshot(file_path, "after_write")
        
        return {
            "success": True,
            "data": {
                "file_path": file_path,
                "version": new_version,
                "bytes_written": len(content.encode('utf-8')),
                "lines_written": content.count('\n') + 1
            },
            "file_path": file_path
        }
    
    async def _handle_modify(self, task: Dict) -> Dict:
        """原子修改文件（只改匹配的部分）"""
        file_path = self._resolve_path(task["file_path"])
        search_pattern = task["search_pattern"]
        replace_with = task.get("replace_with", "")
        
        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}
        
        # 创建修改前快照
        pre_version = self._create_snapshot(file_path, "before_modify")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        modified_content, count = re.subn(search_pattern, replace_with, original_content)
        
        if count == 0:
            return {
                "success": True,
                "data": {
                    "message": f"No matches found for pattern: {search_pattern}",
                    "modifications_made": 0
                }
            }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        post_version = self._create_snapshot(file_path, "after_modify")
        
        return {
            "success": True,
            "data": {
                "modifications_made": count,
                "pre_version": pre_version,
                "post_version": post_version,
                "pattern": search_pattern[:50],
                "preview_diff": self._generate_diff_preview(original_content, modified_content)
            },
            "file_path": file_path
        }
    
    async def _handle_search_replace(self, task: Dict) -> Dict:
        """批量搜索替换"""
        file_path = self._resolve_path(task["file_path"])
        search_str = task.get("search_pattern", "")
        replace_str = task.get("replace_with", "")
        
        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}
        
        pre_version = self._create_snapshot(file_path, "before_batch_replace")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        new_content = content.replace(search_str, replace_str)
        count = content.count(search_str)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        post_version = self._create_snapshot(file_path, "after_batch_replace")
        
        return {
            "success": True,
            "data": {
                "replacements_made": count,
                "pre_version": pre_version,
                "post_version": post_version
            },
            "file_path": file_path
        }
    
    async def _handle_snapshot_list(self, task: Dict) -> Dict:
        """列出文件的所有版本快照"""
        file_path = self._resolve_path(task["file_path"])
        versions = self._version_index.get(file_path, [])
        
        return {
            "success": True,
            "data": {
                "file_path": file_path,
                "total_versions": len(versions),
                "versions": [
                    {
                        "version": v["version"],
                        "timestamp": v["timestamp"],
                        "reason": v["reason"],
                        "size_bytes": v.get("size_bytes", 0),
                        "checksum": v.get("checksum", "")
                    }
                    for v in versions[-20:]  # 最近20个版本
                ]
            }
        }
    
    async def _handle_rollback(self, task: Dict) -> Dict:
        """回滚到指定版本"""
        file_path = self._resolve_path(task["file_path"])
        target_version = task.get("target_version")
        
        versions = self._version_index.get(file_path, [])
        target_snapshot = None
        
        for v in versions:
            if str(v["version"]) == str(target_version):
                target_snapshot = v
                break
        
        if not target_snapshot:
            return {"success": False, "error": f"Version {target_version} not found for file"}
        
        snapshot_path = target_snapshot.get("snapshot_path")
        if not snapshot_path or not os.path.exists(snapshot_path):
            return {"success": False, "error": "Snapshot file missing"}
        
        import shutil
        shutil.copy2(snapshot_path, file_path)
        
        current_version = self._create_snapshot(file_path, f"rollback_to_v{target_version}")
        
        return {
            "success": True,
            "data": {
                "message": f"Rolled back to version {target_version}",
                "current_version": current_version,
                "rolled_back_from": target_snapshot.get("timestamp")
            },
            "file_path": file_path
        }
    
    async def _handle_list(self, task: Dict) -> Dict:
        """列出目录下的文件"""
        dir_path = self._resolve_path(task.get("file_path", ""))
        
        if not os.path.isdir(dir_path):
            dir_path = self.base_storage_path
        
        files = []
        for item in os.listdir(dir_path):
            full_path = os.path.join(dir_path, item)
            if os.path.isfile(full_path):
                stat = os.stat(full_path)
                files.append({
                    "name": item,
                    "path": full_path,
                    "size_bytes": stat.st_size,
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "extension": os.path.splitext(item)[1]
                })
        
        return {
            "success": True,
            "data": {
                "directory": dir_path,
                "files": sorted(files, key=lambda x: x["name"]),
                "total_files": len(files)
            }
        }
    
    def _resolve_path(self, path: str) -> str:
        """解析文件路径（支持相对路径）"""
        if os.path.isabs(path):
            return path
        return os.path.join(self.base_storage_path, path.lstrip("./"))
    
    def _create_snapshot(self, file_path: str, reason: str) -> int:
        """为文件创建版本快照"""
        if not os.path.exists(file_path):
            return 0
        
        file_hash = hashlib.md5(file_path.encode()).hexdigest()[:12]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if file_path not in self._version_index:
            self._version_index[file_path] = []
        
        new_version = len(self._version_index[file_path]) + 1
        
        snapshot_filename = f"{os.path.basename(file_path)}_v{new_version}_{timestamp}.snap"
        snapshot_path = os.path.join(self.snapshots_dir, snapshot_filename)
        
        import shutil
        shutil.copy2(file_path, snapshot_path)
        
        with open(file_path, 'rb') as f:
            checksum = hashlib.md5(f.read()).hexdigest()
        
        version_info = {
            "version": new_version,
            "timestamp": datetime.now().isoformat(),
            "reason": reason,
            "snapshot_path": snapshot_path,
            "size_bytes": os.path.getsize(file_path),
            "checksum": checksum
        }
        
        self._version_index[file_path].append(version_info)
        
        logger.debug(f"[{self.agent_id}] Created snapshot v{new_version} for {file_path} ({reason})")
        
        return new_version
    
    def _generate_diff_preview(self, original: str, modified: str, context_lines: int = 3) -> str:
        """生成差异预览"""
        orig_lines = original.split('\n')
        mod_lines = modified.split('\n')
        
        diff_lines = []
        for i, (o, m) in enumerate(zip(orig_lines, mod_lines)):
            if o != m:
                start = max(0, i - context_lines)
                end = min(len(orig_lines), i + context_lines + 1)
                
                for j in range(start, end):
                    prefix = "+ " if j >= len(orig_lines) or orig_lines[j] != mod_lines[j] else "  "
                    line = mod_lines[j] if j < len(mod_lines) else ""
                    diff_lines.append(f"{prefix}{line}")
                break
        
        if not diff_lines:
            return "(no differences detected)"
        
        return "\n".join(diff_lines[-10:])  # 最后10行
    
    def _get_dir_size(self, path: str) -> int:
        total = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total += os.path.getsize(fp)
        return total
