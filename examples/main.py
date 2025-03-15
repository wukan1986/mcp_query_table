import asyncio

from query_table import *


async def main() -> None:
    # 启动浏览器，browser_path最好是Chrome的绝对路径
    playwright, browser, context, page = await launch_browser(port=9222, browser_path=None)
    print(browser.is_connected(), page.is_closed())

    # 问财需要保证浏览器宽度>768，防止界面变成适应手机
    df = await query(page, '收盘价>50元', query_type=QueryType.CNStock, max_page=3, site=Site.THS)
    print(df.to_markdown())
    df = await query(page, '收盘价>50元', query_type=QueryType.CNStock, max_page=3, site=Site.TDX)
    print(df.to_csv())
    # # TODO 东财翻页要提前登录
    df = await query(page, '收盘价>50元', query_type=QueryType.CNStock, max_page=3, site=Site.EastMoney)
    print(df)

    print('done')
    await browser.close()
    await playwright.stop()


if __name__ == '__main__':
    asyncio.run(main())
