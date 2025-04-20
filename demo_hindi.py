import json
import os
import subprocess
import soundfile as sf
import numpy as np
from manim import *
from misaki.espeak import EspeakG2P
from kokoro_onnx import Kokoro

# === TTS Setup ===
g2p = EspeakG2P(language="hi")
kokoro = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")

OUTPUT_FOLDER = "output_scenes"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# === Generate Scene ===
def scene_generator(line1, line2, classname=1):
    scene_name = f"text_{classname}"
    filename = "main_temp.py"

    # Escape quotes
    line1 = line1.replace('"', '\\"')
    line2 = line2.replace('"', '\\"')

    manim_script = f"""
from manim import *

class {scene_name}(Scene):
    def construct(self):
        t1 = Text("{line1}", font_size=48)
        t1[:].color = YELLOW
        t2 = Text("{line2}", font_size=42)
        t2[:].color = GREEN
        t3 = VGroup(t1, t2)
        t3.arrange(DOWN)
        self.play(Write(t3))
        self.wait(3)
"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(manim_script)

    subprocess.run(["manim", "-pql", filename, scene_name])

    video_path = f"media/videos/{filename[:-3]}/480p15/{scene_name}.mp4"
    return video_path, scene_name

# === Generate Audio from Text ===
def generate_audio(text, output_file):
    phonemes, _ = g2p(text)
    samples, sample_rate = kokoro.create(phonemes, "hf_alpha", is_phonemes=True)
    sf.write(output_file, samples, sample_rate)
    print(f"🔊 Audio created: {output_file} | {len(samples)/sample_rate:.2f}s")

# === Generate Silent Audio ===
def generate_silent_audio(output_file, duration=4.0, sample_rate=22050):
    samples = np.zeros(int(sample_rate * duration), dtype=np.float32)
    sf.write(output_file, samples, sample_rate)
    print(f"🤫 Silent audio created: {output_file} | {duration:.2f}s")

# === Combine Audio + Video ===
def combine_audio_video(video_path, audio_path, output_path):
    subprocess.run([
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_path
    ])

# === Main Function ===
def main(json_file="questions.json", key1="Question", key2="Answer"):
    with open(json_file, "r", encoding="utf-8") as f:
        data_list = json.load(f)

    final_videos = []

    for i, item in enumerate(data_list, start=1):
        line1 = item.get(key1, "").strip()
        line2 = item.get(key2, "").strip()
        include_audio = item.get("include_audio", True)

        if not line1 or not line2:
            continue

        print(f"🎬 Scene {i}: {line1} → {line2} | Audio: {include_audio}")
        raw_video_path, scene_name = scene_generator(line1, line2, classname=i)

        output_video = os.path.join(OUTPUT_FOLDER, f"scene_{i}.mp4")
        audio_file = os.path.join(OUTPUT_FOLDER, f"audio_{i}.wav")

        if include_audio:
            full_text = f"{line1} {line2}"
            generate_audio(full_text, audio_file)
        else:
            generate_silent_audio(audio_file, duration=4.0)  # 4 sec silence

        combine_audio_video(raw_video_path, audio_file, output_video)
        final_videos.append(output_video)

    # === Merge All Final Videos ===
    with open("merge_list.txt", "w", encoding="utf-8") as f:
        for v in final_videos:
            f.write(f"file '{os.path.abspath(v)}'\n")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", "merge_list.txt",
        "-c", "copy", "merged_output.mp4"
    ])

    print("✅ Final video created: merged_output.mp4")

if __name__ == "__main__":
    main(json_file="questions.json", key1="Question", key2="Answer")
