import asyncio

from mcp_query_table import *


async def main() -> None:
    async with BrowserManager(cdp_endpoint=None, executable_path=None, debug=True) as bm:
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
