from datetime import date

from retailpulse.analytics.generators.date_generator import (
    generate_date_dimension,
)
from retailpulse.analytics.loaders.date_loader import (
    load_dates,
)
from retailpulse.common.database import (
    get_connection,
)


def main() -> None:

    dates = generate_date_dimension(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
    )

    with get_connection() as connection:

        loaded = load_dates(
            connection,
            dates,
        )

    print(
        f"Processed {loaded} dates."
    )


if __name__ == "__main__":
    main()