"""
只是为以后各平台安全升级做破解准备，暂时不使用

某网站返回的数据是json中有字段是加密的，需要获取解密后的内容

直接hook请求函数，返回解密后的内容

首页是静态网页，翻页是fetch请求

发现js文件名也是动态变化的
"""
import asyncio

from mcp_query_table import BrowserManager

query = {}


def __hook(x, y, obj):
    if x == '/sun/ranking/fundRankV3':
        global query
        query = y
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
// 原函数注册到window，不是改版函数
window.uXpFetch = uXpFetch;
// 重写局部函数
uXpFetch =async function(e,t) {
    const ret=window.uXpFetch(e,t);
    ret.then((r)=>{window.__hook(e,t,r)});
    return ret;
};
export{""")

    await route.fulfill(content_type="text/javascript; charset=utf-8", body=body)


async def main() -> None:
    async with BrowserManager(port=9222, browser_path=None, debug=True) as bm:
        page = await bm.get_page()
        await page.expose_function("__hook", __hook)
        await page.route("**/_nuxt3/*.js", on_route)
        await page.goto("https://dc.simuwang.com/smph", wait_until="load")

        # 强行翻页，产生fetch请求
        await page.get_by_role("button", name="上一页", disabled=True).evaluate(
            'element => { element.removeAttribute("disabled"); element.removeAttribute("aria-disabled");}')
        await page.get_by_role("button", name="上一页").click()
        # 方便记录请求参数
        print(query)
        print('=' * 60)

        # 相当于requests，但解码麻烦
        # r = await page.request.get('https://sppwapi.simuwang.com/sun/ranking/fundRankV3?page=1&size=50&condition=%7B%22fund_type%22:%226%22%7D&sort_name=ret_6m&sort_asc=desc&tab_type=1')
        # print(await r.text())

        # 更快速的请求方式
        for i in range(1, 4):
            # await page.get_by_role("button", name="下一页").click()
            query['data']['page'] = i
            r = await page.evaluate("([x, y])=>window.uXpFetch(x,y)", ['/sun/ranking/fundRankV3', query])
            print(r)

        print('done')
        await page.wait_for_timeout(1000 * 10)
        bm.release_page(page)
        await bm.cleanup()


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
