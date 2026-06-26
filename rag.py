"""
Day 18：FAISS 向量 RAG —— 语义匹配 + 持久化
==============================================
Day 15 的简化版用关键词/字符重叠匹配——"退货"搜不到"退款"。
Day 18 升级为向量语义匹配——意思相近就能搜到，重启数据不丢。
"""

import os
# 国内镜像必须在 import sentence_transformers 之前设置！
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

import re
import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from config import config


class VectorRAG:
    """向量语义检索——把文字变成数字，找最近的"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", data_dir: str = "./data/rag"):
        # 加载 embedding 模型（第一次从镜像下载，之后从本地加载）
        print("正在加载 embedding 模型...")
        self.model = SentenceTransformer(model_name)
        self.dim = self.model.get_embedding_dimension()  # 384

        # FAISS 索引（向量搜索引擎）
        self.index = faiss.IndexFlatL2(self.dim)
        # IndexFlatL2 = 暴力 L2 距离搜索（精确但较慢）
        # self.dim = 384 维

        # 文档元数据
        self.chunks = []       # 文档块原文
        self.sources = []      # 每块来源

        # 持久化路径
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

        # 尝试从硬盘加载已有数据
        self._load()

    def ingest(self, text: str, source: str = "上传文件") -> int:
        """切块 → 向量化 → 存进 FAISS → 保存到硬盘"""
        paragraphs = re.split(r"\n\s*\n", text.strip())
        new_chunks = []

        for para in paragraphs:
            para = para.strip()
            if len(para) > 30:
                new_chunks.append(para[:1000])

        if not new_chunks:
            return 0

        # 把文字变成向量
        vectors = self.model.encode(new_chunks)
        # vectors.shape = (块数, 384)

        # 加进 FAISS 索引
        self.index.add(vectors.astype(np.float32))

        # 记录原文和来源
        for chunk in new_chunks:
            self.chunks.append(chunk)
            self.sources.append(source)

        # 保存到硬盘（重启不丢）
        self._save()

        return len(new_chunks)

    def retrieve(self, query: str, top_k: int = 3) -> list[str]:
        """问题 → 向量 → FAISS 找最近的几个 → 返回原文"""
        if self.index.ntotal == 0:
            return []

        # 问题变成向量
        query_vec = self.model.encode([query]).astype(np.float32)
        # query_vec.shape = (1, 384)

        # FAISS 搜索最近的 top_k 个
        k = min(top_k, self.index.ntotal)
        distances, indices = self.index.search(query_vec, k)
        # distances = [[0.03, 0.15, 0.82]]  ← 距离，越小越相关
        # indices   = [[2, 0, 5]]            ← 对应 chunks 列表的索引

        results = []
        for i, idx in enumerate(indices[0]):
            if idx >= 0 and idx < len(self.chunks):
                src = self.sources[idx]
                dist = round(float(distances[0][i]), 4)
                results.append(f"[来源：{src}] (相关度：{dist})\n{self.chunks[idx]}")

        return results

    def _save(self) -> None:
        """保存到硬盘——FAISS 索引 + 文档元数据"""
        idx_path = os.path.join(self.data_dir, "faiss.index")
        meta_path = os.path.join(self.data_dir, "meta.pkl")

        faiss.write_index(self.index, idx_path)
        with open(meta_path, "wb") as f:
            pickle.dump({"chunks": self.chunks, "sources": self.sources}, f)

    def _load(self) -> None:
        """从硬盘加载——如果有的话"""
        idx_path = os.path.join(self.data_dir, "faiss.index")
        meta_path = os.path.join(self.data_dir, "meta.pkl")

        if os.path.exists(idx_path) and os.path.exists(meta_path):
            self.index = faiss.read_index(idx_path)
            with open(meta_path, "rb") as f:
                meta = pickle.load(f)
                self.chunks = meta["chunks"]
                self.sources = meta["sources"]
            print(f"从硬盘加载了 {len(self.chunks)} 个文档块")

    def clear(self) -> None:
        """清空全部——内存 + 硬盘"""
        self.chunks = []
        self.sources = []
        self.index = faiss.IndexFlatL2(self.dim)

        idx_path = os.path.join(self.data_dir, "faiss.index")
        meta_path = os.path.join(self.data_dir, "meta.pkl")
        if os.path.exists(idx_path):
            os.remove(idx_path)
        if os.path.exists(meta_path):
            os.remove(meta_path)


# 全局实例
rag = VectorRAG(model_name=config.embedding_model, data_dir=config.rag_data_dir)
# 模块加载时创建一次。tools.py 里 from rag import rag 共用同一个实例。


# ====== Q&A 问答笔记（Day 17-18） ======
#
# Q1: SentenceTransformer 是什么？下载了什么？
# A1: 把文字变成向量的工具。第一次运行时从镜像下载 all-MiniLM-L6-v2 模型（约 80MB），
#     存到 C:\Users\wzyls\.cache\huggingface\ 里。下载一次以后从本地加载，不联网。
#
# Q2: all-MiniLM-L6-v2 是什么？
# A2: 微软训练好的文字转向量模型。all=通用，MiniLM=轻量架构，L6=6层，v2=第二版。
#     输出 384 维向量。主要支持英文，中文效果一般。中文专用模型用 text2vec-base-chinese。
#
# Q3: FAISS 是什么？
# A3: Meta 开源的向量搜索引擎——给一个向量，在几百万个向量里快速找最近的几个。
#     用 C++ 写的，比 Python for 循环快几百倍。IndexFlatL2 = 暴力 L2 距离搜索。
#
# Q4: 为什么国内要设 HF_ENDPOINT 镜像？
# A4: HuggingFace（模型托管网站）在国内连不上。hf-mirror.com 是国内镜像站——
#     内容一样，服务器在国内。必须在 import sentence_transformers 之前设置，否则太晚。
#
# Q5: get_embedding_dimension() 是干什么的？
# A5: 问模型"你输出的向量是几维的"。all-MiniLM-L6-v2 返回 384。
#     换模型时不用手改维度——这个方法自动返回正确值。
#     注意：旧版叫 get_sentence_embedding_dimension()，新版改名了。
#
# Q6: ./data/rag 是哪里？os.makedirs 是干什么的？
# A6: ./ = 你运行 python 命令时所在的文件夹。在 myagent 下跑就是 myagent/data/rag/。
#     os.makedirs(路径, exist_ok=True) = 创建文件夹。exist_ok=True = 已存在不报错。
#     创建一次就行，以后每次启动自动跳过。
#
# Q7: 哪些是自己起的名字，哪些是系统定的？
# A7: 自己起的：model_name, data_dir, self.model, self.dim, self.index,
#              self.chunks, self.sources, self.data_dir, VectorRAG
#     系统定的：__init__, self, SentenceTransformer, get_embedding_dimension(),
#              faiss, IndexFlatL2, os.makedirs, exist_ok
#     模型名 "all-MiniLM-L6-v2" 是模型作者起的——改了找不到模型。
#     记忆口诀：self. 后面的属性名 = 你起的。import 进来的 = 别人定的。
#
# Q8: 向量距离怎么算的？
# A8: L2 欧氏距离 = √((a₁-b₁)² + (a₂-b₂)² + ... + (a₃₈₄-b₃₈₄)²)
#     就是线性代数里两点距离公式——从二维推广到 384 维。
#     Python 写法：sum((a-b)**2 for a,b in zip(v1,v2))**0.5
#     zip() 配对 → (a-b)**2 差的平方 → sum() 求和 → **0.5 开根号
#
# Q9: 为什么测试 3（"今天天气怎么样"）也返回了结果？
# A9: FAISS 总是返回最近的 top_k 个，不管多远。知识库只有一块——
#     不管问什么都返回那一块。加距离阈值过滤（距离>1.2就不返回）可以解决。
#
# Q10: pickle 存了什么？存在哪？
# A10: _save() 存两个文件到 ./data/rag/：
#      faiss.index = FAISS 向量索引（二进制）
#      meta.pkl = 文档原文和来源（pickle 序列化的 Python 字典）
#      _load() 启动时从这两个文件恢复——重启 server.py 数据不丢。
#
# Q11: 这些知识是哪个阶段学的？
# A11: FAISS/Embedding/sentence-transformers = 研究生或 AI 工程师入职培训。
#      pickle/numpy/os.makedirs = 大二 Python 进阶。
#      L2 距离 = 大一线性代数（你已经学了）。
#      你大一用研究生的工具，但用的是工程方式（调 API），不是研究方式（推公式）。
#
# Q12: os.path.join() 为什么不直接写路径字符串？
# A12: Windows 用 \，Linux 用 /。os.path.join() 自动适配——代码搬到服务器也能跑。
#      os.path.join("./data/rag", "faiss.index") → Windows: .\data\rag\faiss.index
#                                                  → Linux: ./data/rag/faiss.index
#
# Q13: open("wb") 和 open("rb") 里的 b 是什么？
# A13: b = binary（二进制）。pickle 存的是二进制数据不是文本。
#      写用 "wb"（write binary），读用 "rb"（read binary）。
#      不加 b 用文本模式会报错或数据损坏。
#
# Q14: pickle.dump 和 pickle.load 分别做什么？
# A14: dump = 把 Python 对象变成二进制写进文件（序列化）。
#      load = 从文件读二进制还原成 Python 对象（反序列化）。
#      存进去是字典，读出来还是字典——格式不变。
#      注意：不要 load 不信任来源的 .pkl 文件——攻击者可以在里面藏恶意代码。
#
# Q15: with open(...) as f 为什么不用手动 f.close()？
# A15: with 是上下文管理器——写完/读完自动关文件。
#      就算中间报错也会自动关——不会留下没关的文件句柄。
#
# Q16: model.encode([query]) 为什么要套方括号？
# A16: encode("你好") 返回一维数组 (384,)——FAISS 不认。
#      encode(["你好"]) 返回二维数组 (1, 384)——FAISS 要这个。
#      FAISS 的 search() 要求输入是二维的，即使只搜一条也要包成列表。
#
# Q17: .astype(np.float32) 为什么必须加？
# A17: model.encode() 输出 float64，FAISS 只认 float32。不转直接报错。
#      float32 精度够用（384 维不需要 64 位），还省一半内存。
#
# Q18: clear() 为什么要同时清内存和硬盘？
# A18: 只清内存不清硬盘 → 重启后 _load() 又读回来了，没清干净。
#      只清硬盘不清内存 → 当前会话还能搜到旧内容，重启后才真正干净。
#      两边都清 → 立刻生效，不用等重启。
#
# Q19: FAISS 索引为什么不能 clear() 只能重建？
# A19: FAISS 的 IndexFlatL2 没有清空方法。
#      self.index = faiss.IndexFlatL2(self.dim) 直接造一个新的空索引替换旧的。
#      旧索引没人引用后被 Python 垃圾回收自动释放内存。
#
# Q20: self.index 是什么？为什么要 faiss.IndexFlatL2(self.dim)？
# A20: self.index 是向量仓库——存向量、搜向量的容器。
#      faiss.IndexFlatL2(384) = 创建一个空仓库：能存 384 维向量，用 L2 距离搜索。
#      Index=索引，Flat=暴力逐个对比，L2=欧氏距离。
#      创建后能干三件事：.add(向量) 存入，.search(向量, k) 搜索，.ntotal 查数量。
#      类比：chunks 是书架（存原文），index 是目录（存向量，按距离快速查找）。
#
# Q21: distances 和 indices 分别是什么？怎么配合使用？
# A21: self.index.search(query_vec, 3) 返回两个数组：
#      distances = [[0.38, 1.15, 1.42]] — 每个结果离问题多远（越小越相关）
#      indices   = [[0, 3, 1]]          — 每个结果在 chunks 列表里的位置（门牌号）
#      distances 告诉你"靠不靠谱"，indices 告诉你"去哪找内容"。
#      用 indices 的值去 self.chunks[idx] 取原文，用 distances 的值显示相关度。
#      类比：distances = 每家店离你多远，indices = 每家店的门牌号。
#
# Q22: 为什么 _save/_load/clear 三个函数重复写 os.path.join？
# A22: 因为 idx_path 和 meta_path 是局部变量——函数结束就消失。
#      三个函数各自独立，一个函数的局部变量另一个看不到。
#      更好的写法：在 __init__ 里存成 self.idx_path 和 self.meta_path，
#      三个函数共享——算一次，到处用。现在的写法不是错，只是重复了。
