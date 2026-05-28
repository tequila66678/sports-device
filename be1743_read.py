"""Read BE-1743 main0.py and find model files."""
import serial, time

s = serial.Serial('COM10', 115200, timeout=2)
time.sleep(0.5)
s.reset_input_buffer()

# First send Ctrl-C to stop boot program
s.write(b'\x03')
time.sleep(2.0)
out = s.read(4096)
print("After Ctrl-C:", out.decode('ascii', errors='replace')[-300:])

def send(cmd):
    s.write((cmd + '\r\n').encode())
    time.sleep(3.0)
    out = s.read(8192)
    r = out.decode('ascii', errors='replace')
    lines = [l.strip() for l in r.split('\r\n') if l.strip() and '>>>' not in l and cmd not in l]
    return lines

# Read main0.py
print("\n=== main0.py content ===")
# Use paste mode to read file
s.write(b'\x05')
time.sleep(0.3)
s.read(256)
s.write(b"with open('main0.py') as f:\r\n    for i, line in enumerate(f):\r\n        if i < 100:\r\n            print(repr(line))\r\n")
s.write(b'\x04')
time.sleep(3.0)
out = s.read(8192)
print(out.decode('ascii', errors='replace')[-4000:])

# Also look for .kmodel files
print("\n=== Searching for models ===")
s.write(b'\x05')
time.sleep(0.3)
s.read(256)
s.write(b"import os\r\nfor f in os.listdir():\r\n    print(f)\r\n")
# Also check /sd
s.write(b"try:\r\n    for f in os.listdir('/sd'):\r\n        print('SD:', f)\r\nexcept:\r\n    print('no sd card')\r\n")
s.write(b'\x04')
time.sleep(3.0)
out = s.read(4096)
print(out.decode('ascii', errors='replace')[-1000:])

s.close()
