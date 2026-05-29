"""Full system test: BE-6311(ultrasonic P6) + BE-1748(face P8) via E6-RCU."""
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

# Test 1: Init mode 10 + poll face ID
print("=" * 60)
print("TEST 1: Face recognition (mode 10)")
print("Stand in front of camera!")
print("=" * 60)
code = (
    "import rcu,utime\r\n"
    "rcu.SetWaitForAICamData(10,0)\r\n"
    "utime.sleep_ms(1000)\r\n"
    "for i in range(8):\r\n"
    "    r=rcu.GetAICamData(1)\r\n"
    "    print('ID='+str(r))\r\n"
    "    utime.sleep_ms(400)\r\n"
    "print('face_done')\r\n"
)
out = paste_code(code, wait=12)
for line in out.split('\r\n'):
    line = line.strip()
    if 'ID=' in line:
        print(f"  {line}")

# Test 2: Ultrasonic distance
print("\n" + "=" * 60)
print("TEST 2: Ultrasonic distance (P6)")
print("=" * 60)
code = (
    "import rcu,utime\r\n"
    "for i in range(5):\r\n"
    "    d=rcu.GetUltrasound(6)\r\n"
    "    print('dist='+str(d))\r\n"
    "    utime.sleep_ms(300)\r\n"
    "print('ultra_done')\r\n"
)
out = paste_code(code, wait=8)
for line in out.split('\r\n'):
    line = line.strip()
    if 'dist=' in line:
        print(f"  {line}")

# Test 3: Combined - face ID + distance simultaneously
print("\n" + "=" * 60)
print("TEST 3: Face ID + Distance simultaneous")
print("Stand in front, move closer/further!")
print("=" * 60)
code = (
    "import rcu,utime\r\n"
    "rcu.SetWaitForAICamData(10,0)\r\n"
    "utime.sleep_ms(500)\r\n"
    "for i in range(10):\r\n"
    "    fid=rcu.GetAICamData(1)\r\n"
    "    dist=rcu.GetUltrasound(6)\r\n"
    "    print(str(fid)+','+str(dist))\r\n"
    "    utime.sleep_ms(350)\r\n"
    "print('dual_done')\r\n"
)
out = paste_code(code, wait=12)
for line in out.split('\r\n'):
    line = line.strip()
    if ',' in line and line[0].isdigit():
        parts = line.split(',')
        fid = parts[0]
        dist = parts[1] if len(parts) > 1 else '?'
        marker = ' <-- FACE!' if fid != '0' else ''
        print(f"  ID={fid}  Dist={dist}cm{marker}")

s.close()
print("\nDone.")
