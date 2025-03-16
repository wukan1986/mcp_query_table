"""
只是为以后各平台安全升级做破解准备，暂时不使用

某网站返回的数据是json中有字段是加密的，需要获取解密后的内容
"""
import pickle
from datetime import datetime

from playwright.sync_api import sync_playwright, Playwright


def hook_parse(obj):
    # 可以hook函数后传递参数，直接解析，跳过了破解这一步，如果能获取到当前请求的url就更好了
    if isinstance(obj, list):
        if obj[0][0] == 'ShallowReactive':
            print(str(datetime.now()) + ' === ' + str(obj))
            # 保存后在另一个文件中做分析
            with open('tmp.pkl', 'wb') as f:
                pickle.dump(obj, f)

            for i in range(0, len(obj)):
                if isinstance(obj[i], dict):
                    if len(obj[i]) == 56:
                        print(obj[i + 1])

            # with open('tmp.pkl', 'rb') as f:
            #     obj = pickle.load(f)
            # print(obj)


def run(playwright: Playwright):
    browser = playwright.chromium.connect_over_cdp(f"http://127.0.0.1:9222", slow_mo=1000, timeout=5000)
    page = browser.contexts[0].pages[0]
    page.expose_function("hook_parse", hook_parse)
    page.add_init_script("""
    (function() {
        var parse = JSON.parse;
        JSON.parse = function(params) {
            // debugger;
            obj = parse(params);
            window.hook_parse(obj);
            return obj;
        }
    })();
    """)
    page.goto("https://dc.simuwang.com/smph/b4n2a0")
    page.wait_for_timeout(1000 * 600)

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


with sync_playwright() as playwright:
    run(playwright)
