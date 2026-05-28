"""BE-1743 final test: correct API via E6-RCU paste mode."""
import serial, time, sys

# Try COM11 first, then COM9
ports = ['COM11', 'COM9', 'COM10']
s = None

for p in ports:
    try:
        s = serial.Serial(p, 115200, timeout=2)
        print(f"Opened {p}")
        break
    except Exception as e:
        print(f"  {p}: {e}")

if s is None:
    print("No COM port available!")
    sys.exit(1)

time.sleep(0.5)
s.read(4096)

def paste_code(code, wait=15):
    """Send MicroPython code via paste mode (Ctrl-E)."""
    s.reset_input_buffer()
    s.write(b'\x05')  # Ctrl-E enter paste mode
    time.sleep(0.3)
    s.read(256)
    s.write(code.encode())
    time.sleep(0.3)
    s.write(b'\x04')  # Ctrl-D execute
    time.sleep(wait)
    out = s.read(4096)
    return out.decode('ascii', errors='replace')

# Test round 1: Just the handshake with correct params (2, 0)
print("=" * 60)
print("TEST 1: Handshake with rcu.SetWaitForAICamData(2, 0)")
print("=" * 60)
code = (
    "import rcu,utime\r\n"
    "t0=utime.ticks_ms()\r\n"
    "rcu.SetWaitForAICamData(2,0)\r\n"
    "t1=utime.ticks_ms()\r\n"
    "print('hs_ok:', utime.ticks_diff(t1,t0), 'ms')\r\n"
)
out = paste_code(code, wait=15)
print(out[-500:])

# Test round 2: Poll GetAICamData(1) - face recognition result
print("\n" + "=" * 60)
print("TEST 2: Poll rcu.GetAICamData(1) - Face recognition")
print("Stand in front of BE-1743 camera!")
print("=" * 60)
code = (
    "import rcu,utime\r\n"
    "rcu.SetWaitForAICamData(2,0)\r\n"
    "utime.sleep_ms(1000)\r\n"
    "for i in range(10):\r\n"
    "    r=rcu.GetAICamData(1)\r\n"
    "    if r!=0:\r\n"
    "        print('R1='+str(r))\r\n"
    "    utime.sleep_ms(500)\r\n"
    "print('done')\r\n"
)
out = paste_code(code, wait=15)
print(out[-500:])

# Test round 3: All fields 1-14
print("\n" + "=" * 60)
print("TEST 3: All data fields (cmd 1-14)")
print("=" * 60)
code = (
    "import rcu,utime\r\n"
    "rcu.SetWaitForAICamData(2,0)\r\n"
    "utime.sleep_ms(500)\r\n"
    "for cmd in range(1,15):\r\n"
    "    r=rcu.GetAICamData(cmd)\r\n"
    "    print('cmd'+str(cmd)+'='+str(r))\r\n"
    "    utime.sleep_ms(100)\r\n"
    "print('fields_done')\r\n"
)
out = paste_code(code, wait=15)
print(out[-1000:])

s.close()
print("\nAll tests complete.")
