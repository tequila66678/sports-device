"""BE-1748: try to discover face registration mode."""
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

# Test modes 0-15 for SetWaitForAICamData and check cmd1
print("=" * 60)
print("Scan all modes 0-15 - check cmd1 value")
print("Keep face in front of camera!")
print("=" * 60)

for mode in range(0, 16):
    code = (
        f"import rcu,utime\r\n"
        f"rcu.SetWaitForAICamData({mode},0)\r\n"
        f"utime.sleep_ms(400)\r\n"
        f"r=rcu.GetAICamData(1)\r\n"
        f"print('M{mode}='+str(r))\r\n"
    )
    out = paste_code(code, wait=8)
    for line in out.split('\r\n'):
        line = line.strip()
        if line.startswith(f'M{mode}='):
            val = line.split('=')[1]
            marker = ' <--' if val != '0' else ''
            print(f"  {line}{marker}")

s.close()
print("\nDone.")
