"""Test BE-1743 handshake protocol on E6-RCU P8 - using paste mode."""
import serial, time

s = serial.Serial('COM11', 115200, timeout=5)
time.sleep(0.5)
s.read(4096)

def send_paste(code, wait=10):
    """Send code via paste mode (Ctrl-E)."""
    s.write(b'\x05')  # Ctrl-E
    time.sleep(0.3)
    s.read(256)
    s.write(code.encode())
    time.sleep(0.3)
    s.write(b'\x04')  # Ctrl-D
    time.sleep(wait)
    out = s.read(4096)
    return out.decode('ascii', errors='replace')

# Test 1: Measure handshake time
print("=== Handshake timing test (may take 15+ seconds) ===")
code = (
    "import ai,utime\r\n"
    "t0=utime.ticks_ms()\r\n"
    "ai.SetWaitForAICamData(8,2)\r\n"
    "t1=utime.ticks_ms()\r\n"
    "print('elapsed ms:', utime.ticks_diff(t1,t0))\r\n"
)
r = send_paste(code, wait=15)
print(r[-400:])

# Test 2: Poll after handshake
print("\n=== Poll GetAICamData ===")
for i in [1, 5, 7, 8]:
    s.write(f'ai.GetAICamData({i})\r\n'.encode())
    time.sleep(0.5)
    out = s.read(256)
    r = out.decode('ascii', errors='replace')
    for ln in r.split('\r\n'):
        ln = ln.strip()
        if ln and ln != '0' and '>>>' not in ln and 'GetAICamData' not in ln:
            print(f'  cmd{i}: {ln}')

# Test 3: Try with different cmd0 values
print("\n=== Try cmd0=0, 1, 2 ===")
for cmd0 in [0, 1, 2]:
    code = (
        f"import ai,utime\r\n"
        f"t0=utime.ticks_ms()\r\n"
        f"ai.SetWaitForAICamData({cmd0},2)\r\n"
        f"t1=utime.ticks_ms()\r\n"
        f"print('cmd0={cmd0} elapsed:', utime.ticks_diff(t1,t0))\r\n"
    )
    r = send_paste(code, wait=15)
    print(r[-200:])

s.close()
print("\nDone")
