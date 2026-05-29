"""Check E6-RCU IOT/WiFi/MQTT capabilities in MicroPython."""
import serial, time

s = serial.Serial('COM12', 115200, timeout=3)
time.sleep(0.5)
s.read(4096)

def paste_code(code, wait=8):
    s.reset_input_buffer()
    s.write(b'\x05')
    time.sleep(0.3)
    s.read(256)
    s.write(code.encode())
    time.sleep(0.3)
    s.write(b'\x04')
    time.sleep(wait)
    out = s.read(4096)
    return out.decode('ascii', errors='replace')

# Search for IOT/WiFi/MQTT functions in rcu
print("=" * 60)
print("Search IOT/WiFi/MQTT functions in rcu module")
print("=" * 60)
code = (
    "import rcu\r\n"
    "funcs = [f for f in dir(rcu) if 'IOT' in f or 'iot' in f or 'MQTT' in f or 'mqtt' in f or 'Wifi' in f or 'wifi' in f or 'Net' in f]\r\n"
    "print(funcs)\r\n"
)
out = paste_code(code, wait=5)
print(out[-500:])

# Show ALL rcu functions (short version)
print("\n" + "=" * 60)
print("All rcu functions containing 'Set' or 'Get'")
print("=" * 60)
code = (
    "import rcu\r\n"
    "funcs = [f for f in dir(rcu) if 'Set' in f or 'Get' in f]\r\n"
    "for f in funcs:\r\n"
    "    print(f)\r\n"
)
out = paste_code(code, wait=5)
for line in out.split('\r\n'):
    line = line.strip()
    if line and '>>>' not in line and '===' not in line and 'import' not in line:
        print(f"  {line}")

s.close()
