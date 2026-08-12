# RetailPulse Data Dictionary

## Key Terminology

### Business Key

A key that identifies a business entity in the source domain.

Examples:

- customer_id
- product_id
- store_id
- order_id

### Surrogate Key

A warehouse-generated key used to uniquely identify a dimensional record.

Examples:

- customer_sk
- product_sk
- store_sk

### Grain

The level of detail represented by one row in a dataset.

### CDC

Change Data Capture.

The process of identifying inserts, updates and deletes from a source system
and delivering those changes downstream.

### SCD Type 1

Historical values are overwritten.

### SCD Type 2

Historical versions are retained using effective dates and current-record
indicators.