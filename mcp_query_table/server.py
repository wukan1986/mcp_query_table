from typing import Annotated, List

from loguru import logger
from mcp.server.fastmcp import FastMCP
from pydantic import Field

from mcp_query_table import QueryType, Site, query as qt_query, chat as qt_chat
from mcp_query_table.enums import Provider
from mcp_query_table.tool import BrowserManager


class QueryServer:
    def __init__(self) -> None:
        self.format: str = "markdown"
        self.browser = None

    def start(self, format, endpoint, executable_path, user_data_dir):
        self.format: str = format
        self.browser = BrowserManager(endpoint=endpoint,
                                      executable_path=executable_path,
                                      user_data_dir=user_data_dir,
                                      devtools=False,
                                      headless=True)

    async def query(self, query_input: str, query_type: QueryType, max_page: int, rename: bool, site: Site):
        page = await self.browser.get_page()
        df = await qt_query(page, query_input, query_type, max_page, rename, site)
        self.browser.release_page(page)

        if self.format == 'csv':
            return df.to_csv()
        if self.format == 'markdown':
            return df.to_markdown()
        if self.format == 'json':
            return df.to_json(force_ascii=False, indent=2)

    async def chat(self, prompt: str, create: bool, files: List[str], provider: Provider):
        page = await self.browser.get_page()
        txt = await qt_chat(page, prompt, create, files, provider)
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
        rename: Annotated[bool, Field(default=False, description="是否重命名列名")],
        site: Annotated[Site, Field(default=Site.THS, description="站点。支持`东方财富`、`通达信`、`同花顺`")]
) -> str:
    return await qsv.query(query_input, query_type, max_page, rename, site)


# chat功能不通过mcp暴露，因为在Cline等客户端中本就有LLM功能，反而导致返回的数据没有正确提交
# @mcp.tool(description="大语言模型对话")
async def chat(
        prompt: Annotated[str, Field(description="提示词。如：`9.9大还是9.11大？`")],
        create: Annotated[bool, Field(default=False, description="是否创建新对话")],
        files: Annotated[List[str], Field(default=None, description="上传的文件列表。不同网站支持程度不同")],
        provider: Annotated[
            Provider, Field(default=Provider.Nami, description="提供商。支持`纳米搜索`、`腾讯元宝`、`百度AI搜索`")]
) -> str:
    return await qsv.chat(prompt, create, files, provider)


def serve(format, endpoint, executable_path, user_data_dir, transport, host, port):
    qsv.start(format, endpoint, executable_path, user_data_dir)
    logger.info(f"{endpoint=}")
    logger.info(f"{executable_path=}")
    logger.info(f"{user_data_dir=}")
    if transport == 'sse':
        logger.info(f"{transport=},{format=},{host=},{port=}")
    else:
        logger.info(f"{transport=},{format=}")

    mcp.settings.host = host
    mcp.settings.port = port
    mcp.run(transport=transport)
