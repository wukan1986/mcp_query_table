"""
360 纳米搜索
"""
import json

from playwright.async_api import Page

import mcp_query_table
from mcp_query_table.tool import GlobalVars, is_image

_PAGE0_ = "https://www.n.cn"
_PAGE1_ = "https://www.n.cn/search"
_PAGE2_ = "https://www.n.cn/api/common/chat/v2"  # 对话
_PAGE3_ = "https://www.n.cn/api/image/upload"  # 上传图片

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
    if response.url == _PAGE2_:
        # print("on_response", response.url)
        text = await response.text()
        G.set_text(read_event_stream(text))


async def chat(page: Page,
               prompt: str,
               create: bool,
               files: list[str],
               ) -> str:
    """

    Parameters
    ----------
    page : playwright.async_api.Page
        页面
    prompt : str
        问题
    create : bool
        是否创建新的对话
    files : list[str] | None
        上传的文件列表。目前仅支持上传图片

    Returns
    -------
    str
        回答
    """
    if not create:
        if not page.url.startswith(_PAGE1_):
            create = True
        if len(files) > 0:
            create = True

    for file in files:
        assert is_image(file), f"仅支持上传图片，{file}不是图片"

    if create:
        name = "输入任何问题"

        await page.goto(_PAGE0_)
        if len(files) > 0:
            # 只能在新会话中上传文件
            async with page.expect_response(_PAGE3_, timeout=mcp_query_table.TIMEOUT_60) as response_info:
                await page.locator("input[type=\"file\"]").set_input_files(files)
    else:
        name = "提出后续问题，Enter发送，Shift+Enter 换行"

    async with page.expect_response(_PAGE2_, timeout=mcp_query_table.TIMEOUT) as response_info:
        textbox = page.get_by_role("textbox", name=name)
        await textbox.fill(prompt)
        await textbox.press("Enter")
    await on_response(await response_info.value)

    return G.get_text()
