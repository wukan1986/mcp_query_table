import asyncio
import random
import string

from playwright.async_api import async_playwright
from playwright_stealth import stealth_async, StealthConfig


async def main():
    # This is the recommended usage. All pages created will have stealth applied:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        class FixedConfig(StealthConfig):
            @property
            def enabled_scripts(self):
                key = "".join(random.choices(string.ascii_letters, k=10))
                for script in super().enabled_scripts:
                    if "const opts" in script:
                        yield script.replace("const opts", f"window.{key}")
                        continue
                    yield script.replace("opts", f"window.{key}")

        await stealth_async(page, FixedConfig())

        w = '收益最好的200只ETF'
        querytype = 'fund'
        url = f"https://www.n.cn"
        print(url)
        await page.goto(url)
        await page.wait_for_timeout(1000 * 15)
        await page.screenshot(path="example.png")
        await page.wait_for_timeout(1000 * 15000)


asyncio.run(main())
