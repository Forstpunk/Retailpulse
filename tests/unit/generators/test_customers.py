from retailpulse.generators.customers import (
    generate_customers,
)


def test_customer_count():
    customers = list(
        generate_customers(
            count=1_000,
            seed=42,
        )
    )

    assert len(customers) == 1_000


def test_customer_ids_are_unique():
    customers = list(
        generate_customers(
            count=1_000,
            seed=42,
        )
    )

    customer_ids = [
        customer.customer_id
        for customer in customers
    ]

    assert len(customer_ids) == len(
        set(customer_ids)
    )


def test_customer_numbers_are_unique():
    customers = list(
        generate_customers(
            count=1_000,
            seed=42,
        )
    )

    customer_numbers = [
        customer.customer_number
        for customer in customers
    ]

    assert len(customer_numbers) == len(
        set(customer_numbers)
    )


def test_customer_emails_are_unique():
    customers = list(
        generate_customers(
            count=1_000,
            seed=42,
        )
    )

    emails = [
        customer.email
        for customer in customers
    ]

    assert len(emails) == len(set(emails))


def test_customer_status_is_valid():
    customers = list(
        generate_customers(
            count=1_000,
            seed=42,
        )
    )

    valid_statuses = {
        "ACTIVE",
        "INACTIVE",
        "BLOCKED",
    }

    assert all(
        customer.status in valid_statuses
        for customer in customers
    )


def test_customer_segment_is_valid():
    customers = list(
        generate_customers(
            count=1_000,
            seed=42,
        )
    )

    valid_segments = {
        "STANDARD",
        "PREMIUM",
        "VIP",
    }

    assert all(
        customer.customer_segment
        in valid_segments
        for customer in customers
    )


def test_generation_is_deterministic():
    first = list(
        generate_customers(
            count=1_000,
            seed=42,
        )
    )

    second = list(
        generate_customers(
            count=1_000,
            seed=42,
        )
    )

    assert first == second


def test_customer_segment_distribution():
    customers = list(
        generate_customers(
            count=10_000,
            seed=42,
        )
    )

    counts = {}

    for customer in customers:
        counts[customer.customer_segment] = (
            counts.get(
                customer.customer_segment,
                0,
            )
            + 1
        )

    total = len(customers)

    standard_ratio = (
        counts["STANDARD"] / total
    )

    premium_ratio = (
        counts["PREMIUM"] / total
    )

    vip_ratio = (
        counts["VIP"] / total
    )

    assert 0.70 <= standard_ratio <= 0.80
    assert 0.15 <= premium_ratio <= 0.25
    assert 0.02 <= vip_ratio <= 0.08