"""Check BE-1743 MaixPy modules and capabilities."""
import serial, time

s = serial.Serial('COM10', 115200, timeout=2)
time.sleep(0.5)
s.read(4096)  # clear boot messages

# List modules
s.write(b"help('modules')\r\n")
time.sleep(2)
out = s.read(8192)
print("=== MODULES ===")
print(out.decode('ascii', errors='replace'))

# Check for camera/sensor modules
for mod in ['camera', 'sensor', 'image', 'KPU', 'kpu', 'face', 'machine', 'fpioa']:
    s.write(f"import {mod}\r\n".encode())
    time.sleep(0.3)
    s.write(f"dir({mod})\r\n".encode())
    time.sleep(0.5)
    out = s.read(2048)
    print(f"=== {mod} ===")
    print(out.decode('ascii', errors='replace')[-500:])

s.close()
