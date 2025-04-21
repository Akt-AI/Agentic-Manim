from pydantic import BaseModel
import subprocess

from ollama import chat


# Define the schema for the response
class SceneJson(BaseModel):
  classname: str
  code: str
  

class SceneInfo(BaseModel):
  outputs: list[SceneJson]


# Define the schema for the response
class PromptJson(BaseModel):
  prompt: str
  

class PromptInfo(BaseModel):
  outputs: list[PromptJson]


def manim_prompt_generator_agent(user_input):
  response = chat(
    model='llama3.1:8b',
    messages=[
              {'role': 'system', 
              'content':"""You are a expert prompt generator for manim Scenes.
              rewrite and enrich the given prompt: {user_input} for impressive manim python code generation.  
              """},
              {'role': 'user', 
              'content': user_input},

      ],
    format=PromptJson.model_json_schema(),  # Use Pydantic to generate the schema or format=schema
    options={'temperature': 0},  # Make responses more deterministic
  )
  response = PromptJson.model_validate_json(response.message.content)
  prompt = response.prompt
  return prompt


def main_agent(user_input):
  response = chat(
    model='llama3.1:8b',
    messages=[
              {'role': 'system', 
              'content':"You only generate Python Manim code." 
                   "No markdown or explanation. "
                   "Import all required libs from manim in code. "
                   "If code generated is latex render wiith Manim"},
              {'role': 'user', 
              'content': user_input},

      ],
    format=SceneJson.model_json_schema(),  # Use Pydantic to generate the schema or format=schema
    options={'temperature': 0},  # Make responses more deterministic
  )
  response = SceneJson.model_validate_json(response.message.content)
  
  return response

def main(user_input):
  prompt = manim_prompt_generator_agent(user_input)
  # Use Pydantic to validate the response
  print(prompt)
  response = main_agent(prompt)
  
  with open("main.py", 'w') as f:
    f.write(response.code)
  print(response.code)
  print(response.classname)
  out = subprocess.run(["uv", "run", "manim", "-pql", "main.py", response.classname])
  return out


if __name__=="__main__":
  while True:
    user_input = input("Enter scene to Generate:")
    main(user_input)