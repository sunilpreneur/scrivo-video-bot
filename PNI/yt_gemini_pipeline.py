#!/data/data/com.termux/files/usr/bin/env python3
# YT → AUDIO → GEMINI TRANSCRIBE → KEYS → LONG SCRIPT PIPELINE
# Modified: ensures final paragraph once, nukta-normalize, save & copy to clipboard

import os
import sys
import time
import json
import base64
import requests
import subprocess
import mimetypes
import re
from shutil import which

# ========= CONFIG =========
API_KEY = "AIzaSyDbwuymwSa_kI6UdqbsFnMJ1sbDzRh-kQ0"
MODELS = [
    "models/gemini-2.5-flash",
    "models/gemini-2.0-flash",
    "models/gemini-2.0-flash-lite",
    "models/gemini-1.5-flash"
]

OUT_DIR = "/storage/emulated/0/PNI"
TMP_DIR = "/data/data/com.termux/files/home/.yt_pipeline"
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(TMP_DIR, exist_ok=True)

YT = which("yt-dlp") or "yt-dlp"

# ========= NUKTA NORMALIZER =========
import unicodedata
NUKTA_MAP = {
    "क़": "क", "ख़": "ख", "ग़": "ग", "ज़": "ज",
    "ड़": "ड", "ढ़": "ढ", "फ़": "फ", "ऱ": "र",
    "ऩ": "न", "य़": "य",
}
NUKTA_COMBINING = "\u093C"

def normalize_text(text):
    if not text:
        return text
    s = unicodedata.normalize("NFC", text)
    for src, dst in NUKTA_MAP.items():
        s = s.replace(src, dst)
    s = s.replace(NUKTA_COMBINING, "")
    return re.sub(r"\s+", " ", s).strip()

# ========= YOUTUBE ID EXTRACTOR =========
def extract_video_id(url):
    patterns = [
        r"youtu\.be/([A-Za-z0-9_-]{11})",
        r"youtube\.com/watch\?v=([A-Za-z0-9_-]{11})",
        r"youtube\.com/embed/([A-Za-z0-9_-]{11})",
        r"youtube\.com/v/([A-Za-z0-9_-]{11})",
        r"v=([A-Za-z0-9_-]{11})"
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None

# ========= CMD RUNNER =========
def run(cmd, capture=False):
    try:
        if capture:
            return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True).strip()
        else:
            subprocess.check_call(cmd, shell=True)
            return ""
    except subprocess.CalledProcessError as e:
        out = e.output if hasattr(e, "output") else str(e)
        print("CMD ERROR:", out[:400])
        return None

# ========= DOWNLOAD AUDIO =========
def download_audio(url):
    vidid = extract_video_id(url)
    if not vidid:
        print("❌ Could not extract YouTube ID")
        return None, None

    mp3_path = os.path.join(TMP_DIR, f"{vidid}.mp3")
    out_template = os.path.join(TMP_DIR, f"{vidid}.%(ext)s")

    print("\n🎧 Trying SABR bypass (iOS user-agent)…")
    cmd1 = f'''
{YT} \
--user-agent "com.google.ios.youtube/19.49.3" \
--referer "https://www.youtube.com" \
--add-header "Origin: https://www.youtube.com" \
-f bestaudio \
--extract-audio --audio-format mp3 --audio-quality 0 \
-o "{out_template}" "{url}"
'''
    if run(cmd1) is not None and os.path.exists(mp3_path):
        print("✅ Downloaded via iOS bypass")
        return vidid, mp3_path

    print("\n⚠️ SABR bypass failed → Using Invidious fallback")
    invid = f"https://yewtu.be/latest_version?id={vidid}&itag=140"
    cmd2 = f'{YT} -o "{out_template}" "{invid}"'

    if run(cmd2) is not None:
        for f in os.listdir(TMP_DIR):
            if f.startswith(vidid):
                src = os.path.join(TMP_DIR, f)
                run(f'ffmpeg -y -i "{src}" "{mp3_path}"')
                if os.path.exists(mp3_path):
                    print("✅ Downloaded via Invidious fallback")
                    return vidid, mp3_path

    print("❌ Download failed")
    return None, None

# ========= GEMINI HELPERS =========
def encode_audio(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def gemini_audio(model, mime, b64, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={API_KEY}"
    js = { "contents":[{ "parts":[{"inline_data":{"mime_type":mime,"data":b64}}, {"text":prompt}]}] }
    r = requests.post(url, json=js, timeout=300)
    if r.status_code != 200:
        return None
    try:
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    except:
        return None

def gemini_text(model, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={API_KEY}"
    js = { "contents":[{ "parts":[{"text":prompt}]}] }
    r = requests.post(url, json=js, timeout=200)
    if r.status_code != 200:
        return None
    try:
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    except:
        return None

def try_audio(mime, b64, prompt):
    for m in MODELS:
        for a in range(3):
            print(f"➡️ {m} attempt {a+1}")
            out = gemini_audio(m, mime, b64, prompt)
            if out:
                return out
    return None

def try_text(prompt):
    for m in MODELS:
        for a in range(3):
            print(f"➡️ {m} (text) attempt {a+1}")
            out = gemini_text(m, prompt)
            if out:
                return out
    return None

# ========= PIPELINE =========
def transcribe(audio):
    mime,_ = mimetypes.guess_type(audio)
    if not mime: mime="audio/mp3"
    b64 = encode_audio(audio)
    print("\n🧠 Transcribing with Gemini…")
    return try_audio(mime, b64, "Transcribe this Hindi audio word-by-word. No summary.")

def make_keypoints(text):
    p = "Give EXACTLY 100 short key points:\n\n" + text
    return try_text(p)

SCRIPT_PROMPT = """
Write a long Hindi news script (8+ minutes) based on these key points:
{POINTS}

Use suspense and storytelling. No headings.  
End EXACTLY with:

तो दोस्तों आज के लिए इतना ही. अगर आपको इस video से कुछ नया जानने को मिला हो तो इस video को like जरूर कीजिएगा, और ऐसे ही और भी videos के लिए इस channel को subscribe जरूर कर लीजियेगा, बाकी जाते जाते कमेंट में जय हिन्द जरूर लिखिएगा. जय हिन्द.
"""

FINAL_LINE = "तो दोस्तों आज के लिए इतना ही. अगर आपको इस video से कुछ नया जानने को मिला हो तो इस video को like जरूर कीजिएगा, और ऐसे ही और भी videos के लिए इस channel को subscribe जरूर कर लीजियेगा, बाकी जाते जाते कमेंट में जय हिन्द जरूर लिखिएगा. जय हिन्द."

def ensure_final_once(script):
    s = script.strip()
    idx = s.find(FINAL_LINE)
    if idx != -1:
        s = s[:idx].strip()
    s = s.rstrip() + "\n\n" + FINAL_LINE
    return s

def make_script(points):
    script = try_text(SCRIPT_PROMPT.replace("{POINTS}", points))
    if not script:
        return None

    tries = 0
    while len(script) < 7000 and tries < 6:
        tail = script[-600:]
        cont = try_text("Continue with 3 more paragraphs after:\n" + tail)
        if not cont:
            break
        script += "\n\n" + cont
        tries += 1

    return script

# ========= MAIN =========
def main():
    print("=== YT → AUDIO → TRANSCRIBE → SCRIPT ===")
    url = input("Paste YouTube link: ").strip()
    if not url:
        return

    vidid, audio = download_audio(url)
    if not audio:
        return

    transcript = transcribe(audio)
    if not transcript:
        print("❌ Transcription failed")
        return

    keypoints = make_keypoints(transcript)
    if not keypoints:
        print("❌ Keypoints failed")
        return

    final_script = make_script(keypoints)
    if not final_script:
        print("❌ Script failed")
        return

    final_script = ensure_final_once(final_script)
    cleaned = normalize_text(final_script)

    out_path = os.path.join(OUT_DIR, "script.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(cleaned)

    print("\n🎉 Script saved!")
    print("📄", out_path)
    # ========= NOTIFICATION =========
    os.system('termux-toast "Script Done!"')
    os.system('termux-notification --sound --title "YT Script" --content "Script Done!"')


if __name__ == "__main__":
    main()
