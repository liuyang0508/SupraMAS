"""
数据分析报告生成技能
分析数据并生成结构化报告，包含趋势、对比、异常检测
"""

import json
import random
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict


def calculate_metrics(data: List[Dict], dimensions: List[str]) -> Dict[str, Any]:
    """计算关键指标"""
    if not data:
        return {}

    numeric_cols = []
    if data and isinstance(data[0], dict):
        sample = data[0]
        numeric_cols = [k for k, v in sample.items() if isinstance(v, (int, float))]

    metrics = {
        "total_records": len(data),
        "numeric_columns": numeric_cols,
        "avg_values": {},
        "min_values": {},
        "max_values": {}
    }

    for col in numeric_cols:
        values = [d.get(col, 0) for d in data if isinstance(d.get(col), (int, float))]
        if values:
            metrics["avg_values"][col] = round(sum(values) / len(values), 2)
            metrics["min_values"][col] = min(values)
            metrics["max_values"][col] = max(values)

    return metrics


def detect_trends(data: List[Dict], value_col: str) -> Dict[str, Any]:
    """检测趋势"""
    if not data or value_col not in data[0]:
        return {}

    values = [d.get(value_col, 0) for d in data if value_col in d]
    if len(values) < 2:
        return {}

    # 计算变化率
    changes = [(values[i] - values[i-1]) / max(values[i-1], 1) * 100
              for i in range(1, len(values))]

    avg_change = sum(changes) / len(changes) if changes else 0

    # 检测异常点
    mean = sum(values) / len(values)
    std = (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5
    anomalies = [i for i, v in enumerate(values) if abs(v - mean) > 2 * std]

    return {
        "start_value": values[0],
        "end_value": values[-1],
        "total_change_pct": round((values[-1] - values[0]) / max(values[0], 1) * 100, 2),
        "avg_change_rate": round(avg_change, 2),
        "trend_direction": "up" if values[-1] > values[0] else "down",
        "anomaly_indices": anomalies
    }


def generate_insights(metrics: Dict, trends: Dict) -> List[str]:
    """生成业务洞察"""
    insights = []

    if trends.get("trend_direction") == "up":
        insights.append(f"📈 指标呈上升趋势，较初始增长 {trends.get('total_change_pct', 0)}%")
    elif trends.get("trend_direction") == "down":
        insights.append(f"📉 指标呈下降趋势，较初始下降 {abs(trends.get('total_change_pct', 0))}%")

    if trends.get("anomaly_indices"):
        insights.append(f"⚠️ 检测到 {len(trends['anomaly_indices'])} 个异常数据点")

    if metrics.get("avg_values"):
        top_metric = max(metrics["avg_values"].items(), key=lambda x: x[1])
        insights.append(f"💡 平均值最高的指标: {top_metric[0]} = {top_metric[1]}")

    return insights


def main(params: Dict[str, Any]) -> Dict[str, Any]:
    data = params.get("data", [])
    report_type = params.get("report_type", "summary")
    dimensions = params.get("dimensions", [])

    if not data:
        return {"success": False, "error": "缺少必需参数: data"}

    metrics = calculate_metrics(data, dimensions)

    # 找到第一个数值列作为主要分析列
    value_col = None
    if data and isinstance(data[0], dict):
        for k, v in data[0].items():
            if isinstance(v, (int, float)):
                value_col = k
                break

    trends = detect_trends(data, value_col) if value_col else {}
    insights = generate_insights(metrics, trends)

    # 生成报告
    report = f"""## 📊 数据分析报告

**报告类型**: {report_type.upper()}
**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**数据记录数**: {metrics.get('total_records', 0)}

---

### 📈 关键指标

| 指标 | 平均值 | 最小值 | 最大值 |
|------|--------|--------|--------|
"""

    for col in metrics.get("numeric_columns", []):
        avg = metrics["avg_values"].get(col, 0)
        min_val = metrics["min_values"].get(col, 0)
        max_val = metrics["max_values"].get(col, 0)
        report += f"| {col} | {avg} | {min_val} | {max_val} |\n"

    if trends:
        report += f"""
---

### 📉 趋势分析

- **趋势方向**: {'上涨 📈' if trends['trend_direction'] == 'up' else '下跌 📉'}
- **总变化率**: {trends.get('total_change_pct', 0)}%
- **平均变化率**: {trends.get('avg_change_rate', 0)}%/期

"""
        if trends.get("anomaly_indices"):
            report += f"- ⚠️ 异常数据点索引: {trends['anomaly_indices']}\n"

    if insights:
        report += "\n---\n\n### 💡 业务洞察\n\n"
        for insight in insights:
            report += f"- {insight}\n"

    report += "\n---\n\n*报告由 AI 自动生成*"

    return {
        "success": True,
        "report": report,
        "metrics": metrics,
        "trends": trends,
        "insights": insights,
        "record_count": len(data)
    }


if __name__ == "__main__":
    # 测试数据
    test_data = [
        {"date": "2026-04-17", "sales": 12000, "visitors": 500},
        {"date": "2026-04-18", "sales": 15000, "visitors": 620},
        {"date": "2026-04-19", "sales": 13500, "visitors": 580},
        {"date": "2026-04-20", "sales": 18000, "visitors": 750},
        {"date": "2026-04-21", "sales": 22000, "visitors": 900},
        {"date": "2026-04-22", "sales": 19500, "visitors": 820},
        {"date": "2026-04-23", "sales": 25000, "visitors": 1000},
    ]

    result = main({
        "data": test_data,
        "report_type": "trend",
        "dimensions": ["sales", "visitors"]
    })
    print(json.dumps(result, ensure_ascii=False, indent=2))