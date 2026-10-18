-- ============================================================
-- 外贸 / 跨境电商数据分析 - SQL (单表版)
-- 对应表名: orders  (由 analysis.py 把 DataFrame 写入 sqlite 内存库)
-- 用途:
--   1) 被 analysis.py 直接读取执行, 驱动 6 张可视化图表
--   2) 展示 GROUP BY 聚合 + 窗口函数 能力 (面试作品集)
-- 运行: 由 analysis.py 自动调用; 也可在任意 sqlite 客户端单独跑
-- ============================================================

-- 1. 月度 GMV 与订单量 (经营趋势) -> 驱动图 01
SELECT strftime('%Y-%m', order_purchase_timestamp) AS month,
       ROUND(SUM(price + freight_value), 2)         AS gmv,
       COUNT(*)                                     AS orders
FROM orders
WHERE order_status = 'delivered'
GROUP BY month
ORDER BY month;

-- 2. 品类收入 (品类结构) -> 驱动图 02
SELECT product_category,
       ROUND(SUM(price), 2) AS revenue,
       COUNT(*)             AS cnt
FROM orders
WHERE order_status = 'delivered'
GROUP BY product_category
ORDER BY revenue DESC;

-- 3. 各国家/地区订单分布 -> 驱动图 03
SELECT country,
       COUNT(*)                AS cnt,
       ROUND(AVG(price), 2)    AS avg_price
FROM orders
WHERE order_status = 'delivered'
GROUP BY country
ORDER BY cnt DESC;

-- 4. 评分分布 (服务质量) -> 驱动图 04
SELECT review_score,
       COUNT(*) AS cnt
FROM orders
GROUP BY review_score
ORDER BY review_score;

-- 5. 支付方式占比 -> 驱动图 05
SELECT payment_type,
       COUNT(*) AS cnt
FROM orders
GROUP BY payment_type
ORDER BY cnt DESC;

-- 6. Top 客户 (高价值客户识别) -> 驱动图 06
SELECT customer_id,
       COUNT(*)                AS orders,
       ROUND(SUM(price), 2)    AS spending
FROM orders
WHERE order_status = 'delivered'
GROUP BY customer_id
ORDER BY spending DESC
LIMIT 10;

-- 7. (进阶) 各品类销售额累计占比 (窗口函数) -> 仅打印, 不出图
SELECT product_category,
       revenue,
       ROUND(SUM(revenue) OVER (ORDER BY revenue DESC)
             / SUM(revenue) OVER () * 100, 1) AS cum_pct
FROM (
    SELECT product_category, SUM(price) AS revenue
    FROM orders
    WHERE order_status = 'delivered'
    GROUP BY product_category
);
