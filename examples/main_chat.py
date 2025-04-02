import asyncio

import mcp_query_table
from mcp_query_table import *
from mcp_query_table.enums import Provider

mcp_query_table.TIMEOUT = 1000 * 60 * 3  # 3分钟超时


async def main() -> None:
    async with BrowserManager(port=9222, browser_path=None, debug=False) as bm:
        page1 = await bm.get_page()
        page2 = await bm.get_page()

        with open("mcp.txt", 'r', encoding='utf-8') as f:
            prompt = f.read()

        output = await chat(page1, "2+3等于多少？", provider=Provider.BaiDu)
        print(output)
        output = await chat(page1, "3*4等于多少？", provider=Provider.BaiDu)
        print(output)
        output = await chat(page2, prompt, provider=Provider.N)
        print(output)
        output = await chat(page2, prompt, provider=Provider.YuanBao)
        print(output)
        bm.release_page(page1)
        bm.release_page(page2)


if __name__ == '__main__':
    asyncio.run(main())
