# 🤖 AgentFlow — AI Agent 框架

**从零实现的轻量级 AI Agent 框架，支持多工具自动调用、流式对话和文档检索。**

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 📖 项目简介

AgentFlow 是一个教学级 AI Agent 框架。普通的 AI 聊天只能回答问题，这个 Agent 可以**自己调用工具**——计算、搜索互联网、执行代码——然后汇总结果回答用户。

**核心思路**：让 AI 从"只会说"变成"可以做"。

---

## 🎯 功能演示

```
用户：12345 × 67890 等于多少？
Agent：[调 calculate 工具] → 838,102,050

用户：搜索 Python 最新版本
Agent：[调 web_search 工具] → 返回搜索结果

用户：写一段代码算斐波那契数列前 20 项的和
Agent：[调 execute_code 工具] → 运行代码 → 10945
```

---

## 🏗️ 架构设计

```
┌─────────────────────────────────────────┐
│              浏览器（网页界面）              │
│          http://localhost:8000            │
└──────────────────┬──────────────────────┘
                   │ SSE 流式推送
┌──────────────────▼──────────────────────┐
│          FastAPI 后端（server.py）         │
│   GET  /         →  返回网页              │
│   POST /chat     →  对话接口（SSE）        │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│            Agent 核心（ReAct 循环）         │
│                                          │
│   while 未完成:                           │
│     ① Think：发给 LLM，决定要干嘛          │
│     ② Act  ：调用工具（计算/搜索/代码执行）  │
│     ③ Observe：把工具结果还给 LLM          │
│     → LLM 有足够信息则输出最终答案          │
└──────────────────┬──────────────────────┘
                   │
     ┌─────────────┼─────────────┐
     ▼             ▼             ▼
┌─────────┐  ┌─────────┐  ┌─────────┐
│ 计算器   │  │ 搜索工具  │  │ 代码执行  │
│ 四层沙箱  │  │ DuckDuckGo│  │ 子进程隔离 │
└─────────┘  └─────────┘  └─────────┘
```

---

## 📂 项目结构

```
myagent/
├── server.py            ← Web 服务入口（FastAPI + SSE）
├── agent.py             ← Agent 核心（ReAct 循环）
├── tools.py             ← 工具注册表（插件式管理）
├── calculator.py        ← 安全计算器（四层沙箱）
├── web_search.py        ← 网络搜索工具
├── code_exec.py         ← 代码执行工具（子进程隔离）
├── .env.example         ← 环境变量模板
├── requirements.txt     ← Python 依赖
└── README.md            ← 本文件
```

---

## 🚀 快速开始

### 1. 环境要求

- Python 3.10 或更高版本
- DeepSeek API Key（或 OpenAI / Ollama）

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 API Key

创建 `.env` 文件，填入你的 Key：

```ini
OPENAI_API_KEY=sk-你的Key
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
```

### 4. 启动

```bash
python server.py
```

看到以下输出表示启动成功：

```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 5. 打开浏览器

访问 **http://localhost:8000**，开始对话。

---

## 🔧 工具系统

Agent 的核心能力来自**可插拔的工具系统**。新增工具只需写一个函数 + 一行注册，不改 `agent.py`。

### 已内置的 3 个工具

| 工具 | 功能 | 安全机制 |
|------|------|---------|
| `calculate` | 数学表达式计算 | 四层沙箱：白名单 + compile 检查 + co_names 验证 + 空 __builtins__ |
| `web_search` | 互联网搜索 | DuckDuckGo 免费 API |
| `execute_code` | Python 代码执行 | 子进程隔离 + asyncio 超时 kill |

---

## 🧠 核心技术点

### 1. ReAct 循环

```
Think（思考）     →  LLM 分析问题，决定是否需要工具
Act（行动）       →  调用 LLM 指定的工具
Observe（观察）   →  把工具结果还给 LLM
Repeat（重复）    →  LLM 判断是否还需要更多工具，否则输出最终答案
```

### 2. Function Calling

- 把工具的"说明书"（name、description、parameters）传给 LLM
- LLM 返回 `tool_calls`：工具名 + 参数
- 程序执行工具，结果塞回对话历史
- LLM 看结果后生成最终回复

### 3. 注册表模式

- 全局字典存储 工具名 → 函数 的映射
- `register()` 添加工具，`execute()` 按名字调用
- 遵循开闭原则——对扩展开放，对修改封闭

### 4. SSE 流式推送

对话接口使用 Server-Sent Events，服务器边生成边推送，用户实时看到"思考 → 调工具 → 结果 → 总结"。

---

## 🛠 技术栈

| 技术 | 用途 |
|------|------|
| **Python 3.10+** | 主语言 |
| **FastAPI** | Web 框架 |
| **Uvicorn** | ASGI 服务器 |
| **OpenAI SDK** | LLM 调用（兼容 DeepSeek/Ollama） |
| **SSE** | 流式推送 |
| **DuckDuckGo Search** | 免费网络搜索 |
| **asyncio** | 异步编程 |

---

## 📊 项目亮点（简历可用）

> - 从零实现 ReAct 模式 AI Agent，支持 Think→Act→Observe 多轮推理
> - 设计插件式工具系统，新增工具不改核心代码
> - 实现安全计算沙箱（四层防护）和子进程代码执行（隔离+超时 kill）
> - 基于 SSE 协议实现 Agent 推理过程的实时流式推送
> - 全链路异步架构（asyncio + FastAPI）

---

## 📝 License

MIT
