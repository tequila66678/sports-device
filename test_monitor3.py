"""Test: raw REPL, 50 loops, stand in front!"""
import serial, time

s = serial.Serial('COM12', 115200, timeout=1)
time.sleep(0.5)
s.read(4096)

# Enter raw REPL
s.write(b'\r\x03\x03')
time.sleep(0.5)
s.read(1024)
s.write(b'\r\x01')
time.sleep(0.5)
s.read(1024)

# 50 loops = ~5 seconds at 100ms interval
code = (
    "import rcu,utime\r\n"
    "rcu.SetWaitForAICamData(10,0)\r\n"
    "utime.sleep_ms(800)\r\n"
    "lt=0\r\n"
    "for i in range(50):\r\n"
    " d=rcu.GetUltrasound(6)\r\n"
    " f=rcu.GetAICamData(1)\r\n"
    " t=utime.ticks_ms()\r\n"
    " if f!=0:\r\n"
    "  print('FACE|'+str(t)+'|'+str(f))\r\n"
    " if d>0 and d<50:\r\n"
    "  print('DIST|'+str(t)+'|'+str(d))\r\n"
    " utime.sleep_ms(90)\r\n"
    "print('END')\r\n"
)

print("Sending code... STAND IN FRONT OF CAMERA NOW!")
s.write(code.encode())
s.write(b'\x04')
time.sleep(8)
out = s.read(4096)
text = out.decode('ascii', errors='replace')

print("\n--- Results ---")
for line in text.split('\r\n'):
    line = line.strip()
    if 'FACE|' in line or 'DIST|' in line or 'END' in line:
        print(f"  {line}")

s.write(b'\r\x03')
s.close()
print("Done.")
