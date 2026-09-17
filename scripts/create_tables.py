from database.connection import (
    Base,
    engine,
)

from database.models import CarbonAudit


def main():

    print(
        "Creating CarbonAI business tables..."
    )

    Base.metadata.create_all(
        bind=engine
    )

    print(
        "Business tables created."
    )


if __name__ == "__main__":
    main()