"""BE-1743: longer waits, match earlier successful approach."""
import serial, time

s = serial.Serial('COM10', 115200, timeout=3)
time.sleep(0.5)
s.reset_input_buffer()

# Ctrl-C
print("1. Ctrl-C...")
s.write(b'\x03')
time.sleep(3)
raw = s.read(4096)
# Check if we got KeyboardInterrupt
text = raw.decode('ascii', errors='replace')
print(f"   Got {len(raw)} bytes")

# Clear and wait more
time.sleep(2)
s.reset_input_buffer()

# Send a simple command with LONG wait
def send_cmd(cmd, wait=4):
    s.write((cmd + '\r\n').encode())
    time.sleep(wait)
    out = s.read(4096)
    text = out.decode('ascii', errors='replace')
    # Clean output
    lines = [l.strip() for l in text.split('\r\n')
             if l.strip() and '>>>' not in l and cmd not in l]
    return lines

print("2. Testing print...")
lines = send_cmd("print('hello')")
print(f"   {lines}")

print("3. Import os...")
s.write(b"import os\r\n")
time.sleep(1)
s.read(1024)
lines = send_cmd("os.listdir()")
print(f"   {lines}")

print("4. Check for boot.py...")
s.write(b"import os\r\n")
time.sleep(1)
s.read(1024)
lines = send_cmd("os.stat('boot.py')")
print(f"   boot.py stat: {lines}")

print("5. Trying to rename boot.py to disable it...")
s.write(b"import os\r\n")
time.sleep(1)
s.read(1024)
lines = send_cmd("os.rename('boot.py', 'boot.py.bak')")
print(f"   rename: {lines}")

print("6. List files again...")
s.write(b"import os\r\n")
time.sleep(1)
s.read(1024)
lines = send_cmd("os.listdir()")
print(f"   {lines}")

s.close()
