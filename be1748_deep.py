"""BE-1748: deep exploration - face registration and data format."""
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

# Test 1: Try mode 2 with different params
print("=" * 60)
print("TEST 1: Mode=2 with different params (0-5)")
print("Stand in front of camera!")
print("=" * 60)
for p in range(0, 6):
    code = (
        f"import rcu,utime\r\n"
        f"rcu.SetWaitForAICamData(2,{p})\r\n"
        f"utime.sleep_ms(800)\r\n"
        f"r1=rcu.GetAICamData(1)\r\n"
        f"r2=rcu.GetAICamData(2)\r\n"
        f"r3=rcu.GetAICamData(3)\r\n"
        f"r4=rcu.GetAICamData(4)\r\n"
        f"print('p{p}: c1='+str(r1)+' c2='+str(r2)+' c3='+str(r3)+' c4='+str(r4))\r\n"
    )
    out = paste_code(code, wait=10)
    for line in out.split('\r\n'):
        line = line.strip()
        if 'p' in line and 'c1=' in line:
            print(f"  {line}")

# Test 2: Try SetAICamData to register face
print("\n" + "=" * 60)
print("TEST 2: Try SetAICamData for face registration")
print("Face camera clearly for registration attempt")
print("=" * 60)
code = (
    "import rcu,utime\r\n"
    "# Init\r\n"
    "rcu.SetWaitForAICamData(2,0)\r\n"
    "utime.sleep_ms(500)\r\n"
    "# Try SetAICamData as enrollment trigger\r\n"
    "# cmd0=face_id, cmd1=trigger?\r\n"
    "for fid in range(1,4):\r\n"
    "    rcu.SetAICamData(fid,1)  # register face_id fid\r\n"
    "    utime.sleep_ms(500)\r\n"
    "    r=rcu.GetAICamData(1)\r\n"
    "    print('reg'+str(fid)+': r='+str(r))\r\n"
    "print('reg_done')\r\n"
)
out = paste_code(code, wait=12)
print(out[-500:])

# Test 3: Check if cam has built-in face enumeration
print("\n" + "=" * 60)
print("TEST 3: Check all COMPackData bytes (cmd 0-31)")
print("Stand in front of camera!")
print("=" * 60)
code = (
    "import rcu,utime\r\n"
    "rcu.SetWaitForAICamData(2,0)\r\n"
    "utime.sleep_ms(1000)\r\n"
    "for cmd in range(0,32):\r\n"
    "    r=rcu.GetAICamData(cmd)\r\n"
    "    if r!=0:\r\n"
    "        print('B'+str(cmd)+'='+str(r))\r\n"
    "    utime.sleep_ms(30)\r\n"
    "print('byte_scan_done')\r\n"
)
out = paste_code(code, wait=10)
print(out[-400:])

# Test 4: AI cam LED test
print("\n" + "=" * 60)
print("TEST 4: AI Cam LED control")
print("=" * 60)
code = (
    "import rcu,utime\r\n"
    "rcu.SetAICamLED(1)\r\n"
    "utime.sleep_ms(500)\r\n"
    "print('LED on')\r\n"
    "utime.sleep_ms(500)\r\n"
    "rcu.SetAICamLED(0)\r\n"
    "print('LED off')\r\n"
)
out = paste_code(code, wait=5)
print(out[-300:])

s.close()
print("\nDone.")
