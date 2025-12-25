#!/data/data/com.termux/files/usr/bin/python

import os
import subprocess

BASE = "/storage/emulated/0/Pictures/Gallery/owner"

# -------------------------------
# SAFETY CHECK
# -------------------------------
if not os.path.exists(BASE):
    print(f"❌ Path not found: {BASE}")
    exit()

# -------------------------------
# READ FOLDERS
# -------------------------------
folder_list = []

for name in os.listdir(BASE):
    full = os.path.join(BASE, name)
    if os.path.isdir(full):
        folder_list.append(name)

if not folder_list:
    print("❌ No folders found inside owner/")
    exit()

# -------------------------------
# SORT FOLDERS A-Z
# -------------------------------
folder_list = sorted(folder_list, key=lambda x: x.lower())

# -------------------------------
# EXPAND COMMA SEPARATED KEYWORDS
# -------------------------------
result_keywords = []

for folder in folder_list:
    clean = folder.replace("'", "").strip()
    parts = [p.strip() for p in clean.split(",")]
    result_keywords.extend(parts)

# -------------------------------
# FINAL STRING
# -------------------------------
final_string = ", ".join(result_keywords)

print("\n📋 SORTED KEYWORDS:\n")
print(final_string)
print("\n📌 Attempting to copy to clipboard...\n")

# -------------------------------
# CLIPBOARD COPY — METHOD 1
# -------------------------------
copied = False

try:
    subprocess.run(
        ["termux-clipboard-set", final_string],
        check=True
    )
    print("✅ Copied using Termux API!")
    copied = True
except Exception as e:
    print("⚠️ Termux API method failed:", e)

# -------------------------------
# CLIPBOARD COPY — METHOD 2 (Fallback)
# -------------------------------
if not copied:
    try:
        subprocess.run([
            "am", "broadcast",
            "-a", "com.termux.app.setclipboard",
            "--es", "text", final_string
        ], check=True)

        print("✅ Copied using fallback Broadcast method!")
        copied = True
    except Exception as e:
        print("⚠️ Broadcast method also failed:", e)

if copied:
    print("\n🎉 Keywords copied to clipboard successfully!\n")
else:
    print("\n❌ Could not copy to clipboard.\n")
