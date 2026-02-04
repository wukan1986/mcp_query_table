from urllib.parse import quote

import pandas as pd
from playwright.async_api import Page

from mcp_query_table.enums import QueryType, Site, Provider


async def query(
        page: Page,
        query_input: str = "收盘价>100元",
        query_type: QueryType = QueryType.CNStock,
        max_page: int = 5,
        rename: bool = False,
        site: Site = Site.THS,
) -> pd.DataFrame:
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
    rename: bool
        是否重命名列名, by default False
    site : Site, optional
        站点, by default Site.iwencai

    Returns
    -------
    pd.DataFrame
        查询结果

    """
    query_input = quote(query_input.strip(), safe='')

    if site == Site.EastMoney:
        from mcp_query_table.sites.eastmoney import query
        return await query(page, query_input, query_type, max_page, rename)
    if site == Site.THS:
        from mcp_query_table.sites.iwencai import query
        return await query(page, query_input, query_type, max_page, rename)
    if site == Site.TDX:
        from mcp_query_table.sites.tdx import query
        return await query(page, query_input, query_type, max_page, rename)

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
