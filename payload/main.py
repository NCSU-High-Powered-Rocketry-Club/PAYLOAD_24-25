"""The main file which will be run on the Raspberry Pi. It will create the PayloadContext object
and run the main loop."""

import argparse
import time

from payload.constants import (
    ARDUINO_SERIAL_PORT,
    ARDUINO_BAUD_RATE,
    DIREWOLF_CONFIG_PATH,
    LOGS_PATH,
    MOCK_RECEIVER_INITIAL_DELAY,
    MOCK_RECEIVER_RECEIVE_DELAY,
    RECEIVER_BAUD_RATE,
    RECEIVER_SERIAL_PORT,
    STOP_MESSAGE,
    TRANSMIT_MESSAGE,
    TRANSMITTER_PIN,
)
from payload.data_handling.data_processor import IMUDataProcessor
from payload.data_handling.logger import Logger
from payload.hardware.imu import IMU
from payload.hardware.receiver import Receiver
from payload.hardware.transmitter import Transmitter
from payload.interfaces.base_imu import BaseIMU
from payload.interfaces.base_receiver import BaseReceiver
from payload.mock.display import FlightDisplay
from payload.mock.mock_imu import MockIMU
from payload.mock.mock_logger import MockLogger
from payload.mock.mock_receiver import MockReceiver
from payload.payload import PayloadContext
from payload.utils import arg_parser


def run_real_flight() -> None:
    """Entry point for the application to run the real flight. Entered when run with
    `uv run real` or `uvx --from git+... real`."""
    args = arg_parser()
    run_flight(args)


def run_mock_flight() -> None:
    """Entry point for the application to run the mock flight. Entered when run with
    `uvx --from git+... mock` or `uv run mock`."""
    args = arg_parser(mock_invocation=True)
    run_flight(args)


def run_flight(args: argparse.Namespace) -> None:
    mock_time_start = time.time()

    imu, logger, data_processor, transmitter, receiver = create_components(args)
    # Initialize the payload context and display
    payload = PayloadContext(imu, logger, data_processor, transmitter, receiver)
    flight_display = FlightDisplay(payload, mock_time_start, args)

    # Run the main flight loop
    run_flight_loop(payload, flight_display, args)


def create_components(
    args: argparse.Namespace,
) -> tuple[BaseIMU, Logger, IMUDataProcessor, Transmitter, BaseReceiver]:
    """
    Creates the system components needed for the payload system. Depending on its arguments, it
    will return either mock or real components.
    :param args: Command line arguments determining the configuration.
    :return: A tuple containing the IMU, Logger, and data processor objects
    """
    if args.mock:
        # Replace hardware with mock objects for mock replay
        imu = (
            IMU(ARDUINO_SERIAL_PORT, ARDUINO_BAUD_RATE)
            if args.real_imu
            else MockIMU(
                log_file_path=args.path,
            )
        )
        logger = MockLogger(LOGS_PATH, delete_log_file=not args.keep_log_file)
        transmitter = (
            Transmitter(TRANSMITTER_PIN, DIREWOLF_CONFIG_PATH) if args.real_transmitter else None
        )
        receiver = (
            Receiver(RECEIVER_SERIAL_PORT, RECEIVER_BAUD_RATE)
            if args.real_receiver
            else MockReceiver(
                MOCK_RECEIVER_INITIAL_DELAY, MOCK_RECEIVER_RECEIVE_DELAY, TRANSMIT_MESSAGE
            )
        )
    else:
        # Use real hardware components
        imu = IMU(ARDUINO_SERIAL_PORT, ARDUINO_BAUD_RATE)
        logger = Logger(LOGS_PATH)
        transmitter = Transmitter(TRANSMITTER_PIN, DIREWOLF_CONFIG_PATH)
        receiver = Receiver(RECEIVER_SERIAL_PORT, RECEIVER_BAUD_RATE)

    # Initialize data processing
    data_processor = IMUDataProcessor()
    return imu, logger, data_processor, transmitter, receiver


def run_flight_loop(
    payload: PayloadContext, flight_display: FlightDisplay, args: argparse.Namespace
) -> None:
    """
    Main flight control loop that runs until shutdown is requested or interrupted.
    :param payload: The payload context managing the state machine.
    :param flight_display: Display interface for flight data.
    :param args: Command line arguments determining the configuration.
    """
    try:
        payload.start()
        flight_display.start()
        while True:
            # Update the state machine
            payload.update()
            # Stop the replay when the data is exhausted
            if args.mock and (not args.real_imu and not payload.imu.is_running):
                break

    # handle user interrupt gracefully
    except KeyboardInterrupt:
        if args.mock:
            flight_display.end_mock_interrupted.set()
    except Exception as e:
        print(e)
        raise e from None
    else:  # This is run if we have landed and the program is not interrupted (see state.py)
        if args.mock:
            # Stop the mock replay naturally if not interrupted
            flight_display.end_mock_natural.set()
    finally:
        # Stop the display and payload
        flight_display.stop()
        payload.stop()


if __name__ == "__main__":
    args = arg_parser()
    run_flight(args)
