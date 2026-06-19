"""
Day 15：RAG 文档检索 —— 先查文档，再回答
=============================================
RAG = Retrieval Augmented Generation（检索增强生成）。
把用户上传的文档切成小块存起来，提问时找到最相关的几块，喂给 AI 参考。

类比：
  上传文档 = 往书架上放书
  提问搜索 = 根据关键词去书架上找到对应那本书，翻到相关那页
"""

import re
# re = 正则表达式模块，用它按段落空行切分文档。


class SimpleRAG:
    # SimpleRAG = 你起的类名，不是专有名词。可以叫 DocStore、KnowledgeBase 都行。
    """简单的文档检索——基于词重叠 + 字符重叠匹配"""

    def __init__(self):
        # __init__ = Python 内置方法，创建实例时自动调用。
        self.chunks = []       # 文档块列表——你起的属性名
        self.sources = []      # 每块来自哪个文件——你起的属性名
        # chunks 和 sources 一一对应：chunks[i] 的内容来自 sources[i]。
        # 两个列表必须同步 append，否则索引对不上。

    def ingest(self, text: str, source: str = "上传文件") -> int:
        # ingest = 你起的方法名（意为"摄入"）。text = 要存的文档全文（你起的参数名）。
        # source = 来源标记（你起的）。-> int = 返回整数——切了多少块。
        """
        把一段文字切块并存储。返回切了多少块。
        """
        # ====== 按段落切分 ======
        # re.split(r"\n\s*\n", text.strip())
        #   \n   = 换行符
        #   \s*  = 零个或多个空白字符（空格、Tab、残留的空行）
        #   \n   = 又一个换行符
        #   合起来 = 匹配段落之间的空行（不管是 Windows \r\n 还是 Linux \n）
        #   text.strip() 先把首尾空白去掉，防止开头空行被切出一个空段落。
        #
        # r"..." = 原始字符串——\n 保持原样交给 re 模块解释。
        paragraphs = re.split(r"\n\s*\n", text.strip())

        count = 0   # 计数器——这次切了多少有效块

        for para in paragraphs:
            para = para.strip()                  # 再去一遍首尾空白
            if len(para) > 30:                   # 太短的跳过（标题、空行残留）
                self.chunks.append(para[:1000])  # 每块最多 1000 字
                # [:1000] = 切片——从头取到第 1000 个字符（不含第 1000 个）
                # 等价于 [0:1000]。防止某一段特别长撑爆内存。
                self.sources.append(source)      # 记录来源（和 chunks 同步 append！）
                count += 1
        return count
        # 返回实际存储的块数。跳过的不算。

    def retrieve(self, query: str, top_k: int = 3) -> list[str]:
        # retrieve = 你起的方法名（意为"检索"）。query = 查询词（你起的）。
        # top_k = 返回前几条（你起的，默认 3）。-> list[str] = 返回字符串列表。
        """
        找到和问题最相关的文档块。
        英文按词重叠计分，中文按字符重叠计分。
        """
        # ====== 空库检查 ======
        if not self.chunks:
            # not [] = True（空列表是假的）。啥都没存 → 直接返回空列表。
            return []

        # ====== 逐块打分 ======
        scored = []  # 存 (分数, 索引) 元组列表

        for i, chunk in enumerate(self.chunks):
            # enumerate() 同时拿索引 i 和内容 chunk。
            # 第 1 轮：i=0, chunk="块A"
            # 第 2 轮：i=1, chunk="块B"

            score = 0

            # ----- 英文：按空格分词 -----
            # .lower() = 转小写——"AgentFlow" 和 "agentflow" 算同一个词
            # .split() = 按空格切词（只对英文有效，中文没空格）
            eng_q = set(query.lower().split())    # query 的英文词集合
            eng_c = set(chunk.lower().split())    # chunk 的英文词集合
            score += len(eng_q & eng_c)
            # & = 集合交集——两边都有的词
            # len(...) = 共有多少个英文词匹配

            # ----- 中文：直接数字符重叠 -----
            # set(字符串) = 把字符串拆成单个字符的集合
            # "你好" → {"你", "好"}
            # 中文没有空格分隔，所以不能 split()，直接数字符重叠。
            cn_q = set(query)                    # query 的字符集合
            cn_c = set(chunk)                    # chunk 的字符集合
            score += len(cn_q & cn_c)            # 共有的中文字符数

            # 分数 > 0 才进候选（0 分 = 完全无关）
            if score > 0:
                scored.append((score, i))
                # (score, i) = 元组——打包分数和索引

        # ====== 按分数排序 ======
        scored.sort(reverse=True)
        # reverse=True = 降序——分最高的排第一

        # ====== 取前 top_k 条 ======
        results = []
        for _, idx in scored[:top_k]:
            # _ = 丢弃分数（不需要了，只要索引）
            # idx = 文档块在 chunks 里的位置
            src = self.sources[idx]             # 这个块来自哪个文件
            results.append(f"[来源：{src}]\n{self.chunks[idx]}")
            # f-string 拼格式——来源 + 换行 + 文档内容

        return results

    def clear(self):
        """清空全部文档——重置为初始状态"""
        self.chunks = []
        self.sources = []


# ====== 全局实例 ======
rag = SimpleRAG()
# 模块加载时创建一次。server.py 里 from rag import rag 共用同一个实例。
# 这是单例模式——所有地方操作同一个知识库。


# ====== Q&A 问答笔记 ======
#
# Q1: SimpleRAG、chunks、sources、ingest、retrieve 是专有名词吗？
# A1: 全是你自己起的名字。SimpleRAG 是类名，chunks/sources 是属性名，
#     ingest/retrieve 是方法名，text/query/top_k 是参数名——一个系统保留词都没有。
#     chunks 可以叫 kuai，ingest 可以叫 chi——但因为英文单词能描述功能，所以大家这么起。
#
# Q2: ingest 和 retrieve 分别是干嘛的？text 和 query 有什么区别？
# A2: ingest(吃进去)——上传文档时用。text 是一大篇文章，切成小块存起来。
#     retrieve(取回来)——提问搜索时用。query 是一句话，用来匹配最相关的文档块。
#     text 几百到几千字，query 几个到十几个字。方向相反：一个存，一个查。
#
# Q3: self 是什么？为什么每个方法第一个参数都是 self？
# A3: Python 自动把"调用者"作为第一个参数传进去。
#     rag.ingest("文档","来源") 看似只传了两个参数，
#     Python 帮你塞了 rag 自己到第一位 → 等价于 SimpleRAG.ingest(rag, "文档", "来源")。
#     self 就是那个被塞进来的 rag。不是关键字，但全世界都这么写。
#
# Q4: re.split(r"\n\s*\n", text.strip()) 是干什么的？能切什么？
# A4: 按段落之间的空行切分文档。
#     \n\s*\n = 换行 + 可能有些空白 + 换行 = 空行。
#     比如 "今天天气很好\n\n我想出去玩" 会被切成 ["今天天气很好", "我想出去玩"]。
#     text.strip() 先把首尾空白去掉，防止开头空行被切出一个空段落。
#
# Q5: \s* 是什么？
# A5: \s = 任何空白字符（空格、Tab、换行、回车）。
#     * = 前面的东西可以出现 0 次或多次。
#     \s* = 可能有空白也可能没有——不管中间夹了几个空格都能匹配空行。
#
# Q6: para[:1000] 是从哪里开始截的？
# A6: 从第一个字符开始（索引 0）。[:1000] 等价于 [0:1000]——从头取到第 1000 个（不含）。
#     冒号左边不写数字 Python 默认填 0。不是截原字符串，是新建一个被截断的副本。
#
# Q7: enumerate() 是干嘛的？
# A7: 同时拿索引和值。for i, chunk in enumerate(self.chunks)——
#     第 1 轮 i=0,chunk="块A"；第 2 轮 i=1,chunk="块B"。比手写 i=0;i+=1 省两行。
#
# Q8: set() 和 & 分别是干嘛的？
# A8: set() 把列表或字符串转成集合（自动去重）。& 是集合交集——两边都有的元素。
#     {"a","b","c"} & {"b","c","d"} → {"b","c"}。len(...) 统计共有多少个。
#
# Q9: for _, idx in scored[:top_k] 里的 _ 是什么？
# A9: Python 约定——"这个变量我不需要，占个位置而已"。
#     scored 里每个元素是 (分数, 索引) 元组，只需要索引不需要分数，用 _ 扔掉分数。
#
# Q10: rag = SimpleRAG() 为什么放在文件最下面而不是里面？
# A10: 全局实例——模块加载时创建一次，所有人共享同一个对象。
#      放在函数里每次调用都新建——知识库就白存了。
#      单例模式：同一个对象到处用，上传和搜索操作同一份数据。
#
# Q11: 上传的文档关掉 server.py 后会消失吗？
# A11: 会。rag.chunks 存在内存里，进程关了就没了。
#      重启后需要重新上传。和 ConversationMemory 一样的命运。
#      持久化存储需要 FAISS + pickle（进阶功能）。