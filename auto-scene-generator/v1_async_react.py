import asyncio
from pydantic import BaseModel
from ollama import chat
import aiofiles
import asyncio.subprocess


class SceneJson(BaseModel):
    classname: str
    code: str


class PromptJson(BaseModel):
    prompt: str


# Generate enriched prompt
async def generate_prompt(user_input: str) -> str:
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
    return PromptJson.model_validate_json(response.message.content).prompt


# Generate Manim scene code
async def generate_code(prompt: str) -> SceneJson:
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


# Save code to file
async def save_code_to_file(code: str):
    async with aiofiles.open("main.py", "w") as f:
        await f.write(code)


# Run Manim
async def run_manim(classname: str):
    print("Action: Running Manim render...")
    process = await asyncio.create_subprocess_exec(
        "uv", "run", "manim", "-pql", "main.py", classname,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    return stdout.decode(), stderr.decode()


# ReAct-style main function with retries
async def react_manim_agent(user_input: str):
    print("Thought: I will generate an enriched prompt for a Manim scene.")
    prompt = await generate_prompt(user_input)
    print("Observation: Prompt generated.\n")

    for attempt in range(1, 4):
        print(f"--- 🔁 Attempt {attempt}/3 ---")
        print("Thought: I will generate Python Manim code based on the prompt.")
        scene = await generate_code(prompt)

        print("Observation: Code generated.")
        print(f"Scene Class: {scene.classname}")
        print(f"Code:\n{scene.code[:200]}...\n")

        await save_code_to_file(scene.code)
        print("Observation: Code written to main.py")

        stdout, stderr = await run_manim(scene.classname)
        print("Observation: Manim process completed.")

        if stderr.strip() == "":
            print("✅ Final Result: Manim rendered successfully!\n")
            print(stdout)
            return

        print("❌ Error observed during Manim execution:")
        print(stderr)

        print("Thought: There was an error. I will try regenerating the prompt and code.")
        prompt = await generate_prompt(user_input + f" (fix error from previous attempt {attempt})")

    print("🛑 Final Result: Failed after 3 attempts. Please check the error above.")


# CLI Loop
if __name__ == "__main__":
    try:
        while True:
            user_input = input("🎨 Enter scene to generate (or type 'exit'): ").strip()
            if user_input.lower() == "exit":
                break
            asyncio.run(react_manim_agent(user_input))
    except KeyboardInterrupt:
        print("\n👋 Exiting.")

