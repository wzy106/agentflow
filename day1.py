import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
      api_key=os.getenv("OPENAI_API_KEY"),
      base_url=os.getenv("OPENAI_BASE_URL"),
  )

response = client.chat.completions.create(
      model=os.getenv("OPENAI_MODEL"),
      messages=[
          {"role":"system","content":"你是我的女朋友，说话非常萌，且甜甜的，但要回答对我的问题哦"},
          {"role": "user", "content": "你好，1314乘520等于几"}
      ],
  )
print(response.choices[0].message.content)
