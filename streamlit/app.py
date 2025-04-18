import asyncio
import hashlib
import os
import sys

import streamlit as st
import streamlit.components.v1 as components
import streamlit_authenticator as stauth
import yaml
from streamlit_authenticator import LoginError

# 添加当前目录和上一层目录到系统路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client import MCPClient
from mcp_query_table import QueryType, Site

Provders = {
    # "about:blank": "空白页",
    "https://yuanbao.tencent.com": "腾讯元宝 - 支持长文|DeepSeek",
    "https://chat.baidu.com": "百度AI搜索 - 长文限制|DeepSeek",
    "https://www.doubao.com/chat": "字节豆包 - 强制联网|支持长文|Doubao",
    "https://www.n.cn": "360纳米搜索 - 强制联网|支持长文|不支持文件|多模型",
    # "https://yiyan.baidu.com": "百度文心一言 - 支持长文|X1",
    # "https://chat.z.ai/": "智谱AI - 无法内嵌|不支持文件",
    # "https://tongyi.aliyun.com": "通义千问 - 无法内嵌|长文限制|QwQ",
}

Sites = {
    "https://xuangu.eastmoney.com": Site.EastMoney,  # 翻页要登录，港股要登录
    "https://www.iwencai.com": Site.THS,
    "https://wenda.tdx.com.cn": Site.TDX,
}

QueryTypes = {
    "https://xuangu.eastmoney.com": [QueryType.CNStock, QueryType.Fund, QueryType.HKStock, QueryType.ConBond,
                                     QueryType.ETF, QueryType.Board],
    "https://www.iwencai.com": [QueryType.CNStock, QueryType.Index, QueryType.Fund, QueryType.HKStock,
                                QueryType.USStock],
    "https://wenda.tdx.com.cn": [QueryType.CNStock, QueryType.Fund, QueryType.Index, QueryType.Info],
}

default_query = "涨幅前10"
default_prompt = """你是一个专业的股票分析师。请忽略文件名，仅根据文件内容，为我提供专业分析报告。不用联网搜索。

文件内容如下："""

st.set_page_config(page_title='财经问答LLM', layout="wide", initial_sidebar_state="expanded")

with open('auth.yaml', 'r', encoding='utf-8') as file:
    config = yaml.safe_load(file)

# Pre-hashing all plain text passwords once
stauth.Hasher.hash_passwords(config['credentials'])

# Creating the authenticator object
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

try:
    authenticator.login()
except LoginError as e:
    st.error(e)

if st.session_state['authentication_status'] is False:
    st.error('Username/password is incorrect')
elif st.session_state['authentication_status'] is None:
    st.warning('Please enter your username and password')
if not st.session_state['authentication_status']:
    st.stop()

# Loading config file
with open('config.yaml', 'r', encoding='utf-8') as file:
    config = yaml.safe_load(file)

os.makedirs("static", exist_ok=True)

if "templates" not in st.session_state:
    st.session_state.templates = config["templates"] or {default_query: default_prompt}
if "queries" not in st.session_state:
    st.session_state.queries = list(st.session_state.templates.keys())
if "query" not in st.session_state:
    st.session_state.query = default_query
if "prompt" not in st.session_state:
    st.session_state.prompt = default_prompt
if "code" not in st.session_state:
    st.session_state.code = ""


def get_md5(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()


async def tool_query(client: MCPClient, query_input, query_type, max_page, site):
    result = await client.invoke_tool('query',
                                      {"query_input": query_input, "query_type": query_type,
                                       "max_page": max_page, "site": site, })
    content = '\n'.join([c.text for c in result.content])
    return result.isError, content


def part1():
    st.session_state.iframe_url = st.selectbox("大模型网站", Provders, format_func=lambda x: Provders[x],
                                               label_visibility="collapsed")
    st.markdown(st.session_state.iframe_url)


@st.fragment
def part2():
    site = st.selectbox("查询网站", Sites, format_func=lambda x: Sites[x].value, label_visibility="collapsed")
    st.session_state.site = Sites[site].value
    st.markdown(site)
    st.session_state.query_type = st.radio("查询类型", [q.value for q in QueryTypes[site]], horizontal=True)


@st.fragment
def part3():
    st.subheader("问题")
    p1 = st.empty()
    p2 = st.empty()
    col1, col2, col3 = st.columns([3, 1, 1], vertical_alignment="bottom")
    p3 = col1.empty()
    p4 = col2.empty()
    p5 = col3.empty()

    qry = p3.selectbox("模板", st.session_state.queries)
    st.session_state.prompt = st.session_state.templates.get(qry, default_prompt)
    query = p1.text_input("查询", qry, placeholder="请输入您要查询的数据", label_visibility='collapsed').strip()
    prompt = p2.text_area("提示词", st.session_state.prompt, height=120).strip()

    st.session_state.query = query
    st.session_state.prompt = prompt

    if p4.button("添加"):
        if len(query) == 0 or len(prompt) == 0:
            st.error("查询/提示词 不能为空")
        else:
            st.session_state.templates[query] = prompt
            if query not in st.session_state.queries:
                st.session_state.queries.append(query)
            st.rerun()

    if p5.button("删除"):
        if len(st.session_state.queries) <= 1:
            st.error("至少保留一条")
        else:
            del st.session_state.templates[qry]
            st.session_state.queries.remove(qry)
            st.rerun()


def part4():
    col1, col2 = st.columns([1, 1], vertical_alignment="center")
    p1 = col1.empty()
    p2 = col2.empty()
    if p1.button("查询", type="primary", use_container_width=True):
        with st.spinner("查询中..."):
            if len(st.session_state.query) == 0 or len(st.session_state.prompt) == 0:
                st.error("查询/提示词 不能为空")
            else:
                safe_name = get_md5(st.session_state.query) + '.md'
                download_url = f"app/static/{safe_name}"
                p2.markdown(f'<a href="{download_url}" download="{safe_name}">下载`MarkDown`</a>',
                            unsafe_allow_html=True)

                st.session_state.client = MCPClient(config['mcp_endpoint'])
                isError, content = asyncio.run(tool_query(st.session_state.client,
                                                          st.session_state.query,
                                                          st.session_state.query_type,
                                                          config['max_page'],
                                                          st.session_state.site))
                if isError:
                    st.error(content)
                else:
                    st.session_state.code = content
                    with open(f"static/{safe_name}", 'w+', encoding='utf-8-sig') as f:
                        f.write(content)


with st.sidebar:
    part1()
    part2()
    part3()
    part4()

components.iframe(st.session_state.iframe_url, height=680)

st.markdown("""
<style>
    .block-container {
        max-width: 100% !important;
        padding-top: 0rem;
        padding-right: 0rem;
        padding-left: 0.5rem;
        padding-bottom: 0rem;
    }
    header {visibility: hidden;}
    .stApp {
        margin-top: -25px;
    }
</style>
""", unsafe_allow_html=True)

if st.session_state.code:
    prompt = st.session_state.prompt
    code = st.session_state.code
    st.code(prompt + "\n\n" + code, language='markdown')

config['templates'] = st.session_state.templates
with open('config.yaml', 'w', encoding='utf-8') as file:
    yaml.dump(config, file, default_flow_style=False, allow_unicode=True)

# streamlit run app.py  -server.enableStaticServing=true --theme.codeFont="SimSun, monospace"
# nohup streamlit run app.py --server.port=51015 --theme.codeFont="SimSun, monospace" --browser.serverAddress=hk.k0s.top  --server.enableStaticServing=true > streamlit.log 2>&1 &
