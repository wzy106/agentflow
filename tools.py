"""
Day 4-5：工具注册表（插件式工具系统）
=========================================
核心设计模式：注册表模式（Registry Pattern）
本质：用字典代替 if-else，加新工具不改核心代码。

启动时：register() 注册工具 → 存函数 + 记录说明书
运行时：get_all_schemas() 把说明书给 AI → AI 说调哪个 → execute() 查字典执行
"""

from calculator import safe_calc
from web_search import web_search
from code_exec import execute_code
from rag import rag


# ====== 全局变量 ======

_tools = {}
# 全局字典：工具名 → 执行函数
# _ 下划线开头 = Python 约定：内部变量，别直接碰，用 register()
# 存储内容：
# {
#     "calculate": safe_calc,          # 工具名 → 函数对象（不加括号！）
#     "web_search": web_search,        # 存的是 safe_calc 本身，不是 safe_calc()
#     "execute_code": execute_code,
# }

_schemas = []
# 全局列表：所有工具的"说明书"（给 AI 看的）
# 和 _tools 的区别：
#   _tools    → 给程序用（查字典找到函数并执行）
#   _schemas  → 给 AI 用（get_all_schemas() 返回，作为 tools 参数传给 API）
# 两条线同时维护，靠 register() 保证不乱。


# ====== 核心函数 ======

def register(name, description, parameters, func):
#          ^^^^   ^^^^^^^^^^^   ^^^^^^^^^^   ^^^^
#          工具名   工具描述      参数定义      执行函数
#          给AI看   给AI看        给AI看       给程序用
    """注册一个工具：同时更新 _tools 和 _schemas"""

    # ====== 操作 1：存函数 → 给程序用的 ======
    _tools[name] = func
    # 等价于：
    # _tools["calculate"] = safe_calc（函数对象，不加括号！）
    # 如果写成 safe_calc() 加括号 → 立刻执行，把返回值存进去 → 错了
    # 之后 execute("calculate") → _tools["calculate"] → safe_calc 函数

    # ====== 操作 2：存说明书 → 给 AI 用的 ======
    _schemas.append({
        # append = 往列表末尾加一个元素（这里加一个字典）

        "type": "function",
        # 固定写法，告诉 AI "这是一个函数类型的工具"

        "function": {
            "name": name,
            # 工具名，AI 按这个名字调用：tool_calls → name = "calculate"

            "description": description,
            # 工具描述，AI 读它判断"该不该用这个工具"
            # 描述写得好不好 → 直接影响 AI 判断准不准

            "parameters": {
                "type": "object",
                # 固定写法，告诉 AI "参数是一个对象（字典）"

                "properties": parameters,
                # 参数定义：{"expression": {"type": "string", "description": "算式"}}
                # 这是 register() 调用者传进来的

                "required": list(parameters.keys()),
                # parameters.keys() → dict_keys(["expression"])  ← 不像列表
                # list(...)         → ["expression"]              ← 真正的列表
                # JSON 序列化需要真正的列表，dict_keys 不能直接转 JSON
            },
        }
    })


def execute(name, **kwargs):
#              ^^^^^^^^
#  **kwargs：把散装命名参数收进一个字典
#  execute("calculate", expression="2+2") → kwargs = {"expression": "2+2"}
    """按名字执行工具"""

    # ====== 查字典找函数 ======
    func = _tools.get(name)
    # .get() 和 [] 的区别：
    # _tools["不存在的"] → KeyError，程序崩溃
    # _tools.get("不存在的") → None，安全返回
    # 用 .get() 防御——AI 可能会叫错工具名

    if func is None:
        return f"错误：未知工具 '{name}'"

    # ====== 执行工具 ======
    try:
        result = func(**kwargs)
        # **kwargs：把字典拆回散装参数
        # func(**{"expression": "2+2"}) 等价于 func(expression="2+2")
        # 等价于 safe_calc(expression="2+2")
        #
        # 同一个 ** 两个方向：
        #   定义时 def f(**kwargs) → ** 收集：散装参数 → 字典
        #   调用时 f(**kwargs)     → ** 拆开：字典 → 散装参数
        #   "收进来是字典，传出去是参数"——透明转发

        # ====== 处理异步函数 ======
        import asyncio
        if asyncio.iscoroutine(result):
            # iscoroutine() 判断是不是"协程对象"（异步函数没跑完的状态）
            # 普通函数（safe_calc）→ 返回 "2+2=4" → iscoroutine → False → 直接返回
            # 异步函数（execute_code）→ 返回 <coroutine> → iscoroutine → True
            return asyncio.run(result)
            # asyncio.run() 启动事件循环，等异步函数跑完，拿到真实结果
        return result

    except Exception as e:
        # 工具内部崩了 → 不炸主程序，转成错误信息返回
        return f"错误：{e}"


def get_all_schemas():
    """获取所有工具的说明书（传给 LLM）"""
    return _schemas
    # agent.py 调用这行 → 拿到三本说明书 → 作为 tools 参数传给 DeepSeek


# ====== 注册所有工具 ======
# 每个工具的四个参数：
#   register("工具名", "描述", {"参数名": {"type": "类型", "description": "说明"}}, 函数名)
#                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#                             这是 properties 部分，外层 type: object 和 required
#                             在 register() 函数内部自动补上

register(
    "calculate",                                                    # ① 工具名
    "计算数学表达式，支持 + - * / sqrt sin cos log 等",               # ② 描述（AI 判断）
    {"expression": {"type": "string", "description": "如 '35*9/5+32'"}},  # ③ 参数定义（AI 生成参数）
    safe_calc,                                                      # ④ 执行函数（不加括号！）
)

register(
    "web_search",
    "搜索互联网获取实时信息",
    {"query": {"type": "string", "description": "搜索关键词"}},
    web_search,
)

register(
    "execute_code",
    "在沙箱中执行 Python 代码并返回输出",
    {"code": {"type": "string", "description": "要执行的 Python 代码"}},
    execute_code,
)


# ====== Day 16 新增：RAG 文档搜索工具 ======

def search_docs(query: str) -> str:
    """从用户上传的知识库中搜索相关文档内容"""
    results = rag.retrieve(query)
    if not results:
        return "知识库中没有找到相关内容"
    return "\n\n".join(results)

register(
    "search_docs",
    "从用户上传的知识库中搜索相关文档内容。用户问到特定项目、产品、公司相关问题时使用",
    {"query": {"type": "string", "description": "搜索关键词"}},
    search_docs,
)


# ====== Q&A 问答笔记 ======
#
# Q1: _tools 和 _schemas 有什么区别？
# A1: _tools 是给程序用的（字典：工具名→函数）。
#     _schemas 是给 AI 看的（列表：所有工具说明书）。
#     register() 同时更新两者。
#
# Q2: register 的四个参数分别给谁用？
# A2: 前三个（name, description, parameters）给 AI 看——构成说明书。
#     第四个（func）给程序用——存进 _tools 等 execute() 调用。
#
# Q3: func 为什么写成 safe_calc 而不是 safe_calc()？
# A3: safe_calc 是函数对象本身，把它存字典里。
#     safe_calc() 加了括号 → 立刻执行函数 → 存的是返回值 "2+2=4" → 错了。
#
# Q4: **kwargs 在 execute 里是干什么的？
# A4: 定义时 **kwargs 收集：execute("calc", expression="2+2") → kwargs={"expression": "2+2"}
#     调用时 func(**kwargs) 拆开：safe_calc(expression="2+2")
#     两次 ** 方向相反：一次打包，一次拆包。"透明转发"。
#
# Q5: parameters.keys() 为什么要套 list()？
# A5: .keys() 返回 dict_keys 对象，不是真正的列表。JSON 序列化需要列表。
#     list(parameters.keys()) → 真正的列表 ["expression", "query"]。
#
# Q6: asyncio.iscoroutine 是干什么的？
# A6: 判断工具函数的返回值是不是"协程对象"（异步函数没跑完的状态）。
#     普通函数（safe_calc）直接返回结果。
#     异步函数（execute_code）需要用 asyncio.run() 跑完再返回结果。
#     execute 自动处理两种类型，上层不需要关心。
#
# Q7: register 解决了什么问题？
# A7: 没有 register → 加一个工具要改 agent.py 三处（import、说明书、if-else）。
#     有 register → 加一个工具只加四行 register()，agent.py 一行不用动。
#     这就是"开闭原则"——对扩展开放，对修改封闭。
#
# Q8: Day 16 加 search_docs 工具时 agent.py 改了几行？
# A8: 零行。只在 tools.py 里加了一个函数 + 一个 register()。
#     agent.py 的 while 循环自动拿到新工具的说明书，AI 自动决定什么时候调它。
#     这就是注册表模式的价值——第四个工具和第一个工具加法一模一样。
