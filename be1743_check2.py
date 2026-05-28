"""Check BE-1743 modules and test camera."""
import serial, time

s = serial.Serial('COM10', 115200, timeout=2)
time.sleep(0.5)
s.read(4096)

# Send commands one at a time
tests = [
    "import sensor",
    "sensor.reset()",
    "sensor.set_pixformat(sensor.RGB565)",
    "sensor.set_framesize(sensor.QVGA)",
    "dir(sensor)",
    "import image",
    "dir(image)",
    "import KPU as kpu",
    "dir(kpu)",
]

for cmd in tests:
    s.write((cmd + '\r\n').encode())
    time.sleep(1.0)
    out = s.read(2048)
    print(f">>> {cmd}")
    result = out.decode('ascii', errors='replace')
    # Show last few lines (skip echo)
    lines = [l.strip() for l in result.split('\r\n') if l.strip() and '>>>' not in l]
    for l in lines[-5:]:
        print(f"    {l}")
    print()

s.close()
print("Done")
