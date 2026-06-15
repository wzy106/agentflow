"""
Day 3-5 + Day 11：Agent 核心 —— 完整版 ReAct 循环
====================================================
从简化版（只调一轮工具）升级为完整版（while 循环，AI 可连续调用多个工具）。
ReAct 循环：Think → Act → Observe → Repeat → Answer
"""

import json
# json = Python 自带的 JSON 处理模块。
# 本文件用它：json.loads(str) → JSON 字符串转 Python 字典。
# 为什么需要？AI 返回的参数是字符串 '{"expression":"2+2"}'，
# 不能直接用 [] 取值，必须先 json.loads() 转成字典。

import os
# 只用 os.getenv() 从内存读取环境变量（load_dotenv() 加载的 .env 内容）

from dotenv import load_dotenv
# load_dotenv() 把 .env 文件抄到内存 os.environ 字典

from openai import OpenAI
# OpenAI 是通信协议名，不是只连 OpenAI 公司。
# 改 base_url 就能连 DeepSeek、Ollama 等任何兼容服务。

from tools import execute, get_all_schemas
# execute(name, **kwargs)        → 按名字执行工具（查字典 → 调函数）
# get_all_schemas()              → 获取所有工具的说明书（给 AI 看）

load_dotenv()
# 把 .env 里的三行密码加载到内存

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
)
# 创建 API 客户端。参数名 api_key/base_url 是库定死的，必须小写。
# 变量名 client 是你起的，可以随便换。


# ====== 核心函数 ======

def chat(user_input: str) -> str:
#          ^^^^^^^^^^^^         ^^^^^^
#     参数：用户输入字符串       返回：AI 的回复字符串
    """完整版 ReAct 循环——AI 可以连续调用多个工具，直到信息够了为止"""

    # ====== 第 1 步：构建对话记录 ======
    messages = [
        {"role": "system", "content": "你是一个助手。遇到计算、搜索、代码执行必须用对应工具，不要自己猜。"},
        {"role": "user", "content": user_input},
    ]

    # ====== 第 2 步：ReAct 循环 ======
    max_steps = 10      # 最多循环 10 次，防止死循环
    step = 0            # 当前步数计数器

    while step < max_steps:
        step += 1

        # 每轮都拿工具说明书 + 传 tools 参数
        # 和简化版的区别：不只是第一轮传 tools，每一轮都传！
        # 因为 AI 每轮都可能需要继续调工具。
        tools = get_all_schemas()
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL"),
            messages=messages,
            tools=tools,        # 每轮都传——AI 随时可以调新工具
        )
        msg = response.choices[0].message

        # ====== 不需要工具 → 这是最终回答！ ======
        if not msg.tool_calls:
            return msg.content
            # 简化版这里要手动调第二轮（不带 tools）做总结。
            # 完整版不需要——while 循环本身就是"持续调工具"的过程。
            # AI 觉得够了就停止返回 tool_calls，直接输出自然语言回答。

        # ====== 需要工具 → 构建 assistant 消息 ======
        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in msg.tool_calls
            ]
        })

        # ====== 逐个执行工具 ======
        for tc in msg.tool_calls:
            func_name = tc.function.name
            func_args = json.loads(tc.function.arguments)
            result = execute(func_name, **func_args)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })
        # 循环回到 while 顶部——工具结果已在 messages 里。
        # 下一轮 AI 看到工具结果，判断"还需要更多工具吗？"
        # 够 → 直接回答（tool_calls 为空 → 走 if 返回）。
        # 不够 → 继续调工具（tool_calls 不为空 → 再执行）。

    # 走到这里说明 10 步用完还没结束
    return "达到最大步数，暂时无法完成。请简化你的问题。"


# 简化版 vs 完整版 对比：
# ==========================
# 简化版：
#   if tool_calls → 执行 → 手动调第二轮（不带 tools）→ 结束
#   AI 只能做一次工具调用，第二轮不准再调工具。
#
# 完整版：
#   while 未完成 → 每轮都带 tools → AI 随时可以继续调 → 够了才停
#   AI 自主决定"什么时候停"——多轮搜索+计算+代码执行都可以。
#
# 完整版 ReAct 执行示例：
#   用户："搜今天北京气温，转成华氏度"
#   Step 1：LLM → web_search("北京气温") → 35°C
#   Step 2：LLM 看到 35°C，觉得还不够 → calculate("35*9/5+32") → 95°F
#   Step 3：LLM 信息够了 → "北京今天 35°C = 95°F"
#   三步，两个工具，一次对话。简化版做不到，完整版做到了。


# ====== 测试 ======
if __name__ == "__main__":
    # __name__ == "__main__"：直接运行本文件才执行测试
    # 被别人 import 时不执行

    print("测试 1：计算")
    print(chat("12345 乘以 67890 等于多少"))
    print("\n" + "=" * 50 + "\n")

    print("测试 2：搜索")
    print(chat("搜索 Python 最新版本"))
    print("\n" + "=" * 50 + "\n")

    print("测试 3：代码执行")
    print(chat("写 Python 代码计算斐波那契数列前 20 项的和"))


# ====== Q&A 问答笔记 ======
#
# Q1: chat() 函数的完整流程是什么？
# A1: 构建 messages → 拿说明书 → 第一轮调 AI（带 tools）→
#     AI 返回 tool_calls → 逐个执行工具 → 结果追加进 messages →
#     第二轮调 AI（不带 tools）→ 返回最终回答。
#     这是"简化版 ReAct"——只调一轮工具就结束。
#
# Q2: 为什么第一轮传 tools，第二轮不传？
# A2: 第一轮：AI 需要 tools 来决定"要不要用工具、用什么工具"。
#     第二轮：工具结果已在 messages 里，AI 只需"总结"，不需要再动手。
#     完整版 ReAct 会循环传 tools，因为 AI 可能需要多次调工具。
#
# Q3: if not msg.tool_calls 是什么意思？
# A3: tool_calls 为 None 或空列表时 → not True → 进 if → 直接返回文本。
#     tool_calls 有内容时 → not False → 跳过 → 执行工具调用。
#
# Q4: json.loads() 为什么必须用？
# A4: AI 返回的 arguments 是 JSON 字符串（'{"expression":"2+2"}'），
#     不能直接用方括号取值。json.loads() 转成字典后才能 ["expression"]。
#
# Q5: tool_call_id 为什么不能省略？
# A5: OpenAI 协议要求——如果 AI 同时调了多个工具，它靠 ID 区分
#     哪个工具调用（tool_call）对应哪个返回结果（tool 消息）。
#
# Q6: messages.append(msg) 为什么要放在工具执行之前？
# A6: OpenAI 要求对话顺序必须是 system → user → assistant(tool_calls) → tool(结果)。
#     assistant 消息必须在 tool 消息之前，不然 API 报错。
#
# Q7: 简化版和完整版 ReAct 有什么区别？（Day 11 已升级为完整版）
# A7: 简化版：if tool_calls → 执行 → 手动第二轮（不带 tools）→ 结束。
#     完整版：while 循环 → 每轮都带 tools → AI 觉得够了就停。
#     区别①——循环方式：if vs while（前者只执行一次工具，后者循环直到满意）
#     区别②——tools 参数：简化版第二轮不带 tools，完整版每轮都带
#     区别③——结束条件：简化版手动写第二轮，完整版 AI 自己决定"信息够了"
#
# Q8: 为什么完整版每轮都传 tools？
# A8: 因为 AI 可能在第 2 步发现"我还需要另一个工具"。
#     如果第二轮不带 tools，AI 想继续调但没说明书——调不了。
#
# Q9: max_steps = 10 是干嘛的？
# A9: 防止死循环。AI 可能在某个问题上反复调工具但永远觉得不够。
#     10 步是安全阀——超了就返回错误信息，不会无限循环烧钱。
#
# Q10: 完整版 ReAct 和简化版在实际使用中有什么区别？
# A10: 简化版适合"单一工具"场景——只计算、只搜索。
#      完整版适合"多工具协作"——先搜再算、算完再搜验证。
#      面试被问"你的 Agent 怎么实现的"，讲完整版。
#
# Q11: messages.append({"role":"assistant","tool_calls":[...]}) 为什么手动构建而不是直接 messages.append(msg)？
# A11: msg 是 SDK 的 Pydantic 模型对象。agent.py 可以直接用（SDK 后续调用时内部转换），
#      但手动拆成纯字典的好处：数据结构透明不依赖 SDK 实现，和 server.py 保持一致，方便调试。
#
# Q12: 哪些是 OpenAI 定死的变量名，哪些是自己起的？
# A12: 引号里的键名 = OpenAI 定的（"role","assistant","tool","content","tool_calls","id","type",
#      "function","name","arguments","tool_call_id"）——一个字母不能改。
#      引号外的变量名 = 你起的（messages, msg, tc, func_name, func_args, result）。
#      点号右边如 .function、.name、.id 也是 SDK 定死的属性名——不用引号但也不能改。
#      记忆口诀：引号里 = 别人定的；引号外 = 你起的；点号右边 = 别人定的。
#
# Q13: for tc in msg.tool_calls 和列表推导式分别干什么？
# A13: 列表推导式 [{"id":tc.id,...} for tc in msg.tool_calls] 把 SDK 对象拆成纯字典，
#      放进 assistant 消息的 tool_calls 字段。
#      for tc in msg.tool_calls 遍历 AI 要调的每个工具，逐个执行。
#      即使 AI 只调了一个工具，tool_calls 也是列表——for 循环统一处理。
#
# Q14: msg.content or "" 是干什么？
# A14: or 短路逻辑。msg.content 有文字 → 取文字。msg.content 是 None → 取 ""。
#      AI 有时只返回 tool_calls 不给 content（不写思考文字直接调工具）。
#      None 写进 messages 里 OpenAI API 不认，用 or "" 兜底。
#
# Q15: 执行工具后 messages.append({"role":"tool",...}) 为什么必须有 tool_call_id？
# A15: OpenAI 协议强制要求。AI 调的每个工具有唯一 ID（tc.id），
#      工具结果必须带同一个 ID。AI 靠 ID 匹配"哪个调用对应哪个结果"。
#      同时调两个工具时 ID 确保返回结果不会对错号。
