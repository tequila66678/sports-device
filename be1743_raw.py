"""Raw BE-1743 test - minimal approach."""
import serial, time

s = serial.Serial('COM10', 115200, timeout=2)
time.sleep(0.5)
s.reset_input_buffer()

# Ctrl-C
s.write(b'\x03')
time.sleep(2)
raw = s.read(4096)
print("After Ctrl-C:", repr(raw[-200:]))

# Very simple command
s.write(b"print(1+1)\r\n")
time.sleep(1)
raw = s.read(1024)
print("1+1:", repr(raw))

# Another
s.write(b"import os\r\n")
time.sleep(0.5)
s.read(512)

s.write(b"os.listdir()\r\n")
time.sleep(1)
raw = s.read(1024)
print("listdir:", repr(raw))

# Try to open boot.py directly
s.write(b"f=open('boot.py'); print(f.readline()); f.close()\r\n")
time.sleep(1)
raw = s.read(1024)
print("boot.py line1:", repr(raw))

# File size
s.write(b"import os; os.stat('boot.py')\r\n")
time.sleep(1)
raw = s.read(1024)
print("stat boot.py:", repr(raw))

s.close()
