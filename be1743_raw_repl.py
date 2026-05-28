"""BE-1743: use raw REPL mode (Ctrl-A) for reliable communication."""
import serial, time

s = serial.Serial('COM10', 115200, timeout=2)
time.sleep(0.5)
s.reset_input_buffer()

# Step 1: Ctrl-C twice to interrupt any running code
print("Interrupting with Ctrl-C...")
s.write(b'\r\x03\x03')
time.sleep(1)
raw = s.read(1024)
print(f"  Got {len(raw)} bytes")

# Step 2: Enter raw REPL mode
print("Entering raw REPL...")
s.write(b'\r\x01')
time.sleep(1)
raw = s.read(1024)
print(f"  Raw REPL response: {raw}")

# Step 3: Execute Python code in raw REPL
code = "print('hello k210')\r\nimport sensor\r\nsensor.reset()\r\nprint('cam init done')\r\n"
# Raw REPL: send code followed by Ctrl-D
s.write(code.encode())
s.write(b'\x04')
time.sleep(5)
out = s.read(4096)
print(f"\nRaw execution output ({len(out)} bytes):")
print(out.decode('ascii', errors='replace'))

# Try to read the result
# In raw REPL, output format is: OK + len + output + \x04
if b'OK' in out:
    print("\n  -> Raw REPL is working!")
else:
    print("\n  -> Unexpected response format")

s.close()
