# query_table

基于`playwright`实现的网页表格查询器。目前可用于

- [同花顺i问财](http://iwencai.com/)
- [通达信问小达](https://wenda.tdx.com.cn/)
- [东方财富条件选股](https://xuangu.eastmoney.com/)

实盘时，如果某网站宕机或改版，可以立即切换到其他网站。(注意：不同网站的表格结构不同，需要提前做适配)

## 安装

```commandline
pip install -i https://pypi.org/simple --upgrade query_table
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade query_table
```

## 使用

```python
from query_table import *


def run() -> None:
    # 启动浏览器，browser_path最好是Chrome的绝对路劲
    playwright, browser, context, page = launch_browser(port=9222, browser_path=None)

    # TODO 问财需要保证浏览器宽度，防止界面变成适应手机
    df = query(page, '收盘价>50元', query_type=QueryType.CNStock, max_page=3, site=Site.iwencai)
    print(df)
    df = query(page, '收盘价>50元', query_type=QueryType.CNStock, max_page=3, site=Site.tdx)
    print(df)
    # TODO 东财翻页要提前登录
    df = query(page, '收盘价>50元', query_type=QueryType.CNStock, max_page=3, site=Site.eastmoney)
    print(df)

    print('done')
    browser.close()


if __name__ == '__main__':
    run()


```

## 注意事项

1. 浏览器最好是`Chrome`。如一定要使用`Edge`,除了关闭`Edge`所有窗口外，还要在任务管理器关闭`Microsoft Edge`的所有进程
2. 浏览器要保证窗口宽度，防止部分网站自动适配成手机版，导致表格查询失败
3. 如有网站账号，请提前登录。此工具无自动登录功能
4. 不同网站的表格结构不同，同条件返回股票数量也不同。需要查询后做适配

## 工作原理

不同于`requests`，`playwright`是基于浏览器的，模拟用户在浏览器中的操作。

1. 它不需要解决登录问题
2. 它不需要解决请求构造、响应解析
3. 可以直接获取表格数据，所见即所得
4. 运行速度慢于`requests`，但开发效率高

数据的获取有：

1. 直接解析HTML表格
    1. 数字文本化了，不利于后期研究
    2. 适用性最强
2. 截获请求，获取返回的json数据
    1. 类似于`requests`，需要做响应解析
    2. 灵活性差点，网站改版后，需要重新做适配

此项目采用的是模拟点击浏览器来发送请求，使用截获响应并解析的方法来获取数据。

后期会根据不同的网站改版情况，使用更适合的方法。

## 参考

- [Playwright](https://playwright.dev/python/docs/intro)
- [Selenium webdriver无法附加到edge实例，edge的--remote-debugging-port选项无效](https://blog.csdn.net/qq_30576521/article/details/142370538)