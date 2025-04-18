import asyncio
import getpass

from mcp_query_table import *


async def main() -> None:
    endpoint = "http://127.0.0.1:9222"
    executable_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    user_data_dir = rf'C:\Users\{getpass.getuser()}\AppData\Local\Google\Chrome\User Data'
    # 以下使用的无头模式，速度快。建议先登录好网站账号再使用无头模式
    async with BrowserManager(endpoint=None,
                              executable_path=executable_path,
                              devtools=False,
                              headless=True,
                              user_data_dir=user_data_dir) as bm:
        # 问财需要保证浏览器宽度>768，防止界面变成适应手机
        page = await bm.get_page()
        df = await query(page, '收益最好的200只ETF', query_type=QueryType.ETF, max_page=1, site=Site.THS)
        print(df.to_markdown())
        df = await query(page, '年初至今收益率前50', query_type=QueryType.Fund, max_page=1, site=Site.TDX)
        print(df.to_csv())
        df = await query(page, '流通市值前10的行业板块', query_type=QueryType.Index, max_page=1, site=Site.TDX)
        print(df.to_csv())
        # TODO 东财翻页要提前登录
        df = await query(page, '今日涨幅前5的概念板块;', query_type=QueryType.Board, max_page=3, site=Site.EastMoney)
        print(df)
        bm.release_page(page)
        print('done')
        await page.wait_for_timeout(2000)


if __name__ == '__main__':
    asyncio.run(main())
