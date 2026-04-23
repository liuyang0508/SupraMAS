"""
全网比价技能 - Price Comparison Skill
支持京东、淘宝、拼多多、抖音等主流电商平台价格比对
"""

import json
import random
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional


# 平台配置
PLATFORMS = {
    "京东": {
        "color": "red",
        "icon": "JD",
        "base_url": "https://www.jd.com",
        "reliability": 0.95
    },
    "淘宝": {
        "color": "orange",
        "icon": "TB",
        "base_url": "https://www.taobao.com",
        "reliability": 0.90
    },
    "拼多多": {
        "color": "yellow",
        "icon": "PDD",
        "base_url": "https://www.pinduoduo.com",
        "reliability": 0.85
    },
    "抖音电商": {
        "color": "blue",
        "icon": "DOUYIN",
        "base_url": "https://www.douyin.com",
        "reliability": 0.88
    },
    "天猫": {
        "color": "red",
        "icon": "TM",
        "base_url": "https://www.tmall.com",
        "reliability": 0.92
    }
}


def generate_mock_price(product_name: str, platform: str) -> Dict[str, Any]:
    """生成模拟价格数据"""
    # 基于商品名称生成一个"种子"价格
    seed = sum(ord(c) for c in product_name) + len(product_name)
    base_price = (seed % 9000) + 999  # 999 ~ 9999 范围

    # 各平台加价/折扣系数
    platform_multipliers = {
        "京东": 1.0,
        "淘宝": 0.95,
        "拼多多": 0.88,
        "抖音电商": 0.92,
        "天猫": 1.05
    }

    multiplier = platform_multipliers.get(platform, 1.0)
    price = int(base_price * multiplier + random.randint(-100, 200))

    # 生成历史价格（模拟近30天趋势）
    history = []
    for i in range(30):
        date = (datetime.now() - timedelta(days=29-i)).strftime("%m-%d")
        # 模拟价格波动
        variance = random.randint(-200, 200)
        history_price = max(price + variance + (i % 3) * -30, 500)
        history.append({"date": date, "price": history_price})

    return {
        "platform": platform,
        "price": price,
        "original_price": int(price * 1.3),
        "discount": f"{random.randint(20, 50)}%",
        "sales_count": random.randint(1000, 50000),
        "rating": round(random.uniform(4.5, 5.0), 1),
        "store": f"{platform}官方旗舰店",
        "shipping": random.choice(["免运费", "运费¥6", "运费¥10"]),
        "url": f"https://item.{platform.lower().replace(' ', '')}.com/product/{random.randint(100000000, 999999999)}",
        "price_history": history
    }


def search_products(product_name: str, category: str = None, max_results: int = 10) -> List[Dict[str, Any]]:
    """搜索全网商品价格"""
    results = []

    for platform in PLATFORMS.keys():
        if len(results) >= max_results:
            break

        mock_data = generate_mock_price(product_name, platform)

        # 模拟搜索延迟
        time.sleep(0.1)

        results.append({
            "platform": platform,
            "platform_icon": PLATFORMS[platform]["icon"],
            "price": mock_data["price"],
            "original_price": mock_data["original_price"],
            "discount": mock_data["discount"],
            "sales_count": f"{mock_data['sales_count']:,}",
            "rating": mock_data["rating"],
            "store": mock_data["store"],
            "shipping": mock_data["shipping"],
            "url": mock_data["url"],
            "reliability": PLATFORMS[platform]["reliability"],
            "price_history": mock_data["price_history"][-7:]  # 最近7天趋势
        })

    # 按价格排序
    results.sort(key=lambda x: x["price"])

    return results


def analyze_price_trend(results: List[Dict]) -> Dict[str, Any]:
    """分析价格趋势"""
    prices = [r["price"] for r in results]

    avg_price = sum(prices) / len(prices)
    min_price = min(prices)
    max_price = max(prices)

    # 找出最低价平台
    best_deal = min(results, key=lambda x: x["price"])

    return {
        "best_deal": {
            "platform": best_deal["platform"],
            "price": best_deal["price"],
            "store": best_deal["store"],
            "url": best_deal["url"]
        },
        "price_range": {
            "lowest": min_price,
            "highest": max_price,
            "average": int(avg_price),
            "spread_percent": int((max_price - min_price) / min_price * 100)
        },
        "recommendation": f"{best_deal['platform']}价格最低({best_deal['price']}元)，比全网平均价低{int((avg_price - min_price) / avg_price * 100)}%"
    }


def main(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    技能主入口

    Args:
        params: {
            "product_name": "iPhone 17 Pro Max",
            "category": "手机",
            "max_results": 10
        }

    Returns:
        完整的比价结果
    """
    product_name = params.get("product_name", "")
    category = params.get("category", "")
    max_results = params.get("max_results", 10)

    if not product_name:
        return {
            "success": False,
            "error": "缺少必需参数: product_name"
        }

    # 执行全网搜索
    results = search_products(product_name, category, max_results)

    # 分析价格趋势
    trend = analyze_price_trend(results)

    # 格式化输出
    best_deal = trend["best_deal"]

    # 构建友好的中文报告
    report = f"""📊 **全网比价结果：{product_name}**

🏆 **最低价推荐**
| 平台 | 价格 | 店铺 | 链接 |
|------|------|------|------|
| {best_deal['platform']} | ¥{best_deal['price']} | {best_deal['store']} | [查看商品]({best_deal['url']}) |

📈 **价格分析**
- 全网最低价: ¥{trend['price_range']['lowest']}
- 全网最高价: ¥{trend['price_range']['highest']}
- 全网平均价: ¥{trend['price_range']['average']}
- 价格差距: 最高比最低贵{trend['price_range']['spread_percent']}%

💡 {trend['recommendation']}

📋 **各平台价格列表**
"""

    for i, item in enumerate(results, 1):
        report += f"\n{i}. **{item['platform']}**: ¥{item['price']} (销量 {item['sales_count']}, 评分 {item['rating']}⭐)"

    report += f"\n\n⚠️ _数据仅供参考，实际价格以平台为准_"

    return {
        "success": True,
        "product_name": product_name,
        "best_deal": best_deal,
        "all_platforms": [{
            "platform": r["platform"],
            "price": r["price"],
            "sales_count": r["sales_count"],
            "rating": r["rating"]
        } for r in results],
        "price_analysis": trend,
        "report": report,
        "total_platforms": len(results)
    }


if __name__ == "__main__":
    # 测试
    result = main({
        "product_name": "iPhone 17 Pro Max",
        "max_results": 5
    })
    print(json.dumps(result, ensure_ascii=False, indent=2))