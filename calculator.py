 # calculator.py —— 安全的数学计算器

import math

def safe_calc(expression: str) -> str:
      """安全地计算一个数学表达式"""

      if not expression.strip():
          return "错误：表达式为空"

      # ====== 防护层 1：白名单 ======
      # 从 math 模块提取所有公开函数名
      # math.__dict__ 是 math 模块的内部字典，存了所有东西
      # k: v 就是遍历这个字典的键和值
      # if not k.startswith("_") 过滤掉私有属性
      allowed = {k: v for k, v in math.__dict__.items() if not k.startswith("_")}
      allowed["abs"] = abs      # 绝对值
      allowed["round"] = round  # 四舍五入
      allowed["pow"] = pow      # 幂运算

      # ====== 防护层 2：编译检查 ======
      try:
          # compile() 把字符串变成字节码，但不执行
          # 第三个参数 "eval" 限制：只能编译表达式，不能编译语句
          # 所以 "import os" "print('hi')" 这类语句直接报错
          code = compile(expression, "<calc>", "eval")
      except SyntaxError as e:
          return f"错误：语法不对 —— {e}"

      # ====== 防护层 3：白名单验证 ======
      # code.co_names 是编译后字节码里引用的所有变量名
      # 比如 "sqrt(4) + pi" 的 co_names = ("sqrt", "pi")
      # 比如 "__import__('os')" 的 co_names = ("__import__",)
      for name in code.co_names:
          if name not in allowed:
              return f"错误：不允许使用 '{name}'"

      # ====== 防护层 4：空内置函数 ======
      try:
          # eval 的第二个参数是"全局命名空间"，第三个是"局部命名空间"
          # {"__builtins__": {}} 清空了所有内置函数
          # 没有 __import__, open, exec, eval, compile
          # 只有 allowed 里面的 math 函数
          result = eval(code, {"__builtins__": {}}, allowed)
          return f"{expression} = {result}"
      except Exception as e:
          return f"错误：{e}"


  # ====== 测试 ======
if __name__ == "__main__":
      # 正常运算
      print(safe_calc("2 + 3 * 4"))
      print(safe_calc("sqrt(144) + 10"))
      print(safe_calc("35 * 9 / 5 + 32"))
      print(safe_calc("520*1314"))

      # 被拦截的危险操作
      print(safe_calc("__import__('os').system('dir')"))
      print(safe_calc("open('secret.txt')"))
      print(safe_calc("print('hello')"))