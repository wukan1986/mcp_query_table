"""
只是为以后各平台安全升级做破解准备，暂时不使用

某网站返回的数据是json中有字段是加密的，需要获取解密后的内容

直接hook请求函数，返回解密后的内容

首页是静态网页，翻页是fetch请求
"""
import asyncio

from query_table import launch_browser


def __hook(x, y, obj):
    print(x)
    print(y)
    print(obj)


async def main() -> None:
    playwright, browser, context, page = await launch_browser(port=9222, browser_path=None, debug=True)
    print(browser.is_connected(), page.is_closed())

    await page.expose_function("__hook", __hook)
    await page.route("**/_nuxt3/rY-FUFEX.js", lambda route: route.fulfill(path="rY-FUFEX.js"))  # 第3行
    await page.goto("https://dc.simuwang.com/smph", wait_until="load")

    # 强行翻页，产生fetch请求
    await page.get_by_role("button", name="上一页", disabled=True).evaluate(
        'element => { element.removeAttribute("disabled"); element.removeAttribute("aria-disabled");}')
    await page.get_by_role("button", name="上一页").click()

    await page.get_by_role("button", name="下一页").click()
    await page.get_by_role("button", name="下一页").click()

    print('done')
    await page.wait_for_timeout(1000 * 10)
    await browser.close()
    await playwright.stop()


if __name__ == '__main__':
    asyncio.run(main())
