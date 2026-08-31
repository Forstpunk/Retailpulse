from collections.abc import Iterable

from psycopg import Connection


def copy_orders(
    connection: Connection,
    orders: Iterable,
) -> None:
    with connection.cursor() as cursor, cursor.copy(
        """
            COPY retail.orders (
                order_id,
                customer_id,
                store_id,
                order_channel,
                order_status,
                order_date,
                currency_code,
                subtotal_amount,
                discount_amount,
                tax_amount,
                shipping_amount,
                total_amount
            )
            FROM STDIN
            """
    ) as copy:
        for order in orders:
            copy.write_row(
                (
                    order.order_id,
                    order.customer_id,
                    order.store_id,
                    order.order_channel,
                    order.order_status,
                    order.order_date,
                    order.currency_code,
                    order.subtotal_amount,
                    order.discount_amount,
                    order.tax_amount,
                    order.shipping_amount,
                    order.total_amount,
                )
            )


def copy_order_items(
    connection: Connection,
    order_items: Iterable,
) -> None:
    with connection.cursor() as cursor, cursor.copy(
        """
            COPY retail.order_items (
                order_item_id,
                order_id,
                product_id,
                quantity,
                unit_price,
                discount_amount,
                tax_amount,
                line_total
            )
            FROM STDIN
            """
    ) as copy:
        for item in order_items:
            copy.write_row(
                (
                    item.order_item_id,
                    item.order_id,
                    item.product_id,
                    item.quantity,
                    item.unit_price,
                    item.discount_amount,
                    item.tax_amount,
                    item.line_total,
                )
            )

def copy_products(
    connection: Connection,
    products: Iterable,
) -> None:
    # ---------------------------------------------------------
    # 1. Create staging table
    #
    # IF NOT EXISTS + TRUNCATE, rather than a bare CREATE:
    # bootstrap_reference_data() calls this once per
    # generation batch without committing in between (the
    # whole bootstrap is one transaction), and ON COMMIT DROP
    # only drops the table at COMMIT, so a bare CREATE would
    # fail with "already exists" from the second batch on.
    # ---------------------------------------------------------
    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TEMP TABLE IF NOT EXISTS
                product_load_staging
            (LIKE retail.products INCLUDING DEFAULTS)
            ON COMMIT DROP
            """
        )

        cursor.execute(
            "TRUNCATE TABLE product_load_staging"
        )

    # ---------------------------------------------------------
    # 2. Bulk load into staging using PostgreSQL COPY
    # ---------------------------------------------------------
    with connection.cursor() as cursor, cursor.copy(
        """
            COPY product_load_staging (
                product_id,
                sku,
                product_name,
                category_id,
                supplier_id,
                unit_price,
                cost_price,
                status
            )
            FROM STDIN
            """
    ) as copy:
        for product in products:
            copy.write_row(
                (
                    product.product_id,
                    product.sku,
                    product.product_name,
                    product.category_id,
                    product.supplier_id,
                    product.unit_price,
                    product.cost_price,
                    product.status,
                )
            )

    # ---------------------------------------------------------
    # 3. Validate staging data
    # ---------------------------------------------------------
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT product_id
            FROM product_load_staging
            GROUP BY product_id
            HAVING COUNT(*) > 1
            LIMIT 1
            """
        )

        duplicate = cursor.fetchone()

        if duplicate is not None:
            raise ValueError(f"Duplicate product_id in load batch: {duplicate[0]}")

    # ---------------------------------------------------------
    # 4. Merge staging data into production table
    # ---------------------------------------------------------
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO retail.products (
                product_id,
                sku,
                product_name,
                category_id,
                supplier_id,
                unit_price,
                cost_price,
                status
            )
            SELECT
                product_id,
                sku,
                product_name,
                category_id,
                supplier_id,
                unit_price,
                cost_price,
                status
            FROM product_load_staging
            ON CONFLICT (product_id) DO NOTHING
            """
        )


def copy_customers(
    connection: Connection,
    customers: Iterable,
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TEMP TABLE IF NOT EXISTS
                customer_load_staging
            (LIKE retail.customers INCLUDING DEFAULTS)
            ON COMMIT DROP
            """
        )

        cursor.execute(
            "TRUNCATE TABLE customer_load_staging"
        )

    with connection.cursor() as cursor, cursor.copy(
        """
            COPY customer_load_staging (
                customer_id,
                customer_number,
                first_name,
                last_name,
                email,
                phone,
                city,
                state,
                country_code,
                customer_segment,
                date_of_birth,
                status
            )
            FROM STDIN
            """
    ) as copy:
        for customer in customers:
            copy.write_row(
                (
                    customer.customer_id,
                    customer.customer_number,
                    customer.first_name,
                    customer.last_name,
                    customer.email,
                    customer.phone,
                    customer.city,
                    customer.state,
                    customer.country_code,
                    customer.customer_segment,
                    customer.date_of_birth,
                    customer.status,
                )
            )

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT customer_id
            FROM customer_load_staging
            GROUP BY customer_id
            HAVING COUNT(*) > 1
            LIMIT 1
            """
        )

        duplicate = cursor.fetchone()

        if duplicate is not None:
            raise ValueError(
                f"Duplicate customer_id in load batch: {duplicate[0]}"
            )

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO retail.customers (
                customer_id,
                customer_number,
                first_name,
                last_name,
                email,
                phone,
                city,
                state,
                country_code,
                customer_segment,
                date_of_birth,
                status
            )
            SELECT
                customer_id,
                customer_number,
                first_name,
                last_name,
                email,
                phone,
                city,
                state,
                country_code,
                customer_segment,
                date_of_birth,
                status
            FROM customer_load_staging
            ON CONFLICT (customer_id) DO NOTHING
            """
        )