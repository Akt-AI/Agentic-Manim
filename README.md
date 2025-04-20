Here’s a comprehensive `README.md` for your project:

---

# 🎬 Kokoro Manim Audio-Visual Generator

This project creates synchronized animated scenes using **Manim** and **Kokoro TTS**, combining custom question-answer content (or any text) into fully narrated educational or presentation-style videos. Output is trimmed and cleaned, perfect for YouTube, reels, or slideshows.

---

## 📦 Features

- ✅ Scene generation with Manim for each Q&A pair
- ✅ Audio narration using `kokoro-onnx` streaming API
- ✅ Automatic silence padding before and after audio
- ✅ Syncs video length to audio duration
- ✅ Merges all scenes into a single video
- ✅ Trims first 2 seconds of the final video to remove unwanted pauses

---

## 🧰 Requirements

Install dependencies using `uv` or `pip`:

```bash
pip install manim soundfile kokoro-onnx
```

Download Kokoro model files:

```bash
wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
```

---

## 📁 Input Format

Create a JSON file (`questions.json`) like this:

```json
[
  {
    "Question": "Welcome to Agentic AI!",
    "Answer": "Let’s learn something amazing.",
    "include_audio": true
  },
  {
    "Question": "What is an Autonomous Agent?",
    "Answer": "An agent that can take actions on its own.",
    "include_audio": true
  }
]
```

---

## 🚀 Running the Script

Simply run:

```bash
python main.py
```

or if using asyncio:

```bash
python -m asyncio main.py
```

This will generate:
- `output_scenes/scene_X.mp4` – each narrated video
- `merged_output.mp4` – all scenes combined
- `merged_output_trimmed.mp4` – final video with 2s trimmed from start

---

## 🖼️ Output Visuals

- Text arranged and animated using `FadeIn` and `FadeOut`
- Font sizes optimized for clarity
- Color-coded: yellow for questions, green for answers

---

## 🧠 Customization

- Change font size, colors, or animation in `scene_generator()`
- Replace `voice="af_nicole"` with other Kokoro-compatible voices
- Adjust silence or trim duration in `generate_combined_audio()` and `ffmpeg` command

---

## 📂 Output Structure

```
output_scenes/
├── audio_1.wav
├── scene_1.mp4
├── ...
merge_list.txt
merged_output.mp4
merged_output_trimmed.mp4
```

---

## 📜 License

This project uses open-source libraries including [kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx), [ManimCE](https://docs.manim.community/), and [SoundFile](https://pysoundfile.readthedocs.io/).

---

Would you like me to paste this into a `README.md` file in your current directory?
