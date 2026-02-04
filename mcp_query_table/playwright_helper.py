import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

import psutil
from loguru import logger
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth


def get_chrome_path() -> str:
    """Chrome可执行文件路径"""
    if sys.platform == "darwin":
        return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    elif sys.platform == "win32":
        return r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    elif sys.platform.startswith("linux"):
        return "/usr/bin/google-chrome"
    return shutil.which('google-chrome')


def get_edge_path() -> str:
    """Edge可执行文件路径"""
    if sys.platform == "darwin":
        return "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
    elif sys.platform == "win32":
        return r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    elif sys.platform.startswith("linux"):
        return "/usr/bin/microsoft-edge"
    return shutil.which('microsoft-edge')


def get_edge_use_data():
    """Edge用户配置路径"""
    if sys.platform == "darwin":
        return Path.home() / "Library/Application Support/Google/Chrome"
    elif sys.platform == "win32":
        return Path.home() / r"AppData\Local\Google\Chrome\User Data"
    elif sys.platform.startswith("linux"):
        return Path.home() / ".config/google-chrome"
    return None


def get_chrome_use_data():
    """Chrome用户配置路径"""
    if sys.platform == "darwin":
        return Path.home() / "Library/Application Support/Microsoft Edge"
    elif sys.platform == "win32":
        return Path.home() / r"AppData\Local\Microsoft\Edge\User Data"
    elif sys.platform.startswith("linux"):
        return Path.home() / ".config/microsoft-edge"
    return None


def get_browser(proc_name: Literal["chrome.exe", "msedge.exe"], port: int | None = None) -> psutil.Process | None:
    """查进程"""
    for proc in psutil.process_iter(["name", "cmdline", "exe"]):
        name = proc.info["name"].lower()
        if proc_name in name:
            exe_path = proc.info.get("exe", "") or ""

            if port is None:
                return proc
            else:
                if any(f"--remote-debugging-port={port}" in arg for arg in proc.info["cmdline"]):
                    return proc
    return None


def kill_browsers(proc_name: Literal["chrome.exe", "msedge.exe"]) -> None:
    """Edge需要退出所有进程，再次启动进程才能生效"""
    for proc in psutil.process_iter(["name", "cmdline", "exe"]):
        name = proc.info["name"].lower()
        if proc_name in name:
            if proc.is_running():
                try:
                    proc.kill()
                except psutil.NoSuchProcess:
                    pass


def start_browser(browser_path: str, port: int, devtools: bool, user_data_dir: str | None = None):
    """启动浏览器进程"""
    command = [browser_path, f'--remote-debugging-port={port}', '--start-maximized']
    if devtools:
        command.append('--auto-open-devtools-for-tabs')
    if user_data_dir:
        # chrome不能使用默认配置，因为安全限制
        command.append(f'--user-data-dir={user_data_dir}')
    return subprocess.Popen(command)


def is_local_url(url: str) -> bool:
    """判断url是否是本地地址"""
    for local in ('localhost', '127.0.0.1', "::1"):
        if local in url.lower():
            return True
    return False


def is_cdp_url(url: str) -> bool:
    """判断url是否是CDP地址"""
    if url.startswith('ws://') or url.startswith('wss://'):
        return False
    return True


def is_url(url: str) -> bool:
    urls = (
        "devtools://",
        "chrome-extension://",
        "extension://",
        "chrome://",
        "edge://",
    )
    for u in urls:
        if url.startswith(u):
            return False
    return True


class BaseBrowser:
    def __init__(self, endpoint: str | None, executable_path: str | None = None, devtools: bool = False, user_data_dir: str | None = None):
        """连接参数

        Parameters
        ----------
        endpoint:
            浏览器CDP地址或服务器WS地址
        executable_path:
            Chrome或Edge的绝对路径
        devtools:
            是否显示开发者工具
        user_data_dir
            用户数据。可解决登录问题

        Examples
        --------
        # python退出chrome也自动退出,需提前`playwright install chromium`
        async with AsyncBrowser(endpoint=None, user_data_dir="D:\\user_data") as browser:
            pass

        # 本地先启动chrome进程，然后使用CDP协议进行控制
        # chrome一定要另外提供`user_data_dir`
        # edge需要完全退出才能启动时启动CDP
        async with AsyncBrowser(endpoint="http://127.0.0.1:9222", executable_path=get_chrome_path(), user_data_dir="D:\\user_data") as browser:
            pass

        # 连接到远程的Playwright Server
        # 参考 https://playwright.dev/python/docs/docker#connecting-to-the-server
        with SyncBrowser(endpoint="ws://127.0.0.1:3000") as browser:
            pass

        """
        self.endpoint = endpoint
        self.executable_path = executable_path
        self.devtools = devtools
        self.user_data_dir = user_data_dir

        self.headless = False
        self.playwright = None
        self.browser = None

        self.timeout = 20000
        self.slow_mo = 1000

    def _start_chrome(self, sleep: int = 5):
        if self.executable_path:
            name = Path(self.executable_path).name
            port = urlparse(self.endpoint).port
            proc = get_browser(name, port)
            if proc is None:
                kill_browsers(name)
                ret = start_browser(self.executable_path, port, self.devtools, self.user_data_dir)
                time.sleep(sleep)
        else:
            logger.warning("连接本地CDP时未提供executable_path，需手工启动带参数的浏览器")


class AsyncBrowser(BaseBrowser):
    async def __aenter__(self):
        await self._launch()

        async def get_page():
            contexts = self.browser.contexts
            if contexts:
                context = contexts[0]
            else:
                context = await self.browser.new_context()

            await Stealth().apply_stealth_async(context)

            pages = context.pages
            if pages:
                for page in pages:
                    if is_url(page.url):
                        return page

            return await context.new_page()

        self.browser.get_page = get_page

        return self.browser

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def _launch(self):
        """启动并连接"""
        self.playwright = await async_playwright().start()
        if self.endpoint is None:
            await self._connect_to_launch()
            return
        elif is_local_url(self.endpoint) and is_cdp_url(self.endpoint):
            self._start_chrome()

        kwargs = {
            "timeout": self.timeout,
            "slow_mo": self.slow_mo,
        }
        if is_cdp_url(self.endpoint):
            self.browser = await self.playwright.chromium.connect_over_cdp(self.endpoint, **kwargs)
        else:
            # https://playwright.dev/python/docs/docker#connecting-to-the-server
            self.browser = await self.playwright.chromium.connect(self.endpoint, **kwargs)

    async def _connect_to_launch(self) -> None:
        logger.info("executable_path={}", self.executable_path)
        kwargs = {
            "executable_path": self.executable_path,
            "headless": self.headless,
            "timeout": self.timeout,
            "slow_mo": self.slow_mo,
            # "devtools": self.devtools,
        }
        if self.user_data_dir:
            logger.info("user_data_dir={}", self.user_data_dir)
            try:
                context = await self.playwright.chromium.launch_persistent_context(user_data_dir=self.user_data_dir, **kwargs)
                self.browser = context.browser
            except:
                raise ConnectionError(f"launch失败，可能已经有浏览器已经打开了数据目录。{self.user_data_dir}")
        else:
            logger.warning("未指定浏览器用户数据目录，部分需要的网站可能无法使用")
            self.browser = await self.playwright.chromium.launch(**kwargs)


class SyncBrowser(BaseBrowser):

    def __enter__(self):
        self._launch()

        def get_page():
            contexts = self.browser.contexts
            if contexts:
                context = contexts[0]
            else:
                context = self.browser.new_context()

            Stealth().apply_stealth_sync(context)

            pages = context.pages
            if pages:
                for page in pages:
                    if is_url(page.url):
                        return page

            return context.new_page()

        self.browser.get_page = get_page

        return self.browser

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def _launch(self):
        """启动并连接"""
        self.playwright = sync_playwright().start()
        if self.endpoint is None:
            self._connect_to_launch()
            return
        elif is_local_url(self.endpoint) and is_cdp_url(self.endpoint):
            self._start_chrome()

        kwargs = {
            "timeout": self.timeout,
            "slow_mo": self.slow_mo,
        }
        if is_cdp_url(self.endpoint):
            self.browser = self.playwright.chromium.connect_over_cdp(self.endpoint, **kwargs)
        else:
            # https://playwright.dev/python/docs/docker#connecting-to-the-server
            self.browser = self.playwright.chromium.connect(self.endpoint, **kwargs)

    def _connect_to_launch(self) -> None:
        logger.info("executable_path={}", self.executable_path)
        kwargs = {
            "executable_path": self.executable_path,
            "headless": self.headless,
            "timeout": self.timeout,
            "slow_mo": self.slow_mo,
            # "devtools": self.devtools,
        }
        if self.user_data_dir:
            logger.info("user_data_dir={}", self.user_data_dir)
            try:
                context = self.playwright.chromium.launch_persistent_context(user_data_dir=self.user_data_dir, **kwargs)
                self.browser = context.browser
            except:
                raise ConnectionError(f"launch失败，可能已经有浏览器已经打开了数据目录。{self.user_data_dir}")
        else:
            logger.warning("未指定浏览器用户数据目录，部分需要的网站可能无法使用")
            self.browser = self.playwright.chromium.launch(**kwargs)


async def async_main():
    async with AsyncBrowser(endpoint="http://127.0.0.1:9222", executable_path=get_chrome_path(), user_data_dir="D:\\user_data") as browser:
        context = await browser.new_context(proxy={"server": "http://127.0.0.1:10808"})
        page = await browser.new_page()
        await page.goto("https://ipw.cn/")
        page = await context.new_page()
        await page.goto("https://ipw.cn/")
        input("AAA")


def sync_main():
    with SyncBrowser(endpoint="http://127.0.0.1:9222", executable_path=get_chrome_path(), user_data_dir="D:\\user_data") as browser:
        context = browser.new_context(proxy={"server": "http://127.0.0.1:10808"})
        page = browser.new_page()
        page.goto("https://ipw.cn/")
        page = context.new_page()
        page.goto("https://ipw.cn/")
        input("BBB")

# if __name__ == "__main__":
#     import asyncio
#
#     asyncio.run(async_main())
#     sync_main()
