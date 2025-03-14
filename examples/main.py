from query_table import *


def run() -> None:
    # 启动浏览器，browser_path最好是Chrome的绝对路劲
    playwright, browser, context, page = launch_browser(port=9222, browser_path=None)

    # 问财需要保证浏览器宽度>768，防止界面变成适应手机
    df = query(page, '收盘价>50元', query_type=QueryType.CNStock, max_page=3, site=Site.iwencai)
    print(df)
    df = query(page, '收盘价>50元', query_type=QueryType.CNStock, max_page=3, site=Site.tdx)
    print(df)
    # TODO 东财翻页要提前登录
    df = query(page, '收盘价>50元', query_type=QueryType.CNStock, max_page=3, site=Site.eastmoney)
    print(df)

    print('done')
    browser.close()
    playwright.stop()


if __name__ == '__main__':
    run()
