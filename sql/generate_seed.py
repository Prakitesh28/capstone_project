import csv
from pathlib import Path

data_dir = Path('../data')
out_file = Path('seed_data.sql')

with open(out_file, 'w', encoding='utf-8') as f:
    f.write('PRAGMA foreign_keys = ON;\n\n')

    # Customers
    with open(data_dir / 'customers.csv', 'r', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        f.write('-- Customers\n')
        for row in reader:
            f.write(f"INSERT INTO customers (customer_id, name, city, city_tier, signup_date, acquisition_source) VALUES ('{row['customer_id']}', '{row['name']}', '{row['city']}', {row['city_tier']}, '{row['signup_date']}', '{row['acquisition_source']}');\n")
    
    # Products
    f.write('\n-- Products\n')
    with open(data_dir / 'products.csv', 'r', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            f.write(f"INSERT INTO products (product_id, product_name, category, price) VALUES ('{row['product_id']}', '{row['product_name']}', '{row['category']}', {row['price']});\n")
            
    # Orders
    f.write('\n-- Orders\n')
    with open(data_dir / 'orders.csv', 'r', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            discount = row['discount_pct']
            rating = row['rating']
            disc_val = discount if discount != '' else 'NULL'
            rate_val = rating if rating != '' else 'NULL'
            f.write(f"INSERT INTO orders (order_id, customer_id, product_id, order_date, quantity, discount_pct, payment_method, rating, returned) VALUES ('{row['order_id']}', '{row['customer_id']}', '{row['product_id']}', '{row['order_date']}', {row['quantity']}, {disc_val}, '{row['payment_method']}', {rate_val}, {row['returned']});\n")
