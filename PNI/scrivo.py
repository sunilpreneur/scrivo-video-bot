import subprocess
import sys
import os

# ========= SCRIPT PATHS =========
STEP_1 = "/storage/emulated/0/PNI/yt_gemini_pipeline.py"
STEP_2 = "/storage/emulated/0/PNI/tts_edge_long.py"
STEP_3 = "/storage/emulated/0/PNI/srtmaker.py"
STEP_4 = "/storage/emulated/0/PNI/deepseek_keyplacer.py"
STEP_5 = "/storage/emulated/0/PNI/vbot.py"


def run_step(step_name, script_path):
    print(f"\n🚀 Running: {step_name}")
    try:
        subprocess.run(
            ["python", script_path],
            check=True
        )
        print(f"✅ Completed: {step_name}")
    except subprocess.CalledProcessError:
        print(f"❌ FAILED: {step_name}")
        print("🛑 Scrivo stopped due to error.")
        sys.exit(1)


def notify_done():
    # Toast
    os.system('termux-toast "Scrivo Completed 🎉"')

    # Notification
    os.system(
        'termux-notification '
        '--sound '
        '--title "Scrivo" '
        '--content "All tasks completed successfully 🎉"'
    )


def main():
    print("🧠 SCRIVO PIPELINE STARTED")

    run_step("Script Writer (YT → Script)", STEP_1)
    run_step("Voiceover (Edge TTS)", STEP_2)
    run_step("SRT Maker", STEP_3)
    run_step("Keyword Placer (DeepSeek)", STEP_4)
    run_step("VBOT (Final Video Build)", STEP_5)

    print("\n🎉 SCRIVO: ALL STEPS COMPLETED SUCCESSFULLY")
    notify_done()


if __name__ == "__main__":
    main()
