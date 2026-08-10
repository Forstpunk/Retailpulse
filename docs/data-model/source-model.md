# RetailPulse Source Data Model

## System

RetailPulse Operational Database

## Database

PostgreSQL

## Schema

retail

## Purpose

The PostgreSQL database represents the operational source system for the
RetailPulse data platform.

The schema is intentionally OLTP-oriented and is not designed to serve
analytical workloads directly.

## Tables

| Table | Grain | Primary Key | CDC | Historical Tracking |
|---|---|---|---|---|
| customers | One row per customer | customer_id | Yes | SCD2 |
| products | One row per product | product_id | Yes | SCD1 |
| categories | One row per category | category_id | Yes | SCD1 |
| suppliers | One row per supplier | supplier_id | Yes | SCD2 |
| stores | One row per store | store_id | Yes | SCD2 |
| orders | One row per order | order_id | Yes | N/A |
| order_items | One row per order line | order_item_id | Yes | N/A |
| payments | One row per payment transaction | payment_id | Yes | N/A |
| returns | One row per return transaction | return_id | Yes | N/A |
| inventory | One row per store/product current state | inventory_id | Yes | N/A |
| promotions | One row per promotion | promotion_id | Yes | SCD2 |


## Key Relationships

customers 1:N orders

orders 1:N order_items

products 1:N order_items

orders 1:N payments

order_items 1:N returns

stores 1:N inventory

products 1:N inventory

categories 1:N products

suppliers 1:N products