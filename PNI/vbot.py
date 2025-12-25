import os, random, re, subprocess

# === PATHS ===
base_dir = "/storage/emulated/0/Video Editing Bot"
script_path = f"{base_dir}/script/keyplace_script.txt"
audio_path = f"{base_dir}/audio/audio.mp3"

# ⬇️ Updated to use internal storage
media_base = "/storage/emulated/0/Pictures/Gallery/owner"

output_path = f"{base_dir}/finaledit/final_video.mp4"
temp_dir = f"{base_dir}/temp"
os.makedirs(temp_dir, exist_ok=True)

# === READ SCRIPT ===
if not os.path.exists(script_path):
    raise SystemExit(f"❌ Script not found: {script_path}")

with open(script_path, "r", encoding="utf-8") as f:
    script = f.read()

# Support SRT-like format with Keywords
pattern = r"(\d+):(\d+):(\d+),\d+\s+-->\s+(\d+):(\d+):(\d+),\d+\s+([\s\S]*?)Keywords:\s*(.+)"
segments = re.findall(pattern, script)

if not segments:
    raise SystemExit("❌ No timestamped segments found. Check your script formatting.")

temp_list_path = os.path.join(temp_dir, "list.txt")
open(temp_list_path, "w").close()

previous_folder = None
previous_keyword = None

def get_video_duration(path):
    """Return duration (seconds) of a video file using ffprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        return float(result.stdout.strip())
    except Exception:
        return 0

for i, (sh, sm, ss, eh, em, es, text, keyword) in enumerate(segments, 1):
    start = int(sh)*3600 + int(sm)*60 + int(ss)
    end = int(eh)*3600 + int(em)*60 + int(es)
    dur = max(1, end - start)
    keyword = keyword.strip().lower()

    matched_folder = None
    if not os.path.exists(media_base):
        raise SystemExit(f"❌ Media base folder not found: {media_base}")

    for folder in os.listdir(media_base):
        keys = [k.strip().lower() for k in folder.split(",")]
        if keyword in keys:
            matched_folder = os.path.join(media_base, folder)
            break

    if not matched_folder:
        if previous_folder:
            print(f"⚠️ No match for '{keyword}', reusing '{previous_keyword}'")
            matched_folder = previous_folder
            keyword = previous_keyword
        else:
            print(f"⚠️ No match for '{keyword}' and no previous folder to reuse.")
            continue

    media_files = [f for f in os.listdir(matched_folder)
                   if f.lower().endswith((".jpg", ".jpeg", ".png", ".mp4"))]
    if not media_files:
        print(f"⚠️ No media in '{matched_folder}', skipping.")
        continue

    chosen = os.path.join(matched_folder, random.choice(media_files))
    temp_out = os.path.join(temp_dir, f"clip_{i}.mp4")

    # === Random clip generation ===
    if chosen.lower().endswith((".jpg", ".jpeg", ".png")):
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", chosen,
            "-t", str(dur), "-vf", "scale=1280:720,setsar=1",
            "-r", "30", temp_out
        ]
    else:
        vid_dur = get_video_duration(chosen)
        if vid_dur > dur:
            start_time = random.uniform(0, max(0, vid_dur - dur))
        else:
            start_time = 0
        cmd = [
            "ffmpeg", "-y", "-ss", f"{start_time:.2f}", "-i", chosen,
            "-t", str(dur), "-vf", "scale=1280:720,setsar=1",
            "-r", "30", temp_out
        ]

    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    with open(temp_list_path, "a") as f:
        f.write(f"file '{temp_out}'\n")

    previous_folder = matched_folder
    previous_keyword = keyword
    print(f"✅ Segment {i}: '{keyword}' ({dur}s) → {os.path.basename(chosen)}")

# === Combine all segments ===
final_temp = os.path.join(temp_dir, "combined.mp4")
subprocess.run([
    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
    "-i", temp_list_path, "-c", "copy", final_temp
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# === STEP 1: Remove original video audio ===
print("🔇 Removing original video audio...")
video_no_audio = os.path.join(temp_dir, "video_no_audio.mp4")
subprocess.run([
    "ffmpeg", "-y", "-i", final_temp,
    "-c:v", "copy", "-an", video_no_audio
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# === STEP 2: Get video duration ===
video_duration = get_video_duration(video_no_audio)
print(f"📹 Video duration: {video_duration:.2f}s")

# Calculate audio cutoff point (17 seconds before end)
main_audio_end = max(0, video_duration - 17)
outro_start = main_audio_end

# Paths for audio files
main_audio = "/storage/emulated/0/PNI/audio.mp3"
outro_audio = "/storage/emulated/0/Video Editing Bot/Stuff/outro.mp3"
bgm_audio = "/storage/emulated/0/Video Editing Bot/Stuff/bgm.mp3"

# Temp files for audio processing
temp_main_audio = os.path.join(temp_dir, "main_audio_processed.wav")
temp_outro_audio = os.path.join(temp_dir, "outro_audio_processed.wav")
temp_voice_track = os.path.join(temp_dir, "voice_track.wav")
temp_bgm_trimmed = os.path.join(temp_dir, "bgm_trimmed.wav")

# === STEP 3: Process main audio (speed 1.1x, trim to main_audio_end, volume 200%) ===
if os.path.exists(main_audio):
    print("🎵 Processing main audio (speed 1.1x, volume 200%)...")
    subprocess.run([
        "ffmpeg", "-y", "-i", main_audio,
        "-af", f"atempo=1.1,volume=2.0,atrim=0:{main_audio_end},asetpts=PTS-STARTPTS",
        "-ar", "48000", "-ac", "2", temp_main_audio
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # === STEP 4: Process outro audio (volume 350%) ===
    if os.path.exists(outro_audio):
        print("🎵 Processing outro audio (volume 350%)...")
        subprocess.run([
            "ffmpeg", "-y", "-i", outro_audio,
            "-af", "volume=3.5",
            "-ar", "48000", "-ac", "2", temp_outro_audio
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # === STEP 5: Combine main audio + silence gap + outro audio ===
        print("🎵 Combining main audio and outro...")
        
        # Create the voice track with proper timing
        subprocess.run([
            "ffmpeg", "-y",
            "-i", temp_main_audio,
            "-i", temp_outro_audio,
            "-filter_complex",
            f"[0:a]apad=whole_dur={main_audio_end}[main];"
            f"[1:a]adelay={int(main_audio_end * 1000)}|{int(main_audio_end * 1000)}[outro];"
            f"[main][outro]amix=inputs=2:duration=longest[voice]",
            "-map", "[voice]", "-ar", "48000", "-ac", "2", temp_voice_track
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        print("⚠️ Outro audio not found, using only main audio")
        temp_voice_track = temp_main_audio
    
    # === STEP 6: Process BGM (volume 10.5% - reduced by 30%, trim to video duration) ===
    if os.path.exists(bgm_audio):
        print("🎵 Processing background music (volume 10.5%)...")
        subprocess.run([
            "ffmpeg", "-y", "-stream_loop", "-1", "-i", bgm_audio,
            "-af", f"volume=0.105,atrim=0:{video_duration},asetpts=PTS-STARTPTS",
            "-t", str(video_duration), "-ar", "48000", "-ac", "2", temp_bgm_trimmed
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # === STEP 7: Mix voice track + BGM ===
        print("🎵 Mixing voice and background music...")
        temp_final_audio = os.path.join(temp_dir, "final_audio.wav")
        subprocess.run([
            "ffmpeg", "-y",
            "-i", temp_voice_track,
            "-i", temp_bgm_trimmed,
            "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=longest[out]",
            "-map", "[out]", "-ar", "48000", "-ac", "2", temp_final_audio
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # === STEP 8: Add final mixed audio to video with HIGH QUALITY ===
        print("🎬 Adding final audio to video...")
        subprocess.run([
            "ffmpeg", "-y",
            "-i", video_no_audio,
            "-i", temp_final_audio,
            "-c:v", "copy", 
            "-c:a", "aac", 
            "-b:a", "320k",
            "-ar", "48000",
            "-shortest", output_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        print("⚠️ BGM not found, using only voice track")
        # Just add voice track to video with HIGH QUALITY
        subprocess.run([
            "ffmpeg", "-y",
            "-i", video_no_audio,
            "-i", temp_voice_track,
            "-c:v", "copy", 
            "-c:a", "aac", 
            "-b:a", "320k",
            "-ar", "48000",
            "-shortest", output_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
else:
    print("⚠️ Main audio not found")
    # No audio processing, just use video without audio
    os.rename(video_no_audio, output_path)

print(f"\n🎬 Final video saved successfully at: {output_path}\n")


# ================= FINAL CLEANUP & MOVE =================
import shutil, uuid

print("\n🧹 Starting cleanup...")

# 1️⃣ Delete all files inside temp folder
temp_dir = "/storage/emulated/0/Video Editing Bot/temp"
if os.path.exists(temp_dir):
    for f in os.listdir(temp_dir):
        try:
            os.remove(os.path.join(temp_dir, f))
        except Exception:
            pass
    print("✅ Temp videos deleted")

# 2️⃣ Delete all txt files from script folder
script_dir = "/storage/emulated/0/Video Editing Bot/script"
if os.path.exists(script_dir):
    for f in os.listdir(script_dir):
        if f.lower().endswith(".txt"):
            try:
                os.remove(os.path.join(script_dir, f))
            except Exception:
                pass
    print("✅ Script txt files deleted")

# 3️⃣ Delete audiosrt.txt
audiosrt_path = "/storage/emulated/0/PNI/audiosrt.txt"
if os.path.exists(audiosrt_path):
    os.remove(audiosrt_path)
    print("✅ audiosrt.txt deleted")

# 4️⃣ Delete script.txt from PNI folder
pni_script_path = "/storage/emulated/0/PNI/script.txt"
if os.path.exists(pni_script_path):
    os.remove(pni_script_path)
    print("✅ PNI/script.txt deleted")

# 5️⃣ Move final video to root storage
final_video_src = "/storage/emulated/0/Video Editing Bot/finaledit/final_video.mp4"
final_video_dst = "/storage/emulated/0/final_video.mp4"
if os.path.exists(final_video_src):
    shutil.move(final_video_src, final_video_dst)
    print("✅ Final video moved to internal storage")

# 6️⃣ Move audio with unique random name
audio_src = "/storage/emulated/0/PNI/audio.mp3"
if os.path.exists(audio_src):
    unique_name = f"{uuid.uuid4().hex}.mp3"
    audio_dst = f"/storage/emulated/0/{unique_name}"
    shutil.move(audio_src, audio_dst)
    print(f"✅ Audio moved as {unique_name}")

print("\n🎉 VBot cleanup completed successfully!")
