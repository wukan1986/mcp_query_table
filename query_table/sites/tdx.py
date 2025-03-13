"""
通达信 小达
https://wenda.tdx.com.cn/
"""
import math

import pandas as pd
from loguru import logger
from playwright.sync_api import Page

from query_table.enums import QueryType

# 查询结果
_PAGE1_ = 'https://wenda.tdx.com.cn/TQL?Entry=NLPSE.NLPQuery'
# 代码数量
_PAGE2_ = 'https://wenda.tdx.com.cn/TQL?Entry=JNLPSE.getAllCode'

_queryType_ = {
    QueryType.CNStock: 'AG',
    QueryType.Fund: 'JJ',
    QueryType.Index: 'ZS',
}


def convert_type(type):
    if type == '':
        return str
    if type == '0|0|0':
        return str
    if type == '2|0|0':
        return float
    if type == '0|9|1':
        return float
    if type == '2|9|1':
        return float
    return None


class Pagination:
    def __init__(self):
        self.datas = {}
        self.last_count = 1
        self.limit = 100
        self.row_count = 1024
        self.dtypes = []
        self.columns = []

    def reset(self):
        self.datas = {}

    def update_row_count(self, row_count):
        self.row_count = row_count

    def update_last_count(self, limit, last_count, columns, dtypes, datas):
        self.limit = limit
        self.last_count = last_count
        self.columns = columns
        self.dtypes = dtypes
        self.datas[last_count] = datas

    def has_next(self, max_page):
        page = math.ceil(self.last_count / self.limit)
        c1 = self.last_count < self.row_count
        c2 = page < max_page
        return c1 & c2

    def current(self):
        return self.last_count

    def get_list(self):
        datas = []
        for k, v in self.datas.items():
            datas.extend(v)
        return datas

    def get_dataframe(self):
        dtypes = [convert_type(x) for x in self.dtypes]
        df = pd.DataFrame(self.get_list(), columns=self.columns)
        for i, v in enumerate(dtypes):
            k = self.columns[i]
            if k == 'POS':
                df[k] = df[k].astype(int)
                continue
            if v is None:
                logger.info("未识别的数据类型{}:{}", k, v)
                continue
            try:
                df[k] = df[k].astype(v)
            except ValueError:
                logger.info("转换失败{}:{}", k, v)
        return df


P = Pagination()


def NLPQuery(json_data):
    limit = json_data[0][2]
    last_count = int(json_data[0][4])
    columns = json_data[1]
    dtypes = json_data[2]
    datas = json_data[3:]

    return limit, last_count, columns, dtypes, datas


def getAllCode(json_data):
    row_count = json_data[0][2]

    return row_count


def on_response(response):
    if response.url.startswith(_PAGE1_):
        P.update_last_count(*NLPQuery(response.json()))
    if response.url.startswith(_PAGE2_):
        P.update_row_count(getAllCode(response.json()))


def query(page: Page,
          message: str = "收盘价>100元",
          queryType: str = 'AG',
          max_page: int = 5) -> pd.DataFrame:
    queryType = _queryType_.get(queryType, queryType)

    page.route("**/*.{png,jpg,jpeg,gif}", lambda route: route.abort())
    page.route("**/*.{png,jpg,jpeg,gif}*", lambda route: route.abort())
    page.on("response", on_response)

    P.reset()
    # 这里不用处理输入编码问题
    page.goto(f"https://wenda.tdx.com.cn/site/wenda/stock_index.html?message={message}&queryType={queryType}",
              wait_until="load")

    while P.has_next(max_page):
        logger.info("当前序号为:{}, 点击`下一页`", P.current())
        page.get_by_role("button", name="下一页").click()

    return P.get_dataframe()
