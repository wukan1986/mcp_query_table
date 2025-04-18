import asyncio
import getpass

from mcp_query_table import *
from mcp_query_table.enums import Provider


async def main() -> None:
    endpoint = "http://127.0.0.1:9222"
    executable_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    user_data_dir = rf'C:\Users\{getpass.getuser()}\AppData\Local\Google\Chrome\User Data'
    async with BrowserManager(endpoint=None,
                              executable_path=executable_path,
                              devtools=False,
                              headless=True,
                              user_data_dir=user_data_dir) as bm:
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
        output = await chat(page1, "3+4等于多少？", provider=Provider.Nami)
        print(output)
        output = await chat(page2, "4+5等于多少？", provider=Provider.YuanBao)
        print(output)
        output = await chat(page2, "这张照片的拍摄参数是多少？", files=files, provider=Provider.Nami)
        print(output)
        output = await chat(page2, "描述下文件内容", files=files, provider=Provider.YuanBao)
        print(output)
        output = await chat(page2, "描述下文件内容", files=files, provider=Provider.BaiDu)
        print(output)

        bm.release_page(page1)
        bm.release_page(page2)


if __name__ == '__main__':
    asyncio.run(main())
