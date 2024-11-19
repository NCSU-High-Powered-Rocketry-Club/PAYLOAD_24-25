import serial
ser = serial.Serial('/dev/ttyACM0', 115200)  # Replace with your port and baud rate
while True:
    try:
        print(ser.readline().decode('utf-8').strip())
    except KeyboardInterrupt:
        print("Exiting...")
        ser.close()
        break