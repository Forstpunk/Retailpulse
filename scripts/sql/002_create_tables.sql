CREATE TABLE retail.categories (
    category_id          BIGINT PRIMARY KEY,
    category_name        VARCHAR(100) NOT NULL,
    parent_category_id   BIGINT,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_category_parent
        FOREIGN KEY (parent_category_id)
        REFERENCES retail.categories(category_id)
);


CREATE TABLE retail.suppliers (
    supplier_id      BIGINT PRIMARY KEY,
    supplier_name    VARCHAR(200) NOT NULL,
    country_code     CHAR(2) NOT NULL,
    status           VARCHAR(30) NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_supplier_status
        CHECK (status IN ('ACTIVE', 'INACTIVE', 'SUSPENDED'))
);


CREATE TABLE retail.products (
    product_id        BIGINT PRIMARY KEY,
    sku               VARCHAR(50) NOT NULL UNIQUE,
    product_name      VARCHAR(255) NOT NULL,
    category_id       BIGINT NOT NULL,
    supplier_id       BIGINT,
    unit_price        NUMERIC(12,2) NOT NULL,
    cost_price        NUMERIC(12,2) NOT NULL,
    status            VARCHAR(30) NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_product_category
        FOREIGN KEY (category_id)
        REFERENCES retail.categories(category_id),

    CONSTRAINT fk_product_supplier
        FOREIGN KEY (supplier_id)
        REFERENCES retail.suppliers(supplier_id),

    CONSTRAINT chk_product_price
        CHECK (unit_price >= 0),

    CONSTRAINT chk_product_cost
        CHECK (cost_price >= 0),

    CONSTRAINT chk_product_status
        CHECK (status IN ('ACTIVE', 'INACTIVE', 'DISCONTINUED'))
);


CREATE TABLE retail.stores (
    store_id          BIGINT PRIMARY KEY,
    store_code        VARCHAR(30) NOT NULL UNIQUE,
    store_name        VARCHAR(200) NOT NULL,
    city              VARCHAR(100) NOT NULL,
    state             VARCHAR(100) NOT NULL,
    country_code      CHAR(2) NOT NULL,
    region            VARCHAR(100) NOT NULL,
    store_type        VARCHAR(50) NOT NULL,
    opened_date       DATE NOT NULL,
    status            VARCHAR(30) NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_store_status
        CHECK (status IN ('OPEN', 'CLOSED', 'TEMPORARILY_CLOSED')),

    CONSTRAINT chk_store_type
        CHECK (store_type IN ('RETAIL', 'WAREHOUSE', 'OUTLET'))
);


CREATE TABLE retail.customers (
    customer_id BIGINT PRIMARY KEY,
    customer_number VARCHAR(30) NOT NULL UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(30),
    city VARCHAR(100),
    state VARCHAR(100),
    country_code CHAR(2),
    customer_segment VARCHAR(50) NOT NULL,
    date_of_birth DATE,
    status VARCHAR(30) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_customer_segment
        CHECK (customer_segment IN ('STANDARD', 'PREMIUM', 'VIP')),

    CONSTRAINT chk_customer_status
        CHECK (status IN ('ACTIVE', 'INACTIVE', 'BLOCKED'))
);


CREATE TABLE retail.orders (
    order_id          BIGINT PRIMARY KEY,
    customer_id       BIGINT NOT NULL,
    store_id          BIGINT,
    order_channel     VARCHAR(30) NOT NULL,
    order_status      VARCHAR(30) NOT NULL,
    order_date        TIMESTAMPTZ NOT NULL,
    currency_code     CHAR(3) NOT NULL,
    subtotal_amount   NUMERIC(14,2) NOT NULL,
    discount_amount   NUMERIC(14,2) NOT NULL DEFAULT 0,
    tax_amount        NUMERIC(14,2) NOT NULL DEFAULT 0,
    shipping_amount   NUMERIC(14,2) NOT NULL DEFAULT 0,
    total_amount      NUMERIC(14,2) NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_order_customer
        FOREIGN KEY (customer_id)
        REFERENCES retail.customers(customer_id),

    CONSTRAINT fk_order_store
        FOREIGN KEY (store_id)
        REFERENCES retail.stores(store_id),

    CONSTRAINT chk_order_channel
        CHECK (order_channel IN (
            'STORE',
            'WEB',
            'MOBILE',
            'MARKETPLACE'
        )),

    CONSTRAINT chk_order_status
        CHECK (order_status IN (
            'CREATED',
            'CONFIRMED',
            'PROCESSING',
            'SHIPPED',
            'DELIVERED',
            'CANCELLED',
            'RETURNED'
        ))
);


CREATE TABLE retail.order_items (
    order_item_id     BIGINT PRIMARY KEY,
    order_id          BIGINT NOT NULL,
    product_id        BIGINT NOT NULL,
    quantity          INTEGER NOT NULL,
    unit_price        NUMERIC(12,2) NOT NULL,
    discount_amount   NUMERIC(12,2) NOT NULL DEFAULT 0,
    tax_amount        NUMERIC(12,2) NOT NULL DEFAULT 0,
    line_total        NUMERIC(14,2) NOT NULL,

    created_at        TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_order_item_order
        FOREIGN KEY (order_id)
        REFERENCES retail.orders(order_id),

    CONSTRAINT fk_order_item_product
        FOREIGN KEY (product_id)
        REFERENCES retail.products(product_id),

    CONSTRAINT chk_order_item_quantity
        CHECK (quantity > 0),

    CONSTRAINT chk_order_item_unit_price
        CHECK (unit_price >= 0)
);


CREATE TABLE retail.payments (
    payment_id       BIGINT PRIMARY KEY,
    order_id         BIGINT NOT NULL,
    payment_method   VARCHAR(30) NOT NULL,
    payment_status   VARCHAR(30) NOT NULL,
    amount           NUMERIC(14,2) NOT NULL,
    transaction_ref  VARCHAR(100) UNIQUE,
    payment_date     TIMESTAMPTZ NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_payment_order
        FOREIGN KEY (order_id)
        REFERENCES retail.orders(order_id),

    CONSTRAINT chk_payment_method
        CHECK (payment_method IN (
            'CARD',
            'UPI',
            'NET_BANKING',
            'WALLET',
            'CASH',
            'COD'
        )),

    CONSTRAINT chk_payment_status
        CHECK (payment_status IN (
            'PENDING',
            'AUTHORIZED',
            'CAPTURED',
            'FAILED',
            'REFUNDED'
        )),

    CONSTRAINT chk_payment_amount
        CHECK (amount >= 0)
);


CREATE TABLE retail.returns (
    return_id          BIGINT PRIMARY KEY,
    order_item_id      BIGINT NOT NULL,
    customer_id        BIGINT NOT NULL,
    return_quantity    INTEGER NOT NULL,
    return_reason      VARCHAR(100) NOT NULL,
    return_status      VARCHAR(30) NOT NULL,
    return_date        TIMESTAMPTZ NOT NULL,
    refund_amount      NUMERIC(14,2) NOT NULL,

    created_at         TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_return_order_item
        FOREIGN KEY (order_item_id)
        REFERENCES retail.order_items(order_item_id),

    CONSTRAINT fk_return_customer
        FOREIGN KEY (customer_id)
        REFERENCES retail.customers(customer_id),

    CONSTRAINT chk_return_quantity
        CHECK (return_quantity > 0),

    CONSTRAINT chk_return_status
        CHECK (return_status IN (
            'REQUESTED',
            'APPROVED',
            'REJECTED',
            'COMPLETED'
        ))
);


CREATE TABLE retail.inventory (
    inventory_id       BIGINT PRIMARY KEY,
    store_id           BIGINT NOT NULL,
    product_id         BIGINT NOT NULL,
    quantity_on_hand   INTEGER NOT NULL,
    quantity_reserved  INTEGER NOT NULL DEFAULT 0,
    reorder_level      INTEGER NOT NULL DEFAULT 0,
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_inventory_store
        FOREIGN KEY (store_id)
        REFERENCES retail.stores(store_id),

    CONSTRAINT fk_inventory_product
        FOREIGN KEY (product_id)
        REFERENCES retail.products(product_id),

    CONSTRAINT chk_inventory_quantity
        CHECK (quantity_on_hand >= 0),

    CONSTRAINT chk_inventory_reserved
        CHECK (quantity_reserved >= 0)
);


CREATE TABLE retail.promotions (
    promotion_id       BIGINT PRIMARY KEY,
    promotion_code     VARCHAR(50) NOT NULL UNIQUE,
    promotion_name     VARCHAR(200) NOT NULL,
    discount_type      VARCHAR(30) NOT NULL,
    discount_value     NUMERIC(12,2) NOT NULL,
    start_date         TIMESTAMPTZ NOT NULL,
    end_date           TIMESTAMPTZ NOT NULL,
    status              VARCHAR(30) NOT NULL,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_promotion_discount_type
        CHECK (discount_type IN (
            'PERCENTAGE',
            'FIXED_AMOUNT'
        )),

    CONSTRAINT chk_promotion_status
        CHECK (status IN (
            'SCHEDULED',
            'ACTIVE',
            'EXPIRED',
            'CANCELLED'
        )),

    CONSTRAINT chk_promotion_dates
        CHECK (end_date > start_date)
);