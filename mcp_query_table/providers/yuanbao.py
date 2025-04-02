"""
腾讯元宝
"""
import json

from playwright.async_api import Page

import mcp_query_table
from mcp_query_table.tool import GlobalVars

_PAGE0_ = "https://yuanbao.tencent.com/"
_PAGE1_ = "https://yuanbao.tencent.com/api/chat"

G = GlobalVars()


def read_event_stream(text):
    text1 = []
    text2 = []
    for event in text.split('\n\n'):
        if 'data: {"type":"think"' in event:
            lines = event.split('\n')
            for line in lines:
                if line.startswith('data: '):
                    t = line[6:]
                    t = json.loads(t)['content']
                    text1.append(t)
        if 'data: {"type":"text"' in event:
            lines = event.split('\n')
            for line in lines:
                if line.startswith('data: '):
                    t = line[6:]
                    t = json.loads(t).get('msg', "")
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
    # print("on_route", route.request.url)
    if route.request.url.startswith(_PAGE1_):
        # TODO 这里会导致数据全部加载，逻辑变了，所以界面可能混乱
        response = await route.fetch(timeout=mcp_query_table.TIMEOUT)
        await route.fulfill(
            # 强行加utf-8，否则编码搞不定
            content_type="text/event-stream; charset=utf-8",
            response=response,
        )
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

    await page.route(f"{_PAGE1_}/*", on_route)
    async with page.expect_response(f"{_PAGE1_}/*", timeout=mcp_query_table.TIMEOUT) as response_info:
        textbox = page.locator(".ql-editor")
        await textbox.fill(prompt)
        await textbox.press("Enter")
    await on_response(await response_info.value)

    return G.get_text()
