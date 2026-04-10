#!/usr/bin/env python3
"""
AI 每日资讯推送
每天早上6点自动抓取 AI 前沿资讯，筛选 5-10 条最重要的推送到微信
"""

import os
import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re
from zhipuai import ZhipuAI

# ============== 配置 ==============
# 从环境变量读取敏感信息
WXPUSHER_TOKEN = os.getenv("WXPUSHER_TOKEN")
WXPUSHER_UID = os.getenv("WXPUSHER_UID")
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY")

# RSS 数据源 - 各大 AI 公司官方博客
RSS_SOURCES = {
    "OpenAI": "https://openai.com/blog/rss.xml",
    "Google AI": "https://ai.googleblog.com/rss.xml",
    "Google DeepMind": "https://deepmind.google/discover/feed/",
    "Microsoft Research": "https://msresearchblog.blob.core.windows.net/blog/rss.xml",
    "Meta AI": "https://ai.meta.com/blog/rss/",
    "Anthropic": "https://www.anthropic.com/index/rss",
    "NVIDIA Blog": "https://feeds.feedburner.com/nvidia_news",
    "MIT AI": "https://www.technologyreview.com/topnews.rss?section=artificial-intelligence",
}

# 推送配置
MAX_ARTICLES = 10  # 最多推送几条
TIMEZONE = "Asia/Shanghai"


class NewsFetcher:
    """资讯抓取器"""

    def __init__(self):
        self.entries = []

    def fetch_from_rss(self) -> List[Dict]:
        """从所有 RSS 源抓取资讯"""
        all_entries = []
        seen_urls = set()

        for source_name, rss_url in RSS_SOURCES.items():
            try:
                print(f"正在抓取 {source_name}...")
                feed = feedparser.parse(rss_url)

                for entry in feed.entries[:10]:  # 每个源取最新10条
                    url = entry.get('link', '')

                    # 去重
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)

                    # 获取发布时间
                    published = entry.get('published_parsed')
                    if published:
                        pub_date = datetime(*published[:6])
                        # 只取最近 48 小时的资讯
                        if datetime.now() - pub_date > timedelta(hours=48):
                            continue

                    all_entries.append({
                        'source': source_name,
                        'title': entry.get('title', ''),
                        'url': url,
                        'summary': entry.get('summary', entry.get('description', '')),
                        'published': published
                    })

                print(f"  ✓ {source_name} 抓取成功")

            except Exception as e:
                print(f"  ✗ {source_name} 抓取失败: {e}")

        print(f"\n共抓取到 {len(all_entries)} 条资讯")
        return all_entries


class NewsSelector:
    """资讯筛选器 - 使用 AI 筛选最重要的资讯"""

    def __init__(self, api_key: str):
        self.client = ZhipuAI(api_key=api_key)

    def select_articles(self, articles: List[Dict]) -> List[Dict]:
        """使用 AI 筛选出最重要、最前沿的资讯"""
        if not articles:
            return []

        print("\n使用 AI 筛选资讯...")

        # 准备输入
        articles_text = "\n".join([
            f"{i+1}. [{a['source']}] {a['title']}\n   摘要: {a['summary'][:200]}..."
            for i, a in enumerate(articles[:30])
        ])

        prompt = f"""你是一个 AI 资讯编辑。请从以下资讯中筛选出 {MAX_ARTICLES} 条**最重要、最前沿**的 AI 资讯。

筛选标准：
1. 重大技术突破、模型发布、产品更新
2. 来自顶级公司（OpenAI、Google、Microsoft、Meta、Anthropic 等）
3. 具有行业影响力
4. 不选普通的教程、课程推广等

请将资讯分类到：
- 📈 前沿动态（技术突破、模型发布）
- 🎓 AI 教育（课程、资源、学习材料）
- 🎨 AI 设计（设计工具、创意应用）

资讯列表：
{articles_text}

请以 JSON 格式输出，包含 selected 数组，每个元素有：
- index: 原资讯序号（从1开始）
- category: 分类（前沿动态/AI教育/AI设计）

输出格式：
{{"selected": [{{"index": 1, "category": "前沿动态"}}, ...]}}

只输出 JSON，不要其他内容。"""

        try:
            response = self.client.chat.completions.create(
                model="glm-4-flash",
                messages=[
                    {"role": "system", "content": "你是一个专业的 AI 资讯编辑，擅长筛选和分类科技新闻。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
            )

            result = response.choices[0].message.content.strip()

            # 清理可能的 markdown 标记
            result = re.sub(r'```json\s*', '', result)
            result = re.sub(r'```\s*', '', result)

            print(f"AI 响应: {result[:200]}...")

            import json
            selection = json.loads(result)

            # 根据筛选结果重新组织资讯
            selected_articles = []
            for item in selection.get('selected', []):
                idx = item['index'] - 1
                if 0 <= idx < len(articles):
                    articles[idx]['category'] = item['category']
                    selected_articles.append(articles[idx])

            print(f"✓ AI 筛选出 {len(selected_articles)} 条资讯")
            return selected_articles

        except Exception as e:
            print(f"✗ AI 筛选失败: {e}")
            # 失败时返回前几条
            return articles[:MAX_ARTICLES]


class NewsTranslator:
    """资讯翻译器 - 将资讯翻译成中文"""

    def __init__(self, api_key: str):
        self.client = ZhipuAI(api_key=api_key)

    def translate_summary(self, article: Dict) -> str:
        """翻译并生成中文摘要"""
        title = article['title']
        summary = article['summary'][:500]

        prompt = f"""请将以下资讯翻译成中文，并生成一句话摘要。

标题: {title}

内容: {summary}

要求：
1. 标题翻译准确
2. 生成 30-50 字的中文摘要
3. 输出格式：
   标题：[中文标题]
   摘要：[中文摘要]

只输出标题和摘要，不要其他内容。"""

        try:
            response = self.client.chat.completions.create(
                model="glm-4-flash",
                messages=[
                    {"role": "system", "content": "你是一个专业的科技翻译。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"翻译失败: {e}")
            return f"标题：{title}\n摘要：{summary[:100]}..."


class WxPusherClient:
    """WxPusher 推送客户端"""

    def __init__(self, token: str, uid: str):
        self.token = token
        self.uid = uid
        self.api_url = "https://wxpusher.zjiecode.com/api/send/message"

    def send(self, content: str) -> bool:
        """发送消息到微信"""
        payload = {
            "appToken": self.token,
            "content": content,
            "summary": f"AI每日资讯 {datetime.now().strftime('%Y-%m-%d')}",
            "contentType": 3,  # 3 表示 Markdown
            "uids": [self.uid],
            "url": ""
        }

        try:
            response = requests.post(self.api_url, json=payload, timeout=30)
            result = response.json()

            if result.get('success'):
                print("✓ 推送成功！")
                return True
            else:
                print(f"✗ 推送失败: {result}")
                return False

        except Exception as e:
            print(f"✗ 推送异常: {e}")
            return False


def format_message(articles: List[Dict]) -> str:
    """格式化推送消息"""
    date_str = datetime.now().strftime('%Y年%m月%d日')
    weekday = ['一', '二', '三', '四', '五', '六', '日'][datetime.now().weekday()]

    message = f"""# 📅 {date_str} 星期{weekday} AI 资讯

---

"""

    # 按分类整理
    categories = {
        '前沿动态': [],
        'AI教育': [],
        'AI设计': []
    }

    for article in articles:
        cat = article.get('category', '前沿动态')
        if cat not in categories:
            cat = '前沿动态'
        categories[cat].append(article)

    # 输出各分类
    icons = {'前沿动态': '📈', 'AI教育': '🎓', 'AI设计': '🎨'}

    for cat, icon in icons.items():
        if categories[cat]:
            message += f"\n## {icon} {cat}\n\n"
            for article in categories[cat]:
                # 如果有翻译结果用翻译，否则用原文
                if 'translated' in article:
                    message += f"**{article['translated']}**\n\n"
                else:
                    message += f"**{article['title']}**\n\n"
                message += f"[查看原文]({article['url']})\n\n"
                message += f"来源：{article['source']}\n\n"
                message += "---\n\n"

    message += f"\n*由 AI 每日资讯自动生成*"

    return message


def main():
    """主函数"""
    print("=" * 50)
    print("AI 每日资讯推送")
    print("=" * 50)

    # 检查环境变量
    if not all([WXPUSHER_TOKEN, WXPUSHER_UID, ZHIPU_API_KEY]):
        print("错误：请设置环境变量 WXPUSHER_TOKEN、WXPUSHER_UID 和 ZHIPU_API_KEY")
        return

    try:
        # 1. 抓取资讯
        fetcher = NewsFetcher()
        articles = fetcher.fetch_from_rss()

        if not articles:
            print("没有抓取到资讯")
            return

        # 2. AI 筛选
        selector = NewsSelector(ZHIPU_API_KEY)
        selected = selector.select_articles(articles)

        if not selected:
            print("没有筛选出资讯")
            return

        # 3. 翻译摘要（可选，为了节省 API 调用可以跳过）
        print("\n翻译资讯摘要...")
        translator = NewsTranslator(ZHIPU_API_KEY)
        for article in selected:
            translated = translator.translate_summary(article)
            article['translated'] = translated

        # 4. 格式化消息
        message = format_message(selected)
        print("\n" + "=" * 50)
        print("推送内容预览：")
        print("=" * 50)
        print(message[:500] + "...")
        print("=" * 50)

        # 5. 推送到微信
        print("\n开始推送...")
        wxpusher = WxPusherClient(WXPUSHER_TOKEN, WXPUSHER_UID)
        wxpusher.send(message)

    except Exception as e:
        print(f"程序异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
