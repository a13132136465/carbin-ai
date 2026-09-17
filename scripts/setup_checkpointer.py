from persistence.checkpointer import (
    get_checkpointer,
)


def main():

    print("Setting up LangGraph " "PostgreSQL checkpointer...")

    checkpointer = get_checkpointer()

    checkpointer.setup()

    print("Checkpoint tables created.")


if __name__ == "__main__":
    main()
