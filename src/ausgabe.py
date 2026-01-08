import serial
import time

# Try different COM ports
com_ports_to_try = ['COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9']

for com_port in com_ports_to_try:
    try:
        print(f"Trying {com_port}...")
        ser = serial.Serial(port=com_port, baudrate=115200, timeout=1)
        print(f"✓ Connected to {com_port}")
        
        # Read some data
        print("Reading data for 5 seconds...")
        start = time.time()
        while time.time() - start < 5:
            if ser.in_waiting:
                data = ser.readline().decode('utf-8', errors='ignore').strip()
                if data:
                    print(f"  {data}")
            time.sleep(0.01)
        
        ser.close()
        print("Success! Use this port in your code.")
        break
        
    except serial.SerialException:
        print(f"  {com_port} not available")
        continue