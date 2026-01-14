import serial
import time

PORT = "/dev/tty.usbserial-14230"
BAUD = 115200

print("Opening port:", PORT)
ser = serial.Serial(PORT, BAUD, timeout=0.2)

# Reset vermeiden
ser.setDTR(False)
ser.setRTS(False)

time.sleep(1.5)
ser.reset_input_buffer()
ser.reset_output_buffer()

def read_all(duration=0.4):
    end = time.time() + duration
    out = b""
    while time.time() < end:
        chunk = ser.read(4096)
        if chunk:
            out += chunk
        else:
            time.sleep(0.02)
    if out:
        print("<<", out.decode("utf-8", errors="replace").strip())

def send(cmd):
    print(">>", cmd)
    ser.write((cmd + "\n").encode("utf-8"))
    ser.flush()
    read_all()

def all_off():
    send("all_off")

def blink(color_on_cmd, color_off_cmd, times=6, on=0.2, off=0.2):
    for _ in range(times):
        send(color_on_cmd)
        time.sleep(on)
        send(color_off_cmd)
        time.sleep(off)

# Boot output lesen (optional)
print("Reading boot output...")
read_all(1.5)

# --- TEST: die Zustände wie du sie wolltest ---
print("\nSTATE READY  -> green_on")
all_off()
send("green_on")
time.sleep(1.0)

print("\nSTATE MOVE   -> green blink")
all_off()
blink("green_on", "green_off", times=8, on=0.15, off=0.15)

print("\nSTATE ILLEGAL -> red blink")
all_off()
blink("red_on", "red_off", times=8, on=0.15, off=0.15)

print("\nSTATE UNKNOWN -> yellow blink")
all_off()
blink("yellow_on", "yellow_off", times=8, on=0.15, off=0.15)

print("\nSTATE OFF -> all_off")
all_off()

ser.close()
print("done")
