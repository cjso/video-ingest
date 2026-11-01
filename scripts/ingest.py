# -*- coding: utf-8 -*-
"""
video-ingest —— 跨平台视频采集工作流

阶段一（当前）：视频下载
  - 抖音分享视频下载（已跑通）
  - 抖音收藏夹下载（规划中）

阶段二（待定）：下载视频的结构化分析归类
  - 视频文案 / 对白 / 画面 / 故事情节 / 风景信息 / 动作信息 / 人物关系 等

平台扩展（待定）：B站 等其他平台。

当前实现：抖音分享视频下载（Playwright 无头浏览器版，免 Cookie，含音视频合并）

原理：
    抖音 web 端把音视频分成两个独立流，URL 末尾分别带 `/media-vide`（视频）和
    `/media-audi`（音频）。本脚本开无头浏览器打开视频页，监听网络请求，
    把这两个流分别截下、下载，再用 ffmpeg 合并成带声音的 mp4。
    不依赖 Cookie，也不需要手算 a_bogus 签名。

用法：
    python ingest.py "https://v.douyin.com/rWWTQLkjyiw/"
    python ingest.py "整段手机分享文本（含口令尾巴）"

可选：
    --cookie "<你的Cookie>"    # 遇到登录才能看的视频时带上，提高成功率
    --headed                   # 显示浏览器窗口（调试用，默认无头）

依赖：
    - playwright + chromium（浏览器自动化，抓取音视频流）
    - imageio-ffmpeg（完整版 ffmpeg，合并音视频）
    - requests（HTTP 下载与短链解析）
"""
import os
import re
import sys
import subprocess

from playwright.sync_api import sync_playwright

SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "downloads")

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def find_ffmpeg() -> str:
    """找完整版 ffmpeg：优先 imageio_ffmpeg 自带的（支持 mp4），其次系统 PATH。"""
    try:
        import imageio_ffmpeg
        p = imageio_ffmpeg.get_ffmpeg_exe()
        if os.path.exists(p):
            return p
    except Exception:
        pass
    return "ffmpeg"


FFMPEG = find_ffmpeg()


def extract_short_url(text: str) -> str:
    """从任意文本里抠出 v.douyin.com 短链。"""
    m = re.search(r"https?://v\.douyin\.com/[A-Za-z0-9]+/", text)
    if not m:
        m = re.search(r"https?://v\.douyin\.com/[A-Za-z0-9_-]+", text)
    if not m:
        raise ValueError("没在输入里找到 v.douyin.com 短链")
    return m.group(0)


def resolve_final_url(short_url: str) -> str:
    """跟随重定向，拿到 douyin.com/video/<id> 最终地址。"""
    import requests
    r = requests.get(short_url, headers={"User-Agent": UA}, allow_redirects=True, timeout=30)
    return r.url


def get_aweme_id(url: str) -> str:
    m = re.search(r"/video/(\d+)", url)
    if m:
        return m.group(1)
    m = re.search(r"(?:modal_id|aweme_id|item_ids?)=(\d+)", url)
    if m:
        return m.group(1)
    raise ValueError(f"没能解析出视频 ID：{url}")


def classify_stream(url: str, content_type: str) -> str:
    """判断一个 douyinvod 请求是 video 流还是 audio 流，返回 'video'/'audio'/None。"""
    if not url or "douyinvod" not in url.lower():
        return None
    if content_type and "video" not in content_type:
        return None
    low = url.lower()
    if "/media-audi" in low or low.endswith("audi"):
        return "audio"
    if "/media-vide" in low or low.endswith("vide"):
        return "video"
    if "video" in low:
        return "video"
    return None


def download(url: str, path: str):
    import requests
    h = {
        "User-Agent": UA,
        "Referer": "https://www.douyin.com/",
        "Range": "bytes=0-",
    }
    r = requests.get(url, headers=h, stream=True, timeout=60)
    r.raise_for_status()
    with open(path, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024 * 256):
            f.write(chunk)


def merge_av(video_path: str, audio_path: str, out_path: str):
    """用 ffmpeg 把纯视频和纯音频合并。"""
    cmd = [
        FFMPEG, "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c", "copy",
        out_path,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg 合并失败：{r.stderr[-500:]}")


def main():
    args = [a for a in sys.argv[1:]]
    cookie = None
    headed = False
    raw = None

    i = 0
    while i < len(args):
        a = args[i]
        if a == "--cookie":
            cookie = args[i + 1]
            i += 2
        elif a == "--headed":
            headed = True
            i += 1
        else:
            raw = a
            i += 1

    if not raw:
        print("用法：python ingest.py \"<手机分享短链或整段文本>\" [--cookie \"...\"] [--headed]")
        sys.exit(1)

    short = extract_short_url(raw)
    print(f"[1/6] 短链：{short}")

    final_url = resolve_final_url(short)
    print(f"[2/6] 重定向后：{final_url}")
    aweme_id = get_aweme_id(final_url)
    print(f"[3/6] 视频 ID：{aweme_id}")

    os.makedirs(SAVE_DIR, exist_ok=True)
    video_url = None
    audio_url = None

    print("[4/6] 打开无头浏览器监听音视频流…")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not headed)
        ctx = browser.new_context(user_agent=UA)
        if cookie:
            cookies = []
            for pair in cookie.split(";"):
                pair = pair.strip()
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    cookies.append({"name": k, "value": v, "domain": ".douyin.com", "path": "/"})
            ctx.add_cookies(cookies)

        page = ctx.new_page()

        def on_response(resp):
            nonlocal video_url, audio_url
            kind = classify_stream(resp.url, resp.headers.get("content-type", ""))
            if kind == "video" and video_url is None:
                video_url = resp.url
                print(f"      捕获视频流：{resp.url[:90]}...")
            elif kind == "audio" and audio_url is None:
                audio_url = resp.url
                print(f"      捕获音频流：{resp.url[:90]}...")

        page.on("response", on_response)

        try:
            page.goto(final_url, timeout=40000)
            page.wait_for_timeout(9000)
        except Exception as e:
            print(f"      页面加载异常：{e}")

        browser.close()

    if not video_url:
        print("[5/6] ❌ 没捕获到视频流。可能原因：")
        print("        1. 需要登录才能看 → 加 --cookie 重试")
        print("        2. 触发了验证码/风控 → 稍后再试")
        sys.exit(1)

    video_path = os.path.join(SAVE_DIR, f"{aweme_id}_video.mp4")
    print("[5/6] 下载视频流…")
    download(video_url, video_path)

    if audio_url:
        audio_path = os.path.join(SAVE_DIR, f"{aweme_id}_audio.mp4")
        print("      下载音频流…")
        download(audio_url, audio_path)

        final_path = os.path.join(SAVE_DIR, f"{aweme_id}.mp4")
        print("[6/6] 合并音视频…")
        merge_av(video_path, audio_path, final_path)
        os.remove(video_path)
        os.remove(audio_path)
        size = os.path.getsize(final_path) / 1024 / 1024
        print(f"✅ 下载完成（含声音）：{final_path}（{size:.1f} MB）")
    else:
        final_path = os.path.join(SAVE_DIR, f"{aweme_id}.mp4")
        os.replace(video_path, final_path)
        size = os.path.getsize(final_path) / 1024 / 1024
        print(f"[6/6] ✅ 下载完成（单一流）：{final_path}（{size:.1f} MB）")


if __name__ == "__main__":
    main()
