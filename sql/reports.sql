/*
a) COUNT(*), total revenue, avg order value (join orders to products).
COUNT(*) | total_revenue | avg_order_value
--------------------------------------------------
180 | 99860.2 | 554.78
*/
SELECT 
    COUNT(*), 
    ROUND(SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS total_revenue, 
    ROUND(SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)) / COUNT(*), 2) AS avg_order_value 
FROM orders o 
JOIN products p ON o.product_id = p.product_id;

/*
b) COUNT(*), COUNT(rating) and their difference.
COUNT(*) | COUNT(rating) | difference
--------------------------------------------------
180 | 165 | 15
*/
SELECT 
    COUNT(*), 
    COUNT(rating), 
    COUNT(*) - COUNT(rating) AS difference 
FROM orders;

/*
c) LEFT JOIN customers to orders, GROUP BY customer, HAVING COUNT(order_id)=0.
customer_id | name
--------------------------------------------------
C045 | Vihaan
*/
SELECT c.customer_id, c.name 
FROM customers c 
LEFT JOIN orders o ON c.customer_id = o.customer_id 
GROUP BY c.customer_id 
HAVING COUNT(o.order_id) = 0;

/*
c) Second independent query using NOT IN (SELECT DISTINCT customer_id FROM orders).
customer_id | name
--------------------------------------------------
C045 | Vihaan
*/
SELECT customer_id, name 
FROM customers 
WHERE customer_id NOT IN (SELECT DISTINCT customer_id FROM orders);

/*
d) Join orders to customers, GROUP BY city: total_orders, returned_orders, return_rate_pct
city | total_orders | returned_orders | return_rate_pct
--------------------------------------------------
Jaipur | 19 | 8 | 42.1
Lucknow | 49 | 15 | 30.6
Bangalore | 33 | 8 | 24.2
*/
SELECT 
    c.city, 
    COUNT(o.order_id) AS total_orders, 
    SUM(o.returned) AS returned_orders, 
    ROUND(SUM(o.returned) * 100.0 / COUNT(o.order_id), 1) AS return_rate_pct 
FROM orders o 
JOIN customers c ON o.customer_id = c.customer_id 
GROUP BY c.city 
HAVING return_rate_pct > 20 
ORDER BY return_rate_pct DESC;

/*
e) Join orders, products, customers; GROUP BY customer; total_spend; ORDER BY total_spend DESC, customer_id ASC LIMIT 5.
customer_id | name | total_spend
--------------------------------------------------
C043 | Reyansh | 12920.0
C026 | Isha | 8371.6
C008 | Meera | 4564.6
C011 | Arjun | 4111.0
C042 | Sanya | 3785.0
*/
-- The tie-break ensures consistent sorting if multiple customers have the exact same total_spend.
SELECT 
    c.customer_id, 
    c.name, 
    ROUND(SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS total_spend 
FROM orders o 
JOIN products p ON o.product_id = p.product_id 
JOIN customers c ON o.customer_id = c.customer_id 
GROUP BY c.customer_id 
ORDER BY total_spend DESC, c.customer_id ASC 
LIMIT 5;

/*
e) LIMIT 3 OFFSET 2
customer_id | name | total_spend
--------------------------------------------------
C008 | Meera | 4564.6
C011 | Arjun | 4111.0
C042 | Sanya | 3785.0
*/
SELECT 
    c.customer_id, 
    c.name, 
    ROUND(SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS total_spend 
FROM orders o 
JOIN products p ON o.product_id = p.product_id 
JOIN customers c ON o.customer_id = c.customer_id 
GROUP BY c.customer_id 
ORDER BY total_spend DESC, c.customer_id ASC 
LIMIT 3 OFFSET 2;

/*
f) Join orders, products, customers; GROUP BY category; order_count and category_revenue DESC.
category | order_count | category_revenue
--------------------------------------------------
Haircare | 54 | 44956.1
Skincare | 60 | 27346.0
Babycare | 30 | 16805.0
PersonalCare | 36 | 10753.1
*/
SELECT 
    p.category, 
    COUNT(o.order_id) AS order_count, 
    ROUND(SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS category_revenue 
FROM orders o 
JOIN products p ON o.product_id = p.product_id 
JOIN customers c ON o.customer_id = c.customer_id 
GROUP BY p.category 
ORDER BY category_revenue DESC;

/*
g) Customers whose name LIKE 'A%'
customer_id | name
--------------------------------------------------
C001 | Aarav
C003 | Aditi
C004 | Ananya
C011 | Arjun
C021 | Aryan
C030 | Anika
C031 | Aditya
C036 | Aisha
C041 | Ayaan
C044 | Aria
*/
SELECT customer_id, name 
FROM customers 
WHERE name LIKE 'A%';

/*
h) SELECT DISTINCT acquisition_source.
acquisition_source
--------------------------------------------------
Ad
Organic
Referral
Social
*/
SELECT DISTINCT acquisition_source 
FROM customers 
ORDER BY acquisition_source;

/*
i) ALTER TABLE customers ADD COLUMN loyalty_tier VARCHAR(10);
   UPDATE customers SET loyalty_tier = CASE WHEN city_tier = 1 THEN 'Gold' ELSE 'Silver' END;
   SELECT loyalty_tier, COUNT(*) FROM customers GROUP BY loyalty_tier;
loyalty_tier | COUNT(*)
--------------------------------------------------
Gold | 28
Silver | 17
*/
ALTER TABLE customers ADD COLUMN loyalty_tier VARCHAR(10);
UPDATE customers SET loyalty_tier = CASE WHEN city_tier = 1 THEN 'Gold' ELSE 'Silver' END;
SELECT loyalty_tier, COUNT(*) FROM customers GROUP BY loyalty_tier;
