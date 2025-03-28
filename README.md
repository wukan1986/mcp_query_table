# query_table

基于`playwright`实现的网页表格爬虫，支持`Model Context Protocol (MCP) `。目前可查询来源为

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
import asyncio

from query_table import *


async def main() -> None:
    # 启动浏览器，browser_path最好是Chrome的绝对路径
    playwright, browser, context, page = await launch_browser(cdp_port=9222, browser_path=None)
    print(browser.is_connected(), page.is_closed())

    # 问财需要保证浏览器宽度>768，防止界面变成适应手机
    df = await query(page, '收益最好的200只ETF', query_type=QueryType.ETF, max_page=1, site=Site.THS)
    print(df.to_markdown())
    df = await query(page, '年初至今收益率前50', query_type=QueryType.Fund, max_page=1, site=Site.TDX)
    print(df.to_csv())
    df = await query(page, '流通市值前10的行业板块', query_type=QueryType.Index, max_page=1, site=Site.TDX)
    print(df.to_csv())
    # TODO 东财翻页要提前登录
    df = await query(page, '今日涨幅前5的概念板块;', query_type=QueryType.Board, max_page=3, site=Site.EastMoney)
    print(df)

    print('done')
    await browser.close()
    await playwright.stop()


if __name__ == '__main__':
    asyncio.run(main())

```

## 注意事项

1. 浏览器最好是`Chrome`。如一定要使用`Edge`,除了关闭`Edge`所有窗口外，还要在任务管理器关闭`Microsoft Edge`
   的所有进程，即`taskkill /f /im msedge.exe`
2. 浏览器要保证窗口宽度，防止部分网站自动适配成手机版，导致表格查询失败
3. 如有网站账号，请提前登录。此工具无自动登录功能
4. 不同网站的表格结构不同，同条件返回股票数量也不同。需要查询后做适配

## 工作原理

不同于`requests`，`playwright`是基于浏览器的，模拟用户在浏览器中的操作。

1. 不需要解决登录问题
2. 不需要解决请求构造、响应解析
3. 可以直接获取表格数据，所见即所得
4. 运行速度慢于`requests`，但开发效率高

数据的获取有：

1. 直接解析HTML表格
    1. 数字文本化了，不利于后期研究
    2. 适用性最强
2. 截获请求，获取返回的`json`数据
    1. 类似于`requests`，需要做响应解析
    2. 灵活性差点，网站改版后，需要重新做适配

此项目采用的是模拟点击浏览器来发送请求，使用截获响应并解析的方法来获取数据。

后期会根据不同的网站改版情况，使用更适合的方法。

## MCP支持

确保可以在控制台中执行`python -m query_table -h`。如果不能，可能要先`pip install query_table`

在`Cline`中可以配置如下。其中`command`是`python`的绝对路径，`browser_path`是`Chrome`的绝对路径。

### STDIO方式

```json
{
  "mcpServers": {
    "query_table": {
      "command": "D:\\Users\\Kan\\miniconda3\\envs\\py312\\python.exe",
      "args": [
        "-m",
        "query_table",
        "--format",
        "markdown",
        "--browser_path",
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
      ]
    }
  }
}
```

### SSE方式

先在控制台中执行如下命令，启动`MCP`服务
```commandline
python -m query_table --format markdown --browser_path "C:\Program Files\Google\Chrome\Application\chrome.exe" --transport sse --mcp_port 8000
```

然后就可以连接到`MCP`服务了
http://localhost:8000/sse

## 使用`MCP Inspector`进行调试

```commandline
npx @modelcontextprotocol/inspector python -m query_table --format markdown
```

第一次尝试编写`MCP`项目，可能会有各种问题，欢迎大家交流。

## `MCP`使用技巧

1. 2024年涨幅最大的100只股票按2024年12月31日总市值排名。三个网站的结果都不一样
    - 同花顺：显示了2201只股票。前5个是工商银行、农业银行、中国移动、中国石油、建设银行
    - 通达信：显示了100只股票，前5个是寒武纪、正丹股份，汇金科技、万丰奥威、艾融软件
    - 东方财富：显示了100只股票，前5个是海光信息、寒武纪、光启技术、润泽科技、新易盛

2. 大语言模型对问题拆分能力弱，所以要能合理的提问，保证查询条件不会被改动。以下推荐第2、3种
    - 2024年涨幅最大的100只股票按2024年12月31日总市值排名
      > 大语言模型非常有可能拆分这句，导致一步查询被分成了多步查询
    - 向东方财富查询“2024年涨幅最大的100只股票按2024年12月31日总市值排名”
      > 用引号括起来，避免被拆分
    - 向东方财富板块查询 “去年涨的最差的行业板块”，再查询此板块中去年涨的最好的5只股票
      > 分成两步查询，先查询板块，再查询股票。但最好不要全自动，因为第一步的结果它不理解“今日涨幅”和“区间涨幅”,需要交互修正

## 参考

- [Playwright](https://playwright.dev/python/docs/intro)
- [Selenium webdriver无法附加到edge实例，edge的--remote-debugging-port选项无效](https://blog.csdn.net/qq_30576521/article/details/142370538)