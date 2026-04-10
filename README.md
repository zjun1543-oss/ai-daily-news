# AI 每日资讯

每天早上 6 点自动抓取 AI 前沿资讯，筛选 5-10 条最重要的推送到微信。

## 功能特点

- 自动抓取 OpenAI、Google AI、DeepMind、Microsoft、Meta、Anthropic、NVIDIA 等顶级公司博客
- AI 智能筛选最重要、最前沿的资讯
- 自动翻译成中文摘要
- 按类别整理（前沿动态、AI 教育、AI 设计）
- 推送到微信（免费）

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`，填入你的配置：

```bash
cp .env.example .env
```

编辑 `.env`：

```env
WXPUSHER_TOKEN=AT_xxxxx         # WxPusher AppToken
WXPUSHER_UID=UID_xxxxx          # 你的微信 UID
ZHIPU_API_KEY=xxxxx             # 智谱 API Key
```

### 3. 运行测试

```bash
python ai_daily_news.py
```

### 4. 部署到 GitHub Actions（推荐）

1. 创建 GitHub 仓库，上传代码
2. 在仓库 Settings > Secrets and variables > Actions 中添加以下 Secrets：
   - `WXPUSHER_TOKEN`
   - `WXPUSHER_UID`
   - `ZHIPU_API_KEY`
3. 启用 Actions，每天早上 6 点自动运行
4. 也可以在 Actions 页面手动触发测试

## 资讯来源

- OpenAI Blog
- Google AI Blog
- Google DeepMind
- Microsoft Research
- Meta AI
- Anthropic
- NVIDIA Blog
- MIT Technology Review (AI)

## 配置说明

| 参数 | 说明 | 获取方式 |
|------|------|---------|
| WXPUSHER_TOKEN | WxPusher 应用 Token | https://wxpusher.zjiecode.com/ |
| WXPUSHER_UID | 你的微信 UID | WxPusher 应用详情页 > 关注者列表 |
| ZHIPU_API_KEY | 智谱 AI API Key | https://open.bigmodel.cn/ |

## 许可

MIT
