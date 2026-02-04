# Streamlit应用

实现在同一页面中查询金融数据，并手工输入到大语言模型网站中进行深度分析。

## 功能

- 直接查询金融网站的数据，免去数据导出的麻烦
- 内嵌大语言模型网站，同一页面中进行大数据分析

## 部署方法

1. 安装两款浏览器，其中一款必须是`Chrome`(用于`playwright`控制)。另外一款用于访问`Streamlit`，如`Edge`
2. 安装依赖
   ```bash
   uv pip install -r requirements.txt
   playwright install chromium
   ```
3. 启动`MCP`服务`SSE`模式
   ```bash
   # Linux下的无头模式，速度更快。不用登录
   uv run python -m mcp_query_table --format markdown --transport sse --port 8000 --endpoint --executable_path --user_data_dir
   ```
4. 启动`Streamlit`应用
   ```bash
   uv run python -m streamlit run app.py --server.enableStaticServing=true --theme.codeFont="SimSun, monospace" --server.port=51015
   ```
5. 打开`Edge`浏览器，访问`http://localhost:51015/`

## streamlit使用方法

1. 选择合适的大语言模型网站，如`腾讯`、`字节`、`阿里`等
2. 选择合适的查询网站，如`东方财富`、`同花顺`、`通达信`
3. 输入查询条件/提示词，如`2024年涨幅最大的100只股票按2024年12月31日总市值排名`
4. 点击`查询`按钮，查询结果会显示在右下页面中（提示词+数据），可以点击复制按钮，将查询结果粘贴到大语言模型网站中进行分析
5. 在`下载Markdown`(只含数据)右键复制链接，在大语言模型网站中点击`上传文件`，打开文件对话框中直接粘贴链接。然后复制提示词过来即可
6. `Markdown`下载到本地，可以在记事本中打开，字体设置成`宋体`表格会显示正常

## 注意

1. 东方财富。翻页要登录，港股要登录

## Linux命令

```bash
# 启动MCP服务
nohup python -m mcp_query_table --format markdown --transport sse --port 8000 --endpoint --executable_path --user_data_dir > mcp.log 2>&1 &
# 启动Streamlit应用
nohup streamlit run app.py --server.enableStaticServing=true --theme.codeFont="SimSun, monospace" --server.port=51015 > streamlit.log 2>&1 &
```

## 参考

https://github.com/zanetworker/mcp-sse-client-python

## .streamlit/config.toml
可以简化成
```bash
nohup streamlit run app.py > streamlit.log 2>&1 &
```