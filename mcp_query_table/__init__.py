from ._version import __version__

from .enums import QueryType, Site, Provider
from .tool import BrowserManager, query, chat

TIMEOUT = 1000 * 60 * 2  # 2分钟，在抓取EventStream数据时等待数据返回，防止外层30秒超时
