# 智能KYC助手 – 反洗钱客户尽职调查 AI 原型

> 一份尽调报告初稿，从 2-3 小时缩短至 3 分钟。

---

## 📌 项目背景

银行客户经理做反洗钱尽调时，需要登录工商、司法、税务等多个系统查询信息，然后手动撰写尽调报告。**80% 的时间耗费在信息搬运和复制粘贴上，真正用于风险判断的时间不到 20%。**

本项目利用 RAG（检索增强生成）技术，自动聚合企业特征并生成结构化风险报告，让客户经理从“文书工作”回归“风险判断”。

---

## 🎯 核心功能

| 功能 | 说明 |
|------|------|
| ✅ 精确查询 + AI报告 | 输入企业名称，一键生成包含风险等级、风险因素、尽调建议的 JSON 报告 |
| ✅ 语义搜索 | 输入“现金流紧张”等自然语言，自动检索最相似的 3 家企业 |
| ✅ 降级模拟报告 | API 不可用时自动切换本地规则，保证可用性 |
| ✅ 报告下载 | 支持导出 JSON 格式，便于对接银行内部系统 |

---

## 🛠️ 技术栈

| 类别 | 技术 |
|------|------|
| 前端 | Streamlit |
| 大模型 | DeepSeek API（强制 JSON 输出） |
| 向量检索 | FAISS + sentence-transformers（中文嵌入模型） |
| 数据处理 | Pandas |
| 部署 | Streamlit Cloud |
| 语言 | Python 3.9+ |

---

## 🚀 在线体验

👉 **[点击体验智能KYC助手](https://kyc-ai-assistant-bjpan8c5zwzwzpzn5vvhts.streamlit.app/)**

首次加载约 10-15 秒，请耐心等待。

---

## 📦 本地运行

如果你想在本地运行和修改：

### 1. 克隆仓库

```bash
git clone https://github.com/jiamiaoli78-cat/kyc-ai-assistant


2. 安装依赖
bash
pip install -r requirements.txt

3. 设置 API Key（DeepSeek）
(1)Windows（PowerShell）：

bash
$env:DEEPSEEK_API_KEY="sk-你的真实Key"

(2)Windows（CMD）：

bash
set DEEPSEEK_API_KEY=sk-你的真实Key

(3)Mac / Linux：

bash
export DEEPSEEK_API_KEY=sk-你的真实Key

4. 启动应用
bash
streamlit run app.py
浏览器访问 http://localhost:8501

🎬 演示视频
B站完整演示（https://b23.tv/DQSNqLQ）
小红书视频演示（http://xhslink.com/o/8Vo2KXvz99n ）

📊 核心价值量化
效率：单份报告初稿从 2-3 小时 → 3 分钟（提升 90%+）
成本：API 调用单次约 0.02 元，远低于人力成本
合规：所有结论基于企业真实描述生成，可追溯、可解释

🗺️ 项目结构
kyc-ai-assistant/
├── app.py                      # 主应用（Streamlit）
├── requirements.txt            # 依赖列表
├── 带企业名称的客户数据.csv    # 企业特征数据
├── faiss_db/                   # FAISS 向量索引（本地运行自动生成）
├── images/                     # README 截图
│   ├── journey_map.png
│   ├── ui_demo.png
│   └── report_demo.png
└── README.md

🔮 下一步计划
接入实时工商 / 司法 API
增加风险雷达图可视化
支持多企业批量报告
引入 Agent 工作流（自动多源检索 + 决策建议）
优化提示词，融入反洗钱专家规则库

👤 作者
Jiamiao
求职方向：AI 风控产品 / 金融科技
项目周期：30 天（2026 年）
GitHub：jiamiaoli78-cat
小红书：411089003

📄 说明

本项目为个人学习与求职作品，欢迎交流探讨。
