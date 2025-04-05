"""
百度AI搜索

限制了输入长度为5000，很多时候会被截断，导致MCP无法正常工作
"""
import json

from playwright.async_api import Page

import mcp_query_table
from mcp_query_table.tool import GlobalVars

_PAGE0_ = "https://chat.baidu.com/search"
_PAGE1_ = "https://chat.baidu.com/aichat/api/conversation"

G = GlobalVars()


def read_event_stream(text):
    text1 = []
    text2 = []
    for event in text.split('\n\n'):
        if '"component":"thinkingSteps"' in event:
            if '"reasoningContent":' not in event:
                continue
            lines = event.split('\n')
            for line in lines:
                if line.startswith('data:'):
                    t = line[5:]
                    t = json.loads(t)['data']['message']['content']['generator']['data']['reasoningContent']
                    text1.append(t)
        if '"component":"markdown-yiyan"' in event:
            lines = event.split('\n')
            for line in lines:
                if line.startswith('data:'):
                    t = line[5:]
                    t = json.loads(t)['data']['message']['content']['generator']['data']['value']
                    text2.append(t)

    text2 = ''.join(text2)
    if len(text1) == 0:
        return text2
    else:
        text1 = ''.join(text1)
        return f"<thinking>{text1}</thinking>\n\n{text2}"


async def on_response(response):
    if response.url.startswith(_PAGE1_):
        # print("on_response", response.url)
        text = await response.text()
        G.set_text(read_event_stream(text))


async def on_route(route):
    # 避免出现 Protocol error (Network.getResponseBody): No data found for resource with given identifier
    # print("on_route", route.request.url)
    if route.request.url == _PAGE1_:
        # TODO 为何只要转发一下就没事了？
        response = await route.fetch(timeout=mcp_query_table.TIMEOUT)
        await route.fulfill(response=response)
    else:
        await route.continue_()


async def chat(page: Page,
               prompt: str,
               create: bool,
               ) -> str:
    if not page.url.startswith(_PAGE0_):
        create = True

    if create:
        await page.goto(_PAGE0_)

    await page.route(_PAGE1_, on_route)
    async with page.expect_response(_PAGE1_, timeout=mcp_query_table.TIMEOUT) as response_info:
        await page.locator("#chat-input-box").fill(prompt)
        await page.locator("#chat-input-box").press("Enter")
    await on_response(await response_info.value)

    return G.get_text()
