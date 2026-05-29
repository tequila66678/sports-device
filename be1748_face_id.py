"""BE-1748: GetCamRecog for face ID, position, size."""
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

# Test 1: Init + GetCamRecog for ID, X, Y, Size
print("=" * 60)
print("TEST 1: Face recognition - ID, X, Y, Size")
print("STAND IN FRONT OF CAMERA NOW!")
print("=" * 60)
code = (
    "import rcu,utime\r\n"
    "rcu.SetWaitForAICamData(2,0)\r\n"
    "utime.sleep_ms(1000)\r\n"
    "for i in range(15):\r\n"
    "    print('F'+str(i)+': ID='+str(rcu.GetCamRecog(7))+' X='+str(rcu.GetCamRecog(5))+' Y='+str(rcu.GetCamRecog(6))+' SZ='+str(rcu.GetCamRecog(8)))\r\n"
    "    utime.sleep_ms(400)\r\n"
    "print('scan_done')\r\n"
)
out = paste_code(code, wait=15)
print(out[-800:])

# Test 2: Without SetWaitForAICamData - does GetCamRecog work standalone?
print("\n" + "=" * 60)
print("TEST 2: GetCamRecog without handshake")
print("Still in front of camera!")
print("=" * 60)
code = (
    "import rcu,utime\r\n"
    "for i in range(5):\r\n"
    "    print('R: ID='+str(rcu.GetCamRecog(7))+' X='+str(rcu.GetCamRecog(5)))\r\n"
    "    utime.sleep_ms(400)\r\n"
    "print('done')\r\n"
)
out = paste_code(code, wait=8)
print(out[-400:])

# Test 3: Check GetWifiPictureData for QR code ID
print("\n" + "=" * 60)
print("TEST 3: GetWifiPictureData")
print("=" * 60)
code = (
    "import rcu,utime\r\n"
    "# Check if function exists\r\n"
    "funcs = [f for f in dir(rcu) if 'WifiPicture' in f]\r\n"
    "print('WifiPicture funcs:', funcs)\r\n"
)
out = paste_code(code, wait=5)
print(out[-400:])

# Test 4: Compare GetAICamData(1) vs GetCamRecog(7)
print("\n" + "=" * 60)
print("TEST 4: Compare both APIs side by side")
print("Face camera!")
print("=" * 60)
code = (
    "import rcu,utime\r\n"
    "rcu.SetWaitForAICamData(2,0)\r\n"
    "utime.sleep_ms(500)\r\n"
    "for i in range(10):\r\n"
    "    a=rcu.GetAICamData(1)\r\n"
    "    b=rcu.GetCamRecog(7)\r\n"
    "    c=rcu.GetCamRecog(5)\r\n"
    "    d=rcu.GetCamRecog(6)\r\n"
    "    if a!=0 or b!=0:\r\n"
    "        print('AI='+str(a)+' ID='+str(b)+' X='+str(c)+' Y='+str(d))\r\n"
    "    utime.sleep_ms(300)\r\n"
    "print('compare_done')\r\n"
)
out = paste_code(code, wait=12)
print(out[-500:])

s.close()
print("\nDone.")
