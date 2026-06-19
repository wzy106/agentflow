"""
Day 1：Python 调用大模型 API
===============================
本文件演示最基础的 LLM 调用——发消息给 DeepSeek，打印回复。
"""

# ====== 1. 导入 ======

import os
# os = Operating System（操作系统）。
# 这里只用了 os.getenv() —— 从内存取出环境变量的值。

from dotenv import load_dotenv
# load_dotenv() 打开 .env 文件，把每行 KEY=VALUE 抄到内存里的 os.environ 字典。
# 相当于"复印一份"—— .env 是原件（硬盘），os.environ 是复印件（内存）。
# 之后 os.getenv("KEY") 从复印件取值，不再读硬盘。

from openai import OpenAI
# OpenAI 是通信协议的名字，不是"只能连 OpenAI 公司"。
# 你改一下 base_url 就能连 DeepSeek / Ollama / 通义千问等任何兼容 OpenAI API 的服务。
# 你的 Key 是 DeepSeek 的，地址是 DeepSeek 的——全程只跟 DeepSeek 通信。

# ====== 2. 读密码 ======

load_dotenv()
# 打开 myagent/.env，把三行配置读进内存：
#   OPENAI_API_KEY    → sk-xxx       (你的身份凭证)
#   OPENAI_BASE_URL   → https://...  (发给谁)
#   OPENAI_MODEL      → deepseek-chat (用哪个模型)

# ====== 3. 创建客户端 ======

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    # 你的身份凭证，DeepSeek 靠这个知道你是谁、扣你多少额度。
    # 参数名 api_key 必须全小写——这是 OpenAI 库定死的，不能改。

    base_url=os.getenv("OPENAI_BASE_URL"),
    # 请求发到哪个地址。这里指向 DeepSeek 服务器而不是 OpenAI。
    # base_url 也必须全小写。
)
# client 是你给这个连接对象起的外号，可以换成任何名字（ai = OpenAI(...) 也行）。
# 但 api_key 和 base_url 这两个参数名是系统定死的，不能改。

# ====== 4. 发消息给 AI ======

response = client.chat.completions.create(
# response 是变量名，你可以自己起（如 result、jieguo 都行）。
# .chat.completions.create 是固定的调用链，一个字母不能改——这是 OpenAI 库规定的。

    model=os.getenv("OPENAI_MODEL"),
    # 用哪个模型，这里从 .env 读取 "deepseek-chat"

    messages=[
        {"role": "system", "content": "你是我的女朋友，说话非常萌，且甜甜的，但要回答对我的问题哦"},
        # role: "system" → 你给 AI 定的人设/规则。
        # 可以换成任何描述："你是猫"、"你是数学老师"、"你只回答10个字以内"……
        # system 越具体，AI 行为越可控。

        {"role": "user", "content": "你好，1314乘520等于几"},
        # role: "user" → 用户问的问题。
        # messages 是一个列表，AI 按顺序阅读全部消息后生成回复。
        # 列表里可以有 system、user、assistant（AI 的回复）、tool（工具结果）四种角色。
    ],
)
# 括号结束，response 收到 AI 的完整回复。

# ====== 5. 取出文本并打印 ======

print(response.choices[0].message.content)
# response 是层层包装的对象，拆开看：
#   response                          ← 整个响应的包裹
#     .choices                        ← [候选回复列表]，通常只有一个元素
#       [0]                           ← 取第一个候选
#         .message                    ← 消息对象
#           .content                  ← 纯文本字符串（你要的东西）
#
# .choices、.message、.content 都是 OpenAI 定死的属性名，不能改。
# 只有 response 和 [0]（列表索引）是你可以控制的。


# ====== Q&A 问答笔记 ======
#
# Q1: 为什么调用的是 openai 而不是 deepseek？
# A1: DeepSeek 的 API 接口模仿了 OpenAI 的格式。OpenAI 是通信协议的名字，
#     改 base_url 就能连到不同服务。就像 iPhone 充电线插小米充电头——线没变，电流照通。
#
# Q2: os 模块有什么用？
# A2: os = 操作系统工具。本项目只用 os.getenv("名字") 从内存取环境变量的值。
#
# Q3: .env 里的名字（OPENAI_API_KEY）是系统定死的吗？
# A3: 不是。.env 里的变量名是随便起的（你可以叫 MY_KEY），
#     但取的时候名字必须对上：os.getenv("MY_KEY")。
#     全大写+下划线只是编程圈的约定俗成，不是语法要求。
#
# Q4: load_dotenv() 为什么能把 .env 的内容读到 os.getenv() 可用？
# A4: load_dotenv() 打开 .env → 逐行按 = 号切开 → 存到 os.environ（内存字典）。
#     相当于把硬盘上的原件抄一份到内存。之后 os.getenv() 从内存复印件取值。
#
# Q5: response.choices[0].message.content 的名字是系统定的吗？
# A5: 除了 response 和 [0]（列表索引），全部是 OpenAI 库定死的属性名，一个字母不能改。
#
# Q6: 大小写需要注意吗？
# A6: OpenAI() 的参数名必须全小写（api_key, base_url）。
#     .env 里的变量名 —— 你取的时候怎么写，.env 里就要一模一样。
