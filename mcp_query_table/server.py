from typing import Annotated, Optional

from loguru import logger
from mcp.server.fastmcp import FastMCP
from pydantic import Field

from mcp_query_table import QueryType, Site, query as qt_query, chat as qt_chat
from mcp_query_table.enums import Provider
from mcp_query_table.tool import BrowserManager


class QueryServer:
    def __init__(self,
                 format: str = 'markdown',
                 cdp_endpoint: Optional[str] = 'http://127.0.0.1:9222',
                 executable_path: Optional[str] = None) -> None:
        self.format: str = format
        self.browser = BrowserManager(cdp_endpoint=cdp_endpoint, executable_path=executable_path, debug=False)

    async def query(self, query_input: str, query_type: QueryType, max_page: int, site: Site):
        page = await self.browser.get_page()
        df = await qt_query(page, query_input, query_type, max_page, site)
        self.browser.release_page(page)

        if self.format == 'csv':
            return df.to_csv()
        if self.format == 'markdown':
            return df.to_markdown()
        if self.format == 'json':
            return df.to_json(force_ascii=False, indent=2)

    async def chat(self, prompt: str, create: bool, provider: Provider):
        page = await self.browser.get_page()
        txt = await qt_chat(page, prompt, create, provider)
        self.browser.release_page(page)
        return txt


# !!!log_level这一句非常重要，否则Cline/MCP Server/Tools工作不正常
mcp = FastMCP("query_table_mcp", log_level="ERROR")
qsv = QueryServer()


@mcp.tool(description="查询金融表格数据")
async def query(
        query_input: Annotated[
            str, Field(description="查询条件。支持复杂查询，如：`2024年涨幅最大的100只股票按市值排名`")],
        query_type: Annotated[QueryType, Field(default=QueryType.CNStock,
                                               description="查询类型。支持`A股`、`指数`、`基金`、`港股`、`美股`等")],
        max_page: Annotated[int, Field(default=1, ge=1, le=10, description="最大页数。只查第一页即可")],
        site: Annotated[Site, Field(default=Site.THS, description="站点。支持`东方财富`、`通达信`、`同花顺`")]
) -> str:
    return await qsv.query(query_input, query_type, max_page, site)


@mcp.tool(description="大语言模型对话")
async def chat(
        prompt: Annotated[str, Field(description="提示词。如：`9.9大还是9.11大？`")],
        create: Annotated[bool, Field(default=False, description="是否创建新对话")],
        provider: Annotated[
            Provider, Field(default=Provider.Nami, description="提供商。支持`纳米搜索`、`腾讯元宝`、`百度AI搜索`")]
) -> str:
    return await qsv.chat(prompt, create, provider)


def serve(format, cdp_endpoint, executable_path, transport, host, port):
    qsv.format = format
    qsv.cdp_endpoint = cdp_endpoint
    qsv.executable_path = executable_path
    logger.info(f"{format=},{transport=}")
    logger.info(f"{cdp_endpoint=},{executable_path=}")
    if transport == 'sse':
        logger.info(f"{host=},{port=}", transport, host, port)

    mcp.settings.host = host
    mcp.settings.port = port
    mcp.run(transport=transport)
