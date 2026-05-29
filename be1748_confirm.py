"""BE-1748: confirm face ID stability and registration API."""
import serial, time

s = serial.Serial('COM12', 115200, timeout=3)
time.sleep(0.5)
s.read(4096)

def paste_code(code, wait=10):
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

# Test 1: Poll mode 10 multiple times to confirm ID stability
print("=" * 60)
print("TEST 1: Poll mode 10 x10 (keep face in view)")
print("=" * 60)
code = (
    "import rcu,utime\r\n"
    "rcu.SetWaitForAICamData(10,0)\r\n"
    "utime.sleep_ms(300)\r\n"
    "for i in range(10):\r\n"
    "    r=rcu.GetAICamData(1)\r\n"
    "    print(str(r))\r\n"
    "    utime.sleep_ms(300)\r\n"
    "print('poll_done')\r\n"
)
out = paste_code(code, wait=10)
for line in out.split('\r\n'):
    line = line.strip()
    if line.isdigit() or line == 'poll_done':
        print(f"  {line}")

# Test 2: Try SetAICamData for face registration
print("\n" + "=" * 60)
print("TEST 2: Try face registration via SetAICamData")
print("Send: SetAICamData(1, 101) then poll")
print("=" * 60)
code = (
    "import rcu,utime\r\n"
    "rcu.SetWaitForAICamData(10,0)\r\n"
    "utime.sleep_ms(300)\r\n"
    "rcu.SetAICamData(1,101)\r\n"
    "utime.sleep_ms(1000)\r\n"
    "r=rcu.GetAICamData(1)\r\n"
    "print('after_reg: '+str(r))\r\n"
)
out = paste_code(code, wait=10)
for line in out.split('\r\n'):
    line = line.strip()
    if 'after_reg' in line:
        print(f"  {line}")

# Test 3: Check if rcu has registration-related functions
print("\n" + "=" * 60)
print("TEST 3: Search for registration functions")
print("=" * 60)
code = (
    "import rcu\r\n"
    "funcs = [f for f in dir(rcu) if 'SetAICam' in f or 'face' in f.lower() or 'reg' in f.lower() or 'enroll' in f.lower()]\r\n"
    "print(funcs)\r\n"
)
out = paste_code(code, wait=5)
print(out[-400:])

# Test 4: Do we need to stay in mode 10, or re-init each time?
print("\n" + "=" * 60)
print("TEST 4: Does mode persist across pastes?")
print("(No SetWaitForAICamData call)")
print("=" * 60)
code = (
    "import rcu\r\n"
    "r=rcu.GetAICamData(1)\r\n"
    "print('no_init: '+str(r))\r\n"
)
out = paste_code(code, wait=5)
for line in out.split('\r\n'):
    line = line.strip()
    if 'no_init' in line:
        print(f"  {line}")

s.close()
print("\nDone.")
