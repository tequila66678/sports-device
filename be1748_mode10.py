"""BE-1748: test mode 10 face recognition and find face ID byte."""
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

# Test 1: Mode 10 - scan all cmd bytes for face ID
print("=" * 60)
print("TEST 1: Mode 10 - scan all cmd bytes 0-31")
print("Registered person stand in front of camera!")
print("=" * 60)
code = (
    "import rcu,utime\r\n"
    "rcu.SetWaitForAICamData(10,0)\r\n"
    "utime.sleep_ms(1000)\r\n"
    "for cmd in range(0,32):\r\n"
    "    r=rcu.GetAICamData(cmd)\r\n"
    "    if r!=0:\r\n"
    "        print('B'+str(cmd)+'='+str(r))\r\n"
    "    utime.sleep_ms(30)\r\n"
    "print('scan_done')\r\n"
)
out = paste_code(code, wait=12)
print(out[-500:])

# Test 2: Mode 10 - continuous poll, show all non-zero bytes
print("\n" + "=" * 60)
print("TEST 2: Mode 10 continuous - all non-zero cmd bytes")
print("Keep face in view!")
print("=" * 60)
code = (
    "import rcu,utime\r\n"
    "rcu.SetWaitForAICamData(10,0)\r\n"
    "utime.sleep_ms(500)\r\n"
    "for i in range(15):\r\n"
    "    vals = []\r\n"
    "    for cmd in range(0,16):\r\n"
    "        r=rcu.GetAICamData(cmd)\r\n"
    "        if r!=0:\r\n"
    "            vals.append(str(cmd)+':'+str(r))\r\n"
    "    if vals:\r\n"
    "        print('@'+str(i)+': '+' '.join(vals))\r\n"
    "    utime.sleep_ms(400)\r\n"
    "print('cont_done')\r\n"
)
out = paste_code(code, wait=15)
print(out[-600:])

# Test 3: Try mode 10 with different params (face ID enrollment?)
print("\n" + "=" * 60)
print("TEST 3: Mode 10 with different params")
print("=" * 60)
for p in [0, 1, 2, 3]:
    code = (
        f"import rcu,utime\r\n"
        f"rcu.SetWaitForAICamData(10,{p})\r\n"
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

# Test 4: Compare mode 2 vs mode 10 output
print("\n" + "=" * 60)
print("TEST 4: Mode 2 vs Mode 10 side by side")
print("Registered person, then unregistered person!")
print("=" * 60)
code = (
    "import rcu,utime\r\n"
    "for mode in [2, 10]:\r\n"
    "    rcu.SetWaitForAICamData(mode,0)\r\n"
    "    utime.sleep_ms(800)\r\n"
    "    vals = []\r\n"
    "    for cmd in range(0,8):\r\n"
    "        r=rcu.GetAICamData(cmd)\r\n"
    "        vals.append(str(r))\r\n"
    "    print('mode'+str(mode)+': '+' '.join(vals))\r\n"
    "print('cmp_done')\r\n"
)
out = paste_code(code, wait=15)
print(out[-400:])

s.close()
print("\nDone.")
