"""
东方财富 条件选股
https://xuangu.eastmoney.com/

1. 部分数据中包含中文单位，如万亿等，导致无法转换为数字，如VOLUME
2. 东财翻页需要提前手工登录
3. 东财翻页是页面已经翻了，然后等数据来更新，这会导致翻页数不对
"""

import pandas as pd
from loguru import logger
from playwright.sync_api import Page

from query_table.enums import QueryType

# 查询结果
_PAGE1_ = 'https://np-pick-b.eastmoney.com/api/smart-tag/stock/v3/pw/search-code'

_type_ = {
    QueryType.CNStock: 'stock',
    QueryType.Fund: 'fund',
    QueryType.HKStock: 'hk',
    QueryType.ConBond: 'cb',
    QueryType.ETF: 'etf',
    QueryType.Board: 'bk',
}


def convert_type(type):
    if type == 'Double':
        return float
    if type == 'String':
        return str
    if type == 'Long':
        return int
    if type == 'Boolean':
        return bool
    if type == 'INT':  # TODO 好像未出现过
        return int
    return None


class Pagination:
    def __init__(self):
        self.datas = {}
        self.pageNo = 1
        self.pageSize = 100
        self.total = 1024
        self.columns = []
        self.datas = {}
        self.lock = False

    def reset(self):
        self.datas = {}

    def update(self, pageNo, pageSize, total, columns, dataList):
        self.pageNo = pageNo
        self.pageSize = pageSize
        self.total = total
        self.columns = columns
        self.datas[self.pageNo] = dataList
        self.lock = False

    def has_next(self, max_page):
        c1 = self.pageNo * self.pageSize < self.total
        c2 = self.pageNo < max_page
        return c1 & c2

    def current(self):
        return self.pageNo

    def get_list(self):
        datas = []
        for k, v in self.datas.items():
            datas.extend(v)
        return datas

    def get_dataframe(self):
        columns = {x['key']: x['title'] for x in self.columns}
        dtypes = {x['key']: convert_type(x['dataType']) for x in self.columns}

        df = pd.DataFrame(self.get_list())
        for k, v in dtypes.items():
            if k == 'SERIAL':
                df[k] = df[k].astype(int)
                continue
            if v is None:
                logger.info("未识别的数据类型{}:{}", k, v)
                continue
            try:
                df[k] = df[k].astype(v)
            except ValueError:
                logger.info("转换失败{}:{}", k, v)

        return df.rename(columns=columns)


P = Pagination()


def search_code(json_data):
    total = json_data['data']['result']['total']
    columns = json_data['data']['result']['columns']
    dataList = json_data['data']['result']['dataList']
    return total, columns, dataList


def on_response(response):
    if response.url == _PAGE1_:
        post_data_json = response.request.post_data_json
        pageNo = post_data_json['pageNo']
        pageSize = post_data_json['pageSize']
        P.update(pageNo, pageSize, *search_code(response.json()))


def query(page: Page,
          q: str = "收盘价>100元",
          type: str = 'stock',
          max_page: int = 5) -> pd.DataFrame:
    type = _type_.get(type, type)

    page.route("**/*.{png,jpg,jpeg,gif}", lambda route: route.abort())
    page.route("**/*.{png,jpg,jpeg,gif}*", lambda route: route.abort())
    page.on("response", on_response)

    P.reset()

    P.lock = True
    # 这里不用处理输入编码问题
    page.goto(f"https://xuangu.eastmoney.com/Result?q={q}&type={type}", wait_until="load")
    while P.lock:
        page.wait_for_event('response')

    while P.has_next(max_page):
        logger.info("当前页为:{}, 点击`下一页`", P.current())

        P.lock = True
        page.get_by_role("button", name="下一页").click()
        while P.lock:
            page.wait_for_event('response')

    return P.get_dataframe()
