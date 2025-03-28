"""
东方财富 条件选股
https://xuangu.eastmoney.com/

1. 部分数据中包含中文单位，如万亿等，导致无法转换为数字，如VOLUME
2. 东财翻页需要提前手工登录
3. 东财翻页是页面已经翻了，然后等数据来更新，懒加载
"""
import re

import pandas as pd
from loguru import logger
from playwright.async_api import Page

from query_table.enums import QueryType

# 查询结果
# 'https://np-pick-b.eastmoney.com/api/smart-tag/stock/v3/pw/search-code'
# 'https://np-pick-b.eastmoney.com/api/smart-tag/fund/v3/pw/search-code'
# 'https://np-pick-b.eastmoney.com/api/smart-tag/hk/v3/pw/search-code'
# 'https://np-pick-b.eastmoney.com/api/smart-tag/cb/v3/pw/search-code'
# 'https://np-pick-b.eastmoney.com/api/smart-tag/etf/v3/pw/search-code'
# 'https://np-pick-b.eastmoney.com/api/smart-tag/bkc/v3/pw/search-code'
# 'https://np-tjxg-b.eastmoney.com/api/smart-tag/bkc/v3/pw/search-code'
_PAGE1_ = 'https://*.eastmoney.com/api/smart-tag/*/v3/pw/search-code'

_type_ = {
    QueryType.CNStock: 'stock',
    QueryType.Fund: 'fund',
    QueryType.HKStock: 'hk',
    QueryType.ConBond: 'cb',
    QueryType.ETF: 'etf',
    QueryType.Board: 'bk',  # 比较坑，bkc和bkc的区别
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
    return type


class Pagination:
    def __init__(self):
        self.datas = {}
        self.pageNo = 1
        self.pageSize = 100
        self.total = 1024
        self.columns = []
        self.datas = {}

    def reset(self):
        self.datas = {}

    def update(self, pageNo, pageSize, total, columns, dataList):
        self.pageNo = pageNo
        self.pageSize = pageSize
        self.total = total
        self.columns = columns
        self.datas[self.pageNo] = dataList

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
            if isinstance(v, str):
                logger.info("未识别的数据类型 {}:{}", k, v)
                continue
            try:
                df[k] = df[k].astype(v)
            except ValueError:
                logger.info("转换失败 {}:{}", k, v)

        return df.rename(columns=columns)


P = Pagination()


def search_code(json_data):
    total = json_data['data']['result']['total']
    columns = json_data['data']['result']['columns']
    dataList = json_data['data']['result']['dataList']
    return total, columns, dataList


async def on_response(response):
    post_data_json = response.request.post_data_json
    pageNo = post_data_json['pageNo']
    pageSize = post_data_json['pageSize']
    P.update(pageNo, pageSize, *search_code(await response.json()))


async def query(page: Page,
                q: str = "收盘价>100元",
                type_: QueryType = 'stock',
                max_page: int = 5) -> pd.DataFrame:
    type = _type_.get(type_, None)
    assert type is not None, f"不支持的类型:{type_}"

    await page.route(re.compile(r'.*\.(?:jpg|jpeg|png|gif|webp)(?:$|\?)'), lambda route: route.abort())

    P.reset()
    async with page.expect_response(_PAGE1_) as response_info:
        # 这里不用处理输入编码问题
        await page.goto(f"https://xuangu.eastmoney.com/Result?q={q}&type={type}", wait_until="load")
    await on_response(await response_info.value)

    while P.has_next(max_page):
        logger.info("当前页为:{}, 点击`下一页`", P.current())

        # 这种写法解决了懒加载问题
        async with page.expect_response(_PAGE1_) as response_info:
            await page.get_by_role("button", name="下一页").click()
        await on_response(await response_info.value)

    return P.get_dataframe()
