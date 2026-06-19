"""
Day 5：网络搜索工具
====================
使用 DuckDuckGo 免费 API 搜索互联网，返回格式化的搜索结果。
不需要 API Key，pip install duckduckgo-search 就能用。
"""


def web_search(query: str, max_results: int = 3) -> str:
#               ^^^^^^^^^^^  ^^^^^^^^^^^^^^^^^^^^^^^^
#          参数：搜索关键词          参数：最多返回几条，默认 3
#          : str = 传字符串          : int = 3 = 默认值（不传自动用 3）
#                                              -> str = 返回值是字符串
    """搜索互联网，返回结果摘要"""

    try:
        # ====== 在函数内部 import ======
        # 好处：只有调用这个函数时才加载模块。
        # 如果用户没装这个库但也没用到搜索功能，不会报错。
        from duckduckgo_search import DDGS
        # DDGS = DuckDuckGo Search 的客户端类

        # ====== 搜索结果列表 ======
        results = []
        # 空列表，等会儿往里塞每条结果

        # ====== 上下文管理器：with ... as ======
        # with 打开连接 → 用完后自动关闭（不管中间是否出错）
        # 等价于：ddgs = DDGS() → ... → ddgs.close()
        with DDGS() as ddgs:

            # ====== 调用搜索 API ======
            # ddgs.text(query, max_results=max_results)
            #   ↑ API 的参数名       ↑ 你的变量名
            #   左边是库作者定死的    右边是你定义的
            #   虽然同名，但是两个不同的东西
            #
            # query 没写 query=query 是因为它是第一个参数，
            # 位置天然对应，可以省略参数名。
            # max_results 写了 max_results=max_results 是为了清晰。
            #
            for r in ddgs.text(query, max_results=max_results):
                # r 是每条搜索结果，是一个字典：
                # {"title": "标题", "href": "网址", "body": "摘要"}

                # ====== f-string 格式化每条结果 ======
                # f"[{r['title']}]\n{r['href']}\n{r['body']}"
                #   f"..." = f-string，花括号里放变量
                #   r['title'] = 标题（字典取值）
                #   \n = 换行符
                # 拼成： [标题]\n网址\n摘要
                results.append(
                    f"[{r['title']}]\n{r['href']}\n{r['body']}"
                )
                # .append() = 往列表末尾加一个元素

        # ====== 无结果处理 ======
        if not results:
            # not [] = True（空列表是"假"的）
            return "没有找到相关结果"

        # ====== join 拼接 ======
        # "\n\n".join(results)
        #   双换行（空一行）把所有结果拼成一个大字符串
        #   列表 [结果1, 结果2, 结果3]
        #   → "结果1\n\n结果2\n\n结果3"
        return "\n\n".join(results)

    # ====== 异常处理：两层 except ======
    # except 从上到下匹配，命中一个就跳过后面的

    except ImportError:
        # ImportError = import 失败（没装 duckduckgo-search）
        return "错误：请先安装 pip install duckduckgo-search"

    except Exception as e:
        # Exception = Python 所有"普通错误"的总父类
        #   → 网络不通、DuckDuckGo 挂了、返回格式不对...全抓
        # as e = 把异常对象存到变量 e
        # {e} = f-string 把异常描述拼进返回信息
        return f"搜索失败：{e}"


# ====== Q&A 问答笔记 ======
#
# Q1: max_results: int = 3 中的 = 3 是什么？
# A1: 默认值。调用时不传这个参数自动用 3：web_search("Python") → max_results=3
#
# Q2: ddgs.text(query, max_results=max_results) 为什么左边右边名字一样？
# A2: 巧合。左边是 API 定死的参数名，右边是你定义的变量。只是恰好同名，
#     实际上它们是两个不同的东西。可以写成 ddgs.text(query=keyword, max_results=limit)。
#
# Q3: 为什么 query 没写 query=query？
# A3: query 是第一个参数，位置天然对应 API 的第一个参数，可以省略参数名。
#     max_results 不是第二个位置参数，所以需要写参数名指定。
#
# Q4: results.append(f"[{r['title']}]...") 中的各部分是干嘛的？
# A4: .append() 往列表加元素。f-string 花括号里取字典值（r['title']）。
#     \n 是换行符。拼成"标题+换行+网址+换行+摘要"的格式。
#
# Q5: .join() 是什么？
# A5: 字符串方法。"分隔符".join(列表) 把列表元素拼成一个大字符串，
#     中间插入分隔符。"\n\n".join(results) 用空行隔开每条结果。
#
# Q6: Exception 和 as e 是什么？
# A6: Exception 是 Python 所有普通错误的总父类（除 Ctrl+C 外）。
#     as e 把捕获到的异常对象存到变量 e。{e} 把具体错误描述拼进返回信息。
#     except 从上到下匹配，ImportError 先匹配，其他错误走 Exception 兜底。
