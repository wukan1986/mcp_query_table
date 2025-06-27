"""
# https://4a735ea38f8146198dc205d2e2d1bd28.z3c.jin10.com/flash?channel=-8200&vip=1&classify=[13]
# https://flash-api.jin10.com/get_flash_list?channel=-8200&vip=1
# wss://wss-flash-2.jin10.com/

socket.io 导致不同浏览器用的机制不同，例如在本人电脑中
chrome 走 https://4a735ea38f8146198dc205d2e2d1bd28.z3c.jin10.com/flash?channel=-8200&vip=1&classify=[13]
edge 走 wss://wss-flash-2.jin10.com/
"""
import asyncio

from mcp_query_table import BrowserManager

query = {}


def __hook(obj):
    print("dealSocketData", obj)


async def on_route(route, request):
    """找到特殊js文件，每过一段时间特殊文件名不同，但内部的函数名不变"""
    response = await route.fetch()
    body = await response.text()
    if "dealSocketData" not in body:
        await route.fulfill(response=response)
        return

    print(request.url)
    # 解决了实时，如何解决历史数据
    body = body.replace("dealSocketData:function(t){", """
dealSocketData:function(t){window.__hook(t);""")

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
        await page.route("**/js/index.*.js", on_route)
        page.on("response", on_flash)
        await page.goto("https://www.jin10.com/", wait_until="load")

        await page.wait_for_timeout(1000 * 1000)
        print('done')
        bm.release_page(page)
        await bm.cleanup()


if __name__ == '__main__':
    asyncio.run(main())
