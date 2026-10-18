# 外贸 / 跨境电商数据分析项目（作品集）

> 作者：刘笑冉 ｜ 用途：求职作品集（跨境运营分析 / AI 产品运营 / 数据运营岗通用弹药）
> 技术栈：Python（pandas / numpy / matplotlib）+ SQL（sqlite3 / 多表 JOIN）

## 一、项目背景
用真实的跨境电商订单数据，从**销售趋势、品类结构、地区分布、服务质量、支付方式、高价值客户**六个维度做数据分析与可视化，输出可直接放进简历 / GitHub 的作品集，证明「能用 SQL + Python 把业务数据变成决策结论」的能力。

## 二、数据来源
- **主数据**：Kaggle — Brazilian E-Commerce Public Dataset by Olist
  https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
  （9 张表、约 10 万订单，含订单 / 商品 / 卖家 / 客户 / 支付 / 评价 / 地理 / 品类翻译）
- **备选宏观数据**：UNCTAD 全球贸易数据 https://unctadstat.unctad.org/ （做国家贸易流向图）

> 如果你手上有自己公司的真实外贸订单 / 询盘数据，请优先用真实数据——说服力最强，直接服务跨境简历。

## 三、目录结构
```
外贸数据分析项目/
├── analysis.py          # 主引擎：取数 → 写入 sqlite 内存库 → 读取并执行 .sql 文件 → 出 6 张图
├── queries.sql          # 单表版分析逻辑(表名 orders)：被 analysis.py 直接读取执行, 驱动图表 (模拟/宽表数据用)
├── queries_olist.sql    # 多表版分析逻辑(9 张原始表, 含 JOIN + 窗口函数)：检测到真实数据时由 py 调用; 也供面试展示 SQL 深度
├── README.md            # 本说明
├── olist_data/          # （可选）放 Olist 的 7 个核心 csv，脚本自动切真实数据并改用 queries_olist.sql
└── output/              # 生成的 6 张图表
    ├── 01_monthly_gmv.png
    ├── 02_category.png
    ├── 03_country.png
    ├── 04_review.png
    ├── 05_payment.png
    └── 06_top_customers.png
```

> **py 与 sql 如何"合作运行"（核心设计）**
> - `analysis.py` 只做三件事：① 取数（真实 Olist 或内置模拟）② 把数据写进 **sqlite 内存库**的表 ③ 打开对应的 `.sql` 文件、按分号拆分执行里面的 `SELECT`、把结果交给画图函数。
> - 分析逻辑**全在 `.sql` 文件里**，Python 不写任何业务 SQL——这样改分析口径不用动代码。
> - 模拟 / 宽表数据 → py 建单表 `orders` → 执行 `queries.sql`；真实 Olist 数据 → py 建 9 张表 → 执行 `queries_olist.sql`（多表 JOIN + 窗口函数）。
> - 二者通过内存库解耦：`py` 写表、`.sql` 查表，跑完即焚。

## 四、运行步骤
```bash
# 1. 安装依赖
pip install pandas numpy matplotlib

# 2. 直接跑（用内置模拟数据，无需下载）
python analysis.py

# 3. 用真实数据：把 Olist 的 7 个核心 csv 放进 olist_data/ 再跑
#    （脚本会自动改用 queries_olist.sql 多表 JOIN 版执行）
python analysis.py
```
运行后 6 张图自动生成在 `output/`，终端打印 GMV 与品类 / 地区汇总。

## 五、分析维度与产出
| 维度 | 方法 | 业务价值 |
|---|---|---|
| 月度 GMV 趋势 | SQL 按月聚合 + 折线图 | 看淡旺季、增长节奏 |
| 品类收入结构 | SQL 分组 + 横向柱状 | 识别核心品类、选品依据 |
| 地区分布 | SQL 分组 + 柱状 | 市场重心、本地化投入 |
| 评分分布 | SQL 分组 + 柱状 | 服务质量、复购风险 |
| 支付方式 | SQL 分组 + 饼图 | 结款偏好、风控 |
| 高价值客户 | SQL TOP N + 柱状 | RFM 中的 M，重点维护 |

## 六、简历话术（真实数据已跑通，详见 `简历话术.md`）
> ⚠️ 数据定位：基于公开数据集(Kaggle Olist)的练手项目，**不是本人任职公司业绩**，面试须如实说明；但 SQL 逻辑 / 代码 / 图表均可现场演示、开源可查。

真实跑出的关键指标（已成交 96,478 笔订单 / 2016.09–2018.08）：
- **总 GMV R$ 15,419,773.75**；月度峰值 **2017-11 R$ 1,153,364.2**（旺季大促）
- **Top3 品类（健康美容 / 手表礼品 / 床浴家居）合计贡献 26.2% 收入**
- 区域：**圣保罗州(SP) 占 42%**（RJ、MG 次之）
- 支付：**信用卡 74% / boleto 19%**；评分 **均值 4.16/5，4–5 星占 79%**

一句话话术（私人求职材料，本地保留未公开）：
> 用 SQL(多表 JOIN + 窗口函数) + Python 对 9.6 万笔真实订单做 6 维度分析：识别 Top3 品类贡献 26% 收入、核心市场 SP 州占 42%、评分均值 4.16/5，输出 6 张可视化看板，支撑选品与区域投放决策。

## 七、下一步可扩展
- 加 RFM 客户分群（用 SQL 窗口函数算 R/F/M 打分）
- 加配送时效分析（下单→送达天数 vs 评分）
- 用 Plotly / Tableau 做交互看板
- 写进 GitHub，README 挂图表与结论
