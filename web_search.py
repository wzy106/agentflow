# web_search.py —— 网络搜索工具

def web_search(query: str, max_results: int = 3) -> str:
    """搜索互联网，返回结果摘要"""
    try:
        from duckduckgo_search import DDGS

        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(
                    f"[{r['title']}]\n{r['href']}\n{r['body']}"
                )

        if not results:
            return "没有找到相关结果"

        return "\n\n".join(results)

    except ImportError:
        return "错误：请先安装 pip install duckduckgo-search"
    except Exception as e:
        return f"搜索失败：{e}"
