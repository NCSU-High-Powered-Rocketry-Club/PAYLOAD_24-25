import serial
import time
import threading
import logging
import math
import csv
from enum import Enum, auto

from .shared.state import SensorState, FlightStats

class LaunchState(Enum):
    STANDBY = auto()
    ARMED = auto()
    LANDED = auto()

class PayloadSystem:
    LOG_FILENAME = "payload.log"
    LOG_INTERVAL = 0.1
    TX_INTERVAL = 0.5
    MINIMUM_ARM_ACCEL = 50  # m/s^2
    MAXIMUM_REST_ACCEL = 0.4  # m/s^2
    MAXIMUM_REST_ALT = 2

    def __init__(self, port: str, baudrate: int = 115200):
        self.setup_logger()
        logging.debug("Initializing payload...")

        self.running = True
        self.state = LaunchState.STANDBY
        self.init_time = time.time()
        self.last_log_time = time.time()
        self.last_tx_time = time.time()
        self.data = SensorState()
        self.stats = FlightStats()

        # Initialize serial connection to Adafruit Feather
        self.serial_connection = serial.Serial(port, baudrate, timeout=1)

        self.sensor_thread = threading.Thread(target=self.read_serial_data)
        logging.debug("Starting serial data read thread...")
        self.sensor_thread.start()

    def setup_logger(self):
        logging.basicConfig(
            handlers=[logging.FileHandler(self.LOG_FILENAME), logging.StreamHandler()],
            level=logging.DEBUG,
            format="[%(asctime)s] %(message)s",
            datefmt="%m/%d/%Y %I:%M:%S %p",
        )

    def read_serial_data(self):
        while self.running:
            if self.serial_connection.in_waiting > 0:
                line = self.serial_connection.readline().decode('utf-8').strip()
                self.parse_data(line)
            time.sleep(0.05)  # Adjust the sleep for your needs

    def parse_data(self, line):
        try:
            # Parse the data assuming a specific structure
            # Example: "Temp: 25.3 °C, Pressure: 101325 Pa, Accel: 0.1, 0.2, 9.8; ..."
            data_fields = line.split(',')
            for field in data_fields:
                key, value = field.split(':')
                key, value = key.strip(), value.strip()

                if "Temp" in key:
                    self.data.temperature = float(value.split()[0])
                elif "Pressure" in key:
                    self.data.pressure = float(value.split()[0])
                elif "Accel" in key:
                    x, y, z = map(float, value.split())
                    self.data.acceleration = (x, y, z)
                elif "Gyro" in key:
                    x, y, z = map(float, value.split())
                    self.data.gyroscope = (x, y, z)
                elif "Mag" in key:
                    x, y, z = map(float, value.split())
                    self.data.magnetic_field = (x, y, z)
                elif "Quat" in key:
                    i, j, k, real = map(float, value.split())
                    self.data.quaternion = (i, j, k, real)
                elif "Lat" in key:
                    self.data.latitude = float(value)
                elif "Lon" in key:
                    self.data.longitude = float(value)
                elif "Alt" in key:
                    self.data.altitude = float(value)

            self.update_stats()
            self.log_data()

        except ValueError as e:
            logging.warning(f"Data parsing error: {e}")

    def update_stats(self):
        if self.data.altitude > self.stats.max_altitude:
            self.stats.max_altitude = self.data.altitude
        if self.data.temperature > self.stats.max_temperature:
            self.stats.max_temperature = self.data.temperature

        magnitude = math.sqrt(sum(axis**2 for axis in self.data.acceleration))
        if magnitude > self.stats.max_acceleration:
            self.stats.max_acceleration = magnitude

    def log_data(self):
        if (time.time() - self.last_log_time) >= self.LOG_INTERVAL:
            logging.info(str(self.data))
            self.last_log_time = time.time()

        with open('CSVLogData.csv', 'w', newline=' ') as csvfile:
            writer = csv.writer(csvfile, delimeter=' ')
            writer.writerow(
                self.data.temperature,
                self.data.pressure,
                self.data.acceleration,
                self.data.gyroscope,
                self.data.magnetic_field,
                self.data.quaternion,
                self.data.latitude,
                self.data.longitude,
                self.data.altitude
            )

    def shutdown(self):
        self.running = False
        self.serial_connection.close()
        self.sensor_thread.join()