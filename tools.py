# tools.py —— 工具注册表（Day 5 完整版）

from calculator import safe_calc
from web_search import web_search
from code_exec import execute_code


# 全局字典
_tools = {}
_schemas = []


def register(name, description, parameters, func):
    """注册一个工具"""
    _tools[name] = func
    _schemas.append({
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": parameters,
                "required": list(parameters.keys()),
            },
        }
    })


def execute(name, **kwargs):
    """按名字执行工具"""
    func = _tools.get(name)
    if func is None:
        return f"错误：未知工具 '{name}'"
    try:
        result = func(**kwargs)
        import asyncio
        if asyncio.iscoroutine(result):
            return asyncio.run(result)
        return result
    except Exception as e:
        return f"错误：{e}"


def get_all_schemas():
    """获取所有工具的说明书（传给 LLM）"""
    return _schemas


# ====== 注册所有工具 ======
register(
    "calculate",
    "计算数学表达式，支持 + - * / sqrt sin cos log 等",
    {"expression": {"type": "string", "description": "如 '35 * 9/5 + 32'"}},
    safe_calc,
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
