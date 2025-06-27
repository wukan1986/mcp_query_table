"""
"""
import asyncio
import re

from mcp_query_table import BrowserManager

query = {}


def __hook(e, a, b):
    print("111", e, a, b)


async def on_route(route, request):
    """找到特殊js文件，每过一段时间特殊文件名不同，但内部的函数名不变"""
    response = await route.fetch()
    body = await response.text()
    if "fetchFeedIndex:" not in body:
        await route.fulfill(response=response)
        return

    print(request.url)

    pattern = r'(fetchFeedIndex:)(.*?)(k\.a\.decrypt\(t\.data,e\.data\)\.split\(","\);)(.*?)(drawTrend:)'
    body = re.sub(pattern, r'\1 \2 \3 window.__hook(e,a,W.a.getDatesList(e.startDate, e.endDate, e.type));\4 \5', body,
                  flags=re.DOTALL)

    await route.fulfill(content_type="text/javascript; charset=utf-8", body=body)


async def on_flash(response):
    if "jin10.com/flash?channel=" in response.url:
        print(response.url)
        json_data = await response.json()
        for i in json_data['data']:
            print("flash?channel=", i)


async def main() -> None:
    # taskkill /f /im msedge.exe
    async with BrowserManager(port=9222, browser_path=r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
                              devtools=False) as bm:
        page = await bm.get_page()
        await page.expose_function("__hook", __hook)
        await page.route("**/static/js/main.*.js", on_route)
        # page.on("response", on_flash)
        await page.goto("https://index.baidu.com/v2/index.html#/")
        await page.get_by_role("searchbox", name="请输入您想查询的关键词").click()
        await page.get_by_role("searchbox", name="请输入您想查询的关键词").fill("上证指数")
        await page.get_by_role("searchbox", name="请输入您想查询的关键词").press("Enter")

        await page.wait_for_timeout(1000 * 1000)
        print('done')
        bm.release_page(page)
        await bm.cleanup()


if __name__ == '__main__':
    asyncio.run(main())
