from typing import NamedTuple


class QueryTypeT(NamedTuple):
    """查询类型"""
    CNStock = 'A股'
    HKStock = '港股'
    USStock = '美股'
    Index = '指数'
    Fund = '基金',
    ETF = 'etf',
    ConBond = '可转债',
    Board = '板块',


QueryType = QueryTypeT()


class SiteT(NamedTuple):
    """站点"""
    eastmoney = '东方财富'
    tdx = '通达信'
    iwencai = 'i问财'  # 同花顺


Site = SiteT()
