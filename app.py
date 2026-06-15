import streamlit as st
import pandas as pd
import json
import requests
import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
import faiss

st.set_page_config(page_title="智能KYC助手", layout="wide")
st.title("智能KYC助手 - 反洗钱客户尽职调查")
st.markdown("输入企业名称，AI 自动生成风险报告（接入 DeepSeek 真实模型）")

@st.cache_data
def load_data():
    df = pd.read_csv("带企业名称的客户数据.csv", encoding="utf-8-sig")
    return df

df = load_data()
company_names = df["企业名称"].tolist()
name_to_desc = dict(zip(df["企业名称"], df["风险特征描述"]))
name_to_risk = dict(zip(df["企业名称"], df["风险等级"]))
name_to_default = dict(zip(df["企业名称"], df["是否违约"]))

# ==================== FAISS 向量库 ====================
@st.cache_resource
def load_faiss_db():
    embeddings = HuggingFaceEmbeddings(model_name="shibing624/text2vec-base-chinese")
    persist_dir = "faiss_db"
    if os.path.exists(persist_dir) and os.path.isdir(persist_dir):
        return FAISS.load_local(persist_dir, embeddings, allow_dangerous_deserialization=True)
    df_local = load_data()
    docs = []
    for _, row in df_local.iterrows():
        doc = Document(
            page_content=row["风险特征描述"],
            metadata={
                "企业名称": row["企业名称"],
                "风险等级": str(row["风险等级"]),
                "是否违约": str(row["是否违约"])
            }
        )
        docs.append(doc)
    vectorstore = FAISS.from_documents(docs, embeddings)
    vectorstore.save_local(persist_dir)
    return vectorstore

# ==================== Session State ====================
if "search_results" not in st.session_state:
    st.session_state.search_results = None
if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "search_report_data" not in st.session_state:
    st.session_state.search_report_data = None
if "search_report_company" not in st.session_state:
    st.session_state.search_report_company = None

# 优先从环境变量读取 API Key
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-b9b7df91a61846db9ced35390cf7f89c")  # 请替换
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

def call_deepseek(prompt):
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是专业的反洗钱风险评估专家，只输出纯 JSON，不要有其他文字。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "response_format": {"type": "json_object"}
    }
    try:
        print("正在调用 DeepSeek API...")   # 调试输出
        response = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=30)
        print(f"HTTP 状态码: {response.status_code}")   # 调试输出
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        print("API 返回内容:", content)   # 调试输出
        return json.loads(content)
    except Exception as e:
        print(f"API 调用失败，错误详情: {e}")   # 调试输出
        st.error(f"API 调用失败: {e}")
        return None

def generate_risk_report(company_name):
    desc = name_to_desc.get(company_name)
    if desc is None:
        return {"error": "未找到该企业"}
    prompt = f"""
你是一位银行反洗钱专家。请根据以下企业信息，生成一份客户尽职调查风险摘要。

【企业信息】
{desc}

请严格按照以下 JSON 格式输出，不要输出任何其他内容：
{{
    "风险等级": "高/中/低",
    "风险因素": ["因素1", "因素2", "因素3"],
    "尽调建议": "具体的下一步行动建议",
    "综合评语": "一句话总结"
}}
"""
    report = call_deepseek(prompt)
    if report is None:
        st.warning("AI 服务暂时不可用，使用模拟报告")
        risk_level = name_to_risk.get(company_name, "中风险")
        if "高" in risk_level:
            report = {
                "风险等级": "高风险",
                "风险因素": ["存在违约记录", "贷款金额较大", "还款负担重"],
                "尽调建议": "建议实地核查经营场所，核实资金用途",
                "综合评语": "该企业风险较高，需重点关注"
            }
        elif "中" in risk_level:
            report = {
                "风险等级": "中风险",
                "风险因素": ["贷款期限较长", "行业波动性大", "征信等级较低"],
                "尽调建议": "建议核查关联交易和资金流向，补充财务报表",
                "综合评语": "该企业存在一定风险，建议加强定期审查"
            }
        else:
            report = {
                "风险等级": "低风险",
                "风险因素": ["经营稳定", "无违约记录", "资产状况良好"],
                "尽调建议": "常规尽调即可，快速通道处理",
                "综合评语": "该企业风险较低，可正常推进业务"
            }
    report["企业名称"] = company_name
    report["原始风险等级"] = name_to_risk.get(company_name, "未知")
    return report

# ==================== 侧边栏 ====================
st.sidebar.header("查询企业")
selected_company = st.sidebar.selectbox("选择企业", company_names)
manual_company = st.sidebar.text_input("或直接输入企业名称")
company_name = manual_company if manual_company else selected_company

# -------------------- 语义搜索 --------------------
st.sidebar.markdown("---")
st.sidebar.header("语义搜索")
search_input = st.sidebar.text_input("输入风险描述（如：现金流紧张）", key="search_input")
search_btn = st.sidebar.button("搜索", key="search_btn", use_container_width=True)

if search_btn and search_input.strip():
    with st.spinner("正在语义搜索..."):
        vectorstore = load_faiss_db()
        st.session_state.search_results = vectorstore.similarity_search(search_input, k=3)
        st.session_state.search_query = search_input
        st.session_state.search_report_data = None
        st.session_state.search_report_company = None
        st.rerun()

# ==================== 主区域：原有企业查询 ====================
if company_name:
    if company_name in company_names:
        st.subheader(f"企业：{company_name}")
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.info(f"原始风险等级：{name_to_risk[company_name]}")
        with col_info2:
            st.info(f"是否违约：{'是' if name_to_default[company_name]==1 else '否'}")
        if st.button("生成风险报告", type="primary"):
            with st.spinner("AI 正在分析中，请稍候..."):
                report = generate_risk_report(company_name)
            if "error" not in report:
                st.success("报告生成完成")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("综合风险等级", report["风险等级"])
                    st.write("**主要风险因素**")
                    for factor in report["风险因素"]:
                        st.write(f"- {factor}")
                with col2:
                    st.write("**尽职调查建议**")
                    st.write(report["尽调建议"])
                    st.write("**综合评语**")
                    st.write(report["综合评语"])
                st.download_button(
                    label="下载报告 (JSON)",
                    data=json.dumps(report, ensure_ascii=False, indent=2),
                    file_name=f"{company_name}_风险报告.json",
                    mime="application/json"
                )
            else:
                st.error(report["error"])
    else:
        st.error("未找到该企业，请检查名称")
else:
    st.info("请在左侧选择或输入企业名称")

# ==================== 语义搜索结果与报告 ====================
if st.session_state.search_results:
    st.markdown("---")
    st.subheader(f"语义搜索结果：'{st.session_state.search_query}'")
    for i, doc in enumerate(st.session_state.search_results):
        meta = doc.metadata
        with st.container(border=True):
            col_a, col_b, col_c = st.columns([3, 1, 1])
            with col_a:
                st.write(f"**{meta['企业名称']}**")
                preview = doc.page_content
                if len(preview) > 120:
                    preview = preview[:120] + "..."
                st.caption(preview)
            with col_b:
                st.write(f"风险等级：{meta.get('风险等级', '未知')}")
            with col_c:
                if st.button("生成报告", key=f"srep_{i}", use_container_width=True):
                    with st.spinner("AI 正在分析中，请稍候..."):
                        report = generate_risk_report(meta["企业名称"])
                    st.session_state.search_report_data = report
                    st.session_state.search_report_company = meta["企业名称"]
                    st.rerun()

if st.session_state.search_report_data and st.session_state.search_report_company:
    report = st.session_state.search_report_data
    target = st.session_state.search_report_company
    st.subheader(f"企业：{target}")
    col_info1, col_info2 = st.columns(2)
    with col_info1:
        st.info(f"原始风险等级：{name_to_risk[target]}")
    with col_info2:
        st.info(f"是否违约：{'是' if name_to_default[target]==1 else '否'}")
    if "error" not in report:
        st.success("报告生成完成")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("综合风险等级", report["风险等级"])
            st.write("**主要风险因素**")
            for factor in report["风险因素"]:
                st.write(f"- {factor}")
        with col2:
            st.write("**尽职调查建议**")
            st.write(report["尽调建议"])
            st.write("**综合评语**")
            st.write(report["综合评语"])
        st.download_button(
            label="下载报告 (JSON)",
            data=json.dumps(report, ensure_ascii=False, indent=2),
            file_name=f"{target}_风险报告.json",
            mime="application/json"
        )
    else:
        st.error(report["error"])

st.markdown("---")
st.caption("报告由 DeepSeek AI 生成，仅供参考。")
