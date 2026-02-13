from dotenv import load_dotenv

from skills import *


def main():
    load_dotenv()

    # Choose which function to test/run
    # record_and_add_task()
    aggregate_and_email_tasks()


if __name__ == "__main__":
    main()
