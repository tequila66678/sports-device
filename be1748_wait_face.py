"""BE-1748: wait for face and dump all data bytes for each mode."""
import serial, time

s = serial.Serial('COM12', 115200, timeout=3)
time.sleep(0.5)
s.read(4096)

def paste_code(code, wait=15):
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

# Test: Mode 10 face recognition, wait for face, dump ALL bytes
print("=" * 60)
print("MODE 10 FACE RECOGNITION - STAND IN FRONT OF CAMERA!")
print("(Waiting for face up to 15 seconds...)")
print("=" * 60)
code = (
    "import rcu,utime\r\n"
    "rcu.SetWaitForAICamData(10,0)\r\n"
    "utime.sleep_ms(500)\r\n"
    "found=False\r\n"
    "for i in range(30):\r\n"
    "    r1=rcu.GetAICamData(1)\r\n"
    "    if r1==1 and not found:\r\n"
    "        found=True\r\n"
    "        print('FACE_DETECTED!')\r\n"
    "        # Dump all 32 bytes\r\n"
    "        for cmd in range(0,32):\r\n"
    "            r=rcu.GetAICamData(cmd)\r\n"
    "            print('B'+str(cmd)+'='+str(r))\r\n"
    "        print('---')\r\n"
    "        # Also check mode 2 for comparison\r\n"
    "        rcu.SetWaitForAICamData(2,0)\r\n"
    "        utime.sleep_ms(500)\r\n"
    "        print('MODE2:')\r\n"
    "        for cmd in range(0,32):\r\n"
    "            r=rcu.GetAICamData(cmd)\r\n"
    "            print('B'+str(cmd)+'='+str(r))\r\n"
    "        # Back to mode 10\r\n"
    "        rcu.SetWaitForAICamData(10,0)\r\n"
    "        utime.sleep_ms(500)\r\n"
    "    utime.sleep_ms(500)\r\n"
    "if not found:\r\n"
    "    print('NO_FACE')\r\n"
    "print('done')\r\n"
)
out = paste_code(code, wait=25)
# Print the results clearly
for line in out.split('\r\n'):
    line = line.strip()
    if '=' in line and 'B' in line:
        print(f"  {line}")
    elif 'FACE' in line or 'MODE' in line or 'NO_FACE' in line:
        print(f"  *** {line} ***")

s.close()
print("\nDone.")
