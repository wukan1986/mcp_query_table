from enum import Enum


class QueryType(Enum):
    """查询类型"""
    CNStock = 'A股'
    HKStock = '港股'
    USStock = '美股'
    Index = '指数'
    Fund = '基金'
    ETF = 'ETF'
    ConBond = '可转债'
    Board = '板块'
    Info = '资讯'


class Site(Enum):
    """站点"""
    EastMoney = '东方财富'  # 东方财富 条件选股
    TDX = '通达信'  # 通达信 问小达
    THS = '同花顺'  # 同花顺 i问财


class Provider(Enum):
    """提供商"""
    Nami = '纳米搜索'  # 360 纳米搜索
    YuanBao = '腾讯元宝'  # 腾讯元宝
    BaiDu = '百度AI搜索'  # 百度AI搜索
