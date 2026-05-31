# agent.py —— AI 自动调用工具（Day 5 版）

import json
import os
from dotenv import load_dotenv
from openai import OpenAI
from tools import execute, get_all_schemas

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
)


def chat(user_input: str) -> str:
    """和 AI 对话，AI 需要时会自动调用工具"""

    messages = [
        {"role": "system", "content": "你是一个助手。遇到计算、搜索、代码执行必须用对应工具，不要自己猜。"},
        {"role": "user", "content": user_input},
    ]

    tools = get_all_schemas()

    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL"),
        messages=messages,
        tools=tools,
    )

    msg = response.choices[0].message

    if not msg.tool_calls:
        return msg.content

    messages.append(msg)

    for tool_call in msg.tool_calls:
        func_name = tool_call.function.name
        func_args = json.loads(tool_call.function.arguments)
        result = execute(func_name, **func_args)

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result,
        })

    final_response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL"),
        messages=messages,
    )

    return final_response.choices[0].message.content


if __name__ == "__main__":
    print("测试 1：计算")
    print(chat("12345 乘以 67890 等于多少"))
    print("\n" + "=" * 50 + "\n")

    print("测试 2：搜索")
    print(chat("搜索 Python 最新版本"))
    print("\n" + "=" * 50 + "\n")

    print("测试 3：代码执行")
    print(chat("写 Python 代码计算斐波那契数列前 20 项的和"))
