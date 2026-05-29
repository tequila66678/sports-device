"""BE-6311 ultrasonic test - P6 on E6-RCU via paste mode."""
import serial, time, sys

s = serial.Serial('COM12', 115200, timeout=3)
time.sleep(0.5)
s.read(4096)

def paste_code(code, wait=8):
    """Send MicroPython code via paste mode (Ctrl-E)."""
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

# Test 1: Try GetUltrasound from rcu module
print("=" * 60)
print("TEST 1: rcu.GetUltrasound(6)")
print("=" * 60)
code = (
    "import rcu,utime\r\n"
    "for i in range(5):\r\n"
    "    r=rcu.GetUltrasound(6)\r\n"
    "    print('dist='+str(r))\r\n"
    "    utime.sleep_ms(500)\r\n"
    "print('done')\r\n"
)
out = paste_code(code, wait=10)
print(out[-400:])

# Test 2: Try different module name
print("\n" + "=" * 60)
print("TEST 2: Try 'sensor' module")
print("=" * 60)
code = (
    "import sensor,utime\r\n"
    "for i in range(5):\r\n"
    "    try:\r\n"
    "        r=sensor.GetUltrasound(6)\r\n"
    "        print('dist='+str(r))\r\n"
    "    except Exception as e:\r\n"
    "        print('err:'+str(e))\r\n"
    "    utime.sleep_ms(500)\r\n"
    "print('done')\r\n"
)
out = paste_code(code, wait=10)
print(out[-400:])

# Test 3: Check available modules/functions
print("\n" + "=" * 60)
print("TEST 3: Check what's available")
print("=" * 60)
code = (
    "import rcu\r\n"
    "print(dir(rcu))\r\n"
)
out = paste_code(code, wait=5)
print(out[-500:])

s.close()
print("\nBE-6311 tests complete.")
