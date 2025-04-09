import asyncio

import mcp_query_table
from mcp_query_table import *
from mcp_query_table.enums import Provider

mcp_query_table.TIMEOUT = 1000 * 60 * 3  # 3分钟超时


async def main() -> None:
    async with BrowserManager(cdp_endpoint="http://127.0.0.1:9222", executable_path=None, debug=False) as bm:
        page1 = await bm.get_page()
        page2 = await bm.get_page()

        with open("mcp.txt", 'r', encoding='utf-8') as f:
            prompt = f.read()

        files = [
            # r"D:\Users\Kan\Documents\GitHub\mcp_query_table\examples\mcp.txt",
            r"d:\1.png"
        ]

        output = await chat(page1, "2+3等于多少？", provider=Provider.BaiDu)
        print(output)
        output = await chat(page1, "2+3等于多少？", provider=Provider.Nami)
        print(output)
        output = await chat(page2, "2+3等于多少？", provider=Provider.YuanBao)
        print(output)
        output = await chat(page2, "这张照片的拍摄参数是多少？", files=files, provider=Provider.Nami)
        print(output)
        output = await chat(page2, "描述下文件内容", files=files, provider=Provider.YuanBao)
        print(output)
        bm.release_page(page1)
        bm.release_page(page2)


if __name__ == '__main__':
    asyncio.run(main())
