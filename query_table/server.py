from typing import Annotated, Optional

from loguru import logger
from mcp.server.fastmcp import FastMCP
from pydantic import Field

from query_table import QueryType, Site, query as query_table_query
from query_table.tool import BrowserManager


class QueryServer:
    def __init__(self, format: str = 'markdown', port: int = 9222, browser_path: Optional[str] = None) -> None:
        self.format: str = format
        self.browser = BrowserManager(port=port, browser_path=browser_path, debug=False)

    async def query(self, query_input: str, query_type: QueryType, max_page: int, site: Site):
        page = await self.browser.get_page()
        df = await query_table_query(page, query_input, query_type, max_page, site)
        self.browser.release_page(page)

        if self.format == 'csv':
            return df.to_csv()
        if self.format == 'markdown':
            return df.to_markdown()
        if self.format == 'json':
            return df.to_json(force_ascii=False, indent=2)


# !!!log_level这一句非常重要，否则stdio不工作
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


def serve(format, cdp_port, browser_path, transport, mcp_host, mcp_port):
    qsv.format = format
    qsv.port = cdp_port
    qsv.browser_path = browser_path
    logger.info("serve:{},{},{},{}", qsv.format, qsv.port, qsv.browser_path, transport)
    if transport == 'sse':
        logger.info("mcp:{},{}:{}", transport, mcp_host, mcp_port)

    mcp.settings.host = mcp_host
    mcp.settings.port = mcp_port
    mcp.run(transport=transport)
