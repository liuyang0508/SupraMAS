"""
代码审查技能
检查代码安全、规范和潜在问题
"""

import json
import re
from typing import Dict, Any, List, Tuple


# 安全检查模式
SECURITY_PATTERNS = [
    (r'eval\s*\(', 'HIGH', 'eval() 执行动态代码，可能导致代码注入'),
    (r'exec\s*\(', 'HIGH', 'exec() 执行动态代码，可能导致代码注入'),
    (r'SQL', 'HIGH', 'SQL查询注意使用参数化查询防止注入'),
    (r'subprocess\.', 'MEDIUM', 'subprocess调用注意命令注入风险'),
    (r'os\.system', 'MEDIUM', 'os.system调用存在命令注入风险'),
    (r'password\s*=', 'MEDIUM', '硬编码密码泄露风险'),
    (r'api[_-]?key\s*=', 'HIGH', '硬编码API密钥泄露风险'),
    (r'secret\s*=', 'HIGH', '硬编码密钥泄露风险'),
    (r'HTTP.*password', 'HIGH', 'HTTP请求中明文传输密码'),
    (r'\.env', 'MEDIUM', '注意.env文件不要提交到代码库'),
]

# 最佳实践检查
BEST_PRACTICES = [
    (r'TODO', 'INFO', '存在未完成的TODO注释'),
    (r'print\s*\(', 'INFO', '存在调试用的print语句'),
    (r'except\s*:\s*pass', 'MEDIUM', '空的异常处理会隐藏错误'),
    (r'import\s+\*', 'LOW', '避免使用 from x import *'),
    (r'global\s+', 'MEDIUM', '使用全局变量可能导致意外副作用'),
]


def analyze_python(code: str) -> Tuple[List[Dict], int]:
    """分析Python代码"""
    issues = []
    line_count = len(code.split('\n'))

    for pattern, severity, message in SECURITY_PATTERNS:
        matches = re.finditer(pattern, code, re.IGNORECASE)
        for match in matches:
            line_num = code[:match.start()].count('\n') + 1
            issues.append({
                "type": "security",
                "severity": severity,
                "message": message,
                "line": line_num,
                "snippet": code.split('\n')[line_num - 1].strip()[:80]
            })

    for pattern, severity, message in BEST_PRACTICES:
        matches = re.finditer(pattern, code, re.IGNORECASE)
        for match in matches:
            line_num = code[:match.start()].count('\n') + 1
            issues.append({
                "type": "best_practice",
                "severity": severity,
                "message": message,
                "line": line_num,
                "snippet": code.split('\n')[line_num - 1].strip()[:80]
            })

    # 代码复杂度检查
    if line_count > 500:
        issues.append({
            "type": "structure",
            "severity": "INFO",
            "message": f"代码行数{line_count}，建议拆分为更小的模块",
            "line": 1
        })

    # 计算评分
    if issues:
        severity_weights = {"HIGH": 30, "MEDIUM": 15, "LOW": 5, "INFO": 2}
        deducted = sum(severity_weights.get(i["severity"], 10) for i in issues)
        score = max(0, 100 - deducted)
    else:
        score = 100

    return issues, score


def generate_suggestions(issues: List[Dict]) -> List[str]:
    """生成改进建议"""
    suggestions = []

    high_count = sum(1 for i in issues if i["severity"] == "HIGH")
    if high_count > 0:
        suggestions.append(f"⚠️ 发现 {high_count} 个高危问题，建议优先修复")

    security_issues = [i for i in issues if i["type"] == "security"]
    if security_issues:
        suggestions.append("🔒 安全建议：使用参数化查询，避免eval/exec，密钥不要硬编码")

    best_practice_issues = [i for i in issues if i["type"] == "best_practice"]
    if best_practice_issues:
        suggestions.append("📝 规范建议：清理TODO注释和调试print，改进异常处理")

    if not issues:
        suggestions.append("✅ 代码质量良好，未发现明显问题")

    return suggestions


def main(params: Dict[str, Any]) -> Dict[str, Any]:
    code = params.get("code", "")
    language = params.get("language", "python")
    check_types = params.get("check_types", ["security", "best_practices"])

    if not code:
        return {"success": False, "error": "缺少必需参数: code"}

    issues, score = analyze_python(code)
    suggestions = generate_suggestions(issues)

    report = f"""## 🔍 代码审查报告

**代码语言**: {language.upper()}
**代码行数**: {len(code.split(chr(10)))}
**质量评分**: {score}/100

---

### {'🚨 高危问题' if any(i['severity'] == 'HIGH' for i in issues) else '✅ 未发现高危问题'}

"""

    for i, issue in enumerate([x for x in issues if x["severity"] == "HIGH"], 1):
        report += f"**{i}. [{issue['severity']}] Line {issue['line']}**\n"
        report += f"- {issue['message']}\n"
        report += f"- 代码: `{issue['snippet']}`\n\n"

    report += "### 📋 其他问题\n\n"

    medium_issues = [x for x in issues if x["severity"] == "MEDIUM"]
    if medium_issues:
        for i, issue in enumerate(medium_issues, 1):
            report += f"- [{issue['severity']}] L{issue['line']}: {issue['message']}\n"

    low_issues = [x for x in issues if x["severity"] in ["LOW", "INFO"]]
    if low_issues:
        report += f"\n*另有 {len(low_issues)} 个低优先级问题*\n"

    report += "\n---\n\n### 💡 改进建议\n\n"
    for s in suggestions:
        report += f"- {s}\n"

    return {
        "success": True,
        "report": report,
        "issues": issues,
        "score": score,
        "suggestions": suggestions,
        "issue_count": len(issues),
        "high_count": sum(1 for i in issues if i["severity"] == "HIGH"),
        "medium_count": sum(1 for i in issues if i["severity"] == "MEDIUM")
    }


if __name__ == "__main__":
    result = main({
        "code": """
import os
import eval

def get_password():
    password = "hardcoded_password_123"
    return password

def query(sql):
    exec(sql)
    pass
""",
        "language": "python"
    })
    print(json.dumps(result, ensure_ascii=False, indent=2))