CREATE INDEX idx_orders_customer_id
    ON retail.orders(customer_id);

CREATE INDEX idx_orders_store_id
    ON retail.orders(store_id);

CREATE INDEX idx_orders_order_date
    ON retail.orders(order_date);

CREATE INDEX idx_orders_updated_at
    ON retail.orders(updated_at);

CREATE INDEX idx_order_items_order_id
    ON retail.order_items(order_id);

CREATE INDEX idx_order_items_product_id
    ON retail.order_items(product_id);

CREATE INDEX idx_payments_order_id
    ON retail.payments(order_id);

CREATE INDEX idx_payments_updated_at
    ON retail.payments(updated_at);

CREATE INDEX idx_returns_order_item_id
    ON retail.returns(order_item_id);

CREATE INDEX idx_inventory_store_product
    ON retail.inventory(store_id, product_id);

CREATE INDEX idx_inventory_updated_at
    ON retail.inventory(updated_at);

CREATE INDEX idx_customers_updated_at
    ON retail.customers(updated_at);

CREATE INDEX idx_products_updated_at
    ON retail.products(updated_at);

CREATE INDEX idx_stores_updated_at
    ON retail.stores(updated_at);