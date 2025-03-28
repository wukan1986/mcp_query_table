from typing import Annotated, Optional

from loguru import logger
from mcp.server.fastmcp import FastMCP
from playwright.async_api import Page, Playwright
from pydantic import Field

from query_table import QueryType, Site, launch_browser, query as query_table_query


# class QueryInput(BaseModel):
#     query_input: Annotated[str, Field(description="查询条件。支持复杂查询，如：`2024年涨幅最大的100只股票按市值排名`")]
#     query_type: Annotated[
#         QueryType, Field(default=QueryType.CNStock, description="查询类型。支持`A股`、`指数`、`基金`、`港股`、`美股`等")]
#     site: Annotated[Site, Field(default=Site.THS, description="站点。支持`东方财富`、`通达信`、`同花顺`")]
#     max_page: Annotated[int, Field(default=1, ge=1, le=10, description="最大页数。只查第一页即可")]


class QueryServer:
    def __init__(self, format: str = 'markdown', cdp_port: int = 9222, browser_path: Optional[str] = None) -> None:
        self.playwright: Optional[Playwright] = None
        self.browser = None
        self.page: Optional[Page] = None
        self.format: str = format
        self.cdp_port: int = cdp_port
        self.browser_path: str = browser_path

    async def try_launch(self) -> None:
        if self.page is None:
            self.playwright, self.browser, context, self.page = await launch_browser(self.playwright,
                                                                                     cdp_port=self.cdp_port,
                                                                                     browser_path=self.browser_path)
            return None
        if not self.browser.is_connected():
            self.playwright, self.browser, context, self.page = await launch_browser(self.playwright,
                                                                                     cdp_port=self.cdp_port,
                                                                                     browser_path=self.browser_path)
            return None
        if self.page.is_closed():
            self.playwright, self.browser, context, self.page = await launch_browser(self.playwright,
                                                                                     cdp_port=self.cdp_port,
                                                                                     browser_path=self.browser_path)
            return None

    async def query(self, query_input: str, query_type: QueryType, max_page: int, site: Site):
        await self.try_launch()
        df = await query_table_query(self.page, query_input, query_type, max_page, site)

        if self.format == 'csv':
            return df.to_csv()
        if self.format == 'markdown':
            return df.to_markdown()
        if self.format == 'json':
            return df.to_json(force_ascii=False, indent=2)


# !!!log_level这一句非常重要，否则stdio不工作
mcp = FastMCP("query_table_mcp", log_level="ERROR")
query_server = QueryServer()


@mcp.tool(description="查询金融表格数据")
async def query(
        query_input: Annotated[
            str, Field(description="查询条件。支持复杂查询，如：`2024年涨幅最大的100只股票按市值排名`")],
        query_type: Annotated[QueryType, Field(default=QueryType.CNStock,
                                               description="查询类型。支持`A股`、`指数`、`基金`、`港股`、`美股`等")],
        max_page: Annotated[int, Field(default=1, ge=1, le=10, description="最大页数。只查第一页即可")],
        site: Annotated[Site, Field(default=Site.THS, description="站点。支持`东方财富`、`通达信`、`同花顺`")]
) -> str:
    return await query_server.query(query_input, query_type, max_page, site)


def serve(format, cdp_port, browser_path, transport, mcp_host, mcp_port):
    query_server.format = format
    query_server.cdp_port = cdp_port
    query_server.browser_path = browser_path
    logger.info("serve:{},{},{},{}", format, cdp_port, browser_path, transport)
    if transport == 'sse':
        logger.info("mcp:{},{}:{}", transport, mcp_host, mcp_port)

    mcp.settings.host = mcp_host
    mcp.settings.port = mcp_port
    mcp.run(transport=transport)
