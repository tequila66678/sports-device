"""Scan all SetWaitForAICamData modes for person showing ID1 on BE-1748 screen."""
import serial, time

s = serial.Serial('COM12', 115200, timeout=3)
time.sleep(0.5)
s.read(4096)

print("Person whose BE-1748 screen shows ID=1, stand in front!")
print("Scanning modes 0-15...")

for mode in range(16):
    s.write(b'\r\x03\x03')
    time.sleep(0.3)
    s.read(1024)
    s.write(b'\r\x01')
    time.sleep(0.3)
    s.read(256)

    code = (
        f'import rcu,utime\r\n'
        f'rcu.SetWaitForAICamData({mode},0)\r\n'
        f'utime.sleep_ms(300)\r\n'
        f'print(str(rcu.GetAICamData(1)))\r\n'
        f'utime.sleep_ms(100)\r\n'
        f'print(str(rcu.GetAICamData(2)))\r\n'
        f'utime.sleep_ms(100)\r\n'
        f'print(str(rcu.GetAICamData(3)))\r\n'
        f'print(\"M{mode}DONE\")\r\n'
    )
    s.write(code.encode())
    time.sleep(0.2)
    s.write(b'\x04')
    time.sleep(3)
    out = s.read(4096)
    text = out.decode('ascii', errors='replace')

    vals = []
    for line in text.split('\r\n'):
        line = line.strip().replace('\x04','').replace('>','').replace('OK','')
        if line.isdigit():
            vals.append(int(line))

    non_zero = [v for v in vals if v > 0]
    if non_zero:
        print(f'  Mode {mode}: cmd1={vals[0] if len(vals)>0 else \"?\"} '
              f'cmd2={vals[1] if len(vals)>1 else \"?\"} '
              f'cmd3={vals[2] if len(vals)>2 else \"?\"} '
              f'*** NON-ZERO! ***')
    else:
        print(f'  Mode {mode}: all zero')

s.write(b'\r\x03')
s.close()
print('\nDone.')
