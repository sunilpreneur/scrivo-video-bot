import asyncio
import edge_tts
import os

input_path = "/storage/emulated/0/PNI/script.txt"
output_folder = "/storage/emulated/0/PNI"
output_path = "/storage/emulated/0/PNI/audio.mp3"

voice = "hi-IN-MadhurNeural"  # You can change to hi-IN-MadhurNeural
CHUNK_SIZE = 2500  # characters per segment

# --- Split the text safely ---
def split_text(text, max_len=CHUNK_SIZE):
    sentences = text.replace("\n", " ").split(". ")
    chunks, current = [], ""
    for sentence in sentences:
        if len(current) + len(sentence) + 1 < max_len:
            current += sentence + ". "
        else:
            chunks.append(current.strip())
            current = sentence + ". "
    if current:
        chunks.append(current.strip())
    return chunks

# --- Main async function ---
async def main():
    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read().strip()

    parts = split_text(text)
    print(f"🔊 Splitting text into {len(parts)} parts...")

    temp_files = []
    for i, part in enumerate(parts):
        temp_path = os.path.join(output_folder, f"part_{i}.mp3")
        print(f"🗣️  Generating part {i+1}/{len(parts)}...")
        tts = edge_tts.Communicate(part, voice)
        await tts.save(temp_path)
        temp_files.append(temp_path)

    # Combine all MP3s
    print("🎧 Combining audio parts...")
    with open(output_path, "wb") as outfile:
        for fname in temp_files:
            with open(fname, "rb") as infile:
                outfile.write(infile.read())
            os.remove(fname)  # delete temp part

    print(f"✅ Done! Final audio saved: {output_path}")
    # ======= NOTIFICATION + POPUP =======
    os.system('termux-toast "Voiceover Done!"')
    os.system('termux-notification --sound --title "TTS Engine" --content "Voiceover Done!"')

asyncio.run(main())
