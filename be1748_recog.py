"""BE-1748: test GetCamRecog for face recognition data."""
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

# Test 1: Check if rcu has GetCamRecog
print("=" * 60)
print("TEST 1: Check rcu.GetCamRecog")
print("=" * 60)
code = (
    "import rcu\r\n"
    "funcs = [f for f in dir(rcu) if 'Cam' in f or 'cam' in f or 'Recog' in f or 'Scan' in f]\r\n"
    "print(funcs)\r\n"
)
out = paste_code(code, wait=5)
print(out[-400:])

# Test 2: Try GetCamRecog via try/except
print("\n" + "=" * 60)
print("TEST 2: Try GetCamRecog directly")
print("=" * 60)
code = (
    "try:\r\n"
    "    r = GetCamRecog(1)\r\n"
    "    print('GetCamRecog(1)='+str(r))\r\n"
    "except Exception as e:\r\n"
    "    print('err:'+str(e))\r\n"
    "try:\r\n"
    "    r = rcu.GetCamRecog(1)\r\n"
    "    print('rcu.GetCamRecog(1)='+str(r))\r\n"
    "except Exception as e:\r\n"
    "    print('rcu err:'+str(e))\r\n"
)
out = paste_code(code, wait=5)
print(out[-400:])

# Test 3: Check what other modules are available
print("\n" + "=" * 60)
print("TEST 3: Available modules")
print("=" * 60)
code = (
    "import sys\r\n"
    "print(sys.modules.keys())\r\n"
)
out = paste_code(code, wait=3)
print(out[-400:])

# Test 4: Help on rcu module (if available)
print("\n" + "=" * 60)
print("TEST 4: help(rcu) - first 500 chars")
print("=" * 60)
code = (
    "import rcu\r\n"
    "try:\r\n"
    "    help(rcu)\r\n"
    "except Exception as e:\r\n"
    "    print('help err:'+str(e))\r\n"
)
out = paste_code(code, wait=5)
print(out[-600:])

s.close()
print("\nDone.")
