#!/usr/bin/env python3
"""
AI 每日内参
每天早上6点自动抓取 AI 前沿资讯，生成内参风格的深度分析报告
"""

import os
import feedparser
import requests
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
import re
import json
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

# 关注的行业
FOCUS_INDUSTRIES = ["教育", "创意设计", "心理学"]

# 推送配置
MAX_ARTICLES = 5  # 每天分析 5 条重大新闻
TIMEZONE = "Asia/Shanghai"


class NewsFetcher:
    """资讯抓取器"""

    def __init__(self):
        self.entries = []

    def fetch_from_rss(self, days_back: int = 2) -> List[Dict]:
        """从所有 RSS 源抓取资讯"""
        all_entries = []
        seen_urls = set()

        for source_name, rss_url in RSS_SOURCES.items():
            try:
                print(f"正在抓取 {source_name}...")
                feed = feedparser.parse(rss_url)

                for entry in feed.entries[:15]:
                    url = entry.get('link', '')

                    # 去重
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)

                    # 获取发布时间
                    published = entry.get('published_parsed')
                    if published:
                        pub_date = datetime(*published[:6])
                        # 只取最近 N 天的资讯
                        if datetime.now() - pub_date > timedelta(days=days_back):
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


class NewsAnalyzer:
    """AI 资讯深度分析器"""

    def __init__(self, api_key: str):
        self.client = ZhipuAI(api_key=api_key)

    def analyze_news(self, article: Dict) -> Dict:
        """对单条新闻进行深度分析"""
        title = article['title']
        summary = article.get('summary', '')[:800]
        source = article['source']
        url = article['url']

        prompt = f"""你是一位资深 AI 行业分析师，负责撰写 AI 领域的内参报告。请对以下新闻进行深度分析。

【新闻标题】
{title}

【新闻来源】
{source}

【新闻内容】
{summary}

【新闻链接】
{url}

请从以下维度进行分析，输出格式严格按要求：

一、新闻阐述
用200-300字客观阐述这条新闻的核心内容、技术细节和关键信息。

二、深度思考
从以下三个行业视角进行分析，每个行业100-150字：
1. 教育：这对教育领域意味着什么？教学方式、学习体验会有什么变化？
2. 创意设计：这对创意设计行业有什么影响？设计师的工作方式会如何改变？
3. 心理学：从心理学角度，这对人的认知、情感、社交行为有什么深层影响？

三、底层逻辑串联
分析这条新闻与 AI 发展的底层逻辑关系，以及它代表的行业趋势方向（100-150字）。

请按照上述格式输出，不要添加其他内容。注意保持正式、专业的内参风格。"""

        try:
            print(f"  正在分析: {title[:30]}...")
            response = self.client.chat.completions.create(
                model="glm-4-flash",
                messages=[
                    {"role": "system", "content": "你是一位资深 AI 行业分析师，擅长撰写深度内参报告。你的分析专业、深入、具有前瞻性。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
            )

            result = response.choices[0].message.content.strip()

            return {
                'title': title,
                'source': source,
                'url': url,
                'summary': summary,
                'analysis': result
            }

        except Exception as e:
            print(f"  ✗ 分析失败: {e}")
            return {
                'title': title,
                'source': source,
                'url': url,
                'summary': summary,
                'analysis': f"[分析失败: {str(e)}]"
            }


class NewsSelector:
    """重大新闻筛选器"""

    def __init__(self, api_key: str):
        self.client = ZhipuAI(api_key=api_key)

    def select_major_news(self, articles: List[Dict]) -> List[Dict]:
        """筛选出最重要的重大新闻"""
        if not articles:
            return []

        print("\n筛选重大新闻...")

        # 准备输入
        articles_text = "\n".join([
            f"{i+1}. [{a['source']}] {a['title']}\n   {a['summary'][:150]}..."
            for i, a in enumerate(articles[:40])
        ])

        prompt = f"""你是一位 AI 行业主编。请从以下资讯中筛选出 {MAX_ARTICLES} 条**最重要的重大新闻**。

筛选标准（优先级从高到低）：
1. 重大技术突破（新模型发布、能力大幅提升）
2. 行业里程碑事件（重要收购、战略合作、产品发布）
3. 政策法规重大变化
4. 对教育、创意设计、心理学有深远影响的事件

排除标准：
- 普通的产品更新
- 课程推广、活动宣传
- 琐碎的功能改进

资讯列表：
{articles_text}

请以 JSON 格式输出，包含 selected 数组，每个元素有：
- index: 原资讯序号（从1开始）
- reason: 选择理由（20字以内）

输出格式：
{{"selected": [{{"index": 1, "reason": "GPT-5发布意义重大"}}, ...]}}

只输出 JSON，不要其他内容。"""

        try:
            response = self.client.chat.completions.create(
                model="glm-4-flash",
                messages=[
                    {"role": "system", "content": "你是一位经验丰富的科技新闻主编。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
            )

            result = response.choices[0].message.content.strip()

            # 清理可能的 markdown 标记
            result = re.sub(r'```json\s*', '', result)
            result = re.sub(r'```\s*', '', result)

            print(f"筛选结果: {result[:200]}...")

            selection = json.loads(result)

            # 根据筛选结果重新组织资讯
            selected_articles = []
            for item in selection.get('selected', []):
                idx = item['index'] - 1
                if 0 <= idx < len(articles):
                    articles[idx]['reason'] = item.get('reason', '')
                    selected_articles.append(articles[idx])

            print(f"✓ 筛选出 {len(selected_articles)} 条重大新闻")
            for i, art in enumerate(selected_articles, 1):
                print(f"  {i}. {art['title'][:40]}... ({art.get('reason', '')})")

            return selected_articles

        except Exception as e:
            print(f"✗ 筛选失败: {e}")
            # 失败时返回前几条
            return articles[:MAX_ARTICLES]


class IndustryConnector:
    """行业底层逻辑串联分析器"""

    def __init__(self, api_key: str):
        self.client = ZhipuAI(api_key=api_key)

    def connect_industries(self, analyzed_news: List[Dict]) -> str:
        """分析多条新闻之间的底层逻辑串联"""
        if not analyzed_news:
            return ""

        print("\n分析行业底层逻辑串联...")

        # 准备输入
        news_summary = "\n".join([
            f"{i+1}. {n['title']}\n   来源: {n['source']}"
            for i, n in enumerate(analyzed_news)
        ])

        prompt = f"""你是一位具有跨行业视野的 AI 战略分析师。请分析以下 {len(analyzed_news)} 条重大新闻之间的底层逻辑关联。

【今日重大新闻】
{news_summary}

【关注行业】
教育、创意设计、心理学

请从以下角度分析，输出格式严格按要求：

一、宏观趋势
这批新闻整体反映了 AI 发展的什么宏观趋势？（150字以内）

二、行业联动
这批新闻在教育、创意设计、心理学三个行业之间有什么联动关系？
- 技术→教育→设计的传导路径
- 心理学视角的深层影响
（200字以内）

三、前瞻洞察
基于这些新闻，预测未来 3-6 个月可能出现的行业变化。（150字以内）

请按照上述格式输出，保持正式、专业的内参风格。"""

        try:
            response = self.client.chat.completions.create(
                model="glm-4-flash",
                messages=[
                    {"role": "system", "content": "你是一位具有跨行业视野的 AI 战略分析师，擅长发现行业间的深层关联。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
            )

            result = response.choices[0].message.content.strip()
            print("✓ 行业串联分析完成")

            return result

        except Exception as e:
            print(f"✗ 行业串联分析失败: {e}")
            return ""


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
            "summary": f"AI内参 {datetime.now().strftime('%Y-%m-%d')}",
            "contentType": 3,  # 3 表示 Markdown
            "uids": [self.uid],
            "url": ""
        }

        try:
            response = requests.post(self.api_url, json=payload, timeout=60)
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


def format_message(analyzed_news: List[Dict], industry_connection: str) -> str:
    """格式化内参风格推送消息"""
    today = date.today()
    year = today.year
    month = today.month
    day = today.day
    weekday = ['一', '二', '三', '四', '五', '六', '日'][today.weekday()]

    message = f"""# AI 每日内参

**{year}年{month}月{day}日 星期{weekday}**

---

## 一、今日要闻概览

"""

    # 概览
    for i, news in enumerate(analyzed_news, 1):
        message += f"{i}. **{news['title']}**\n   来源：{news['source']}\n\n"

    message += "## 二、深度分析\n\n"

    # 深度分析
    for i, news in enumerate(analyzed_news, 1):
        message += f"### {i}. {news['title']}\n\n"
        message += f"**来源**：{news['source']}\n\n"
        message += f"**链接**：[查看原文]({news['url']})\n\n"

        # 添加分析内容
        analysis = news.get('analysis', '')
        if analysis:
            # 清理分析内容中的 markdown 标题符号冲突
            analysis = analysis.replace('###', '####').replace('##', '###')
            message += f"{analysis}\n\n"

        message += "---\n\n"

    # 行业串联
    if industry_connection:
        message += "## 三、行业底层逻辑串联\n\n"
        connection = industry_connection.replace('###', '####').replace('##', '###')
        message += f"{connection}\n\n"

    message += f"""
---

*本内参由 AI 自动生成，内容仅供参考*

*生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

    return message


def main():
    """主函数"""
    print("=" * 60)
    print("AI 每日内参生成器")
    print("=" * 60)

    # 检查环境变量
    if not all([WXPUSHER_TOKEN, WXPUSHER_UID, ZHIPU_API_KEY]):
        print("错误：请设置环境变量 WXPUSHER_TOKEN、WXPUSHER_UID 和 ZHIPU_API_KEY")
        return

    try:
        # 1. 抓取资讯（取前3天的新闻）
        fetcher = NewsFetcher()
        articles = fetcher.fetch_from_rss(days_back=3)

        if not articles:
            print("没有抓取到资讯")
            return

        # 2. 筛选重大新闻
        selector = NewsSelector(ZHIPU_API_KEY)
        major_news = selector.select_major_news(articles)

        if not major_news:
            print("没有筛选出重大新闻")
            return

        # 3. 深度分析每条新闻
        print("\n开始深度分析...")
        analyzer = NewsAnalyzer(ZHIPU_API_KEY)
        analyzed_news = []

        for news in major_news:
            analyzed = analyzer.analyze_news(news)
            analyzed_news.append(analyzed)

        # 4. 分析行业底层逻辑串联
        connector = IndustryConnector(ZHIPU_API_KEY)
        industry_connection = connector.connect_industries(analyzed_news)

        # 5. 格式化消息
        message = format_message(analyzed_news, industry_connection)

        print("\n" + "=" * 60)
        print("内参预览（前500字）：")
        print("=" * 60)
        print(message[:500] + "...")
        print("=" * 60)

        # 6. 推送到微信
        print("\n开始推送...")
        wxpusher = WxPusherClient(WXPUSHER_TOKEN, WXPUSHER_UID)
        wxpusher.send(message)

    except Exception as e:
        print(f"程序异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
