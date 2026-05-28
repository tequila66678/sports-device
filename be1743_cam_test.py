"""BE-1743: stop boot.py, test camera snapshot."""
import serial, time

s = serial.Serial('COM10', 115200, timeout=2)
time.sleep(0.5)
s.reset_input_buffer()

# Ctrl-C to stop boot.py
s.write(b'\x03')
time.sleep(3)
raw = s.read(4096)
print("After Ctrl-C:", raw.decode('ascii', errors='replace')[-300:])

# Enter paste mode
s.write(b'\x05')
time.sleep(0.3)
s.read(256)

# Simple camera test
code = (
    "import sensor, image, lcd\r\n"
    "sensor.reset()\r\n"
    "sensor.set_pixformat(sensor.RGB565)\r\n"
    "sensor.set_framesize(sensor.QVGA)\r\n"
    "sensor.skip_frames(10)\r\n"
    "img = sensor.snapshot()\r\n"
    "print('Camera OK:', img.width(), 'x', img.height())\r\n"
    "sensor.shutdown(0)\r\n"
)
s.write(code.encode())
s.write(b'\x04')  # Ctrl-D
time.sleep(5)
out = s.read(4096)
print("Test result:", out.decode('ascii', errors='replace')[-500:])

s.close()
