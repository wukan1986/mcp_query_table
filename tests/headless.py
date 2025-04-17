from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

with sync_playwright() as p:
    # 启动有头浏览器
    browser = p.chromium.launch(headless=False)
    page = browser.new_page(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36')
    stealth_sync(page)
    w = '收益最好的200只ETF'
    querytype = 'fund'
    url = f"https://www.iwencai.com/unifiedwap/result?w={w}&querytype={querytype}"
    print(url)
    page.goto(url)
    page.wait_for_timeout(1000 * 15)
    page.screenshot(path="example.png")
    page.wait_for_timeout(1000 * 15000)
    # browser.close()
