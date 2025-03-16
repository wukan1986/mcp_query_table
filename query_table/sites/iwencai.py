"""
同花顺 i问财
https://www.iwencai.com/

1. 一定要保证浏览器宽度>768，防止界面变成适应手机

"""
import re

import pandas as pd
from loguru import logger
from playwright.async_api import Page

from query_table.enums import QueryType

# 初次查询页面
_PAGE1_ = 'https://www.iwencai.com/customized/chart/get-robot-data'
# 翻页
_PAGE2_ = 'https://www.iwencai.com/gateway/urp/v7/landing/getDataList'

_querytype_ = {
    QueryType.CNStock: 'stock',
    QueryType.Index: 'zhishu',
    QueryType.Fund: 'fund',
    QueryType.HKStock: 'hkstock',
    QueryType.USStock: 'usstock',
    '新三板': 'threeboard',
    QueryType.ConBond: 'conbond',
    '保险': 'insurance',
    '期货': 'futures',
    '理财': 'lccp',
    '外汇': 'foreign_exchange',
    '宏观': 'macro',
    #
    QueryType.ETF: 'fund',  # 查ETF定位到基金
}


def convert_type(type):
    if type == 'LONG':
        return int
    if type == 'DOUBLE':
        return float
    if type == 'STR':
        return str
    if type == 'INT':  # TODO 好像未出现过
        return int
    return type


class Pagination:
    def __init__(self):
        self.datas = {}
        self.limit = 100
        self.page = 1
        self.row_count = 1024
        self.columns = []

    def reset(self):
        self.datas = {}

    def update(self, datas, columns, page, limit, row_count):
        self.datas[page] = datas
        self.columns = columns
        self.limit = limit
        self.page = page
        self.row_count = row_count

    def has_next(self, max_page):
        c1 = self.page * self.limit < self.row_count
        c2 = self.page < max_page
        return c1 & c2

    def current(self):
        return self.page

    def get_list(self):
        datas = []
        for k, v in self.datas.items():
            datas.extend(v)
        return datas

    def get_dataframe(self):
        columns = {x['key']: x['index_name'] for x in self.columns}
        dtypes = {x['key']: convert_type(x['type']) for x in self.columns}

        df = pd.DataFrame(self.get_list())
        for k, v in dtypes.items():
            if isinstance(v, str):
                logger.info("未识别的数据类型 {}:{}", k, v)
                continue
            try:
                df[k] = df[k].astype(v)
            except ValueError:
                logger.info("转换失败 {}:{}", k, v)

        return df.rename(columns=columns)


P = Pagination()


def get_robot_data(json_data):
    """
json_data['data']['answer'][0]['txt'][0]['content']['components'][0]['data']['datas']
json_data['data']['answer'][0]['txt'][0]['content']['components'][0]['data']['meta']['limit'] 100
json_data['data']['answer'][0]['txt'][0]['content']['components'][0]['data']['meta']['page'] 1
json_data['data']['answer'][0]['txt'][0]['content']['components'][0]['data']['meta']['extra']['row_count'] 1364
    """
    _1 = json_data['data']['answer'][0]['txt'][0]['content']['components'][0]['data']
    _2 = _1['meta']

    datas = _1['datas']
    columns = _1['columns']
    page = _2['page']
    limit = _2['limit']
    row_count = _2['extra']['row_count']

    return datas, columns, page, limit, row_count


def getDataList(json_data):
    """
json_data['answer']['components'][0]['data']['datas']
json_data['answer']['components'][0]['data']['meta']['page']
json_data['answer']['components'][0]['data']['meta']['limit']
json_data['answer']['components'][0]['data']['meta']['extra']['row_count']
    """
    _1 = json_data['answer']['components'][0]['data']
    _2 = _1['meta']

    datas = _1['datas']
    columns = _1['columns']
    page = _2['page']
    limit = _2['limit']
    row_count = _2['extra']['row_count']

    return datas, columns, int(page), int(limit), row_count


async def on_response(response):
    if response.url == _PAGE1_:
        P.update(*get_robot_data(await response.json()))
    if response.url == _PAGE2_:
        P.update(*getDataList(await response.json()))


async def query(page: Page,
                w: str = "收盘价>1000元",
                type_: QueryType = 'stock',
                max_page: int = 5) -> pd.DataFrame:
    querytype = _querytype_.get(type_, None)
    assert querytype is not None, f"不支持的类型:{type_}"

    await page.route(re.compile(r'.*\.(?:jpg|jpeg|png|gif|webp)(?:$|\?)'), lambda route: route.abort())

    P.reset()
    # page.viewport_size # 取出来是None
    # 宽度<=768会认为是手机,>768是PC
    await page.set_viewport_size({"width": 1280, "height": 800})
    async with page.expect_response(_PAGE1_) as response_info:
        await page.goto(f"https://www.iwencai.com/unifiedwap/result?w={w}&querytype={querytype}", wait_until="load")
    await on_response(await response_info.value)

    while P.has_next(max_page):
        logger.info("当前页为:{}, 点击`下页`", P.current())
        async with page.expect_response(_PAGE2_) as response_info:
            await page.get_by_text("下页").click()
        await on_response(await response_info.value)

    return P.get_dataframe()
