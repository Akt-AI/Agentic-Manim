import asyncio

from ollama import AsyncClient


async def main(user_input, model_name):
  messages = [
    {
      'role': 'system',
      'content': "You only generate python code. No other text",
    },
    {
      'role': 'tool',
      'content': user_input,
    },
  ]

  client = AsyncClient()
  response = await client.chat(model_name, messages=messages)
  print(response['message']['content'])


if __name__ == '__main__':
  while True:
    model_name = "qwen2.5-coder:0.5b"
    # model_name = "marco-o1:latest"
    
    user_input = input("Enter Your Query:")
    asyncio.run(main(user_input, model_name))