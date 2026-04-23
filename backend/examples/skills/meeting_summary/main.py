"""
会议纪要生成技能
将会议内容整理成结构化纪要，包含待办、决策、关键点
"""

import json
from typing import Dict, Any, List
from datetime import datetime


def parse_meeting_content(content: str) -> Dict[str, Any]:
    """解析会议内容，提取关键信息"""
    lines = content.split('\n')
    decisions = []
    action_items = []
    key_points = []

    keywords_decision = ['决定', '结论', '通过', '确认', '同意', '批准', '通过']
    keywords_action = ['待办', '行动', 'TODO', '负责人', '完成时间', '截止', '跟进']
    keywords_point = ['讨论', '提到', '认为', '分析', '观点', '建议']

    for line in lines:
        line = line.strip()
        if any(k in line for k in keywords_decision) and line:
            decisions.append(line)
        if any(k in line for k in keywords_action) and line:
            action_items.append(line)
        if any(k in line for k in keywords_point) and line:
            key_points.append(line)

    if not decisions:
        decisions = ["所有议题经讨论达成初步共识", "后续跟进落实"]
    if not action_items:
        action_items = ["会后整理纪要并发给全体参会人", "下次会议确认执行进展"]
    if not key_points:
        key_points = [content[:200] + "..." if len(content) > 200 else content]

    return decisions, action_items, key_points


def main(params: Dict[str, Any]) -> Dict[str, Any]:
    meeting_title = params.get("meeting_title", "未命名会议")
    meeting_date = params.get("meeting_date", datetime.now().strftime("%Y-%m-%d"))
    participants = params.get("participants", [])
    content = params.get("content", "")

    if not content:
        content = "用户提供的主题会议，无详细记录。根据主题自动生成纪要框架。"
        decisions, action_items, key_points = parse_meeting_content(content)
    else:
        decisions, action_items, key_points = parse_meeting_content(content)

    summary = f"""📋 **会议纪要**

**会议标题**: {meeting_title}
**会议日期**: {meeting_date}
**参会人员**: {', '.join(participants) if participants else '未记录'}

---

### 📌 决策事项

"""
    for i, d in enumerate(decisions, 1):
        summary += f"{i}. {d}\n"

    summary += """
---

### ✅ 待办事项（行动项）

"""
    for i, a in enumerate(action_items, 1):
        summary += f"{i}. {a}\n"

    summary += """
---

### 💡 关键讨论点

"""
    for i, p in enumerate(key_points, 1):
        summary += f"- {p}\n"

    summary += f"""
---

*纪要生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*"""

    return {
        "success": True,
        "summary": summary,
        "decisions": decisions,
        "action_items": action_items,
        "key_points": key_points,
        "meeting_title": meeting_title,
        "meeting_date": meeting_date,
        "participants_count": len(participants)
    }


if __name__ == "__main__":
    result = main({
        "meeting_title": "Q2产品规划会议",
        "meeting_date": "2026-04-23",
        "participants": ["张三", "李四", "王五"],
        "content": """
讨论了Q2产品规划方向，决定在5月底完成新功能开发。
张三分管设计，6月前提交UI稿。李四负责技术实现。
建议增加用户调研环节，待确认后执行。
下次会议定于4月30日。
        """
    })
    print(json.dumps(result, ensure_ascii=False, indent=2))