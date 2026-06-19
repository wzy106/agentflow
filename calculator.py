"""
Day 2：安全计算器（四层沙箱）
================================
本文件实现一个安全的数学表达式计算器。
直接 eval() 能执行任何 Python 代码（包括删除文件）——这个计算器用四层防护阻止危险操作。
"""

import math
# math 是 Python 自带的数学模块。里面有 sqrt、sin、cos、log、pi 等所有数学函数和常量。


def safe_calc(expression: str) -> str:
#               ^^^^^^^^^^           ^^^^^^
#          参数名: 类型注解             -> 返回值类型注解
#          告诉读代码的人：传字符串进来，返回字符串出去。
#          Python 不强制检查——你不写也能跑。写它是为了方便读代码 + VS Code 自动补全。

    """安全地计算一个数学表达式"""
    # 三引号字符串 = 文档字符串。Python 不执行它，纯粹给人看的。

    if not expression.strip():
        return "错误：表达式为空"
    # 拆解：
    # expression.strip() → 去掉首尾空格
    # ""（空字符串）→ Python 认为是 False
    # "2+2"（非空）→ Python 认为是 True
    # not "" → True → 进入 if → 返回错误
    # not "2+2" → False → 跳过

    # ====== 防护层 1：白名单 ======
    # 字典推导式：遍历 math 模块的所有内容，只保留公开的数学函数。
    #
    # {k: v for k, v in math.__dict__.items() if not k.startswith("_")}
    #  ↑  ↑       ↑  ↑                        ↑
    #  │  │       │  └── 值（临时变量）          └── 过滤条件：不以 _ 开头
    #  │  │       └── 键（临时变量）
    #  │  └── 新字典的值
    #  └── 新字典的键
    #
    # math.__dict__ → math 模块的内部字典，装了所有东西
    # .items() → 返回 (键, 值) 对：("sqrt", 函数), ("pi", 3.14), ...
    # .startswith("_") → 判断字符串是否以 _ 开头
    #    Python 约定：_ 开头 = 内部私有属性，别碰（如 __name__、_private）
    #
    allowed = {k: v for k, v in math.__dict__.items() if not k.startswith("_")}
    allowed["abs"] = abs      # 绝对值，不在 math 模块里，手动加
    allowed["round"] = round  # 四舍五入
    allowed["pow"] = pow      # 幂运算

    # ====== 防护层 2：编译检查 ======
    # compile(str, "<calc>", "eval")
    #   参数 1：要编译的 Python 代码字符串
    #   参数 2：文件名（报错时显示用，随便写的）
    #   参数 3：编译模式
    #     "eval"  → 只接受表达式（2+2、sqrt(4)），拒绝语句（import、print、for）
    #     "exec"  → 接受任何语句
    #     "single"→ 接受单条语句
    #
    # 用 "eval" 模式的目的：在编译阶段就拦截 import、print 等语句。
    #
    try:
        code = compile(expression, "<calc>", "eval")
    except SyntaxError as e:
        # try/except：试着做 → 出错时走备用方案（不崩溃）
        # SyntaxError：语法错误。eval 模式碰到 import/print 就抛这个异常
        # as e：把异常对象存到变量 e，后面 f"{e}" 拼进返回信息
        return f"错误：语法不对 —— {e}"

    # ====== 防护层 3：白名单验证 ======
    # code.co_names 是编译后字节码里引用的所有变量名（元组）。
    # 例如：
    #   "sqrt(4) + pi" → co_names = ("sqrt", "pi")           ← 安全的
    #   "__import__('os')" → co_names = ("__import__",)       ← 危险的！
    #
    # 检查每个名字是否在白名单里——这就是第三道防线。
    #
    for name in code.co_names:
        if name not in allowed:
            return f"错误：不允许使用 '{name}'"

    # ====== 防护层 4：空内置函数 + 安全执行 ======
    # eval(source, globals, locals)
    #   参数 1 (source)：要执行的代码（字节码或字符串）
    #   参数 2 (globals)：全局命名空间——{"__builtins__": {}} 把所有内置函数清空！
    #     __builtins__ 本来存着：open、__import__、exec、eval、print、input...
    #     传 {} 空字典 → 这些函数全部消失！
    #   参数 3 (locals)：局部命名空间——传 allowed（白名单数学函数）
    #
    # 结果：eval() 执行代码时：
    #   ✅ 能找到 sqrt、sin、abs（allowed 里有）
    #   ❌ 找不到 open、__import__、exec（__builtins__ 清空了）
    #   ✅ 能做 2+2、3*5（纯数字运算不需要函数）
    #
    # 为什么先 compile() 再 eval()？
    #   → 中间可以插 co_names 检查（第 3 层）。直接 eval(字符串) 就跳过这层了。
    #
    try:
        result = eval(code, {"__builtins__": {}}, allowed)
        return f"{expression} = {result}"
        # f-string：花括号里放变量，拼成一句话。
        # 例：expression="2+2", result=4 → "2+2 = 4"
    except Exception as e:
        return f"错误：{e}"


# ====== 测试 ======
# __name__ == "__main__"：判断"是直接运行本文件还是被别人 import"
# 直接运行 python calculator.py → True → 执行测试
# 被 import（from calculator import safe_calc）→ False → 不执行测试
if __name__ == "__main__":
    # 正常运算（四层全通过）
    print(safe_calc("2 + 3 * 4"))          # → 14
    print(safe_calc("sqrt(144) + 10"))     # → 22.0
    print(safe_calc("35 * 9 / 5 + 32"))    # → 95.0
    print(safe_calc("520*1314"))           # → 683280

    # 危险操作（分别被不同防护层拦截）
    print(safe_calc("__import__('os').system('dir')"))  # 第 3 层：__import__ 不在白名单
    print(safe_calc("open('secret.txt')"))              # 第 3 层：open 不在白名单
    print(safe_calc("print('hello')"))                  # 第 2 层：print 是语句，compile("eval") 拒绝


# ====== Q&A 问答笔记 ======
#
# Q1: expression: str 和 -> str 是什么？
# A1: 类型注解（Type Hints）。expression: str = 参数应该传字符串。
#     -> str = 返回值是字符串。Python 不强制检查，纯粹给人看 + VS Code 提示用。
#
# Q2: not expression.strip() 是什么意思？
# A2: expression.strip() 去首尾空格 → 如果是空字符串（""）→ Python 认为是 False
#     → not False = True → 进入 if 报错。
#
# Q3: {k: v for k, v in math.__dict__.items() if not k.startswith("_")} 为什么有两个 k,v？
# A3: 不是两个 k，是一个 k 出现两次。for 后面：k=键, v=值（临时变量名）。
#     前面 {k: v 是新字典的键:值。可以换成 {name: func for name, func in ...}。
#
# Q4: if not k.startswith("_") 是什么？
# A4: .startswith("_") 判断字符串是否以下划线开头。Python 约定：_ 开头 = 内部私有。
#     not 取反：不以 _ 开头才留下。过滤掉 __doc__、_private 等。
#
# Q5: compile(str, "", "eval") 的知识点？
# A5: compile() 把字符串翻译成字节码但不执行。"eval" 模式只接受表达式，拒绝语句
#     （import、print、for 全拒绝）。try/except SyntaxError as e 捕获语法错误。
#
# Q6: eval(code, {"__builtins__": {}}, allowed) 的知识点？
# A6: eval() 三个参数：source(代码), globals(全局命名空间), locals(局部命名空间)。
#     {"__builtins__": {}} 清空所有内置函数（open、__import__ 全没）。
#     allowed 是白名单（只有数学函数）。先 compile 再 eval 是因为中间能检查 co_names。
#
# Q7: 四层沙箱总结？
# A7: 第 1 层：白名单（allowed 字典）。第 2 层：compile("eval") 拦语句。
#     第 3 层：co_names 白名单验证。第 4 层：eval(code, 空__builtins__, allowed)。
