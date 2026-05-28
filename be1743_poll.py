"""Continuous poll BE-1743 via E6-RCU after handshake."""
import serial, time

s = serial.Serial('COM11', 115200, timeout=3)
time.sleep(0.5)
s.read(4096)

# Paste mode
s.write(b'\x05')
time.sleep(0.2)
s.read(256)

# Continuous poll after handshake
code = (
    "import ai,utime\r\n"
    "ai.SetWaitForAICamData(8,4)\r\n"
    "print('hs_done')\r\n"
    "for i in range(15):\r\n"
    "    for cmd in (1,5,7,8):\r\n"
    "        r=ai.GetAICamData(cmd)\r\n"
    "        if r!=0:\r\n"
    "            print('cmd'+str(cmd)+'='+str(r))\r\n"
    "    utime.sleep_ms(400)\r\n"
    "print('poll_done')\r\n"
)
s.write(code.encode())
time.sleep(0.2)
s.write(b'\x04')
time.sleep(12)  # 15 * 400ms ≈ 6s + handshake
out = s.read(4096)
print(out.decode('ascii', errors='replace'))

# Also try GetCamRecog
print("\n=== GetCamRecog ===")
for m in [5, 6, 7, 8]:
    s.write(f'sensor.GetCamRecog({m})\r\n'.encode())
    time.sleep(0.5)
    out = s.read(256)
    r = out.decode('ascii', errors='replace')
    for ln in r.split('\r\n'):
        ln = ln.strip()
        if ln and ln != '0' and '>>>' not in ln and 'GetCamRecog' not in ln:
            print(f'  mode{m}: {ln}')

s.close()
