from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from random import Random


@dataclass(frozen=True)
class Customer:
    customer_id: int
    customer_number: str
    first_name: str
    last_name: str
    email: str
    phone: str
    city: str
    state: str
    country_code: str
    customer_segment: str
    date_of_birth: date
    status: str


FIRST_NAMES = [
    "Aarav",
    "Aditi",
    "Arjun",
    "Ananya",
    "Kabir",
    "Meera",
    "Rohan",
    "Ishita",
    "Vikram",
    "Priya",
    "Rahul",
    "Sneha",
    "Karan",
    "Neha",
    "Aditya",
]


LAST_NAMES = [
    "Sharma",
    "Patel",
    "Reddy",
    "Iyer",
    "Nair",
    "Mehta",
    "Kapoor",
    "Verma",
    "Rao",
    "Singh",
    "Gupta",
    "Joshi",
]


CUSTOMER_LOCATIONS = [
    ("Bengaluru", "Karnataka", "IN"),
    ("Mumbai", "Maharashtra", "IN"),
    ("Delhi", "Delhi", "IN"),
    ("Hyderabad", "Telangana", "IN"),
    ("Chennai", "Tamil Nadu", "IN"),
    ("Pune", "Maharashtra", "IN"),
    ("Kolkata", "West Bengal", "IN"),
    ("Ahmedabad", "Gujarat", "IN"),
]


CUSTOMER_SEGMENTS = [
    "STANDARD",
    "PREMIUM",
    "VIP",
]


SEGMENT_WEIGHTS = [
    0.75,
    0.20,
    0.05,
]


def generate_customers(
    count: int,
    seed: int,
) -> Iterator[Customer]:
    """
    Generate deterministic synthetic customers lazily.

    The function yields one Customer at a time rather than
    constructing the entire dataset in memory.

    Parameters
    ----------
    count:
        Number of customers to generate.

    seed:
        Seed used to make generation deterministic.

    Yields
    ------
    Customer
        A generated customer record.
    """

    if count < 0:
        raise ValueError("count cannot be negative")

    rng = Random(seed)

    for customer_id in range(1, count + 1):
        first_name = rng.choice(FIRST_NAMES)
        last_name = rng.choice(LAST_NAMES)

        city, state, country_code = rng.choice(
            CUSTOMER_LOCATIONS
        )

        customer_segment = rng.choices(
            CUSTOMER_SEGMENTS,
            weights=SEGMENT_WEIGHTS,
            k=1,
        )[0]

        date_of_birth = date(
            rng.randint(1960, 2005),
            rng.randint(1, 12),
            rng.randint(1, 28),
        )

        email = (
            f"{first_name.lower()}."
            f"{last_name.lower()}."
            f"{customer_id}"
            "@example.com"
        )

        phone = f"+919{customer_id:09d}"

        yield Customer(
            customer_id=customer_id,
            customer_number=f"CUST-{customer_id:08d}",
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            city=city,
            state=state,
            country_code=country_code,
            customer_segment=customer_segment,
            date_of_birth=date_of_birth,
            status="ACTIVE",
        )