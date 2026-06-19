"""
Day 6：Web 服务 —— 把 Agent 变成网页（已更新 Q&A 21 条）
=========================================================
用 FastAPI 把之前命令行里的 Agent 变成浏览器可访问的网页服务。
前端（HTML）是装修，后端（/chat 接口 + SSE）是你的专业范围。
"""

import json
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
# FastAPI              → Python 的 Web 框架，创建网页服务
# Request              → 请求对象，前端发来的所有数据

from fastapi.responses import HTMLResponse, StreamingResponse
# HTMLResponse          → 返回网页
# StreamingResponse      → 返回持续推送的数据流（SSE）

from openai import OpenAI

from tools import execute, get_all_schemas
from memory import ConversationMemory
from rag import rag

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
)

# 全局记忆——server.py 也需要日记本！
memory = ConversationMemory(
    system_prompt="你是一个助手。遇到计算、搜索、代码执行必须用工具。用中文回答。"
)

app = FastAPI(title="AgentFlow")
# FastAPI() 创建 Web 应用——"开一家店"
# title 显示在自动生成的 API 文档页面（/docs）上


# ====== 首页（前端内容——后端面试不需要深究） ======
@app.get("/", response_class=HTMLResponse)
# @app.get("/") = 装饰器，把函数绑定到"访问首页"这件事上
# 浏览器打开 http://localhost:8000 → 执行 home() → 返回下面的 HTML
async def home():
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AgentFlow</title>
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
        background: #1a1a2e; color: #eee;
        font-family: system-ui, sans-serif;
        height: 100vh; display: flex; flex-direction: column;
    }
    header {
        background: #16213e; padding: 14px 20px;
        font-size: 18px; font-weight: 600; border-bottom: 1px solid #0f3460;
    }
    #chat {
        flex: 1; overflow-y: auto; padding: 16px;
        display: flex; flex-direction: column; gap: 10px;
    }
    .msg {
        max-width: 75%; padding: 10px 14px; border-radius: 8px;
        line-height: 1.5; white-space: pre-wrap; word-break: break-word;
        animation: fadeIn 0.3s;
    }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } }
    .msg.user { align-self: flex-end; background: #0f3460; color: #fff; }
    .msg.ai { align-self: flex-start; background: #16213e; border: 1px solid #0f3460; }
    .msg.tool {
        align-self: flex-start; background: #1a1a2e;
        border: 1px solid #533483; font-size: 12px; color: #a0a0c0;
    }
    #input-area {
        background: #16213e; padding: 12px 16px; display: flex; gap: 8px;
        border-top: 1px solid #0f3460;
    }
    #input-area input {
        flex: 1; background: #1a1a2e; border: 1px solid #0f3460;
        border-radius: 6px; padding: 10px; color: #eee; font-size: 14px; outline: none;
    }
    #input-area button {
        background: #533483; color: #fff; border: none;
        border-radius: 6px; padding: 10px 18px; cursor: pointer; font-size: 14px;
    }
</style>
<!-- 以上 <style> 是 CSS——控制颜色和布局。后端面试不问。 -->
</head>
<body>
<header>AgentFlow — 我的 AI 助手</header>
<div id="chat">
    <div class="msg ai">你好！我能计算、搜索、执行代码。试试问我问题吧！</div>
</div>
<div id="input-area">
    <input id="userInput" placeholder="输入消息，按 Enter 发送..." autofocus>
    <button id="sendBtn">发送</button>
</div>
<script>
// 以下 <script> 是 JavaScript——前端逻辑。后端面试不问。
// 只需要知道：用户点发送 → JS 往 /chat 发 POST 请求 → 用 EventSource 接收 SSE 流
const chatBox = document.getElementById('chat');
const input = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
let sending = false;

function addMsg(role, text, cls) {
    const div = document.createElement('div');
    div.className = 'msg ' + (cls || role);
    div.textContent = text;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
    return div;
}

async function send() {
    const text = input.value.trim();
    if (!text || sending) return;
    sending = true;
    input.value = '';
    sendBtn.disabled = true;
    addMsg('user', text);

    try {
        const res = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text }),
        });
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buf = '';
        let finalDiv = null;

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buf += decoder.decode(value, { stream: true });
            const lines = buf.split('\\n');
            buf = lines.pop() || '';

            for (const line of lines) {
                if (!line.startsWith('data: ')) continue;
                try {
                    const d = JSON.parse(line.slice(6));
                    if (d.type === 'tool') {
                        addMsg('tool', '工具：' + d.tool + '\\n' + d.result, 'tool');
                    } else if (d.type === 'final') {
                        finalDiv = finalDiv || addMsg('ai', d.content);
                        finalDiv.textContent = d.content;
                    }
                } catch(e) {}
            }
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    } catch(e) {
        addMsg('ai', '错误：无法连接服务器');
    }
    sending = false;
    sendBtn.disabled = false;
    input.focus();
}

input.addEventListener('keydown', e => {
    if (e.key === 'Enter') send();
});
sendBtn.addEventListener('click', send);
</script>
</body>
</html>
"""


# ====== 聊天接口（SSE 流式推送）—— 后端核心！ ======
@app.post("/chat")
# @app.post("/chat") = 装饰器：浏览器 POST /chat 时执行这个函数
# 用户点发送 → 前端 fetch('/chat', {body: ...}) → 这个函数被调用
async def chat_endpoint(request: Request):
# ^^^^^                      ^^^^^^^^^^^^^^^^
# async def = 异步函数        FastAPI 的请求对象（前端发的所有数据都在里面）
    """接收用户消息，调用 Agent 处理，用 SSE 流式推送结果"""

    # ====== 解析请求 ======
    body = await request.json()
    # request.json() 把 HTTP 请求体中的 JSON 字符串转成 Python 字典
    # await = 等网络数据读完（不阻塞其他请求）
    # 前端发来的是：{"message": "35°C等于多少°F"}

    user_input = body.get("message", "")
    # .get(key, default) = 安全取值
    # key 存在 → 返回对应值
    # key 不存在 → 返回默认值 ""（不报错）
    # 对比：body["message"] 如果 key 不存在 → KeyError → 程序崩溃

    # ====== 异步生成器（核心引擎） ======
    async def stream():
    # 函数里定义函数 → 闭包。内层 stream() 能访问外层 user_input。
    # stream() 是一个异步生成器——用 yield 一条一条推送数据，而不是一次性返回。

        # ====== 推送 1：开始信号 ======
        yield "data: {}\n\n".format(json.dumps({"type": "start"}))
        # yield = 推一条给前端，然后暂停，等下一条好了再推。
        # 和 return 的区别：
        #   return → 返回后函数结束，后面代码不执行
        #   yield  → 返回后函数"待机"，下次从上一行继续
        #
        # SSE 消息格式：data: JSON内容\n\n
        #   data: → 前缀，浏览器识别
        #   \n\n  → 双换行，SSE 协议的消息分隔符
        #
        # .format() 而不是 f-string 的原因：
        #   JSON 里也是 {}，f-string 会混淆。.format() 只有一个占位符 {}。

        # ====== 把用户消息写入记忆（同 agent.py Day 12） ======
        memory.add_user_message(user_input)

        tools = get_all_schemas()
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL"),
            messages=memory.get_messages(),   # ← 从记忆拿全部历史
            tools=tools,
        )

        msg = response.choices[0].message

        # ====== 不需要工具 → 直接推送结果 ======
        if not msg.tool_calls:
            memory.add_assistant_message(msg.content)
            yield "data: {}\n\n".format(json.dumps({"type": "final", "content": msg.content}))
            yield "data: {}\n\n".format(json.dumps({"type": "done"}))
            return

        # ====== 需要工具 → 写入记忆 ======
        tool_calls_list = [
            {"id": tc.id, "type": "function",
             "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
            for tc in msg.tool_calls
        ]
        memory.add_assistant_message(msg.content or "", tool_calls_list)

        # ====== 逐个执行工具 ======
        for tc in msg.tool_calls:
            name = tc.function.name
            args = json.loads(tc.function.arguments)
            result = execute(name, **args)

            yield "data: {}\n\n".format(json.dumps({
                "type": "tool",
                "tool": name,
                "result": result,
            }))

            memory.add_tool_result(tc.id, result)

        # ====== 第二轮调 AI（总结） ======
        final = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL"),
            messages=memory.get_messages(),
        )

        # ====== 推送 3：最终回答 ======
        yield "data: {}\n\n".format(json.dumps({
            "type": "final",
            "content": final.choices[0].message.content,
        }))

        # ====== 推送 4：结束信号 ======
        yield "data: {}\n\n".format(json.dumps({"type": "done"}))

    # ====== 返回 SSE 流 ======
    return StreamingResponse(stream(), media_type="text/event-stream")
    # StreamingResponse  = FastAPI 内置的流式响应类
    # stream()           = 调用异步生成器（注意括号！调用后返回生成器对象）
    # media_type=        = 告诉浏览器：这不是普通 HTML，是 SSE 事件流
    #                      浏览器按 data: 前缀和 \n\n 分隔符解析每条消息


# ====== RAG 文档上传 ======
@app.post("/rag/upload")
async def rag_upload(request: Request):
    """上传文本到知识库"""
    body = await request.json()
    text = body.get("text", "")
    source = body.get("source", "上传文档")

    if not text.strip():
        return {"ok": False, "error": "内容为空"}

    count = rag.ingest(text, source)
    return {"ok": True, "chunks": count, "total": len(rag.chunks)}


# ====== RAG 检索 ======
@app.get("/rag/search")
async def rag_search(q: str = ""):
    """搜索知识库"""
    if not q.strip():
        return {"ok": False, "error": "查询为空"}
    results = rag.retrieve(q)
    return {"ok": True, "query": q, "results": results, "count": len(results)}


# ====== 启动服务器 ======
if __name__ == "__main__":
    import uvicorn
    # uvicorn = ASGI 服务器（跑 FastAPI 的程序）

    uvicorn.run(app, host="0.0.0.0", port=9000)
    #           ^^^   ^^^^^          ^^^^
    #           FastAPI 应用  0.0.0.0 = 监听所有网络接口
    #                          本机 + 局域网内其他设备都能访问
    #                          127.0.0.1 = 只有本机能访问
    #
    #           8000 = 服务的门牌号（端口）
    #           一台电脑跑多个服务，端口号区分它们
    #           你的 Agent = 8000 号房


# ====== Q&A 问答笔记 ======
#
# Q1: @app.get("/") 和 @app.post("/chat") 是什么？
# A1: 装饰器。把函数绑定到"访问这个路径"这件事上。
#     GET /  → 打开首页 → 执行 home() → 返回 HTML 网页
#     POST /chat → 发消息 → 执行 chat_endpoint() → 返回 SSE 流
#
# Q2: request.json() 是干什么的？
# A2: 把前端发来的 HTTP 请求体（JSON 字符串）转成 Python 字典。
#     前端发 '{"message": "你好"}' → request.json() → {"message": "你好"}
#
# Q3: .get(key, default) 和 [key] 有什么区别？
# A3: .get() key 不存在返回默认值，不报错。[key] key 不存在抛 KeyError。
#     用 .get() 防御——万一前端发错格式，程序继续跑。
#
# Q4: yield 和 return 的区别？
# A4: return → 一次性返回，函数结束。
#     yield  → 返回一条，函数暂停，下次从上一行继续推下一条。
#     SSE 流式推送靠 yield 实现——"边生成边推，不等到全完"
#
# Q5: SSE 消息格式为什么是 "data: JSON\n\n"？
# A5: data: 是 SSE 协议的前缀，浏览器 EventSource 识别。
#     \n\n 双换行是消息分隔符，每条消息独立。
#     这是 W3C 标准，不是自己定的。
#
# Q6: StreamingResponse 是什么？
# A6: FastAPI 内置的流式响应类。传一个生成器，逐条读 yield 的内容，
#     通过 HTTP 连接持续推送给浏览器。media_type 告诉浏览器"这是 SSE 流"。
#
# Q7: agent.py 和 server.py 的 chat 逻辑一样吗？
# A7: 核心逻辑完全一样——构建 messages、调 AI、执行工具、第二轮总结。
#     区别只有输出方式：agent.py 用 print 打印，server.py 用 yield 推送 SSE。
#
# Q8: uvicorn.run(app, host="0.0.0.0", port=8000) 各参数什么意思？
# A8: app = FastAPI 应用。host="0.0.0.0" = 监听所有网卡（局域网可访问）。
#     port=8000 = 门牌号。0.0.0.0 vs 127.0.0.1：
#       127.0.0.1 → 只有本机能打开 localhost:8000
#       0.0.0.0   → 局域网内手机/其他电脑也能通过你的 IP 访问
#
# Q9: 这段 HTML 需要学吗？
# A9: 后端面试不需要。只需要知道三个部分：
#     <style>  = 颜色和布局（CSS）
#     <body>   = 输入框和按钮（HTML 结构）
#     <script> = 发消息到 /chat，接收 SSE 流（JavaScript 逻辑）
#
# Q10: server.py 和 agent.py 的消息格式为什么不同？
# A10: agent.py 的 msg 是 SDK 自己的对象类型，SDK 内部处理时自动转 JSON。
#      server.py 需要 json.dumps() 推给前端，json.dumps() 只认 Python 原生类型
#      (str/int/dict/list)，不认 SDK 自定义的 Pydantic 对象，必须手动拆成纯字典。
#
# Q11: 装饰器 @app.post("/chat") 的本质是什么？
# A11: 语法糖。等价于 chat_endpoint = app.post("/chat")(chat_endpoint)。
#      把函数注册到 FastAPI 路由表——"有人访问 /chat 就调用这个函数"。
#      /chat 是你自己起的名字，和前端 fetch('/chat') 里保持一致就行。
#
# Q12: 什么是闭包？stream() 为什么放在 chat_endpoint 里面？
# A12: 函数里面定义函数。内层 stream() 能访问外层 user_input（客人说了什么）。
#      放在外面就拿不到，因为每次请求 user_input 不一样。
#
# Q13: json.dumps() 和 json.loads() 分别是干嘛的？
# A13: json.dumps(dict) → Python 字典转 JSON 字符串（发出去时用）。
#      json.loads(str)  → JSON 字符串转 Python 字典（收到时用）。
#      记忆：dumps = dump string（转出），loads = load string（转入）。
#
# Q14: .format() 和 f-string 有什么区别？为什么这里用 .format()？
# A14: .format() 只有一个 {} 占位符，JSON 的 {} 原样保留，互不冲突。
#      f-string 的 {} 和 JSON 的 {} 是同一个符号，混在一起分不清。
#      你的 yield 行用 .format() 就是这个原因——避免花括号冲突。
#
# Q15: StreamingResponse 的两个参数分别是什么？
# A15: 第 1 个 stream() — 异步生成器对象（有括号！写成 stream 是函数本身，不对）。
#      第 2 个 media_type="text/event-stream" — 告诉浏览器"这是 SSE 流，按 data:\n\n 格式解析"。
#
# Q16: 每个 yield 推送了什么内容？
# A16: yield {"type":"start"}  → 对话开始，前端准备接收
#      yield {"type":"tool",...} → 调用了工具，前端显示工具卡片
#      yield {"type":"final",...} → 最终回答，前端显示在气泡里
#      yield {"type":"done"}   → 对话结束，前端解锁按钮
#      "type"是你和前端约定的暗号——名字可改，但前后端必须一致。
#
# Q17: 为什么要两轮调用 LLM？
# A17: 第一轮（带 tools）→ 决策"要不要用工具/用什么工具"。
#      工具执行后，第二轮（不带 tools）→ 总结"工具结果拿到了，现在回答"。
#      完整版 ReAct 会循环多轮——工具不够继续调。
#
# Q18: assistant 是什么？为什么必须有它？
# A18: 四种 role 之一（system/user/assistant/tool），代表 AI。
#      OpenAI 协议要求：每条 tool 消息前面必须有一条 assistant 消息说"我要调工具"。
#      没有 assistant 直接放 tool → API 报 400 错误。是格式要求，不是语义描述。
#
# Q19: 列表推导式里为什么 for 放在最后？
# A19: Python 语法：[操作 for 变量 in 列表]。从中间的 for 往左读。
#      [{"id": tc.id} for tc in msg.tool_calls]
#      等价于 for tc in msg.tool_calls: result.append({"id": tc.id})
#
# Q20: tool_calls 里的字段名是固定的吗？
# A20: 全是 OpenAI 定的：id/type/function/name/arguments 一个字母不能改。
#      路径 /chat 是自定义的——前者不能改，后者随便换。
#
# Q21: 整个 server.py 的设计逻辑是什么？
# A21: 开一家店（FastAPI）→ 贴铭牌（@app.post）→ 客人递纸条（request.json）
#      → 厨房做菜不能等全做完（StreamingResponse）→ 做一道上一道（yield）
#      → 每一步都给客人反馈（SSE data:）→ 客人吃完走人。每一步都解决前一步的问题。
