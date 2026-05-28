"""BE-1743 camera test - robust REPL handling."""
import serial, time

s = serial.Serial('COM10', 115200, timeout=2)
time.sleep(0.5)
s.reset_input_buffer()

# Ctrl-C
print("Sending Ctrl-C...")
s.write(b'\x03')
time.sleep(3)
raw = s.read(4096)
print("Got:", len(raw), "bytes")

# Send simple command
print("\nTesting print...")
s.write(b"print('hello from k210')\r\n")
time.sleep(1.5)
raw = s.read(1024)
print("Response:", raw.decode('ascii', errors='replace'))

# Import sensor
print("\nImporting sensor...")
s.write(b"import sensor\r\n")
time.sleep(1.5)
raw = s.read(2048)
print("Response:", raw.decode('ascii', errors='replace')[-300:])

# Init camera
print("\nInit camera...")
s.write(b"sensor.reset()\r\n")
time.sleep(2)
raw = s.read(2048)
print("Response:", raw.decode('ascii', errors='replace')[-300:])

s.write(b"sensor.set_pixformat(sensor.RGB565)\r\n")
time.sleep(1)
raw = s.read(512)

s.write(b"sensor.set_framesize(sensor.QVGA)\r\n")
time.sleep(1)
raw = s.read(512)

s.write(b"sensor.skip_frames(10)\r\n")
time.sleep(2)
raw = s.read(512)

# Take snapshot
print("\nTaking snapshot...")
s.write(b"img = sensor.snapshot()\r\n")
time.sleep(1)
raw = s.read(1024)
print("Response:", raw.decode('ascii', errors='replace')[-200:])

s.write(b"print('size:', img.width(), img.height())\r\n")
time.sleep(1)
raw = s.read(1024)
print("Size:", raw.decode('ascii', errors='replace')[-200:])

s.close()
print("\nDone")
