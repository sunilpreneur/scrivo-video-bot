#!/usr/bin/env python3

import subprocess
import requests
import json
import sys
import os
import time

# ---------------- CONFIG ----------------

API_KEY = "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"
MODEL = "nex-agi/deepseek-v3.1-nex-n1:free"

KEYWORD_SCRIPT = "/storage/emulated/0/PNI/copy_sorted_keywords.py"
AUDIOSRT_PATH = "/storage/emulated/0/PNI/audiosrt.txt"
OUTPUT_PATH = "/storage/emulated/0/Video Editing Bot/script/keyplace_script.txt"

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# ----------------------------------------

def run_keyword_script():
    print("🔹 Running keyword script...")
    try:
        result = subprocess.check_output(
            ["python", KEYWORD_SCRIPT],
            stderr=subprocess.STDOUT,
            text=True
        )
        return result.strip()
    except subprocess.CalledProcessError as e:
        print("❌ Failed to run keyword script")
        print(e.output)
        sys.exit(1)

def read_file(path):
    if not os.path.exists(path):
        print(f"❌ File not found: {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def send_to_deepseek(prompt):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "Termux DeepSeek Keyword Placer"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a precise text-formatting assistant. Follow instructions exactly."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2,
        "max_tokens": 8192
    }

    print("🚀 Sending to DeepSeek...")
    r = requests.post(
        OPENROUTER_URL,
        headers=headers,
        data=json.dumps(payload),
        timeout=180
    )

    if r.status_code != 200:
        print("❌ API Error")
        print(r.text)
        sys.exit(1)

    data = r.json()
    return data["choices"][0]["message"]["content"]

def main():
    keywords_output = run_keyword_script()
    print("✅ Keywords captured")

    audiosrt_text = read_file(AUDIOSRT_PATH)

    USER_PROMPT = f"""
{audiosrt_text}

KEYWORDS:
{keywords_output}

write the text in same format aswritten below, same timestamp format, while keeping the duration as same as writtem in the file.

write full, cover full text from the file, don't stop midway.

from this file remove all the serial numbers lile 1, 2, 3 etc.

and second 
Place the right 1 keyword from these keywords only on each timestamped segment in the txt file. 
remember i said just 1 keyword, i have sent you multiple keywords that are written comma seperated, choose one for each line
And return me txt file once all segments done.
only use these keywords i am giving you. 

eg.
00:00:00,220 --> 00:00:04,180
नमस्कार, स्वागत है आपका हमारे चैनल पर। आज
Keywords: india

00:00:04,220 --> 00:00:06,820
हम एक ऐसी खबर पर बात करने जा रहे हैं जिसने
Keywords: global

00:00:06,840 --> 00:00:09,800
दिल्ली से मॉस्को तक और वाशिंगटन के
Keywords: india-russia

00:00:09,820 --> 00:00:12,940
गलियारों में हलचल मचा दी है। यह सिर्फ एक
Keywords: indian army

Important Note :
you will surely make this mistake, so that's why i am informing you before :
00:00:54,000 --> 01:00:00,000

this timestamp is wrong, as after 54 seconds itshould be 1 minute,  not 1 hour :

00:00:54,000 --> 00:01:00,000

this is how it should be.

And another important note :
there should be no segment longer than 5 seconds, the difference should only be between 3-5 seconds.

do not miss any line, cover all the text.i dont want to see erorrs lile this (�), so dont cut out any line in between.
"""

    result = send_to_deepseek(USER_PROMPT)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(result)

    print("🎉 Keyword placement completed successfully!")
    print(f"📄 Saved to: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
