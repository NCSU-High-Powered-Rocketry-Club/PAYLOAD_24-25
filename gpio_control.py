import RPi.GPIO as GPIO
import time

# Set up GPIO pin
GPIO.setmode(GPIO.BCM)  # Use Broadcom pin numbering
GPIO.setwarnings(False)  # Disable GPIO warnings
GPIO.setup(21, GPIO.OUT)  # Set GPIO 21 as an output

try:
    # Toggle GPIO 21
    while True:
        GPIO.output(21, GPIO.HIGH)  # Set GPIO 21 to high
        time.sleep(1)  # Wait 1 second
        GPIO.output(21, GPIO.LOW)  # Set GPIO 21 to low
        time.sleep(1)  # Wait 1 second
except KeyboardInterrupt:
    # Clean up GPIO on CTRL+C exit
    pass
finally:
    GPIO.cleanup()  # Clean up GPIO on any exit
