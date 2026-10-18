-- ============================================================
-- 外贸 / 跨境电商数据分析 - SQL (多表版, 真实 Olist 数据)
-- 对应表名: olist_orders_dataset / olist_order_items_dataset /
--           olist_customers_dataset / olist_products_dataset /
--           olist_order_payments_dataset / olist_order_reviews_dataset /
--           product_category_name_translation
-- 用途:
--   1) 在 analysis.py 检测到 ./olist_data 真实 CSV 时自动调用, 驱动同 6 张图
--   2) 展示 多表 JOIN + 聚合 + 窗口函数 的硬 SQL 能力 (面试作品集)
-- 运行: 由 analysis.py 自动调用; 也可在 sqlite/MySQL 客户端单独跑
-- ============================================================

-- 1. 月度 GMV 与订单量 (经营趋势) -> 驱动图 01
SELECT strftime('%Y-%m', o.order_purchase_timestamp) AS month,
       ROUND(SUM(oi.price + oi.freight_value), 2)     AS gmv,
       COUNT(DISTINCT o.order_id)                     AS orders
FROM olist_orders_dataset o
JOIN olist_order_items_dataset oi ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
GROUP BY month
ORDER BY month;

-- 2. 品类收入 (需翻译表映射英文品类) -> 驱动图 02
SELECT t.product_category_name_english AS product_category,
       ROUND(SUM(oi.price), 2)          AS revenue,
       COUNT(*)                         AS cnt
FROM olist_order_items_dataset oi
JOIN olist_products_dataset p        ON oi.product_id = p.product_id
JOIN product_category_name_translation t ON p.product_category_name = t.product_category_name
WHERE EXISTS (SELECT 1 FROM olist_orders_dataset o
              WHERE o.order_id = oi.order_id AND o.order_status = 'delivered')
GROUP BY 1
ORDER BY revenue DESC;

-- 3. 各州 (地区) 销售分布 -> 驱动图 03
SELECT c.customer_state AS country,
       COUNT(DISTINCT o.order_id) AS cnt,
       ROUND(AVG(oi.price), 2)    AS avg_price
FROM olist_orders_dataset o
JOIN olist_order_items_dataset oi ON o.order_id = oi.order_id
JOIN olist_customers_dataset c    ON o.customer_id = c.customer_id
WHERE o.order_status = 'delivered'
GROUP BY 1
ORDER BY cnt DESC;

-- 4. 评分分布 (服务质量) -> 驱动图 04
SELECT review_score,
       COUNT(*) AS cnt
FROM olist_order_reviews_dataset
GROUP BY 1
ORDER BY 1;

-- 5. 支付方式占比 -> 驱动图 05
SELECT payment_type,
       COUNT(*) AS cnt
FROM olist_order_payments_dataset
GROUP BY 1
ORDER BY cnt DESC;

-- 6. Top 客户 (高价值客户识别) -> 驱动图 06
SELECT o.customer_id,
       COUNT(*)                AS orders,
       ROUND(SUM(oi.price), 2) AS spending
FROM olist_orders_dataset o
JOIN olist_order_items_dataset oi ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
GROUP BY 1
ORDER BY spending DESC
LIMIT 10;

-- 7. (进阶) 各品类销售额累计占比 (窗口函数) -> 仅打印, 不出图
SELECT product_category,
       revenue,
       ROUND(SUM(revenue) OVER (ORDER BY revenue DESC)
             / SUM(revenue) OVER () * 100, 1) AS cum_pct
FROM (
    SELECT t.product_category_name_english AS product_category,
           SUM(oi.price) AS revenue
    FROM olist_order_items_dataset oi
    JOIN olist_products_dataset p ON oi.product_id = p.product_id
    JOIN product_category_name_translation t ON p.product_category_name = t.product_category_name
    WHERE EXISTS (SELECT 1 FROM olist_orders_dataset o
                  WHERE o.order_id = oi.order_id AND o.order_status = 'delivered')
    GROUP BY 1
);
