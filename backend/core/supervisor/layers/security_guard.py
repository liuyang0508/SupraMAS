"""
Layer 5: Security Guard - 安全审计与权限管控
负责：权限交集检查、数据脱敏、操作审计、威胁检测
"""

import re
import json
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..state import SecurityDecision

logger = logging.getLogger(__name__)


class SecurityGuard:
    """
    Layer 5: 安全守护者
    
    核心原则：权限交集 (Permission Intersection)
    AI的权限 = 用户权限 ∩ 请求发起者权限
    
    六层安全体系实现：
    1. 双层规则体系 - 基础安全底线 + 企业自定义规则
    2. 统一身份认证 - OAuth2/JWT验证
    3. 专属沙箱隔离 - 技能执行隔离
    4. Skill安全管控 - 上架前扫描 + 运行时策略评估
    5. 专属模型部署 - 敏感数据本地处理
    6. 网络代理防护 - 外网访问可追溯
    """
    
    SENSITIVE_PATTERNS = {
        "id_card": r"\d{17}[\dXx]",  # 身份证号
        "bank_card": r"\d{16,19}",    # 银行卡号
        "phone": r"1[3-9]\d{9}",      # 手机号
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "api_key": r"(?:sk-|api[_-]?key|token)[a-zA-Z0-9_-]{20,}",
        "password": r"(?:password|passwd|pwd)[:\s]+[^\s]{8,}"
    }
    
    DANGEROUS_OPERATIONS = [
        "delete_database",
        "drop_table",
        "format_disk",
        "rm_rf",
        "sudo",
        "eval_exec",
        "system_command"
    ]
    
    HIGH_RISK_AGENTS = ["mcp", "skill"]  # 需要额外审查的Agent类型
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enable_permission_intersection = config.get("enable_permission_intersection", True)
        self.enable_data_sanitization = config.get("enable_data_sanitization", True)
        self.enable_audit_logging = config.get("enable_audit_logging", True)
        
        self.audit_log: List[Dict] = []
    
    async def pre_check(
        self,
        action: Dict[str, Any],
        user_id: str,
        session_id: str,
        trace_id: str
    ) -> SecurityDecision:
        """
        执行前的安全预检
        
        Args:
            action: 操作描述 {agent_type, action, params}
            user_id: 用户ID
            session_id: 会话ID
            trace_id: 追踪ID
            
        Returns:
            SecurityDecision: 安全决策
        """
        agent_type = action.get("agent_type", "")
        action_name = action.get("action", "")
        params = action.get("params", {})
        
        risk_level = self._assess_risk_level(agent_type, action_name, params)
        
        # Step 1: 危险操作检测
        if self._is_dangerous_operation(action_name):
            return self._deny(action, user_id, trace_id, 
                             f"Dangerous operation detected: {action_name}", 
                             "high")
        
        # Step 2: 权限交集检查（核心机制）
        if self.enable_permission_intersection:
            permission_ok = await self._check_permission_intersection(user_id, agent_type, action_name)
            if not permission_ok:
                return self._deny(action, user_id, trace_id,
                                 "Insufficient permissions (intersection check failed)",
                                 "medium")
        
        # Step 3: 数据脱敏
        sanitized_action = action
        if self.enable_data_sanitization and params:
            sanitized_params = self._sanitize_sensitive_data(params)
            sanitized_action = {**action, "params": sanitized_params}
        
        # Step 4: 审计日志记录
        audit_entry = None
        if self.enable_audit_logging:
            audit_entry = await self._record_audit_log(
                action=sanitized_action,
                user_id=user_id,
                session_id=session_id,
                trace_id=trace_id,
                risk_level=risk_level,
                decision="approved"
            )
        
        return SecurityDecision(
            allowed=True,
            reason="Security check passed",
            risk_level=risk_level,
            required_approval=(risk_level == "critical"),
            sanitized_action=sanitized_action,
            audit_entry=audit_entry
        )
    
    def _assess_risk_level(self, agent_type: str, action: str, params: Dict) -> str:
        """评估操作风险等级"""
        risk_score = 0
        
        # Agent类型风险
        if agent_type in self.HIGH_RISK_AGENTS:
            risk_score += 3
        
        # 操作关键词风险
        dangerous_keywords = ["delete", "remove", "drop", "modify", "write", "exec"]
        for keyword in dangerous_keywords:
            if keyword in action.lower():
                risk_score += 2
        
        # 参数敏感度
        params_str = json.dumps(params, ensure_ascii=False)
        for pattern_name, pattern in self.SENSITIVE_PATTERNS.items():
            if re.search(pattern, params_str):
                risk_score += 2
        
        # 确定等级
        if risk_score >= 7:
            return "critical"
        elif risk_score >= 5:
            return "high"
        elif risk_score >= 3:
            return "medium"
        else:
            return "low"
    
    def _is_dangerous_operation(self, action: str) -> bool:
        """检测危险操作"""
        action_lower = action.lower()
        return any(dangerous in action_lower for dangerous in self.DANGEROUS_OPERATIONS)
    
    async def _check_permission_intersection(self, user_id: str, agent_type: str, action: str) -> bool:
        """
        权限交集检查
        
        原理：
        effective_permissions = user_permissions ∩ requester_permissions
        返回 effective_permissions 是否包含所需权限
        """
        # TODO: 从数据库/缓存获取实际权限
        # 模拟实现：假设所有已认证用户都有基础权限
        base_permissions = {"chat", "rag_query", "file_read"}
        
        agent_permissions = {
            "rag": {"rag_query", "rag_write"},
            "file": {"file_read", "file_write", "file_modify"},
            "skill": {"skill_execute"},
            "mcp": {"mcp_call", "external_api"},
            "intent": {"intent_recognize"}
        }
        
        required = agent_permissions.get(agent_type, set())
        has_permission = required.issubset(base_permissions)
        
        if not has_permission:
            logger.warning(f"[SecurityGuard] Permission denied for {agent_type}.{action}: need {required}")
        
        return has_permission
    
    def _sanitize_sensitive_data(self, data: Any) -> Any:
        """脱敏处理"""
        if isinstance(data, str):
            return self._sanitize_string(data)
        elif isinstance(data, dict):
            return {k: self._sanitize_sensitive_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_sensitive_data(item) for item in data]
        else:
            return data
    
    def _sanitize_string(self, text: str) -> str:
        """字符串脱敏"""
        sanitized = text
        
        for pattern_name, pattern in self.SENSITIVE_PATTERNS.items():
            def replace_match(m):
                value = m.group()
                if len(value) > 6:
                    return value[:3] + "*" * (len(value) - 6) + value[-3:]
                return "*" * len(value)
            
            sanitized = re.sub(pattern, replace_match, sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    async def _record_audit_log(
        self,
        action: Dict,
        user_id: str,
        session_id: str,
        trace_id: str,
        risk_level: str,
        decision: str
    ) -> Dict:
        """记录审计日志"""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "trace_id": trace_id,
            "user_id": user_id,
            "session_id": session_id,
            "agent_type": action.get("agent_type"),
            "action": action.get("action"),
            "action_params_hash": hash(json.dumps(action.get("params", {}), sort_keys=True)),
            "risk_level": risk_level,
            "decision": decision,
            "ip_address": "",  # TODO: 从请求上下文获取
            "user_agent": ""
        }
        
        self.audit_log.append(entry)
        
        # 保持日志大小（实际应写入持久化存储）
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-5000:]
        
        logger.debug(f"[SecurityGuard] Audit log recorded: {entry['trace_id']} - {entry['decision']}")
        
        return entry
    
    def _deny(
        self,
        action: Dict,
        user_id: str,
        trace_id: str,
        reason: str,
        risk_level: str
    ) -> SecurityDecision:
        """生成拒绝决策"""
        audit_entry = None
        if self.enable_audit_logging:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(self._record_audit_log(
                        action, user_id, "", trace_id, risk_level, "denied"
                    ))
            except:
                pass
        
        return SecurityDecision(
            allowed=False,
            reason=reason,
            risk_level=risk_level,
            audit_entry={"reason": reason}
        )
    
    def get_audit_logs(self, limit: int = 100) -> List[Dict]:
        """获取审计日志"""
        return self.audit_log[-limit:]
