"""BE-1748: explore SmartEye modes and face enrollment."""
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

# Test 1: Try SetSmartEyeMode with different values
print("=" * 60)
print("TEST 1: SetSmartEyeMode exploration")
print("=" * 60)
code = (
    "import rcu,utime\r\n"
    "for m in range(0,8):\r\n"
    "    try:\r\n"
    "        rcu.SetSmartEyeMode(m)\r\n"
    "        utime.sleep_ms(300)\r\n"
    "        r=rcu.GetAICamData(1)\r\n"
    "        print('SM'+str(m)+': cmd1='+str(r))\r\n"
    "    except Exception as e:\r\n"
    "        print('SM'+str(m)+': err='+str(e))\r\n"
    "print('sm_done')\r\n"
)
out = paste_code(code, wait=12)
print(out[-500:])

# Test 2: Try SetAICamData for potential enrollment
print("\n" + "=" * 60)
print("TEST 2: SetAICamData - enrollment attempt")
print("Face the camera clearly!")
print("=" * 60)
code = (
    "import rcu,utime\r\n"
    "# First init face recognition\r\n"
    "rcu.SetWaitForAICamData(2,0)\r\n"
    "utime.sleep_ms(500)\r\n"
    "# Try SetAICamData with different params\r\n"
    "for p in [1,2,3]:\r\n"
    "    rcu.SetAICamData(1,p)  # maybe cmd1=1,cmd2=face_id?\r\n"
    "    utime.sleep_ms(300)\r\n"
    "    print('enroll'+str(p)+': cmd1='+str(rcu.GetAICamData(1)))\r\n"
    "print('enroll_done')\r\n"
)
out = paste_code(code, wait=10)
print(out[-500:])

# Test 3: Continuous poll with face present - check if cmd1 returns different values
print("\n" + "=" * 60)
print("TEST 3: Continuous face poll - check if cmd1 value changes")
print("Move in/out of frame!")
print("=" * 60)
code = (
    "import rcu,utime\r\n"
    "rcu.SetWaitForAICamData(2,0)\r\n"
    "utime.sleep_ms(500)\r\n"
    "last = -1\r\n"
    "for i in range(20):\r\n"
    "    r=rcu.GetAICamData(1)\r\n"
    "    if r != last:\r\n"
    "        print('c1='+str(r)+' @'+str(i))\r\n"
    "        last = r\r\n"
    "    utime.sleep_ms(300)\r\n"
    "print('poll_done')\r\n"
)
out = paste_code(code, wait=15)
print(out[-500:])

# Test 4: Check ALL rcu functions
print("\n" + "=" * 60)
print("TEST 4: Full rcu function list")
print("=" * 60)
code = "import rcu\r\nfor f in dir(rcu):\r\n    print(f)\r\n"
out = paste_code(code, wait=5)
print(out[-1000:])

s.close()
print("\nDone.")
