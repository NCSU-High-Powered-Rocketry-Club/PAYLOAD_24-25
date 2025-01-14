
import spidev
import RPi.GPIO as GPIO
import time

# Pin Definitions (adjust these to your setup)
SDN_PIN = 27
CS_PIN = 8
IRQ_PIN = 17  # Optional

# Si4464 Commands
CMD_PART_INFO = 0x01
CMD_GET_INT_STATUS = 0x20

# Initialize GPIOs and SPI
def initialize_pins():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SDN_PIN, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(CS_PIN, GPIO.OUT, initial=GPIO.HIGH)
    if IRQ_PIN != -1:
        GPIO.setup(IRQ_PIN, GPIO.IN)
    
    spi = spidev.SpiDev()
    spi.open(0, 0)  # Use bus 0, device 0
    spi.max_speed_hz = 20000  # Set SPI speed
    return spi

def power_on_module():
    GPIO.output(SDN_PIN, GPIO.LOW)
    time.sleep(0.02)  # Increased delay to 20ms
    print("Si4464 module powered on.")

def reset_si4464():
    print("Resetting Si4464...")
    GPIO.output(SDN_PIN, GPIO.HIGH)
    time.sleep(0.02)  # Increased delay to 20ms
    GPIO.output(SDN_PIN, GPIO.LOW)
    time.sleep(0.02)  # Increased delay to 20ms
    print("Si4464 reset complete.")

# Send a command to the Si4464
def send_command(spi, cmd, args=[]):
    GPIO.output(CS_PIN, GPIO.LOW)
    spi.xfer([cmd] + args)
    GPIO.output(CS_PIN, GPIO.HIGH)

# Read response from the Si4464
def read_response(spi, length):
    cts = 0
    timeout = 1000
    
    response = []
    while cts != 0xFF and timeout > 0:
        GPIO.output(CS_PIN, GPIO.LOW)
        cts = spi.xfer2([0x44, 0x00])[1]
        GPIO.output(CS_PIN, GPIO.HIGH)
        if cts == 0xFF:
            response = spi.xfer2([0x00] * length)
        else:
            time.sleep(0.001)
        timeout -= 1

    if cts != 0xFF:
        print("Error: Timeout waiting for CTS.")
    return response

# Read Part Info
def read_part_info(spi):
    print("Sending PART_INFO command...")
    send_command(spi, CMD_PART_INFO)
    response = read_response(spi, 8)
    print_buffer("PART_INFO Response", response)

# Print buffer contents
def print_buffer(label, buffer):
    print(f"{label} [{len(buffer)} bytes]:")
    for byte in buffer:
        print(f"0x{byte:02X} ", end="")
    print()

# Debug GPIO states
def debug_pins():
    print("CS_PIN:", GPIO.input(CS_PIN))
    print("SDN_PIN:", GPIO.input(SDN_PIN))
    if IRQ_PIN != -1:
        print("IRQ_PIN:", GPIO.input(IRQ_PIN))

# Main Program
spi = initialize_pins()
debug_pins()
power_on_module()
debug_pins()
reset_si4464()
read_part_info(spi)
