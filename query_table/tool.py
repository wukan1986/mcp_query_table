import subprocess
import time
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
from loguru import logger
from playwright.async_api import async_playwright, Playwright, Browser, BrowserContext, Page

from query_table.enums import QueryType, Site


async def launch_browser(playwright: Optional[Playwright] = None,
                         cdp_port: int = 9222,
                         browser_path: Optional[str] = None,
                         debug: bool = False) -> Tuple[Playwright, Browser, BrowserContext, Page]:
    r"""启动浏览器，并连接CDP协议

    Parameters
    ----------
    playwright:
        同步playwright对象。设成None时，会自动启动playwright对象。
    cdp_port:int
        浏览器调试端口
    browser_path
        浏览器可执行路径。推荐使用chrome，因为Microsoft Edge必须在任务管理器中完全退出才能启动调试端口
    debug:bool
        是否显示开发者工具

    Returns
    -------
    playwright, browser, context, page

    References
    ----------
    https://blog.csdn.net/qq_30576521/article/details/142370538

    """
    if playwright is None:
        playwright = await async_playwright().start()

    try:
        # 尝试连接已打开的浏览器
        browser = await playwright.chromium.connect_over_cdp(f"http://127.0.0.1:{cdp_port}", slow_mo=1000, timeout=5000)
    except:
        if browser_path is None:
            browser_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
            if not Path(browser_path).exists():
                # Microsoft Edge必须在任务管理器中完全退出才能启动调试端口
                browser_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
                if not Path(browser_path).exists():
                    raise ValueError("未找到浏览器可执行文件")

        # 执行完成后不会关闭浏览器
        if debug:
            command = f'"{browser_path}" --remote-debugging-port={cdp_port} --start-maximized --auto-open-devtools-for-tabs'
        else:
            command = f'"{browser_path}" --remote-debugging-port={cdp_port} --start-maximized'
        logger.info(f"start browser:{command}")
        subprocess.Popen(command, shell=True)
        time.sleep(3)

        try:
            browser = await playwright.chromium.connect_over_cdp(f"http://127.0.0.1:{cdp_port}", slow_mo=1000,
                                                                 timeout=5000)
        except:
            logger.warning("是否提前打开了浏览器，但未开启远程调试端口？请关闭浏览器全部进程后重试")
            raise

    context = browser.contexts[0]
    page = context.pages[0]

    return playwright, browser, context, page


async def query(page: Page,
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
        from query_table.sites.eastmoney import query
        return await query(page, query_input, query_type, max_page)
    if site == Site.THS:
        from query_table.sites.iwencai import query
        return await query(page, query_input, query_type, max_page)
    if site == Site.TDX:
        from query_table.sites.tdx import query
        return await query(page, query_input, query_type, max_page)

    raise ValueError(f"未支持的站点:{site}")
