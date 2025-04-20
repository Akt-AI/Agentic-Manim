import os
import json
import subprocess
import asyncio
import tempfile
import numpy as np
import soundfile as sf
from textwrap import wrap
from manim import *
from kokoro_onnx import Kokoro, SAMPLE_RATE

# === Initialize Kokoro ===
kokoro = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")

OUTPUT_FOLDER = "output_scenes"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# === Async enumerate helper ===
from typing import AsyncIterator, Tuple

async def aenumerate(aiter: AsyncIterator, start: int = 0):
    i = start
    async for item in aiter:
        yield i, item
        i += 1

# === Scene Generator ===
def scene_generator(line1, line2, classname=1, audio_duration=None):
    scene_name = f"text_{classname}"
    filename = "main_temp.py"

    wrapped_line1 = "\\n".join(wrap(line1.replace('"', '\\"'), width=40))
    wrapped_line2 = "\\n".join(wrap(line2.replace('"', '\\"'), width=60))

    # Use audio duration to adjust wait time
    wait_time = max(3, int(audio_duration) + 1) if audio_duration else 3

    manim_script = f"""
from manim import *

class {scene_name}(Scene):
    def construct(self):
        t1 = Paragraph("{wrapped_line1}", alignment='center', font_size=52).scale_to_fit_width(config.frame_width * 0.9)
        t1.set_color(YELLOW)
        t2 = Paragraph("{wrapped_line2}", alignment='center', font_size=64).scale_to_fit_width(config.frame_width * 0.9)
        t2.set_color(GREEN)
        group = VGroup(t1, t2).arrange(DOWN, buff=0.8).move_to(ORIGIN)
        self.play(FadeIn(group, shift=UP, scale=0.9))
        self.wait({wait_time})
        self.play(FadeOut(group, shift=DOWN))
"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(manim_script)

    subprocess.run(["manim", "-pql", filename, scene_name])
    return f"media/videos/{filename[:-3]}/480p15/{scene_name}.mp4", scene_name

# === Audio Generation with Streaming + Disk Write ===
async def generate_combined_audio(text, output_path, voice="af_heart"):
    stream = kokoro.create_stream(
        text=text,
        voice=voice,
        speed=1.0,
        lang="en-us",
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        chunk_files = []
        async for idx, (samples, _) in aenumerate(stream, start=1):
            chunk_path = os.path.join(temp_dir, f"chunk_{idx}.wav")
            sf.write(chunk_path, samples, SAMPLE_RATE)
            print(f"✅ Wrote chunk {idx} to {chunk_path}")
            chunk_files.append(chunk_path)

        combined_audio = []
        silence = np.zeros(int(1 * SAMPLE_RATE), dtype=np.float32)  # 1 second silence
        combined_audio.append(silence)  # Start silence

        for file in chunk_files:
            audio, _ = sf.read(file, dtype="float32")
            combined_audio.append(audio)

        combined_audio.append(silence)  # End silence
        final_audio = np.concatenate(combined_audio)
        sf.write(output_path, final_audio, SAMPLE_RATE)
        print(f"🎉 Final audio written: {output_path} ({len(final_audio)/SAMPLE_RATE:.2f}s)")
        return len(final_audio) / SAMPLE_RATE

# === Silent Audio Generator ===
def generate_silent_audio(output_path, duration=4.0):
    silent = np.zeros(int(SAMPLE_RATE * duration), dtype=np.float32)
    sf.write(output_path, silent, SAMPLE_RATE)
    print(f"🤫 Silent audio: {output_path} ({duration}s)")
    return duration

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

# === Main Async Runner ===
async def main(json_file="questions.json", key1="Question", key2="Answer"):
    with open(json_file, "r", encoding="utf-8") as f:
        data_list = json.load(f)

    final_videos = []

    for i, item in enumerate(data_list, start=1):
        line1 = item.get(key1, "").strip()
        line2 = item.get(key2, "").strip()
        include_audio = item.get("include_audio", True)

        if not line1 or not line2:
            continue

        print(f"🎬 Scene {i}: {line1} | {line2} | Audio: {include_audio}")

        audio_file = os.path.join(OUTPUT_FOLDER, f"audio_{i}.wav")
        output_video = os.path.join(OUTPUT_FOLDER, f"scene_{i}.mp4")

        if include_audio:
            combined_text = f"{line1}. {line2}"
            audio_duration = await generate_combined_audio(combined_text, audio_file)
        else:
            audio_duration = generate_silent_audio(audio_file, duration=4.0)

        raw_video_path, _ = scene_generator(line1, line2, classname=i, audio_duration=audio_duration)

        combine_audio_video(raw_video_path, audio_file, output_video)
        final_videos.append(output_video)

    # Merge all final videos
    with open("merge_list.txt", "w") as f:
        for path in final_videos:
            f.write(f"file '{os.path.abspath(path)}'\n")

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", "merge_list.txt", "-c", "copy", "merged_output.mp4"
    ])

    print("✅ Final video created: merged_output.mp4")

if __name__ == "__main__":
    asyncio.run(main(json_file="agents.json", key1="Question", key2="Answer"))
