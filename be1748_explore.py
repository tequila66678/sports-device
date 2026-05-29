"""BE-1748: explore face recognition modes and registration."""
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

# Test 1: Check rcu module for face/enroll related functions
print("=" * 60)
print("TEST 1: Search rcu module for face/enroll functions")
print("=" * 60)
code = (
    "import rcu\r\n"
    "funcs = dir(rcu)\r\n"
    "for f in funcs:\r\n"
    "    fl = f.lower()\r\n"
    "    if 'face' in fl or 'enroll' in fl or 'reg' in fl or 'cam' in fl or 'ai' in fl or 'smart' in fl or 'recog' in fl:\r\n"
    "        print(f)\r\n"
    "print('---')\r\n"
    "# Check SmartEyeMode function\r\n"
    "print('SmartEyeMode doc:')\r\n"
    "try:\r\n"
    "    print(rcu.SmartEyeMode.__doc__)\r\n"
    "except:\r\n"
    "    print('no doc')\r\n"
)
out = paste_code(code, wait=8)
print(out[-500:])

# Test 2: Try different cmd values while face is present
print("\n" + "=" * 60)
print("TEST 2: Try all cmd 0-20 while face present")
print("Stand in front of camera!")
print("=" * 60)
code = (
    "import rcu,utime\r\n"
    "rcu.SetWaitForAICamData(2,0)\r\n"
    "utime.sleep_ms(1500)\r\n"
    "for cmd in range(0,21):\r\n"
    "    r=rcu.GetAICamData(cmd)\r\n"
    "    print('c'+str(cmd)+'='+str(r))\r\n"
    "    utime.sleep_ms(50)\r\n"
    "print('scan_done')\r\n"
)
out = paste_code(code, wait=12)
print(out[-800:])

# Test 3: Try different modes (0-6) for SetWaitForAICamData
print("\n" + "=" * 60)
print("TEST 3: Try modes 0-6")
print("=" * 60)
for mode in range(0, 7):
    code = (
        f"import rcu,utime\r\n"
        f"t0=utime.ticks_ms()\r\n"
        f"rcu.SetWaitForAICamData({mode},0)\r\n"
        f"t1=utime.ticks_ms()\r\n"
        f"r=rcu.GetAICamData(1)\r\n"
        f"r2=rcu.GetAICamData(2)\r\n"
        f"print('mode{mode}: '+str(utime.ticks_diff(t1,t0))+'ms cmd1='+str(r)+' cmd2='+str(r2))\r\n"
    )
    out = paste_code(code, wait=8)
    # Print last meaningful lines
    for line in out.split('\r\n'):
        line = line.strip()
        if 'mode' in line and 'ms' in line:
            print(f"  {line}")

s.close()
print("\nDone.")
