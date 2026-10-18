# -*- coding: utf-8 -*-
"""
外贸 / 跨境电商数据分析与可视化 (作品集项目)
作者: 刘笑冉
技术栈: Python(pandas / numpy / matplotlib) + SQL(sqlite3 内存库)

===== py 文件 与 sql 文件 如何"合作运行" =====
这是本项目的核心设计:
  - analysis.py  = "引擎": 负责 取数(真实/模拟) -> 把数据写入 sqlite 内存库 -> 读取 .sql 文件执行 -> 拿结果画 6 张图
  - queries.sql  = "单表版分析逻辑"(表名 orders): 被 py 直接读取执行, 驱动图表 (模拟/宽表数据用)
  - queries_olist.sql = "多表版分析逻辑"(9 张原始 Olist 表, 含 JOIN + 窗口函数): 检测到真实数据时由 py 读取执行

协作链路:  py 把数据写进内存表 --> 打开对应的 .sql 文件 --> 按分号拆分执行 SELECT --> 结果 DataFrame 交 visualization 画图
也就是说: 改 SQL 不用动 Python, 分析逻辑与画图彻底解耦。

运行: python analysis.py   ->   在 output/ 生成 6 张分析图 + 打印汇总
"""
import os
import re
import sqlite3
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # 无界面保存 PNG
import matplotlib.pyplot as plt

# ===================== 配置 =====================
DATA_DIR = "./olist_data"          # 把 Olist 的 7 个核心 csv 放这里即自动切换真实数据
OUT_DIR = "./output"
os.makedirs(OUT_DIR, exist_ok=True)


# ===================== 1. 获取数据 =====================
def load_data():
    """真实 Olist 数据存在则读真实(返回多表字典 + 对应 sql 文件), 否则用内置模拟宽表。"""
    needed = [
        "olist_orders_dataset.csv", "olist_order_items_dataset.csv",
        "olist_customers_dataset.csv", "olist_products_dataset.csv",
        "olist_order_payments_dataset.csv", "olist_order_reviews_dataset.csv",
        "product_category_name_translation.csv",
    ]
    if os.path.isdir(DATA_DIR) and all(os.path.exists(os.path.join(DATA_DIR, f)) for f in needed):
        print(">> 使用真实 Olist 数据")
        return load_real_tables(), "queries_olist.sql"
    print(">> 未检测到真实数据, 使用内置模拟外贸订单数据 (演示用)")
    return {"orders": make_mock()}, "queries.sql"


def make_mock():
    """生成 5000 条模拟外贸订单, 结构与统一宽表一致, 保证不下载也能跑。"""
    np.random.seed(42)
    n = 5000
    start = pd.Timestamp("2025-01-01")
    dates = [start + pd.Timedelta(days=int(d)) for d in np.random.randint(0, 330, n)]
    prices = np.round(np.random.lognormal(4.2, 0.6, n), 2)
    df = pd.DataFrame({
        "order_id": [f"o{i:05d}" for i in range(n)],
        "customer_id": np.random.randint(1000, 2000, n),
        "seller_id": np.random.randint(1, 30, n),
        "order_purchase_timestamp": dates,
        "product_category": np.random.choice(
            ["electronics", "home", "apparel", "beauty", "tools", "sports"],
            n, p=[0.25, 0.2, 0.2, 0.15, 0.1, 0.1]),
        "country": np.random.choice(
            ["US", "BR", "DE", "FR", "JP", "AE"], n, p=[0.3, 0.2, 0.15, 0.15, 0.1, 0.1]),
        "price": prices,
        "freight_value": np.round(prices * np.random.uniform(0.05, 0.2, n), 2),
        "order_status": np.random.choice(["delivered", "shipped", "canceled"], n, p=[0.85, 0.1, 0.05]),
        "review_score": np.random.choice([1, 2, 3, 4, 5], n, p=[0.03, 0.04, 0.08, 0.25, 0.6]),
        "payment_type": np.random.choice(["credit_card", "boleto", "voucher", "debit"],
                                         n, p=[0.7, 0.15, 0.1, 0.05]),
    })
    return df


def load_real_tables():
    """读取真实 Olist CSV, 返回 {表名: DataFrame}, 表名与 queries_olist.sql 完全一致。"""
    d = DATA_DIR
    return {
        "olist_orders_dataset": pd.read_csv(f"{d}/olist_orders_dataset.csv", parse_dates=["order_purchase_timestamp"]),
        "olist_order_items_dataset": pd.read_csv(f"{d}/olist_order_items_dataset.csv"),
        "olist_customers_dataset": pd.read_csv(f"{d}/olist_customers_dataset.csv"),
        "olist_products_dataset": pd.read_csv(f"{d}/olist_products_dataset.csv"),
        "olist_order_payments_dataset": pd.read_csv(f"{d}/olist_order_payments_dataset.csv").drop_duplicates("order_id"),
        "olist_order_reviews_dataset": pd.read_csv(f"{d}/olist_order_reviews_dataset.csv")[["order_id", "review_score"]].drop_duplicates("order_id"),
        "product_category_name_translation": pd.read_csv(f"{d}/product_category_name_translation.csv"),
    }


# ===================== 2. SQL 分析 (读取 .sql 文件执行) =====================
def run_sql_file(conn, path):
    """打开 .sql 文件, 去掉注释, 按分号拆分执行每个 SELECT, 返回 {q1:df, q2:df, ...}。"""
    print(f">> 执行 SQL 文件: {path}")
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    raw = re.sub(r"--[^\n]*", "", raw)          # 去掉 -- 行注释
    stmts = [s.strip() for s in raw.split(";") if s.strip() and s.strip().upper().startswith("SELECT")]
    results = {}
    for i, stmt in enumerate(stmts, 1):
        results[f"q{i}"] = pd.read_sql_query(stmt, conn)
    return results


def build_db(tables):
    """把多个 DataFrame 写进 sqlite 内存库, 表名即字典 key (与 .sql 里的表名对应)。"""
    conn = sqlite3.connect(":memory:")
    for name, df in tables.items():
        df.to_sql(name, conn, index=False)
    return conn


# ===================== 3. 可视化 =====================
def visualize(res):
    plt.rcParams["axes.unicode_minus"] = False
    # 1 月度 GMV
    ms = res["q1"]
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(ms["month"], ms["gmv"], marker="o", color="#2563eb")
    ax.set_title("Monthly GMV Trend"); ax.set_ylabel("GMV")
    ax.tick_params(axis="x", rotation=45)
    plt.tight_layout(); plt.savefig(f"{OUT_DIR}/01_monthly_gmv.png", dpi=100); plt.close()

    # 2 品类收入
    bc = res["q2"]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.barh(bc["product_category"], bc["revenue"], color="#16a34a")
    ax.set_title("Revenue by Category")
    plt.tight_layout(); plt.savefig(f"{OUT_DIR}/02_category.png", dpi=100); plt.close()

    # 3 国家/地区分布
    co = res["q3"]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(co["country"], co["cnt"], color="#9333ea")
    ax.set_title("Orders by Country/Region")
    plt.tight_layout(); plt.savefig(f"{OUT_DIR}/03_country.png", dpi=100); plt.close()

    # 4 评分分布
    rv = res["q4"]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(rv["review_score"].astype(str), rv["cnt"], color="#f59e0b")
    ax.set_title("Review Score Distribution")
    plt.tight_layout(); plt.savefig(f"{OUT_DIR}/04_review.png", dpi=100); plt.close()

    # 5 支付方式
    pt = res["q5"]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.pie(pt["cnt"], labels=pt["payment_type"], autopct="%1.1f%%")
    ax.set_title("Payment Type Share")
    plt.tight_layout(); plt.savefig(f"{OUT_DIR}/05_payment.png", dpi=100); plt.close()

    # 6 Top 客户
    tc = res["q6"].head(10)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(tc["customer_id"].astype(str), tc["spending"], color="#dc2626")
    ax.set_title("Top 10 Customers by Spending")
    plt.tight_layout(); plt.savefig(f"{OUT_DIR}/06_top_customers.png", dpi=100); plt.close()
    print(">> 已生成 6 张图表到 output/")

    # 7 窗口函数结果 (仅打印, 不出图)
    if "q7" in res:
        print("\n各品类销售额累计占比 (窗口函数):\n", res["q7"].to_string(index=False))


# ===================== 主流程 =====================
if __name__ == "__main__":
    tables, sql_path = load_data()
    conn = build_db(tables)
    res = run_sql_file(conn, sql_path)
    visualize(res)
    conn.close()
    print("\n总 GMV (delivered):", res["q1"]["gmv"].sum())
    print("\n各品类收入:\n", res["q2"].to_string(index=False))
    print("\n各国家/地区订单:\n", res["q3"].to_string(index=False))
