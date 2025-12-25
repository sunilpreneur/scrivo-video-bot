import subprocess
import os
import re
import sys

# ===== PATHS =====
WHISPER_DIR = "/data/data/com.termux/files/home/whisper.cpp"
WHISPER_BIN = os.path.join(WHISPER_DIR, "build/bin/whisper-cli")
MODEL_PATH = os.path.join(WHISPER_DIR, "models/ggml-small.bin")

PNI_DIR = "/storage/emulated/0/PNI"
AUDIO_FILE = os.path.join(PNI_DIR, "audio.mp3")
TEMP_SRT = os.path.join(PNI_DIR, "temp_output.srt")
FINAL_TXT = os.path.join(PNI_DIR, "audiosrt.txt")

# ===== CHECKS =====
if not os.path.isfile(AUDIO_FILE):
    print("❌ audio.mp3 not found in PNI folder")
    sys.exit(1)

# ===== RUN WHISPER =====
cmd = [
    WHISPER_BIN,
    "-m", MODEL_PATH,
    "-f", AUDIO_FILE,
    "--translate",
    "--output-srt",
    "--threads", "4",
    "--temperature", "0.0",
    "--max-context", "0",
    "--max-len", "60",
    "--split-on-word",
    "--output-file", os.path.join(PNI_DIR, "temp_output")
]

print("🎙️ Running Whisper...")
subprocess.run(cmd, cwd=WHISPER_DIR, check=True)

# ===== CONVERT SRT → TXT =====
print("📝 Converting SRT to text...")

with open(TEMP_SRT, "r", encoding="utf-8") as f:
    srt = f.read()

# Remove timestamps & indices
text = re.sub(r"\d+\n", "", srt)
text = re.sub(r"\[.*?\]", "", text)
text = re.sub(r"\n{2,}", "\n", text)

with open(FINAL_TXT, "w", encoding="utf-8") as f:
    f.write(text.strip())

# Cleanup
os.remove(TEMP_SRT)

print(f"✅ Done! Saved to:\n{FINAL_TXT}")

