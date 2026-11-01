# video-ingest

把外部平台的视频「摄取」进来，转成本地可用的文件。

> 目前只实现了**抖音分享视频下载**。收藏夹下载、结构化分析、其他平台等能力后续再补充。

## 这个 skill 能做什么

**目前唯一功能：下载抖音视频（无水印 + 带声音）。**

你只要把抖音 App 里「复制链接」得到的那段文字贴过来，它就能自动下载出 1080P 无水印、带声音的 mp4 文件。

> 后续会扩展：抖音收藏夹下载、下载视频的结构化分析归类（文案/对白/画面/人物关系等）、以及 B 站等其他平台。

## 用户怎么用

### 方式一：手动跑脚本

```bash
# 1. 装依赖（详见下方「依赖与安装」）
pip install playwright imageio-ffmpeg requests
python -m playwright install chromium

# 2. 下载视频
python scripts/ingest.py "复制打开抖音，看看... https://v.douyin.com/xxxx/ ..."
```

第 2 步贴进去的，可以是你从抖音 App「复制链接」得到的**整段分享文本**（含口令尾巴也没关系），也可以直接是那个 `https://v.douyin.com/...` 短链。脚本会自动识别。

下载好的视频输出到 `downloads/` 目录。

### 方式二：作为 skill 装进 AI 工具（推荐）

把这个仓库作为 skill 装进你的 AI 工具（WorkBuddy / codex / 豆包 / deepseek harness 等）。之后你只需对 AI 说一句「下载这个抖音视频」，AI 会按 `SKILL.md` 的指引自动装依赖、跑脚本、下载视频。

安装依赖前，AI 会先问你要装到**默认位置**还是**指定路径**（详见 `SKILL.md` 的「安装引导」一节）。

### 可选参数

```bash
python scripts/ingest.py "链接" --cookie "你的Cookie"   # 遇到需登录才能看的视频时带上
python scripts/ingest.py "链接" --headed               # 显示浏览器窗口（调试用）
```

## 依赖与安装

- Python 3.13+
- `playwright` + chromium 内核（无头浏览器，抓取音视频流）
- `imageio-ffmpeg`（完整版 ffmpeg，合并音视频）
- `requests`（HTTP 下载与短链解析）

```bash
pip install playwright imageio-ffmpeg requests
python -m playwright install chromium
```

> 安装位置的引导（默认 or 指定路径）见 `SKILL.md`。

## 目录结构

```
video-ingest/
├── SKILL.md          # skill 定义（供 AI 工具加载）
├── README.md         # 本文件
├── scripts/
│   └── ingest.py     # 核心脚本
└── downloads/        # 下载产物（不提交）
```

## 技术要点（排错）

1. 抖音 web 端把音视频分成两个独立流（URL 末尾 `/media-vide` / `/media-audi`），脚本会两路都抓下来再合并，所以下载的视频带声音。
2. 无需登录态即可下载大部分视频；只有部分需登录的视频才要加 `--cookie`。

## 许可

MIT
