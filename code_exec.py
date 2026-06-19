"""
Day 5：代码执行工具（子进程沙箱）
==================================
在隔离的子进程里执行 AI 生成的 Python 代码。
子进程崩溃/死循环都不影响主程序——这是和 eval() 最大的区别。
"""

import asyncio
# asyncio = Python 自带的异步编程模块。
# 本文件用它三个功能：
#   1. asyncio.create_subprocess_exec() → 创建子进程
#   2. asyncio.wait_for()              → 超时自动 kill
#   3. asyncio.TimeoutError            → 超时的异常类型
#
# 课程归属：操作系统（并发/进程间通信）→ 大二下

import sys
# sys = Python 自带的系统信息模块。
# 本文件只用 sys.executable —— 当前 Python 解释器的完整路径。
# 例如你的电脑："D:\dev\python\python.exe"
# 为什么不写死？换个电脑路径就变了，sys.executable 自动适配。
#
# 课程归属：Python 程序设计 → 大一


async def execute_code(code: str, timeout: int = 10) -> str:
# ^^^^^              ^^^^         ^^^^^         ^^
# async def = 异步函数  参数: 代码   参数: 超时秒数   -> 返回字符串
# 可以"暂停"去          : str = 字符串  : int = 整数
# 处理别的请求                        = 10 = 默认值
#
# async def 和 def 的区别：
#   def f():     → 直接返回值，中间不能停
#   async def f(): → 返回"协程对象"，里面可以用 await 暂停

    """在隔离的子进程中执行 Python 代码，返回输出"""

    if not code.strip():
        return "错误：代码为空"

    # ====== Preamble（前导 import） ======
    # 用户的代码前面自动拼接常用库的 import。
    # 为什么不在 code_exec.py 开头 import？
    # → 子进程是完全独立的 Python 解释器，看不到主进程 import 了什么。
    #   你在主进程 import math ≠ 子进程也有 math，必须子进程自己 import。
    #   就像你和你室友——你电脑装了软件，他电脑不会自动也有。
    preamble = "import math, json, re, itertools, collections\n"
    # math       → 数学函数
    # json       → JSON 解析
    # re         → 正则表达式
    # itertools  → 迭代工具
    # collections→ 高级数据结构

    try:
        # ====== 第一层 wait_for：控制子进程启动超时 ======
        proc = await asyncio.wait_for(
            #                          ↑ 给下面的操作加超时限制
            #                            5 秒内没启动起来 → 抛 TimeoutError

            # ====== 创建子进程 ======
            asyncio.create_subprocess_exec(
                # ① 用哪个程序
                sys.executable,
                # 当前 Python 解释器的完整路径

                # ② 运行方式：-c = 执行字符串而不是文件
                "-c",

                # ③ 执行的代码：preamble（import）+ AI 写的代码
                preamble + code,

                # ④ 标准输出：捕获 print() 出来的内容
                stdout=asyncio.subprocess.PIPE,
                # PIPE = 管道，把子进程的输出引导到主进程的变量里
                # 没有 PIPE → 输出直接打印到终端，程序拿不到

                # ⑤ 标准错误：捕获报错信息
                stderr=asyncio.subprocess.PIPE,
            ),
            timeout=5,  # 启动超时 5 秒
        )

        # ====== 第二层 wait_for：控制代码执行超时 ======
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            # .communicate() = 等待子进程结束，一次性收回所有输出
            # 返回 (stdout, stderr) 两个字节串（bytes 类型）
            # 注意：是 b"5050" 不是 "5050"！b 前缀 = 字节串

            timeout=timeout,  # 默认 10 秒超时
        )

        # ====== 字节串 → 字符串 ======
        out = stdout.decode("utf-8", errors="replace").strip()
        #     .decode("utf-8") = 字节串 → UTF-8 编码的字符串
        #     errors="replace" = 解码不了的乱码用 � 替代
        #     .strip() = 去掉首尾空白（空格、换行、制表符）

        err = stderr.decode("utf-8", errors="replace").strip()
        # 错误输出做相同处理

        # ====== 返回结果 ======
        if err:
            # 有错误输出 → 把错误和标准输出都展示
            return f"错误输出:\n{err}\n\n标准输出:\n{out}"

        return out or "(无输出)"
        # out or "(无输出)"：Python 的短路逻辑
        #   out = "5050"    → 真 → 返回 "5050"
        #   out = ""        → 假 → 返回 "(无输出)"

    except asyncio.TimeoutError:
        # 第一层或第二层 wait_for 超时了
        # 子进程被自动 kill，不会继续占用系统资源
        return f"错误：代码执行超时（>{timeout}秒）"

    except Exception as e:
        # 兜底——其他所有想不到的错误
        return f"错误：{e}"


# ====== Q&A 问答笔记 ======
#
# Q1: import asyncio 和 import sys 是干什么的？
# A1: asyncio = 异步编程（子进程 + 超时控制）。
#     sys = 系统信息（sys.executable 取 Python 解释器路径）。
#     两个都是 Python 自带的，不需要 pip install。
#
# Q2: async def 和 def 有什么区别？
# A2: async def 定义的函数里可以用 await（等待时让出 CPU 去干别的事）。
#     子进程执行需要 5-10 秒，用 async 让等的时候不闲着。
#
# Q3: 为什么 preamble 不写在文件头部 import？
# A3: 文件头部的 import 是给主进程用的。子进程是独立的 Python 解释器，
#     有自己独立的内存空间，看不到主进程 import 了什么。
#
# Q4: 子进程的标志是什么？
# A4: 看代码里有没有 asyncio.create_subprocess_exec()。
#     有 → 代码跑在独立子进程。没有 → 跑在主进程。
#
# Q5: 为什么有两层 asyncio.wait_for？
# A5: 第一层管子进程启动（5 秒），第二层管代码执行（默认 10 秒）。
#     两道保险，防止不同阶段卡死。
#
# Q6: PIPE 是干什么的？
# A6: 管道。把子进程的 print 输出和报错信息"接"到主进程的变量里。
#     没有 PIPE → 输出直接打印到终端，主程序拿不到。
#
# Q7: .decode("utf-8") 是干什么？
# A7: 字节串（b"5050"）→ 字符串（"5050"）。
#     子进程返回的是原始字节，必须解码才能当普通文本用。
#     errors="replace" = 乱码用 � 替代，不崩溃。
#
# Q8: 子进程 vs eval() 的区别？
# A8: eval() 在当前进程跑代码 → 共享内存、文件、网络。
#     子进程在独立进程跑 → 崩溃、死循环、搞破坏都不影响主程序。
#     就像在一个隔音房间里拆弹——炸也炸隔壁，不影响你。
