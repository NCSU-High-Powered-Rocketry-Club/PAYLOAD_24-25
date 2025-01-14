import spidev
import RPi.GPIO as GPIO  # Import the GPIO library
import time

# SPI Configuration
SPI_BUS = 0      # SPI Bus 0
SPI_DEVICE = 0   # SPI Device 0 (CS0)
SPI_SPEED = 500000  # 500kHz

# GPIO Pin for Chip Select (CS)
CS_PIN = 8  # GPIO8 (Pin 24)

# DPS310 Registers
REG_PROD_ID = 0x0D  # Product ID register
EXPECTED_PROD_ID = 0x10  # Expected ID for DPS310

# Initialize GPIO
GPIO.setmode(GPIO.BCM)  # Use BCM pin numbering
GPIO.setup(CS_PIN, GPIO.OUT)  # Set CS_PIN as an output
GPIO.output(CS_PIN, GPIO.HIGH)  # Default to deselect the sensor

# Initialize SPI
spi = spidev.SpiDev()
spi.open(SPI_BUS, SPI_DEVICE)
spi.max_speed_hz = SPI_SPEED
spi.mode = 0b00  # SPI mode 0 (CPOL=0, CPHA=0)

def read_register(register):
    """
    Read a single byte from a specified register.
    :param register: The register address to read from.
    :return: The value read from the register.
    """
    GPIO.output(CS_PIN, GPIO.LOW)  # Select the DPS310
    response = spi.xfer2([register | 0x80, 0x00])  # MSB=1 for reading
    GPIO.output(CS_PIN, GPIO.HIGH)  # Deselect the DPS310
    return response[1]

def test_dps310():
    """
    Test communication with the DPS310 by reading the product ID.
    """
    print("Testing communication with DPS310...")
    prod_id = read_register(REG_PROD_ID)
    if prod_id == EXPECTED_PROD_ID:
        print(f"Success! DPS310 Product ID: {hex(prod_id)}")
    else:
        print(f"Failed to communicate with DPS310. Received: {hex(prod_id)}")

try:
    test_dps310()
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    spi.close()
    GPIO.cleanup()
