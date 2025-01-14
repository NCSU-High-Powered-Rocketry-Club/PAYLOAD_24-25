import spidev

def spi0_loopback_test():
    spi = spidev.SpiDev()
    spi.open(0, 0)  # SPI0 bus, CS0
    spi.max_speed_hz = 500000  # Use 500 kHz for stability
    spi.mode = 0  # SPI Mode 0

    # Test data to send
    test_data = [0xAA, 0x55, 0xFF, 0x00]  # Example data pattern
    print("Sent:     ", test_data)
    response = spi.xfer2(test_data)  # Send and receive data
    print("Received: ", response)

    spi.close()

if __name__ == "__main__":
    spi0_loopback_test()
