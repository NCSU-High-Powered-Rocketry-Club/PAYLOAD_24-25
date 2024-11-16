import argparse
import serial
import time
import datetime
import logging
import json
import csv
import os  # For directory management
from enum import Enum, auto

msg = "Subscale HPRC Payload Program for 2024-2025."


class LaunchState(Enum):
    STANDBY = auto()
    ARMED = auto()
    LANDED = auto()


class SubscaleSystem:
    LOG_FILENAME = "subscale.log"
    LOG_INTERVAL = 0.1
    TX_INTERVAL = 0.5
    MINIMUM_ARM_ACCEL = 50  # m/s^2
    MAXIMUM_REST_ACCEL = 0.4  # m/s^2
    MAXIMUM_REST_ALT = 2
    LOG_DIR = "/home/pi/Payload-2024-2025/logs"  # Directory for logs

    def __init__(self, port: str, baudrate: int = 115200):
        self.setup_logger()
        logging.debug("Initializing subscale payload...")

        # Prompt for calibration data
        self.sea_level_pressure = float(input("Enter sea-level pressure (P0) in Pa (default 101325 Pa): ") or 101325)

        self.running = True
        self.state = LaunchState.STANDBY
        self.init_time = time.time()
        self.last_log_time = time.time()
        self.last_tx_time = time.time()

        # Initialize sensor state
        self.data = {
            "accel": {"x": 0.0, "y": 0.0, "z": 0.0},
            "gyro": {"x": 0.0, "y": 0.0, "z": 0.0},
            "quat": {"i": 0.0, "j": 0.0, "k": 0.0, "real": 1.0},
            "magn": {"x": 0.0, "y": 0.0, "z": 0.0},  # Fixed `mag` handling
            "gps": {"lat": None, "lon": None, "alt": None},
            "voltage": 0.0,
            "temperature": 0.0,
            "pressure": 0.0,
            "altitude": None,  # Arduino-provided altitude
        }

        # Initialize serial connection to Adafruit Feather
        self.serial_connection = serial.Serial(port, baudrate, timeout=1)

    def setup_logger(self):
        # Ensure the logs directory exists
        os.makedirs(self.LOG_DIR, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.filename = os.path.join(self.LOG_DIR, f"FlightLog_{timestamp}.csv")

        print("Creating file " + self.filename)
        self.csvfile = open(self.filename, 'w')
        self.writer = csv.writer(self.csvfile, delimiter=',')
        self.writer.writerow([
            "Time",
            "Voltage(V)",
            "Battery_Status(%)",
            "Temperature(C)",
            "Pressure(Pa)",
            "GPS_Altitude(m)",
            "Arduino_Altitude(m)",
            "Calculated_Altitude(m)",
            "Accel_X(m/s^2)",
            "Accel_Y(m/s^2)",
            "Accel_Z(m/s^2)",
            "Gyro_X",
            "Gyro_Y",
            "Gyro_Z",
            "Mag_X",
            "Mag_Y",
            "Mag_Z",
            "Quat_I",
            "Quat_J",
            "Quat_K",
            "Quat_Real",
            "Latitude",
            "Longitude",
        ])

        logging.basicConfig(
            handlers=[logging.FileHandler(os.path.join(self.LOG_DIR, self.LOG_FILENAME)), logging.StreamHandler()],
            level=logging.DEBUG,
            format="[%(asctime)s] %(message)s",
            datefmt="%m/%d/%Y %I:%M:%S %p",
        )

    def calculate_battery_status(self, voltage):
        """Calculate battery status as a percentage based on voltage."""
        min_voltage = 1.0
        max_voltage = 2.9
        if voltage >= max_voltage:
            return 100  # Cap at 100%
        elif voltage <= min_voltage:
            return 0  # Cap at 0%
        else:
            # Linear mapping from 1.0V to 2.9V
            return int((voltage - min_voltage) / (max_voltage - min_voltage) * 100)

    def calculate_altitude(self, pressure, temperature):
        """
        Calculate altitude using the barometric formula.
        Assumes temperature is in degrees Celsius and pressure is in Pascals.
        """
        if pressure <= 0 or temperature <= -273.15:
            return None  # Invalid pressure or temperature values

        T0 = temperature + 273.15  # Convert temperature to Kelvin
        L = 0.0065  # Temperature lapse rate in K/m
        R = 287.05  # Specific gas constant for dry air in J/(kg·K)
        g = 9.80665  # Gravity in m/s^2

        # Calculate altitude
        try:
            altitude = (T0 / L) * ((self.sea_level_pressure / pressure) ** (R * L / g) - 1)
            return altitude
        except ZeroDivisionError:
            return None  # Handle division by zero gracefully

    def parse_data(self, line: bytes):
        try:
            print(f"Raw line: {line}")  # Log raw input for debugging

            try:
                decoded = json.loads(line.decode("utf-8"))  # Decode the JSON data
            except json.JSONDecodeError as e:
                print(f"JSON Decode Error: {e}")
                return

            # Map sensor data, with specific handling for `mag` values
            self.data.update(decoded)

            # Fix `mag` to ensure correct reading
            self.data["magn"]["x"] = decoded.get("mag", {}).get("x", 0.0)
            self.data["magn"]["y"] = decoded.get("mag", {}).get("y", 0.0)
            self.data["magn"]["z"] = decoded.get("mag", {}).get("z", 0.0)

            # Retrieve altitude sources
            if self.data.get("gps", None):
                gps_altitude = self.data["gps"].get("alt")
                arduino_altitude = self.data.get("altitude")
                calculated_altitude = self.calculate_altitude(self.data["pressure"], self.data["temperature"])
            else:
                gps_altitude = -1
                arduino_altitude = -1
                calculated_altitude = -1


            # Calculate battery percentage
            battery_status = self.calculate_battery_status(self.data["voltage"])

            # Compact printout
            print(f"\n--- Sensor Data ---")
            print(f"Voltage: {self.data['voltage']:.4f} V (Battery: {battery_status}%) | Temp: {self.data['temperature']:.2f}°C | "
                f"Pressure: {self.data['pressure']:.2f} Pa")
            print(f"GPS Alt: {gps_altitude:.2f} m | Arduino Alt: {arduino_altitude:.2f} m | Calc Alt: {calculated_altitude:.2f} m")
            print(f"Accel: X={self.data['accel']['x']:.2f}, Y={self.data['accel']['y']:.2f}, Z={self.data['accel']['z']:.2f}")
            print(f"Gyro: X={self.data['gyro']['x']:.2f}, Y={self.data['gyro']['y']:.2f}, Z={self.data['gyro']['z']:.2f}")
            print(f"Mag: X={self.data['magn']['x']:.2f}, Y={self.data['magn']['y']:.2f}, Z={self.data['magn']['z']:.2f}")
            print(f"Quat: i={self.data['quat']['i']:.2f}, j={self.data['quat']['j']:.2f}, k={self.data['quat']['k']:.2f}, real={self.data['quat']['real']:.2f}")
            print(f"GPS: Lat={self.data['gps']['lat']}, Lon={self.data['gps']['lon']}")
            print("-------------------\n")

            # Write data to CS/deodeV
            self.writer.writerow([
                datetime.datetime.now().strftime("%H:%M:%S"),
                self.data["voltage"],
                battery_status,
                self.data["temperature"],
                self.data["pressure"],
                gps_altitude,
                arduino_altitude,
                calculated_altitude,
                self.data["accel"]["x"],
                self.data["accel"]["y"],
                self.data["accel"]["z"],
                self.data["gyro"]["x"],
                self.data["gyro"]["y"],
                self.data["gyro"]["z"],
                self.data["magn"]["x"],
                self.data["magn"]["y"],
                self.data["magn"]["z"],
                self.data["quat"]["i"],
                self.data["quat"]["j"],
                self.data["quat"]["k"],
                self.data["quat"]["real"],
                self.data["gps"]["lat"],
                self.data["gps"]["lon"],
            ])
        except:
           print("An exception occured")

    def update(self):
        """Update the main payload state machine"""
        line = self.serial_connection.readline().rstrip(b"\r\n")
        self.parse_data(line)
        self.csvfile.flush()

    def shutdown(self):
        self.running = False
        self.csvfile.flush()
        self.csvfile.close()
        self.serial_connection.close()


# Initialize parser
parser = argparse.ArgumentParser(description=msg)

# Callsign argument
parser.add_argument(
    "-c", "--callsign", help="Callsign to use for transmission. NOTRANSMIT to disable.", default="NOTRANSMIT",
)

# Port argument
parser.add_argument("-p", "--port", help="Port to use for XBee communication", default="/dev/ttyACM0")

args = parser.parse_args()


def main(args):
    payload = SubscaleSystem(args.port)

    try:
        while payload.running:
            payload.update()
    except KeyboardInterrupt:
        payload.shutdown()

    print("Subscale program complete. Waiting for recovery.")


if __name__ == "__main__":
    main(args)
