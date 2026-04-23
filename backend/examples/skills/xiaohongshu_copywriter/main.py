"""
小红书文案生成技能
生成小红书风格的种草文案，爆款语法高互动
"""

import json
import random
from typing import Dict, Any, List


EMOJIS = ['✨', '💫', '🔥', '💕', '🌟', '👍', '📌', '💯', '🙋', '👀', '🤩', '😱', '💗']
POUND_KEYWORDS = ['必买', '宝藏', '好物', '神器', '绝了', '超A', '少女心', '高级感', '氛围感', '炸裂']


def generate_title(product_name: str, copy_type: str) -> str:
    """生成爆款标题"""
    templates = [
        f"姐妹们！{product_name}真的绝了！",
        f"救命🆘 {product_name}给我冲！",
        f"被问爆的{product_name}，真的太好用了！",
        f"✨{product_name}✨这个价位居然能买到！",
        f"私藏已久！{product_name}清单分享",
        f"不是我说，{product_name}也太香了吧",
        f"挑战全网最{product_name}！真的绝",
        f"答应我！{product_name}一定要试试",
        f"后悔没早点买{product_name}",
        f"谁懂啊家人们，{product_name}绝了"
    ]
    return random.choice(templates)


def generate_tags(product_name: str, keywords: List[str]) -> List[str]:
    """生成标签"""
    base_tags = ["好物分享", "种草", "购物分享", "护肤", "美妆"]
    if keywords:
        base_tags.extend(keywords[:3])
    base_tags.append(product_name)
    return list(set(base_tags))[:10]


def generate_body(product_name: str, copy_type: str, target_audience: str) -> str:
    """生成正文内容"""
    if copy_type == "review":
        body = f"""姐妹们！今天来聊聊最近挖到的宝藏——{product_name}！

✅ 先说结论：真的好用！已经回购了三次那种

【为什么买】
最近刷到好多人在推，实在忍不住入手了
结果真香了！完全超出预期

【使用感受】
1. 效果真的绝 肉眼可见的变化
2. 质地很舒服 不会黏黏的
3. 包装也很好看 摆梳妆台超治愈

💰 性价比绝了！这个价格能买到这种品质的真的不多

👭 适合人群：{target_audience or '想尝试的姐妹都可以冲'}

⏰ 使用频率：每天早晚都用，已经离不开啦

姐妹们冲！不好用来打我！"""
    elif copy_type == "discovery":
        body = f"""📍 探店 | {product_name}

刚去完！真的超预期！

🏠 环境：装修很有氛围感，拍照超出片
👅 味道：{random.choice(['绝了', '很惊喜', '完全不踩雷'])}
📸 拍照：随便拍都好看，已经发了朋友圈

💰 消费：人均{random.randint(50, 200)}，{random.choice(['性价比超高', '稍贵但值得', '对学生党友好'])}

⭐ 总结：{random.choice(['会再来', '已经推荐给朋友了', '列入常去清单'])}

姐妹们有机会一定要去试试！"""
    else:
        body = f"""✨{product_name} | 我的日常分享

Hi 大家好～今天来聊聊最近在用的{product_name}

🌿 使用场景：
{random.choice(['日常通勤', '约会必备', '宅家神器', '旅行携带'])}

💡 亮点：
• {random.choice(['颜值超高', '效果肉眼可见', '使用感超棒', '性价比绝了'])}
• {random.choice(['方便携带', '超级耐用', '回购三次了', '真的离不开'])}

📝 个人感受：
整体用下来非常满意！{random.choice(['已经推荐给闺蜜了', '准备再囤一波', '列入年度爱用物'])}

👍 推荐指数：⭐⭐⭐⭐⭐

以上就是今天的分享啦，有问题评论区见～"""
    return body


def main(params: Dict[str, Any]) -> Dict[str, Any]:
    product_name = params.get("product_name", "")
    copy_type = params.get("copy_type", "review")
    target_audience = params.get("target_audience", "")
    keywords = params.get("keywords", [])

    if not product_name:
        return {"success": False, "error": "缺少必需参数: product_name"}

    title = generate_title(product_name, copy_type)
    body = generate_body(product_name, copy_type, target_audience)
    tags = generate_tags(product_name, keywords)

    content = f"""{title}

{body}

🏷️ {' '.join(['#' + t for t in tags])}

💬 评论区留言告诉我你们的想法！"""

    return {
        "success": True,
        "title": title,
        "content": content,
        "tags": tags,
        "word_count": len(content),
        "copy_type": copy_type
    }


if __name__ == "__main__":
    result = main({
        "product_name": "某品牌精华液",
        "copy_type": "review",
        "target_audience": "25-35岁都市女性"
    })
    print(json.dumps(result, ensure_ascii=False, indent=2))