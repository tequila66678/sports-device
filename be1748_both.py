"""BE-1748: test both AI Camera + SmartEye protocols."""
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

# Test 1: SmartEye distance + mode
print("=" * 60)
print("TEST 1: GetSmartEyeDist from BE-1748 on P8")
print("=" * 60)
code = (
    "import rcu,utime\r\n"
    "# Try GetSmartEyeDist\r\n"
    "for i in range(5):\r\n"
    "    d=rcu.GetSmartEyeDist(8)\r\n"
    "    print('dist='+str(d))\r\n"
    "    utime.sleep_ms(300)\r\n"
    "print('dist_done')\r\n"
)
out = paste_code(code, wait=8)
print(out[-400:])

# Test 2: SetSmartEyeMode(8, mode, color)
print("\n" + "=" * 60)
print("TEST 2: SetSmartEyeMode(8, mode, 0)")
print("=" * 60)
code = (
    "import rcu,utime\r\n"
    "for m in range(0,8):\r\n"
    "    rcu.SetSmartEyeMode(8,m,0)\r\n"
    "    utime.sleep_ms(200)\r\n"
    "    d=rcu.GetSmartEyeDist(8)\r\n"
    "    print('SM'+str(m)+' dist='+str(d))\r\n"
    "print('mode_done')\r\n"
)
out = paste_code(code, wait=12)
print(out[-500:])

# Test 3: Face detect + SmartEye dist simultaneously
print("\n" + "=" * 60)
print("TEST 3: Face detect + distance simultaneously")
print("Stand in front of camera at different distances!")
print("=" * 60)
code = (
    "import rcu,utime\r\n"
    "rcu.SetWaitForAICamData(2,0)\r\n"
    "utime.sleep_ms(500)\r\n"
    "for i in range(10):\r\n"
    "    face=rcu.GetAICamData(1)\r\n"
    "    dist=rcu.GetSmartEyeDist(8)\r\n"
    "    if face!=0 or dist>0:\r\n"
    "        print('F='+str(face)+' D='+str(dist))\r\n"
    "    utime.sleep_ms(400)\r\n"
    "print('dual_done')\r\n"
)
out = paste_code(code, wait=12)
print(out[-500:])

# Test 4: Check if GetSmartEyeIRcode works (might return face ID?)
print("\n" + "=" * 60)
print("TEST 4: GetSmartEyeIRcode(8)")
print("=" * 60)
code = (
    "import rcu,utime\r\n"
    "rcu.SetSmartEyeMode(8,1,0)\r\n"
    "utime.sleep_ms(300)\r\n"
    "for i in range(5):\r\n"
    "    ir=rcu.GetSmartEyeIRcode(8)\r\n"
    "    print('IR='+str(ir))\r\n"
    "    utime.sleep_ms(300)\r\n"
    "print('ir_done')\r\n"
)
out = paste_code(code, wait=8)
print(out[-400:])

s.close()
print("\nDone.")
