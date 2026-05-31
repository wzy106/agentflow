# server.py —— 把 Agent 变成网页服务

import json
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from openai import OpenAI

from tools import execute, get_all_schemas

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
)

app = FastAPI(title="AgentFlow")


# ====== 首页（网页界面） ======
@app.get("/", response_class=HTMLResponse)
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


# ====== 聊天接口（SSE 流式推送） ======
@app.post("/chat")
async def chat_endpoint(request: Request):
    body = await request.json()
    user_input = body.get("message", "")

    async def stream():
        yield "data: {}\n\n".format(json.dumps({"type": "start"}))

        messages = [
            {"role": "system", "content": "你是一个助手。遇到计算、搜索、代码执行必须用工具。用中文回答。"},
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
            yield "data: {}\n\n".format(json.dumps({"type": "final", "content": msg.content}))
            yield "data: {}\n\n".format(json.dumps({"type": "done"}))
            return

        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in msg.tool_calls
            ]
        })

        for tc in msg.tool_calls:
            name = tc.function.name
            args = json.loads(tc.function.arguments)
            result = execute(name, **args)

            yield "data: {}\n\n".format(json.dumps({"type": "tool", "tool": name, "result": result}))

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })

        final = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL"),
            messages=messages,
        )
        yield "data: {}\n\n".format(json.dumps({"type": "final", "content": final.choices[0].message.content}))
        yield "data: {}\n\n".format(json.dumps({"type": "done"}))

    return StreamingResponse(stream(), media_type="text/event-stream")


# ====== 启动 ======
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
