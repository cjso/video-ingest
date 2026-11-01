---
name: video-ingest
description: 跨平台视频采集与下载工作流。当用户需要下载抖音视频（分享链接或收藏夹）、解析视频地址、或规划视频的结构化分析归类时使用。当前已实现抖音分享视频的无水印下载（含音视频合并）。触发词：下载抖音视频、抖音去水印、下载这个视频、video ingest、采集视频。
---

# video-ingest —— 跨平台视频采集工作流

把外部平台的视频「摄取」进来，转成本地可用的文件，并逐步扩展为结构化分析。

## 当前能力（阶段一）

| 能力 | 状态 |
|---|---|
| 抖音分享视频下载（无水印 + 音视频合并） | ✅ 已跑通 |
| 抖音收藏夹下载 | ⏳ 规划中 |

## 规划中（阶段二，待定）

下载视频的结构化分析归类：视频文案、对白、画面、故事情节、风景信息、动作信息、人物关系等。

## 规划中（平台扩展，待定）

B站 等其他平台。

---

## 使用方式

### 下载抖音视频（当前唯一已实现能力）

用户给一段「手机抖音 App 分享的文本」（含短链和口令尾巴）或直接给短链，执行：

```bash
python scripts/ingest.py "用户给的整段分享文本或短链"
```

脚本自动完成：抠短链 → 解析视频 ID → 无头浏览器抓音视频两路流 → 下载 → ffmpeg 合并 → 输出 1080P 无水印带声音 mp4 到 `downloads/`。

可选参数：
- `--cookie "<Cookie>"`：遇到需登录才能看的视频时带上，提高成功率
- `--headed`：显示浏览器窗口（调试用）

## 依赖

- Python 3.13+
- `playwright` + chromium 内核（浏览器自动化）
- `imageio-ffmpeg`（完整版 ffmpeg，合并音视频）
- `requests`（HTTP 下载与短链解析）

安装：

```bash
pip install playwright imageio-ffmpeg requests -i https://mirrors.aliyun.com/pypi/simple/
python -m playwright install chromium
```

## 技术要点（排错必读）

1. **抖音 web 端音视频分离**：视频流 URL 末尾是 `/media-vide`，音频流是 `/media-audi`，必须两个都抓到再 ffmpeg 合并，否则没声音。
2. **视频流 URL 无扩展名**：真正的视频本体 URL 是纯路径（无 `.mp4`），判定要认「域名是 `douyinvod` + content-type 是 `video/mp4`」，不能靠扩展名。
3. **Playwright 自带 ffmpeg 是阉割版**：只支持 webm/matroska，读不了 mp4，合并必须用完整版（`imageio-ffmpeg`）。
4. **免 Cookie 可下载大部分视频**：无头浏览器会自动算 a_bogus 签名；只有部分需登录的视频才要 `--cookie`。

## 架构预留

- `scripts/ingest.py` 是平台无关的入口，后续加 B站/收藏夹，往这里加「源」的解析逻辑即可，不改名字。
- 阶段二的「分析归类」将作为独立模块挂进来，与「下载」解耦。
