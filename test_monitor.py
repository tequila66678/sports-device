"""Quick test: inject monitoring loop and read events for 15 seconds."""
import serial, time, threading

MONITOR_CODE = (
    "import rcu,utime\r\n"
    "rcu.SetWaitForAICamData(10,0)\r\n"
    "utime.sleep_ms(800)\r\n"
    "lt=0\r\n"
    "while True:\r\n"
    " d=rcu.GetUltrasound(6)\r\n"
    " f=rcu.GetAICamData(1)\r\n"
    " t=utime.ticks_ms()\r\n"
    " if d>0 and d<50 and f!=0:\r\n"
    "  if utime.ticks_diff(t,lt)>3000 or lt==0:\r\n"
    "   lt=t\r\n"
    "   print('T|'+str(t)+'|'+str(f)+'|'+str(d))\r\n"
    " utime.sleep_ms(60)\r\n"
)

s = serial.Serial('COM12', 115200, timeout=1)
time.sleep(0.5)
s.read(4096)

# Ctrl-C
s.write(b'\r\x03\x03')
time.sleep(0.5)
s.read(1024)

# Paste mode inject
print("Injecting monitor code...")
s.write(b'\x05')
time.sleep(0.3)
s.read(256)
s.write(MONITOR_CODE.encode())
time.sleep(0.5)
s.write(b'\x04')
print("Code sent. Reading events for 15 seconds...")
print("Stand in front of camera and move within 50cm of ultrasonic!")
print("-" * 40)

# Continuous read
stop = time.time() + 15
buf = ""
while time.time() < stop:
    data = s.read(128)
    if data:
        buf += data.decode('ascii', errors='replace')
        while '\n' in buf:
            line, buf = buf.split('\n', 1)
            line = line.strip()
            if 'T|' in line:
                print(f"  EVENT: {line}")
            elif 'dist=' in line or 'ID=' in line:
                print(f"  DEBUG: {line}")
    time.sleep(0.05)

# Ctrl-C to stop the loop
print("\nStopping monitor...")
s.write(b'\r\x03\x03')
time.sleep(1)
s.read(1024)

s.close()
print("Done.")
