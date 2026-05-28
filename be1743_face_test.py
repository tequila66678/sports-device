"""Test BE-1743 face detection capability."""
import serial, time

s = serial.Serial('COM10', 115200, timeout=3)
time.sleep(0.5)
s.reset_input_buffer()

# Ctrl-C to stop boot.py
s.write(b'\x03')
time.sleep(2)
raw = s.read(4096)
print("Ctrl-C result:", repr(raw[-200:]))

# Wait for REPL prompt, then import modules
def repl(cmd, wait=2):
    s.write((cmd + '\r\n').encode())
    time.sleep(wait)
    out = s.read(4096)
    return out.decode('ascii', errors='replace')

# Test basic imports
for cmd in [
    'import sensor',
    'import image',
    'import KPU as kpu',
    'print("imports OK")',
]:
    r = repl(cmd)
    lines = [l.strip() for l in r.split('\r\n') if l.strip() and '>>>' not in l]
    if lines:
        print(f"  {cmd}: {lines[-3:]}")

# Try to initialize camera and test snapshot
r = repl('import sensor, image; sensor.reset(); sensor.set_pixformat(sensor.RGB565); sensor.set_framesize(sensor.QVGA); print("cam OK")')
print("Camera init:", r[-300:])

r = repl('img=sensor.snapshot(); print("img:", img.width(), img.height())')
print("Snapshot:", r[-300:])

# Try to find face in image using Haar cascade or similar
r = repl("objects = img.find_features(image.HaarCascade('/sd/face.haar'))")
print("Haar:", r[-200:])

# Try KPU face detection
r = repl("try:\n    task = kpu.load('/sd/face.kmodel')\n    print('face model loaded')\nexcept Exception as e:\n    print('no face model:', e)")
print("Model:", r[-300:])

s.close()
