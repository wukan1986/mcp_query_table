import subprocess
import time
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
from loguru import logger
from playwright.sync_api import sync_playwright, Playwright, Browser, BrowserContext, Page

from query_table.enums import QueryType, Site


def launch_browser(playwright: Optional[Playwright] = None,
                   port: int = 9222,
                   browser_path: Optional[str] = None) -> Tuple[Playwright, Browser, BrowserContext, Page]:
    r"""启动浏览器，并连接CDP协议

    Parameters
    ----------
    playwright:
        同步playwright对象。设成None时，会自动启动playwright对象。
    port:int
        浏览器调试端口
    browser_path
        浏览器可执行路径。推荐使用chrome，因为Microsoft Edge必须在任务管理器中完全退出才能启动调试端口

    Returns
    -------
    playwright, browser, context, page

    References
    ----------
    https://blog.csdn.net/qq_30576521/article/details/142370538

    """
    if playwright is None:
        # TODO 这写法会不会又问题？
        playwright = sync_playwright().__enter__()

    try:
        # 尝试连接已打开的浏览器
        browser = playwright.chromium.connect_over_cdp(f"http://127.0.0.1:{port}", slow_mo=1000, timeout=5000)
    except:
        if browser_path is None:
            browser_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
            if not Path(browser_path).exists():
                # Microsoft Edge必须在任务管理器中完全退出才能启动调试端口
                browser_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
                if not Path(browser_path).exists():
                    raise ValueError("未找到浏览器可执行文件")

        # 执行完成后不会关闭浏览器
        command = f'"{browser_path}" --remote-debugging-port={port}'
        logger.info(f"启动浏览器:{command}")
        subprocess.Popen(command, shell=True)
        time.sleep(3)

        # 可能出现edge打开远程调试端口失败
        browser = playwright.chromium.connect_over_cdp(f"http://127.0.0.1:{port}", slow_mo=1000, timeout=5000)

    context = browser.contexts[0]
    # page = context.new_page()
    page = context.pages[0]

    return playwright, browser, context, page


def query(page: "Page",
          input: str = "收盘价>100元",
          query_type: QueryType = QueryType.CNStock,
          max_page: int = 5,
          site=Site.iwencai) -> pd.DataFrame:
    """查询表格

    Parameters
    ----------
    page : playwright.sync_api.Page
        页面
    input : str, optional
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

    if site == Site.eastmoney:
        from query_table.sites.eastmoney import query
        return query(page, input, query_type, max_page)
    if site == Site.iwencai:
        from query_table.sites.iwencai import query
        return query(page, input, query_type, max_page)
    if site == Site.tdx:
        from query_table.sites.tdx import query
        return query(page, input, query_type, max_page)

    raise ValueError(f"未支持的站点:{site}")
