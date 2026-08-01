-- gc-379 SEALED dataset seed. Do not modify this file.
-- Deterministic pseudo-random dataset: ~1.5M orders, 50k customers, no indexes.
SELECT setseed(0.42);
CREATE TABLE customers AS
SELECT g AS id,
       'cust_' || g AS name,
       (random() * 50)::int AS region_id,
       (random() * 1000)::numeric(10,2) AS credit
FROM generate_series(1, 50000) g;

SELECT setseed(0.137);
CREATE TABLE orders AS
SELECT g AS id,
       1 + (random() * 49999)::int AS customer_id,
       date '2024-01-01' + (random() * 365)::int AS order_date,
       (random() * 500)::numeric(10,2) AS amount,
       (random() * 999)::int AS product_id,
       CASE WHEN random() < 0.02 THEN 'refunded' ELSE 'settled' END AS status
FROM generate_series(1, 1500000) g;
