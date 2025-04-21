import asyncio
from pydantic import BaseModel
from ollama import chat
import aiofiles
import asyncio.subprocess


# Schema for a single scene
class SceneJson(BaseModel):
    classname: str
    code: str


# Schema for the generated prompt
class PromptJson(BaseModel):
    prompt: str


# Async function to enrich user prompt using Ollama
async def manim_prompt_generator_agent(user_input: str) -> str:
    response = await asyncio.to_thread(
        chat,
        model='llama3.1:8b',
        messages=[
            {
                'role': 'system',
                'content': (
                    "You are an expert prompt generator for Manim scenes. "
                    "Rewrite and enrich the given prompt: {user_input} "
                    "for impressive Manim Python code generation."
                )
            },
            {'role': 'user', 'content': user_input},
        ],
        format=PromptJson.model_json_schema(),
        options={'temperature': 0},
    )
    result = PromptJson.model_validate_json(response.message.content)
    return result.prompt


# Async function to generate Manim code using enriched prompt
async def main_agent(prompt: str) -> SceneJson:
    response = await asyncio.to_thread(
        chat,
        model='llama3.1:8b',
        messages=[
            {
                'role': 'system',
                'content': (
                    "You only generate Python Manim code. "
                    "No markdown or explanation. "
                    "Import all required libs from manim in code. "
                    "If code generated is LaTeX, render with Manim."
                )
            },
            {'role': 'user', 'content': prompt},
        ],
        format=SceneJson.model_json_schema(),
        options={'temperature': 0},
    )
    return SceneJson.model_validate_json(response.message.content)


# Main async runner
async def main(user_input: str):
    prompt = await manim_prompt_generator_agent(user_input)
    print(f"\n🧠 Enriched Prompt:\n{prompt}\n")

    scene = await main_agent(prompt)

    # Save the generated Manim code to a file
    async with aiofiles.open("main.py", "w") as f:
        await f.write(scene.code)

    print(f"\n🧾 Manim Code:\n{scene.code}")
    print(f"\n🎬 Scene Class: {scene.classname}")

    # Run Manim using asyncio subprocess
    print("\n🚀 Running Manim...")
    process = await asyncio.create_subprocess_exec(
        "uv", "run", "manim", "-pql", "main.py", scene.classname,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    print(stdout.decode())
    if stderr:
        print("❌ Error:\n", stderr.decode())


# REPL Loop
if __name__ == "__main__":
    try:
        while True:
            user_input = input("🎨 Enter scene to generate (or type 'exit'): ").strip()
            if user_input.lower() == "exit":
                print("👋 Goodbye!")
                break
            asyncio.run(main(user_input))
    except KeyboardInterrupt:
        print("\n👋 Interrupted. Exiting.")
