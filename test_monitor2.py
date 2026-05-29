"""Test: raw REPL for continuous monitoring."""
import serial, time

s = serial.Serial('COM12', 115200, timeout=1)
time.sleep(0.5)
s.read(4096)

# Enter raw REPL
print("Entering raw REPL...")
s.write(b'\r\x03\x03')  # Interrupt
time.sleep(0.5)
s.read(1024)

s.write(b'\r\x01')  # Ctrl-A = raw REPL
time.sleep(0.5)
out = s.read(1024)
print(f"Raw REPL: {out[:100]}")

# In raw REPL, send code then Ctrl-D
code = (
    "import rcu,utime\r\n"
    "rcu.SetWaitForAICamData(10,0)\r\n"
    "utime.sleep_ms(800)\r\n"
    "lt=0\r\n"
    "for i in range(30):\r\n"
    " d=rcu.GetUltrasound(6)\r\n"
    " f=rcu.GetAICamData(1)\r\n"
    " t=utime.ticks_ms()\r\n"
    " if d>0 and d<50 and f!=0:\r\n"
    "  if utime.ticks_diff(t,lt)>2000 or lt==0:\r\n"
    "   lt=t\r\n"
    "   print('T|'+str(t)+'|'+str(f)+'|'+str(d))\r\n"
    " utime.sleep_ms(80)\r\n"
    "print('loop_done')\r\n"
)

print("Sending code via raw REPL...")
s.write(code.encode())
s.write(b'\x04')  # Ctrl-D
print("Waiting for execution (30 loops ≈ 3 seconds)...")
print("Stand in front of camera!")

time.sleep(6)
out = s.read(4096)
text = out.decode('ascii', errors='replace')

print("\n--- Output ---")
for line in text.split('\r\n'):
    line = line.strip()
    if 'T|' in line:
        print(f"  EVENT: {line}")
    elif 'loop_done' in line:
        print(f"  {line}")
    elif line and 'OK' not in line and 'import' not in line and len(line) < 100:
        print(f"  {line}")

# Exit raw REPL
s.write(b'\r\x03')
time.sleep(0.3)

s.close()
print("\nDone.")
