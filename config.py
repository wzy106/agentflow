"""
Day 20：统一配置管理 —— 一处改，处处生效
============================================

环境变量的完整链路（从硬盘到代码）：
  .env 文件（纯文本，硬盘）
    → load_dotenv() 打开文件 + 逐行解析 key=value + 注入 os.environ
    → os.getenv("KEY") 从内存字典取值
    → Config 类属性（集中整理 + 类型转换）
    → 其他模块通过 from config import config 使用

为什么 os.getenv() 全写在 config.py 而不是散落各处？
  1. Python import 顺序：config.py 最先被导入，load_dotenv() 最先执行，保证后续代码拿到值
  2. 单点真理：默认值、类型转换（int/float）集中管理，改一处全局生效
  3. IDE 友好：config.xxx 有自动补全，不用记环境变量名

为什么 .env 文件名能生效？
  python-dotenv 库在 load_dotenv() 里硬编码了默认名 ".env"：
    dotenv_path = ".env"   →   open(dotenv_path)   →   逐行 key=value 解析
  没有黑魔法——就是 open() 读普通文本文件。换成 load_dotenv(".env.prod") 也能跑。
  ".env" 只是社区约定（类似 .gitignore / Dockerfile），不是操作系统强制的。

为什么环境变量名全大写（OPENAI_API_KEY 而不是 openai_api_key）？
  POSIX 标准 + Unix 几十年传统。$PATH、$HOME 全大写，后人跟着写。
  Python 不强制大小写，但全大写约定让所有人一眼看出"这是环境变量"。
  Docker / K8s / CI/CD 也遵循此约定，统一风格避免额外映射。
"""

import os
from dotenv import load_dotenv

# ========== 第 1 步：把 .env 文件内容加载到 os.environ ==========
# load_dotenv() 内部做的事：
#   1. 找到 .env 文件（默认当前目录）
#   2. open() 打开，当普通文本逐行读
#   3. 按 = 号切分成 key 和 value
#   4. os.environ[key] = value  —— 注入进程环境变量字典
# 此后 os.getenv("KEY") 就能读到 .env 里的值了。
load_dotenv()


class Config:
    """统一管理所有配置。

    每条配置的写入/读取路径：
      .env 文件（硬盘）→ load_dotenv() → os.environ（内存）→ os.getenv() → Config 属性

    os.getenv("KEY", "默认值") 的参数：
      第 1 个参数：环境变量名（查 os.environ 字典的键）
      第 2 个参数：找不到时返回的默认值（不传则返回 None）
      返回值永远是 str，需要数字时用 int() / float() 包一层。
    """

    # ========== LLM 配置 ==========
    # llm_provider 目前是预留字段——未来可做条件逻辑（如 if provider == "ollama": ...）
    llm_provider = os.getenv("LLM_PROVIDER", "ollama")
    api_key = os.getenv("OPENAI_API_KEY", "ollama")
    base_url = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")

    primary_model = os.getenv("OPENAI_MODEL", "qwen2.5:3b")
    backup_model = os.getenv("BACKUP_MODEL", "deepseek-r1:7b")

    # ========== Agent 配置 ==========
    max_steps = int(os.getenv("MAX_STEPS", "10"))
    temperature = float(os.getenv("TEMPERATURE", "0.7"))
    max_tokens = int(os.getenv("MAX_TOKENS", "4096"))

    # ========== RAG 配置 ==========
    embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    rag_data_dir = os.getenv("RAG_DATA_DIR", "./data/rag")

    # ========== Auth 配置（空字符串 = 不启用认证） ==========
    api_auth_key = os.getenv("API_AUTH_KEY", "")

    # ========== Server 配置 ==========
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "9000"))

    # ========== System Prompt ==========
    system_prompt = os.getenv(
        "SYSTEM_PROMPT",
        "你是一个助手。遇到计算、搜索、代码执行必须用工具。用中文回答。"
    )


# ========== 第 2 步：创建单例，供其他模块导入 ==========
# 其他模块通过 from config import config 拿到同一个实例。
# 模块加载时这行只执行一次——后续 import 都返回已创建好的对象。
config = Config()


# ========== Q&A 问答笔记 ==========
#
# Q1: load_dotenv() 为什么要放在 config.py 里？
# A1: config.py 是其他模块最先 import 的文件。Python 执行 import 时会把被导入
#     的模块从头到尾跑一遍——load_dotenv() 最先执行，后续代码用到 os.getenv()
#     时环境变量已经准备好了。放在这最安全——不会出现"还没加载就去取值"的问题。
#
# Q2: .env 是操作系统的东西吗？
# A2: 不是。OS 自带的环境变量是 PATH、HOME、USERNAME 这些，进程从父进程继承。
#     .env 是 python-dotenv 这个第三方库发明的约定——用一个纯文本文件存放敏感配置，
#     然后在进程启动时手动注入 os.environ，伪装成"OS 环境变量"的样子。
#     这也是为什么 .env 不上传 git——里面是 API Key，明文，谁捡到谁用。
#
# Q3: os.getenv() 和 os.environ.get() 有区别吗？
# A3: 几乎没有。os.getenv("KEY") 内部就是调 os.environ.get("KEY")。
#     os.getenv 多一层函数调用开销，但可忽略不计。习惯用 os.getenv 就好。
#
# Q4: 为什么不直接 os.getenv() 而是包一层 Config 类？
# A4: 裸调 os.getenv() 的问题：
#     ① 散落各处——改默认值要搜全项目
#     ② 每次调用都读字典——虽然快但不如一次读完存属性
#     ③ 没有类型——os.getenv 返回 str，数字要手动 int()，散落各处容易忘
#     ④ 没有补全——IDE 不知道有哪些可用的环境变量名
#     Config 类解决了所有四个问题。
#
# Q5: agent.py 和 server.py 也有 load_dotenv()，重复调用会有问题吗？
# A5: 不会。load_dotenv() 多次调用幂等——后面调用会覆盖前面同名 key 的值，
#     但值相同所以无实际影响。不过严格来说只需在 config.py 调用一次，
#     因为 config.py 一定是第一个被导入的。agent.py/server.py 里的 load_dotenv()
#     是历史遗留——早期没有 config.py 时写的，现在删掉也能正常跑。
#
# Q6: 环境变量名为什么全大写 + 下划线？
# A6: 源于 POSIX 标准 + Unix 几十年的惯例（PATH、HOME、USER）。
#     全大写 = 一眼识别这是环境变量，和普通 Python 变量区分。
#     Python 本身不强制大小写——os.getenv("openai_api_key") 也能读，
#     但所有工具链（Docker、K8s、CI/CD）都用大写下划线，不跟约定会被同事骂。
#
# Q7: 明明 .env 只有 3 行，为什么 Config 里这么多配置？
# A7: os.getenv 的第二参数给了默认值。.env 只覆盖需要改的——
#     不需要改的就用默认值。这叫"约定大于配置"：
#       开发环境：.env 只写 API Key + URL + 模型名
#       生产环境：.env 可以覆盖更多（如 MAX_STEPS、TEMPERATURE）
