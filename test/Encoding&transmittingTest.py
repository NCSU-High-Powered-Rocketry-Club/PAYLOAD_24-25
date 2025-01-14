import re
import subprocess
import time
import RPi.GPIO as GPIO

# GPIO pin setup
GPIO_PIN = 8

def setup_gpio():
    GPIO.setmode(GPIO.BCM)  # Use Broadcom pin-numbering scheme
    GPIO.setup(GPIO_PIN, GPIO.OUT, initial=GPIO.HIGH)  # Set pin as an output and initially high

def pull_pin_low():
    GPIO.output(GPIO_PIN, GPIO.LOW)  # Pull the pin low

def pull_pin_high():
    GPIO.output(GPIO_PIN, GPIO.HIGH)  # Pull the pin high

def cleanup_gpio():
    GPIO.cleanup()  # Clean up GPIO to ensure no resources are left hanging

def update_beacon_comment(config_path, new_comment):
    with open(config_path, 'r') as file:
        lines = file.readlines()

    found = False
    for i, line in enumerate(lines):
        if line.startswith('PBEACON'):
            lines[i] = re.sub(r'comment="[^"]*"', f'comment="{new_comment}"', line)
            found = True
            break

    if not found:
        print("PBEACON line not found in the configuration file.")
        return False

    with open(config_path, 'w') as file:
        file.writelines(lines)

    return True

def restart_direwolf():
    subprocess.run(['pkill', '-f', 'direwolf'], check=False)  # Try to stop Direwolf
    time.sleep(2)  # Wait for a moment to ensure the process has terminated
    subprocess.Popen(['direwolf'])  # Start Direwolf again
    print("Direwolf has been restarted.")

def main():
    while True:
        setup_gpio()
        config_path = '/home/pi/direwolf.conf'
        print("Please enter the new beacon comment:")
        new_comment = "test message 1!2@3#4$5%6^7&8*9(0)-_=+[{]}\|;:'""] " # Take user input for the new comment

        if update_beacon_comment(config_path, new_comment):
            print("Configuration updated successfully.")
            pull_pin_low()  # Activate PTT via GPIO pin pull-down
            restart_direwolf()
            time.sleep(5)  # Duration for which the pin should remain low
            pull_pin_high()  # Deactivate PTT via GPIO pin pull-up
            print("Transmission complete. Pin reset.")
            subprocess.run(['pkill', '-f', 'direwolf'], check=False)  # Try to stop Direwolf

        else:
            print("Failed to update the configuration. Please check the file and try again.")

        cleanup_gpio()

if __name__ == "__main__":
    main()
