# code_exec.py —— 安全代码执行（子进程沙箱）

import asyncio
import sys


async def execute_code(code: str, timeout: int = 10) -> str:
    """在隔离的子进程中执行 Python 代码，返回输出"""
    if not code.strip():
        return "错误：代码为空"

    preamble = "import math, json, re, itertools, collections\n"

    try:
        proc = await asyncio.wait_for(
            asyncio.create_subprocess_exec(
                sys.executable, "-c", preamble + code,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            ),
            timeout=5,
        )

        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=timeout
        )

        out = stdout.decode("utf-8", errors="replace").strip()
        err = stderr.decode("utf-8", errors="replace").strip()

        if err:
            return f"错误输出:\n{err}\n\n标准输出:\n{out}"
        return out or "(无输出)"

    except asyncio.TimeoutError:
        return f"错误：代码执行超时（>{timeout}秒）"
    except Exception as e:
        return f"错误：{e}"
