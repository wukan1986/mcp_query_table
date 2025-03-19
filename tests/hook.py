"""
只是为以后各平台安全升级做破解准备，暂时不使用

某网站返回的数据是json中有字段是加密的，需要获取解密后的内容
"""
import asyncio

from query_table import launch_browser


def __hook(obj):
    print(obj)


async def main() -> None:
    playwright, browser, context, page = await launch_browser(port=9222, browser_path=None)
    print(browser.is_connected(), page.is_closed())

    await page.expose_function("__hook", __hook)
    # TODO 为何都是第一次hook不成，这可都是改文件了，怎么回事？
    await page.route("https://dc.simuwang.com/_nuxt3/rY-FUFEX.js",
                     lambda route: route.fulfill(path="rY-FUFEX.js"))  # 第3行
    # await page.route("https://dc.simuwang.com/_nuxt3/DNmjgBLm.js",
    #                  lambda route: route.fulfill(path="DNmjgBLm.js"))  # 第18268行
    await page.goto("https://dc.simuwang.com/smph", wait_until="load")

    await page.wait_for_timeout(1000 * 600)

    # 这是另一种方式，直接获取页面的html，然后解析
    """
    tables = page.get_by_role("table")
    for table in tables.all():
        print("=" * 60)
        inner_html = "<table>" + table.inner_html() + "</table>"
        df = pd.read_html(StringIO(inner_html))
        if len(df) > 0:
            print(df[0])
    """


if __name__ == '__main__':
    asyncio.run(main())
