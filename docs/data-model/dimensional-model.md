# RetailPulse Dimensional Model

## Business Processes

The platform will model:

1. Sales
2. Returns
3. Inventory
4. Payments
5. Fulfillment

## Dimensions

- dim_customer
- dim_product
- dim_category
- dim_store
- dim_supplier
- dim_promotion
- dim_date
- dim_channel

## Facts

- fact_sales
- fact_returns
- fact_inventory
- fact_payments
- fact_fulfillment

## Fact Sales Grain

One row per product line sold in an order.

## Fact Returns Grain

One row per returned order line transaction.

## Fact Inventory Grain

One row per inventory movement for a product at a store at a point in time.

## Fact Payments Grain

One row per payment transaction.

## Fact Fulfillment Grain

One row per fulfillment/shipping event associated with an order line.