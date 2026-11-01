# video-ingest

跨平台视频采集与下载工作流。把外部平台的视频「摄取」进来，转成本地可用文件，并逐步扩展为结构化分析。

## 路线图

```
阶段一（现在）：下载
  ├─ 抖音分享视频下载 ✅ 已跑通
  └─ 抖音收藏夹下载 ⏳ 规划中
       ↓
阶段二（待定）：分析归类
  └─ 文案 / 对白 / 画面 / 故事情节 / 风景 / 动作 / 人物关系 等
       ↓
平台扩展（待定）：B站 等
```

## 快速开始

```bash
# 1. 装依赖
pip install playwright imageio-ffmpeg requests
python -m playwright install chromium

# 2. 下载一个抖音视频（贴手机分享的整段文本即可）
python scripts/ingest.py "复制打开抖音，看看... https://v.douyin.com/xxxx/ ..."
```

输出：1080P 无水印带声音 mp4，落在 `downloads/`。

## 目录结构

```
video-ingest/
├── SKILL.md          # skill 定义（供 WorkBuddy 加载）
├── README.md         # 本文件
├── scripts/
│   └── ingest.py     # 核心脚本（平台无关入口）
└── downloads/        # 下载产物（不提交）
```

## 技术要点

详见 `SKILL.md` 的「技术要点」一节：音视频分离、URL 无扩展名、ffmpeg 阉割版问题、免 Cookie 原理。

## 许可

MIT
