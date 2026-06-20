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
rag = VectorRAG()
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
