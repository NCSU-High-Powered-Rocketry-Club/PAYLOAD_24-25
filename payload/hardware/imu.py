"""Module for interacting with the IMU (Inertial measurement unit) on the rocket."""

import contextlib
import multiprocessing

from payload.constants import (
    ESTIMATED_DESCRIPTOR_SET,
    MAX_QUEUE_SIZE,
    RAW_DESCRIPTOR_SET,
)
from payload.data_handling.imu_data_packet import (
    EstimatedDataPacket,
    IMUDataPacket,
    RawDataPacket,
)
from payload.hardware.base_imu import BaseIMU


class IMU(BaseIMU):
    """
    Represents the IMU on the rocket. It's used to get the current acceleration of the rocket.
    This is used to interact with the data collected by the BNO055

    It uses multiprocessing rather than threading to truly run in parallel with the main loop.
    We're doing this is because the IMU constantly polls data and can be slow, so it's better to
    run it in parallel.
    """

    def __init__(self, port: str) -> None:
        """
        Initializes the object that interacts with the physical IMU connected to the pi.
        :param port: the port that the IMU is connected to
        """
        # Shared Queue which contains the latest data from the IMU. The MAX_QUEUE_SIZE is there
        # to prevent memory issues. Realistically, the queue size never exceeds 50 packets when
        # it's being logged.
        data_queue = multiprocessing.Queue(maxsize=MAX_QUEUE_SIZE)
        # Starts the process that fetches data from the IMU
        data_fetch_process = multiprocessing.Process(
            target=self._query_imu_for_data_packets, args=(port,), name="IMU Process"
        )
        super().__init__(data_fetch_process, data_queue)

    # ------------------------ ALL METHODS BELOW RUN IN A SEPARATE PROCESS -------------------------
    @staticmethod
    def _initialize_packet(packet) -> IMUDataPacket | None:
        """
        Initialize an IMU data packet.
        :param packet: The data packet from the IMU.
        :return: An IMUDataPacket, or None if the packet is unrecognized.
        """
        # Extract the timestamp from the packet.
        timestamp = packet.collectedTimestamp().nanoseconds()

        # Initialize packet with the timestamp, determines if the packet is raw or estimated
        if packet.descriptorSet() == ESTIMATED_DESCRIPTOR_SET:
            return EstimatedDataPacket(timestamp)
        if packet.descriptorSet() == RAW_DESCRIPTOR_SET:
            return RawDataPacket(timestamp)
        return None

    @staticmethod
    def _process_data_point(
        data_point, channel: str, imu_data_packet: IMUDataPacket
    ) -> None:
        """
        Process an individual data point and set its value in the data packet object. Modifies
        `imu_data_packet` in place.
        :param data_point: The IMU data point containing the measurement.
        :param channel: The channel name of the data point.
        :param imu_data_packet: The data packet object to update.
        """
        # Handle special channels that represent quaternion data.
        if channel in {"estAttitudeUncertQuaternion", "estOrientQuaternion"}:
            # Convert quaternion data into a 4x1 matrix and set its components.
            matrix = data_point.as_Matrix()
            setattr(imu_data_packet, f"{channel}W", matrix.as_floatAt(0, 0))
            setattr(imu_data_packet, f"{channel}X", matrix.as_floatAt(0, 1))
            setattr(imu_data_packet, f"{channel}Y", matrix.as_floatAt(0, 2))
            setattr(imu_data_packet, f"{channel}Z", matrix.as_floatAt(0, 3))
        else:
            # Set other data points directly as attributes in the data packet.
            setattr(imu_data_packet, channel, data_point.as_float())

        # Check if the data point is invalid and update the invalid fields list.
        if not data_point.valid():
            if imu_data_packet.invalid_fields is None:
                imu_data_packet.invalid_fields = []
            imu_data_packet.invalid_fields.append(channel)

    @staticmethod
    def _process_packet_data(packet, imu_data_packet: IMUDataPacket) -> None:
        """
        Process the data points in the packet and update the data packet object. Modifies
        `imu_data_packet` in place.
        :param packet: The IMU data packet containing multiple data points.
        :param imu_data_packet: The initialized data packet object to populate.
        """
        # Iterate through each data point in the packet.
        for data_point in packet.data():
            # Extract the channel name of the data point.
            channel = data_point.channelName()

            # Check if the channel is relevant for the data packet, we check for quaternions
            # separately because the IMU sends them over as a matrix, but we store each of them
            # individually as fields.
            if hasattr(imu_data_packet, channel) or "Quaternion" in channel:
                # Process and set the data point value in the data packet.
                IMU._process_data_point(data_point, channel, imu_data_packet)

    def _fetch_data_loop(self) -> None:
        """
        Continuously fetch data packets from the IMU and process them.
        :param port: The serial port to connect to the IMU.
        """
        while self.is_running:
            # Retrieve data packets from the IMU.
            packets = ["placeholder"]
            for packet in packets:
                # Initialize the appropriate data packet.
                imu_data_packet = IMU._initialize_packet(packet)
                if imu_data_packet is None:
                    # Skip unrecognized packets.
                    continue

                # Process the packet's data and populate the data packet object.
                IMU._process_packet_data(packet, imu_data_packet)

                # Add the processed data packet to the shared queue.
                self._data_queue.put(imu_data_packet)

    def _query_imu_for_data_packets(self, port: str) -> None:
        """
        The loop that fetches data from the IMU. It runs in parallel with the main loop.
        :param port: the port that the IMU is connected to
        """
        with contextlib.suppress(KeyboardInterrupt):
            self._fetch_data_loop(port)
