"""File which contains a few basic utility functions which can be reused in the project."""

import argparse
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import multiprocessing


def get_all_from_queue(self, *args, **kwargs) -> list:
    """Used to get all the items from a queue at once. Only relevant if you are running the mock
    replay on Windows, as the multiprocessing.Queue doesn't have a `get_many` method"""
    kwargs.pop("max_messages_to_get", None)  # Argument only used in the Linux version
    return [self.get(*args, **kwargs) for _ in range(self.qsize())]


def get_always_list(self, *args, **kwargs) -> list:
    """Used to get items from the queue, and always returns a list. Only relevant on Windows,
    as the multiprocessing.Queue doesn't have a `get_many` method"""
    fetched = self.get(*args, **kwargs)
    if isinstance(fetched, list):
        return fetched
    return [fetched]


def modify_multiprocessing_queue_windows(obj: "multiprocessing.Queue") -> None:
    """Initializes the multiprocessing queue on Windows by adding the missing methods from the
    faster_fifo library. Modifies `obj` in place.

    :param obj: The multiprocessing.Queue object to add the methods to.
    """
    obj.get_many = partial(get_always_list, obj)
    obj.put_many = obj.put


def convert_to_milliseconds(timestamp_str: str) -> int | None:
    """Converts seconds to milliseconds, if it isn't already in milliseconds."""
    try:
        # check if value is already in milliseconds:
        return int(timestamp_str)
    except ValueError:
        try:
            timestamp_float = float(timestamp_str)
            return int(timestamp_float * 1e3)  # return the value in milliseconds
        except ValueError:
            return None


def convert_to_seconds(timestamp: float) -> float | None:
    """Converts milliseconds to seconds"""
    return timestamp / 1e3


def convert_str_to_float(value: str) -> float | None:
    """Converts a value to a float, returning None if the conversion fails."""
    try:
        return float(value)  # Attempt to convert to float
    except (ValueError, TypeError):
        return None  # Return None if the conversion fails


def deadband(input_value: float, threshold: float) -> float:
    """
    Returns 0 if the input_value is within the deadband threshold.
    Otherwise, returns the input_value adjusted by the threshold.
    :param input_value: The value to apply the deadband to.
    :param threshold: The deadband threshold.
    :return: Adjusted input_value or 0 if within the deadband.
    """
    if abs(input_value) < threshold:
        return 0.0
    return input_value


def arg_parser(mock_invocation: bool = False) -> argparse.Namespace:
    """Handles the command line arguments for the main payload script.

    :param mock_invocation: Whether the application is running in mock mode from `uv run mock`.
    Defaults to False, to keep compatibility with the `python -m payload.main` invocation method.

    :return: The parsed arguments as a class with attributes.
    """

    parser = argparse.ArgumentParser(
        description="Configuration for the main payload script."
        "No arguments should be supplied when you are actually launching the rocket."
    )

    parser.add_argument(
        "-m",
        "--mock",
        help="Run in replay mode with mock data",
        action="store_true",
        default=mock_invocation,
    )

    parser.add_argument(
        "-l",
        "--keep-log-file",
        help="Keep the log file after the mock replay stops",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-f",
        "--fast-replay",
        help="Run the mock replay at full speed instead of in real time.",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-d",
        "--debug",
        help="Run the mock replay in debug mode. This will not "
        "print the flight data and allow you to inspect the values of your print() statements.",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-p",
        "--path",
        help="Define the pathname of flight data to use in mock replay.",
        type=Path,
        default=None,
    )

    args = parser.parse_args()

    # Check if the user has passed any options that are only available in mock replay mode:
    if any([args.keep_log_file, args.fast_replay, args.path]) and not args.mock:
        parser.error(
            "The, `--keep-log-file`, `--fast-replay`, and `--path` "
            "options are only available in mock replay mode. Please pass `-m` or `--mock` "
            "to run in mock replay mode."
        )

    return args
