"""Simple interactive test with BE-1743 - one command at a time."""
import serial, time

s = serial.Serial('COM10', 115200, timeout=2)
time.sleep(0.5)
s.reset_input_buffer()

def send(cmd):
    s.write((cmd + '\r\n').encode())
    time.sleep(2.0)
    out = s.read(4096)
    r = out.decode('ascii', errors='replace')
    # Clean up output
    lines = [l.strip() for l in r.split('\r\n') if l.strip() and '>>>' not in l and cmd not in l]
    return lines

# Check REPL is working
print("1. Testing REPL...")
lines = send("print('hello')")
print(f"   {lines}")

# List files
print("2. Listing files...")
s.write(b"import os\r\n")
time.sleep(0.5)
s.read(512)
lines = send("os.listdir()")
print(f"   {lines}")

# Try to see what program is running (Ctrl-C to stop)
print("3. Sending Ctrl-C to stop any running program...")
s.write(b'\x03')
time.sleep(1.0)
out = s.read(1024)
print(f"   {out.decode('ascii', errors='replace')[-200:]}")

# After Ctrl-C, try again
print("4. After Ctrl-C, list files...")
s.write(b"import os\r\n")
time.sleep(0.3)
s.read(256)
lines = send("os.listdir()")
print(f"   {lines}")

# Try multi-line paste mode
print("5. Paste mode test...")
s.write(b'\x05')  # Ctrl-E
time.sleep(0.5)
s.read(256)

code = "import os\r\nfor f in os.listdir():\r\n    print(f)\r\n"
s.write(code.encode())
s.write(b'\x04')  # Ctrl-D
time.sleep(2.0)
out = s.read(2048)
print(f"   {out.decode('ascii', errors='replace')[-500:]}")

s.close()
