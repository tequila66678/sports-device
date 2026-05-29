"""Quick face ID test for new registrations."""
import serial, time, sys

s = serial.Serial('COM12', 115200, timeout=3)
time.sleep(0.5)
s.read(4096)
s.write(b'\r\x03\x03')
time.sleep(0.5)
s.read(1024)
s.write(b'\r\x01')
time.sleep(0.3)
s.read(256)

code = (
    'import rcu,utime\r\n'
    'rcu.SetWaitForAICamData(10,0)\r\n'
    'utime.sleep_ms(500)\r\n'
    'print("F0="+str(rcu.GetAICamData(1)))\r\n'
    'utime.sleep_ms(400)\r\n'
    'print("F1="+str(rcu.GetAICamData(1)))\r\n'
    'utime.sleep_ms(400)\r\n'
    'print("F2="+str(rcu.GetAICamData(1)))\r\n'
    'utime.sleep_ms(400)\r\n'
    'print("F3="+str(rcu.GetAICamData(1)))\r\n'
    'utime.sleep_ms(400)\r\n'
    'print("F4="+str(rcu.GetAICamData(1)))\r\n'
    'print("END")\r\n'
)
s.write(code.encode())
time.sleep(0.3)
s.write(b'\x04')
time.sleep(6)
out = s.read(4096)
text = out.decode('ascii', errors='replace')

for line in text.split('\r\n'):
    line = line.strip().replace('\x04', '').replace('>', '').replace('OK', '')
    if line.startswith('F') and '=' in line:
        try:
            fid = int(line.split('=')[1])
            if fid == 99:
                print(f'  {line} (your old face)')
            elif fid != 0:
                print(f'  {line} *** NEW FACE ID! ***')
            else:
                print(f'  {line}')
        except ValueError:
            pass

s.write(b'\r\x03')
s.close()
