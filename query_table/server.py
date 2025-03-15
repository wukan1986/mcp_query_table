from typing import List, Sequence, Annotated, Optional

from loguru import logger
from mcp import Tool, stdio_server
from mcp.server import Server
from mcp.types import TextContent, ImageContent, EmbeddedResource
from playwright.async_api import Page, Playwright
from pydantic import BaseModel, Field

from query_table import QueryType, Site, launch_browser, query


class QueryInput(BaseModel):
    query_input: Annotated[str, Field(description="查询条件。支持复杂查询，如：`2024年涨幅最大的100只股票按市值排名`")]
    query_type: Annotated[
        QueryType, Field(default=QueryType.CNStock, description="查询类型。支持`A股`、`指数`、`基金`、`港股`、`美股`等")]
    site: Annotated[Site, Field(default=Site.THS, description="站点。支持`东方财富`、`通达信`、`同花顺`")]
    max_page: Annotated[int, Field(default=1, ge=1, le=10, description="最大页数。只查第一页即可")]


class QueryServer:
    def __init__(self, format: str, port: int, browser_path: str) -> None:
        self.playwright: Optional[Playwright] = None
        self.browser = None
        self.page: Optional[Page] = None
        self.format: str = format
        self.port: int = port
        self.browser_path: str = browser_path

    async def try_launch(self) -> None:
        if self.page is None:
            self.playwright, self.browser, context, self.page = await launch_browser(self.playwright,
                                                                                     port=self.port,
                                                                                     browser_path=self.browser_path)
            return None
        if not self.browser.is_connected():
            self.playwright, self.browser, context, self.page = await launch_browser(self.playwright,
                                                                                     port=self.port,
                                                                                     browser_path=self.browser_path)
            return None
        if self.page.is_closed():
            self.playwright, self.browser, context, self.page = await launch_browser(self.playwright,
                                                                                     port=self.port,
                                                                                     browser_path=self.browser_path)
            return None

    async def query(self, query_input: str, query_type: QueryType, max_page: int, site: Site):
        await self.try_launch()
        df = await query(self.page, query_input, query_type, max_page, site)

        if self.format == 'csv':
            return df.to_csv()
        if self.format == 'markdown':
            return df.to_markdown()
        if self.format == 'json':
            return df.to_json(force_ascii=False, indent=2)


async def serve(format: str, port: int, browser_path: str) -> None:
    logger.info("serve:{},{},{}", format, port, browser_path)
    server = Server("mcp_query_table")

    query_server = QueryServer(format, port, browser_path)

    @server.list_tools()
    async def list_tools() -> List[Tool]:
        tools = [
            Tool(
                name="query",
                description="查询金融表格数据",
                inputSchema=QueryInput.model_json_schema(),
            ),
        ]
        # logger.info("list_tools: {}", len(tools))
        return tools

    @server.call_tool()
    async def call_tool(
            name: str, arguments: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:

        match name:
            case "query":
                args = QueryInput(**arguments)
                # logger.info("call_tool:{}:{}", name, args)
                result = await query_server.query(**args.dict())
            case _:
                # logger.error("call_tool:{}:{}", name, arguments)
                raise ValueError(f"Unknown tool: {name}")

        return [
            TextContent(type="text", text=result)
        ]

    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options, raise_exceptions=True)
