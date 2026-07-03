import asyncio

from mcp_query_table import *
from mcp_query_table.playwright_helper import AsyncBrowser, get_chrome_path, kill_browsers  # noqa


async def main() -> None:
    kill_browsers("chrome.exe")
    # kill_browsers("msedge.exe")
    async with AsyncBrowser(endpoint="http://127.0.0.1:9222",
                            executable_path=get_chrome_path(),
                            devtools=True,
                            user_data_dir="D:\\user_data") as browser:
        # 问财需要保证浏览器宽度>768，防止界面变成适应手机
        page = await browser.get_page()
        df = await query(page, '收益最好的175只ETF', query_type=QueryType.ETF, max_page=3, site=Site.THS)
        print(df.to_markdown())
        df = await query(page, '年初至今收益率前50', query_type=QueryType.Fund, max_page=3, site=Site.TDX)
        print(df.to_csv())
        df = await query(page, '流通市值前10的行业板块', query_type=QueryType.Index, max_page=1, site=Site.TDX)
        print(df.to_csv())
        # # TODO 东财翻页要提前登录
        df = await query(page, '今日涨幅前5的概念板块;', query_type=QueryType.Board, max_page=3, site=Site.EastMoney)
        print(df)
        print('done')
        await page.wait_for_timeout(2000)


if __name__ == '__main__':
    asyncio.run(main())
