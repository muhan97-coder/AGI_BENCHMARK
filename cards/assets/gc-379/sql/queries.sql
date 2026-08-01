\timing on
-- gc-379 SEALED query workload. Do not modify this file.
SELECT count(*), sum(amount) FROM orders WHERE status = 'refunded';
SELECT customer_id, sum(amount) AS total
  FROM orders
 WHERE order_date BETWEEN date '2024-06-01' AND date '2024-06-07'
 GROUP BY customer_id ORDER BY total DESC LIMIT 10;
SELECT c.region_id, sum(o.amount)
  FROM orders o JOIN customers c ON c.id = o.customer_id
 WHERE o.product_id = 512
 GROUP BY c.region_id;
SELECT * FROM orders WHERE customer_id = 4242 ORDER BY order_date DESC LIMIT 5;
SELECT count(*) FROM orders WHERE amount > 495;
