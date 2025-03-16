"""
本示例演示了如何使用同步风格来调用异步函数编写代码
但还是有局限性，可以在Python REPL环境中一行行输入使用，但无法在Windows下的Jupyter Notebook中使用

使用方法有3种，选一种即可
1. 直接`python main_sync.py`运行本文件
2. 在控制台中输入`python`,提示`>>>`,然后输入代码
3. 在VSCode中选中一行，让后右键`Run Python` > `Run Selection/Line in Native Python REPL`
    - 可以使用Shift+Enter来运行选中代码。但要在插件中禁用`Jupyter`，因为`Run in Interactive Window`下的功能快捷键冲突

"""
# %%

import revolving_asyncio  # pip install revolving_asyncio
# revolving_asyncio.apply()

# %%
from query_table import launch_browser, query, QueryType, Site

launch_browser = revolving_asyncio.to_sync(launch_browser)
query = revolving_asyncio.to_sync(query)

# %%
playwright, browser, context, page = launch_browser(port=9222, browser_path=None)
# %%
df = query(page, '收盘价>50元的港股', query_type=QueryType.HKStock, max_page=3, site=Site.THS)
print(df.to_markdown())
# %%
df = query(page, '年初至今收益率前50', query_type=QueryType.Fund, max_page=3, site=Site.TDX)
print(df.to_csv())
# %%
df = query(page, '收盘价>50元', query_type=QueryType.HKStock, max_page=3, site=Site.EastMoney)
print(df)
