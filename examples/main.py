import asyncio

from query_table import *


async def main() -> None:
    # 启动浏览器，browser_path最好是Chrome的绝对路径
    playwright, browser, context, page = await launch_browser(cdp_port=9222, browser_path=None)
    print(browser.is_connected(), page.is_closed())

    # 问财需要保证浏览器宽度>768，防止界面变成适应手机
    df = await query(page, '收益最好的200只ETF', query_type=QueryType.ETF, max_page=1, site=Site.THS)
    print(df.to_markdown())
    df = await query(page, '年初至今收益率前50', query_type=QueryType.Fund, max_page=1, site=Site.TDX)
    print(df.to_csv())
    df = await query(page, '流通市值前10的行业板块', query_type=QueryType.Index, max_page=1, site=Site.TDX)
    print(df.to_csv())
    # TODO 东财翻页要提前登录
    df = await query(page, '今日涨幅前5的概念板块;', query_type=QueryType.Board, max_page=3, site=Site.EastMoney)
    print(df)

    print('done')
    await page.wait_for_timeout(1000 * 600)
    await browser.close()
    await playwright.stop()


if __name__ == '__main__':
    asyncio.run(main())
