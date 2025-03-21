"""
只是为以后各平台安全升级做破解准备，暂时不使用

某网站返回的数据是json中有字段是加密的，需要获取解密后的内容

直接hook请求函数，返回解密后的内容

首页是静态网页，翻页是fetch请求

发现js文件名也是动态变化的
"""
import asyncio

from query_table import launch_browser


def __hook(x, y, obj):
    if x == '/sun/ranking/fundRankV3':
        print(x)
        print(y)
        print(obj)


async def on_route(route, request):
    """找到特殊js文件，每过一段时间特殊文件名不同，但内部的函数名不变"""
    response = await route.fetch()
    body = await response.text()
    if "uXpFetch" not in body:
        await route.fulfill(response=response)
        return

    # 网页中引用的js文件，会变化
    # <script type="module" src="/_nuxt3/BFem2fS2.js" crossorigin></script>
    print(request.url)
    body = body.replace("export{", """
var _hook = uXpFetch;
uXpFetch =async function(e,t) {
const ret=_hook(e,t);
ret.then((r)=>{window.__hook(e,t,r)});
return ret;
};
export{""")

    await route.fulfill(content_type="text/javascript; charset=utf-8", body=body)


async def main() -> None:
    playwright, browser, context, page = await launch_browser(port=9222, browser_path=None, debug=True)
    print(browser.is_connected(), page.is_closed())

    await page.expose_function("__hook", __hook)
    await page.route("**/_nuxt3/*.js", on_route)
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

"""
<script type="module" src="/_nuxt3/BFem2fS2.js" crossorigin></script>

var _hook = uXpFetch;
uXpFetch =async function(e,t) {
    const ret=_hook(e,t);
    ret.then((r)=>{window.__hook(e,t,r)});
    return ret;
};
"""
