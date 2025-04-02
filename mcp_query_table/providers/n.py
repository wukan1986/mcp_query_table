"""
360 纳米搜索
"""
import json

from playwright.async_api import Page

import mcp_query_table
from mcp_query_table.tool import GlobalVars

_PAGE0_ = "https://www.n.cn"
_PAGE1_ = "https://www.n.cn/search"
_PAGE2_ = "https://www.n.cn/api/common/chat/v2"

G = GlobalVars()


def read_event_stream(text):
    text1 = []
    text2 = []
    for event in text.split('\n\n'):
        if "event: 102" in event:
            if 'data: {"type":"reasoning_text"' in event:
                lines = event.split('\n')
                for line in lines:
                    if line.startswith('data: '):
                        t = line[6:]
                        t = json.loads(t)['message']
                        text1.append(t)
        if "event: 200" in event:
            lines = event.split('\n')
            for line in lines:
                if line.startswith('data: '):
                    t = line[6:]
                    if t == '':
                        text2.append('\n')
                    elif t == ' ':
                        text2.append('\n')
                    else:
                        text2.append(t)

    text2 = ''.join(text2)
    if len(text1) == 0:
        return text2
    else:
        text1 = ''.join(text1)
        return f"<thinking>{text1}</thinking>\n\n{text2}"


async def on_response(response):
    if response == _PAGE2_:
        # print("on_response", response.url)
        text = await response.text()
        G.set_text(read_event_stream(text))


async def chat(page: Page,
               prompt: str,
               create: bool,
               ) -> str:
    if not create:
        if not page.url.startswith(_PAGE1_):
            create = True

    if create:
        await page.goto(_PAGE0_)
        name = "输入任何问题"
    else:
        name = "提出后续问题，Enter发送，Shift+Enter 换行"

    async with page.expect_response(_PAGE2_, timeout=mcp_query_table.TIMEOUT) as response_info:
        textbox = page.get_by_role("textbox", name=name)
        await textbox.fill(prompt)
        await textbox.press("Enter")
    await on_response(await response_info.value)

    return G.get_text()
