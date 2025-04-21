import asyncio
from pydantic import BaseModel
from ollama import chat
import logging
import subprocess

model = "qwen2.5-coder:0.5b"

# --- Logging Setup ---
logging.basicConfig(
    filename="agent.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
def log(msg):
    print(msg)
    logging.info(msg)


# --- Pydantic Schemas ---
class SceneJson(BaseModel):
    classname: str
    code: str

class PromptJson(BaseModel):
    prompt: str

class ErrorAnalysisJson(BaseModel):
    summary: str

class CodeFixJson(BaseModel):
    code: str


# --- Prompt Generator ---
async def generate_prompt(user_input: str) -> str:
    log("Thought: Generating enriched prompt.")
    response = await asyncio.to_thread(
        chat,
        model=model,
        messages=[
            {
                'role': 'system',
                'content': (
                    "You are an expert prompt generator for Manim scenes. "
                    "Rewrite and enrich the given prompt for impressive Manim Python code generation."
                )
            },
            {'role': 'user', 'content': user_input},
        ],
        format=PromptJson.model_json_schema(),
        options={'temperature': 0},
    )
    prompt = PromptJson.model_validate_json(response.message.content).prompt
    log(f"Observation: Prompt generated.\nPrompt: {prompt}")
    return prompt


# --- Error Analysis Agent ---
async def analyze_error(error_text: str) -> str:
    log("Action: Analyzing error with error analysis agent.")
    response = await asyncio.to_thread(
        chat,
        model=model,
        messages=[
            {
                'role': 'system',
                'content': (
                    "You are a helpful AI that extracts only the key actionable error message "
                    "from technical logs for fixing Python code."
                )
            },
            {'role': 'user', 'content': f"Extract key error from this:\n{error_text}"},
        ],
        format=ErrorAnalysisJson.model_json_schema(),
        options={'temperature': 0.3},
    )
    summary = ErrorAnalysisJson.model_validate_json(response.message.content).summary
    log(f"Observation: Key error extracted: {summary}")
    return summary


# --- Bug Fix Agent ---
async def fix_code_agent(code: str, error: str) -> str:
    log("Action: Fixing code based on error analysis.")
    response = await asyncio.to_thread(
        chat,
        model=model,
        messages=[
            {
                'role': 'system',
                'content': (
                    "You are a Manim Python code fixer. "
                    "Given the existing buggy code and a key error message, rewrite the code to fix the issue. "
                    "Only return the corrected code as Python, no explanation."
                )
            },
            {'role': 'user', 'content': f"Code:\n{code}\n\nError:\n{error}"},
        ],
        format=CodeFixJson.model_json_schema(),
        options={'temperature': 0.2},
    )
    fixed_code = CodeFixJson.model_validate_json(response.message.content).code
    log("Observation: Fixed code generated.")
    return fixed_code


# --- Manim Code Generator ---
async def generate_code(prompt: str) -> SceneJson:
    log("Thought: Generating Manim Python code.")
    response = await asyncio.to_thread(
        chat,
        model=model,
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
    scene = SceneJson.model_validate_json(response.message.content)
    log(f"Observation: Code generated for scene `{scene.classname}`.")
    return scene


# --- Save Code to File ---
def save_code_to_file(code: str):
    with open("main.py", "w") as f:
        f.write(code)
    log("Observation: Code written to main.py")


# --- Run Manim ---
async def run_manim(classname: str):
    log(f"Action: Running Manim for class `{classname}`.")
    process = await asyncio.create_subprocess_exec(
        "uv", "run", "manim", "-pql", "main.py", classname,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    return stdout.decode(), stderr.decode()


# --- Main Agent Loop ---
async def react_manim_agent(user_input: str):
    log(f"\n🎨 New Request: {user_input}")
    
    prompt = await generate_prompt(user_input)
    scene = await generate_code(prompt)
    current_code = scene.code
    current_classname = scene.classname

    for attempt in range(1, 4):
        log(f"\n--- 🔁 Attempt {attempt}/3 ---")

        save_code_to_file(current_code)
        print(current_code)
        stdout, stderr = await run_manim(current_classname)

        if stderr.strip() == "":
            log("✅ Final Result: Manim rendered successfully!")
            log(stdout)
            return

        log("❌ Error during Manim rendering:")
        log(stderr)

        key_error = await analyze_error(stderr)
        current_code = await fix_code_agent(current_code, key_error)

    log("🛑 Final Result: Failed after 3 attempts. Please check `agent.log` for full trace.")


# --- CLI Entry ---
if __name__ == "__main__":
    try:
        while True:
            user_input = input("🎨 Enter scene to generate (or type 'exit'): ").strip()
            if user_input.lower() == "exit":
                print("👋 Goodbye!")
                break
            asyncio.run(react_manim_agent(user_input))
    except KeyboardInterrupt:
        print("\n👋 Interrupted. Exiting.")
