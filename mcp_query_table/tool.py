import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, List, Tuple
from urllib.parse import urlparse

import pandas as pd
from loguru import logger
from playwright.async_api import async_playwright, Playwright, Page

from mcp_query_table.enums import QueryType, Site, Provider


def create_detached_process(command):
    # 设置通用参数
    kwargs = {}

    if sys.platform == 'win32':
        kwargs.update({
            # 在PyCharm中运行还是会出现新建进程被关闭
            'creationflags': subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        })
    else:
        # Unix-like 系统（Linux, macOS）特定设置
        kwargs.update({
            'start_new_session': True  # 创建新的会话
        })
    return subprocess.Popen(command, **kwargs)


def is_local_url(url: str) -> bool:
    """判断url是否是本地地址"""
    for local in ('localhost', '127.0.0.1'):
        if local in url.lower():
            return True
    return False


def is_cdp_url(url: str) -> bool:
    """判断url是否是CDP地址"""
    if url.startswith('ws://') or url.startswith('wss://'):
        return False
    return True


def get_executable_path(executable_path) -> Optional[str]:
    """获取浏览器可执行文件路径"""
    browsers = {
        "default": executable_path,
        "chrome.exe": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "msedge.exe": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    }
    for k, v in browsers.items():
        if v is None:
            continue
        if Path(v).exists():
            return v
    return None


class BrowserManager:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()

    def __init__(self,
                 endpoint: Optional[str] = None,
                 executable_path: Optional[str] = None,
                 debug: bool = False):
        """

        Parameters
        ----------
        endpoint:str
            浏览器CDP地址/WS地址
        executable_path:str
            浏览器可执行文件路径。推荐使用chrome，因为Microsoft Edge必须在任务管理器中完全退出才能启动调试端口
        debug:bool
            是否显示开发者工具

        """
        self.endpoint = endpoint or 'http://127.0.0.1:9222'
        self.executable_path = executable_path
        self.debug = debug

        self.playwright: Optional[Playwright] = None
        self.browser = None
        self.context = None
        # 空闲page池
        self.pages = []

    async def cleanup(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def _connect_to_local(self) -> None:
        """连接本地浏览器"""
        port = urlparse(self.endpoint).port
        executable_path = get_executable_path(self.executable_path)
        command = [executable_path, f'--remote-debugging-port={port}', '--start-maximized']
        if self.debug:
            command.append('--auto-open-devtools-for-tabs')

        for i in range(2):
            try:
                self.browser = await self.playwright.chromium.connect_over_cdp(self.endpoint,
                                                                               timeout=10000, slow_mo=1000)
                break
            except:
                if i == 0:
                    logger.info(f"start browser:{command}")
                    create_detached_process(command)
                    time.sleep(3)
                    continue
                if i == 1:
                    raise ConnectionError(
                        f"已提前打开了浏览器，但未开启远程调试端口？请关闭浏览器全部进程后重试 `taskkill /f /im {Path(executable_path).name}`")

    async def _connect_to_remote(self) -> None:
        """连接远程浏览器"""
        try:
            if is_cdp_url(self.endpoint):
                self.browser = await self.playwright.chromium.connect_over_cdp(self.endpoint,
                                                                               timeout=10000, slow_mo=1000)
            else:
                self.browser = await self.playwright.chromium.connect(self.endpoint,
                                                                      timeout=10000, slow_mo=1000)
        except:
            raise ConnectionError(f"连接远程浏览器失败，请检查CDP/WS地址和端口是否正确。{self.endpoint}")

    async def _launch(self) -> None:
        """启动浏览器，并连接CDP协议

        References
        ----------
        https://blog.csdn.net/qq_30576521/article/details/142370538

        """
        self.playwright = await async_playwright().start()

        if is_local_url(self.endpoint) and is_cdp_url(self.endpoint):
            await self._connect_to_local()
        else:
            await self._connect_to_remote()

        if len(self.browser.contexts) == 0:
            self.context = await self.browser.new_context()
        else:
            self.context = self.browser.contexts[0]
        # 复用打开的page
        for page in self.context.pages:
            # 防止开发者工具被使用
            if page.url.startswith("devtools://"):
                continue
            # 防止chrome扩展被使用
            if page.url.startswith("chrome-extension://"):
                continue
            # 防止edge扩展被使用
            if page.url.startswith("extension://"):
                continue
            self.pages.append(page)

    async def _try_launch(self) -> None:
        if self.browser is None:
            await self._launch()
        if not self.browser.is_connected():
            await self._launch()

    async def get_page(self) -> Page:
        """获取可用Page。无空闲标签时会打开新标签"""
        await self._try_launch()

        # 反复取第一个tab
        while len(self.pages) > 0:
            page = self.pages.pop()
            if page.is_closed():
                continue
            return page

        # 不够，新建一个
        return await self.context.new_page()

    def release_page(self, page) -> None:
        """用完的Page释放到池中。如果用完不放回，get_page会一直打开新标签"""
        if page.is_closed():
            return
        # 放回
        self.pages.append(page)


class GlobalVars:
    """全局变量"""

    def __init__(self):
        self.text = ""

    def set_text(self, text):
        self.text = text

    def get_text(self):
        return self.text


async def query(
        page: Page,
        query_input: str = "收盘价>100元",
        query_type: QueryType = QueryType.CNStock,
        max_page: int = 5,
        site: Site = Site.THS) -> pd.DataFrame:
    """查询表格

    Parameters
    ----------
    page : playwright.sync_api.Page
        页面
    query_input : str, optional
        查询条件, by default "收盘价>100元"
    query_type : QueryType, optional
        查询类型, by default QueryType.astock
    max_page : int, optional
        最大页数, by default 5
    site : Site, optional
        站点, by default Site.iwencai

    Returns
    -------
    pd.DataFrame
        查询结果

    """

    if site == Site.EastMoney:
        from mcp_query_table.sites.eastmoney import query
        return await query(page, query_input, query_type, max_page)
    if site == Site.THS:
        from mcp_query_table.sites.iwencai import query
        return await query(page, query_input, query_type, max_page)
    if site == Site.TDX:
        from mcp_query_table.sites.tdx import query
        return await query(page, query_input, query_type, max_page)

    raise ValueError(f"未支持的站点:{site}")


async def chat(
        page: Page,
        prompt: str = "9.9大还是9.11大？",
        create: bool = False,
        files: list[str] | None = None,
        provider: Provider = Provider.Nami) -> str:
    """大语言对话

    Parameters
    ----------
    page : playwright.sync_api.Page
        页面
    prompt : str, optional
        对话内容, by default "9.9大还是9.11大？"
    create : bool, optional
        是否创建新对话, by default False
    files : list[str] | None, optional
        上传的文件列表。不同网站支持程度不同
    provider : Provider, optional
        提供商, by default Provider.N

    Returns
    -------
    str
        对话结果

    """
    # 空列表转None
    if files is None:
        files = []

    if provider == Provider.Nami:
        from mcp_query_table.providers.n import chat
        return await chat(page, prompt, create, files)
    if provider == Provider.YuanBao:
        from mcp_query_table.providers.yuanbao import chat
        return await chat(page, prompt, create, files)
    if provider == Provider.BaiDu:
        from mcp_query_table.providers.baidu import chat
        return await chat(page, prompt, create, files)

    raise ValueError(f"未支持的提供商:{provider}")


def is_image(path: str) -> bool:
    """判断是否是图片文件"""
    img_ext = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    ext = Path(path).suffix.lower()
    return ext in img_ext


def split_images(files: List[str]) -> Tuple[List[str], List[str]]:
    """图片列表分成两部分"""
    imgs = []
    docs = []
    for f in files:
        if is_image(f):
            imgs.append(f)
        else:
            docs.append(f)
    return imgs, docs
