"""
Day 12：对话记忆 —— 让 AI 记住之前的对话
=============================================
就像给 AI 买了一本日记本——每次对话都写下来，下次翻一翻就知道之前说了什么。
以前每次 chat() 都新建 messages 列表，AI 像金鱼一样转身就忘。
"""


class ConversationMemory:
    """对话记忆——维护消息历史，限制最大长度"""

    def __init__(self, system_prompt: str = "", max_messages: int = 20):
        """
        新建一本日记本。
        __init__ 是 Python 内置方法——创建对象时自动调用（双下划线是固定格式）。
        system_prompt：规矩，记在日记本第一页（永远不撕）
        max_messages：最多保留多少条（滑动窗口上限）
        """
        self.system_prompt = system_prompt
        self.max_messages = max_messages
        self.messages = []          # 日记本内页，初始为空
        if system_prompt:           # 如果给了规矩，写进第一页
            self.messages.append({
                "role": "system", "content": system_prompt
            })

    def add(self, role: str, content: str, **kwargs) -> None:
        """
        最通用的一行写法——往日记本贴一张便签。
        role：谁说的（"user"/"assistant"/"tool"——OpenAI 定的）
        content：说了什么
        **kwargs：额外标签（如 tool_call_id）——有就贴上，没有就跳过
        """
        msg = {"role": role, "content": content}
        msg.update(kwargs)          # update 是 Python 字典自带的方法——合并额外字段
        # 如果 kwargs 里有 tool_call_id，update 后 msg 里就多了一个 tool_call_id 字段
        # 如果 kwargs 是空的，update 什么也不加
        self.messages.append(msg)
        self._trim()                # 写完了检查厚度——太厚就撕旧页

    def get_messages(self) -> list[dict]:
        """翻日记本。只给 AI 看最近 max_messages 条——滑动窗口"""
        return self.messages[-self.max_messages:]
        # [-20:] = 从倒数第 20 条到最末——太旧的自动掉出窗口
        # 为什么限制长度？AI 有 token 上限，对话太长会超限

    def add_user_message(self, text: str) -> None:
        """帮你记"用户说了什么"——不用手写 {"role":"user"}"""
        self.add("user", text)

    def add_assistant_message(self, text: str = "", tool_calls: list = None) -> None:
        """
        帮你记"AI 说了什么"。
        text or "" = 如果 AI 只返回 tool_calls 没说话，写空字符串
        tool_calls 有就贴上去，没有就跳过
        """
        msg = {"role": "assistant", "content": text or ""}
        if tool_calls:
            msg["tool_calls"] = tool_calls
        self.messages.append(msg)

    def add_tool_result(self, tool_call_id: str, result: str) -> None:
        """帮你记"工具执行结果"——贴上角色标签和调用 ID"""
        self.messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": result,
        })

    def _trim(self) -> None:
        """
        检查厚度——超过上限就撕旧页。
        _ 下划线开头 = Python 约定：私有方法，外人别碰。
        当页数超过 max_messages * 2 时才动手（不是每次写都检查，省力气）。
        撕的时候保留 1.5 倍 max_messages（留缓冲，避免下次写一行又得撕）。
        """
        if len(self.messages) > self.max_messages * 2:
            keep = min(self.max_messages * 3 // 2, len(self.messages))
            self.messages = self.messages[-keep:]

    def clear(self) -> None:
        """换一本新日记本。清空全部内容，但规矩（system prompt）还在第一页。"""
        self.messages = []
        if self.system_prompt:
            self.messages.append({
                "role": "system", "content": self.system_prompt
            })


# ====== 专有 vs 自己定义的 ======
#
# 专有（Python 语法，不能改）：
#   class, def, __init__, self, str, int, list, dict, None
#   "role"/"content"/"tool_call_id" = OpenAI 协议定死的键名
#   .update() = 字典内置方法；.append() = 列表内置方法；len() = Python 内置函数
#   _ 下划线开头 = Python 约定私有
#
# 自己定义的（可以换）：
#   ConversationMemory = 类名（你起的）
#   system_prompt, max_messages, messages = 属性名（你起的）
#   add, get_messages, add_user_message, add_assistant_message, add_tool_result, _trim, clear = 方法名（你起的）
#   role, content, text, tool_calls, tool_call_id, result = 参数名（你起的）
#   msg, keep = 局部变量（你起的）
#
# 记忆口诀：
#   全小写 = Python 关键字。大写开头 = 类型名或你定义的类。
#   下划线开头 = 约定私有。引号里的键名 = OpenAI 定的。
#   剩下全是你自己起的变量名。


# ====== Q&A 问答笔记 ======
#
# Q1: 为什么要做记忆？
# A1: 之前每次 chat() 都新建 messages 列表。用户说"我叫小明"，下一轮全忘。
#     记忆就是把 messages 从"每次新建"变成"全局共享"，AI 能跨轮记住上下文。
#
# Q2: 为什么用 class 而不是普通函数？
# A2: class 把数据和操作打包在一起。self.messages 存数据，self.add() 操作数据。
#     每个 Agent 可以有自己的记忆实例，互不干扰。用函数只能维护全局变量——不方便扩展。
#
# Q3: __init__ 是干嘛的？双下划线是什么意思？
# A3: __init__ 是 Python 内置的特殊方法——创建对象时自动调用。双下划线是 Python 约定——
#     "这是系统内置方法，不是你随便写的普通函数"。
#     memory = ConversationMemory() 时，Python 自动调用 __init__()。
#
# Q4: _trim 为什么以下划线开头？
# A4: Python 约定——_ 开头 = 私有的，模块内部自己用，外人别碰。
#     不是语法强制（你依然可以从外部调用 memory._trim()），是一种礼貌标记。
#
# Q5: 为什么 _trim 里用 max_messages * 2 而不是 max_messages？
# A5: 不是每次加消息都裁剪——太频繁浪费性能。等页数翻倍了再动手。
#     而且保留下来的不是刚好 max_messages 而是 1.5 倍——留缓冲，避免下次写一行又得撕。
#
# Q6: get_messages() 为什么用 [-max_messages:] 切片？
# A6: Python 列表的负数切片——从倒数第 N 个取到末尾。[-20:] = 最近 20 条。
#     这不叫删除旧数据（messages 列表实际没变短），只是返回视图时截断。
#     真正的删除在 _trim() 里。
#
# Q7: add_assistant_message 里 text or "" 是干嘛的？
# A7: or 短路逻辑。AI 有时只返回 tool_calls 不给 text（直接调工具不说话）。
#     text = None → None or "" → 取 ""，避免把 None 写进消息里。
#
# Q8: 整个记忆的工作流程是怎样的？
# A8: 你问"我叫小明" → add_user_message → 日记本：[system, user:"我叫小明"]
#     → AI 回答"好的小明~" → add_assistant_message → 日记本：[system, user, assistant]
#     → 下次你问"我叫什么" → get_messages() → AI 看到完整历史 → "你叫小明！"
#
# Q9: _trim() 里 keep = min(max_messages * 3 // 2, len(messages)) 每部分是什么意思？
# A9: max_messages * 3 // 2 = 20 * 3 // 2 = 30 —— 保留 1.5 倍（留缓冲）。
#      // 是整除（地板除），返回整数——切片只能用整数索引，不能用浮点数。

#      min(30, len(messages)) = 取两者中较小值。
#      消息不到 30 条时保留全部（不扩容），超过 30 条时裁剪到 30。
#
#      messages[-keep:] = 负数切片——从倒数第 keep 个取到末尾。
#      messages[-30:] = 最近 30 条，旧的全部扔掉。
#
# Q10: 为什么 _trim 保留 1.5 倍而不是刚好 max_messages？
# A10: 如果每次都裁到刚好 20 条——下次 add() 加一条又超了，又裁剪。
#      每次加消息都触发切片，浪费性能。多保留 50% 缓冲——下次加几条不会立刻又超。