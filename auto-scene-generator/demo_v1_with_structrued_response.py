from pydantic import BaseModel
import subprocess

from ollama import chat


# Define the schema for the response
class SceneJson(BaseModel):
  classname: str
  code: str
  

class SceneInfo(BaseModel):
  friends: list[SceneJson]


def main(user_input):
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

  # Use Pydantic to validate the response
  response = SceneJson.model_validate_json(response.message.content)
  
  with open("main.py", 'w') as f:
    f.write(response.code)
  print(response.code)
  print(response.classname)
  subprocess.run(["uv", "run", "manim", "-pql", "main.py", response.classname])


if __name__=="__main__":
  while True:
    user_input = input("Enter scene to Generate:")
    main(user_input)