#!/data/data/com.termux/files/usr/bin/env python3
import os
import re
import subprocess
import unicodedata
import requests
from shutil import which

# ================= CONFIG =================
OPENROUTER_API_KEY = "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"
MODEL = "nex-agi/deepseek-v3.1-nex-n1:free"

PNI = "/storage/emulated/0/PNI"
TMP = "/data/data/com.termux/files/home/.yt_pipeline"
WHISPER = "/data/data/com.termux/files/home/whisper.cpp/build/bin/whisper-cli"
MODEL_PATH = "/data/data/com.termux/files/home/whisper.cpp/models/ggml-small.bin"

os.makedirs(PNI, exist_ok=True)
os.makedirs(TMP, exist_ok=True)

YT = which("yt-dlp") or "yt-dlp"

# ================= NUKTA =================
NUKTA_MAP = {
    "क़": "क", "ख़": "ख", "ग़": "ग", "ज़": "ज",
    "ड़": "ड", "ढ़": "ढ", "फ़": "फ", "ऱ": "र",
    "ऩ": "न", "य़": "य",
}

def normalize_nukta(text):
    if not text:
        return text
    text = unicodedata.normalize("NFC", text)
    for k, v in NUKTA_MAP.items():
        text = text.replace(k, v)
    text = text.replace("\u093C", "")
    return re.sub(r"\s+", " ", text).strip()

# ================= RUN CMD =================
def run(cmd):
    subprocess.check_call(cmd, shell=True)

# ================= YTDLP =================
def extract_id(url):
    m = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", url)
    return m.group(1) if m else None

def download_audio(url):
    vid = extract_id(url)
    if not vid:
        raise RuntimeError("Invalid YouTube URL")

    out = f"{TMP}/{vid}.mp3"
    cmd = f'''
{YT} -f bestaudio --extract-audio --audio-format mp3 \
-o "{TMP}/{vid}.%(ext)s" "{url}"
'''
    run(cmd)
    return out

# ================= WHISPER =================
def whisper_translate(audio_path):
    txt_out = audio_path + ".txt"
    cmd = f'''
"{WHISPER}" -m "{MODEL_PATH}" -f "{audio_path}" \
--translate --output-txt --no-timestamps
'''
    run(cmd)
    with open(txt_out, "r", encoding="utf-8") as f:
        return f.read()

# ================= DEEPSEEK =================
def deepseek(prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }
    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=300
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

# ================= SCRIPT LOGIC =================
def make_keypoints(text):
    p = "Give EXACTLY 100 short key points:\n\n" + text
    return deepseek(p)

SCRIPT_PROMPT = """
Write a long Hindi news script (8+ minutes) based on these key points:
{POINTS}

Use suspense and storytelling. No headings.
Do NOT speak channel name anywhere in the video.

End EXACTLY with:

तो दोस्तों आज के लिए इतना ही. अगर आपको इस video से कुछ नया जानने को मिला हो तो इस video को like जरूर कीजिएगा, और ऐसे ही और भी videos के लिए इस channel को subscribe जरूर कर लीजियेगा, बाकी जाते जाते कमेंट में जय हिन्द जरूर लिखिएगा. जय हिन्द.
"""

FINAL_LINE = "तो दोस्तों आज के लिए इतना ही. अगर आपको इस video से कुछ नया जानने को मिला हो तो इस video को like जरूर कीजिएगा, और ऐसे ही और भी videos के लिए इस channel को subscribe जरूर कर लीजियेगा, बाकी जाते जाते कमेंट में जय हिन्द जरूर लिखिएगा. जय हिन्द."

def make_script(points):
    script = deepseek(SCRIPT_PROMPT.replace("{POINTS}", points))
    tries = 0
    while len(script) < 7000 and tries < 5:
        tail = script[-700:]
        script += "\n\n" + deepseek("Continue the script after:\n" + tail)
        tries += 1
    if FINAL_LINE in script:
        script = script.split(FINAL_LINE)[0].strip()
    return script + "\n\n" + FINAL_LINE

# ================= MAIN =================
def main():
    print("🎬 Script Writer (Whisper → DeepSeek)")
    url = input("Paste YouTube link: ").strip()
    audio = download_audio(url)

    print("🗣️ Transcribing with Whisper (small, translate)...")
    transcript = whisper_translate(audio)

    print("🧠 Generating keypoints...")
    points = make_keypoints(transcript)

    print("✍️ Writing script...")
    script = make_script(points)
    script = normalize_nukta(script)

    out = f"{PNI}/script.txt"
    with open(out, "w", encoding="utf-8") as f:
        f.write(script)

    os.system('termux-toast "Script Ready 🎉"')
    print("✅ Saved:", out)

if __name__ == "__main__":
    main()
