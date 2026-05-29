"""BE-1748: simple mode 10 test - dump bytes when face detected."""
import serial, time

s = serial.Serial('COM12', 115200, timeout=3)
time.sleep(0.5)
s.read(4096)

def paste_code(code, wait=12):
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

# Step 1: Init mode 10
print("Step 1: Init mode 10...")
code = (
    "import rcu\r\n"
    "rcu.SetWaitForAICamData(10,0)\r\n"
    "print('init_ok')\r\n"
)
out = paste_code(code, wait=10)
print(out[-200:])

# Step 2: poll once, print cmd 0-7
print("\nStep 2: Poll cmd 0-7 (stand in front!)...")
code = (
    "import rcu\r\n"
    "print('c0='+str(rcu.GetAICamData(0)))\r\n"
    "print('c1='+str(rcu.GetAICamData(1)))\r\n"
    "print('c2='+str(rcu.GetAICamData(2)))\r\n"
    "print('c3='+str(rcu.GetAICamData(3)))\r\n"
    "print('c4='+str(rcu.GetAICamData(4)))\r\n"
    "print('c5='+str(rcu.GetAICamData(5)))\r\n"
    "print('c6='+str(rcu.GetAICamData(6)))\r\n"
    "print('c7='+str(rcu.GetAICamData(7)))\r\n"
)
out = paste_code(code, wait=8)
for line in out.split('\r\n'):
    line = line.strip()
    if line.startswith('c'):
        print(f"  {line}")

# Step 3: poll cmd 8-15
print("\nStep 3: Poll cmd 8-15 (still in front!)...")
code = (
    "import rcu\r\n"
    "print('c8='+str(rcu.GetAICamData(8)))\r\n"
    "print('c9='+str(rcu.GetAICamData(9)))\r\n"
    "print('c10='+str(rcu.GetAICamData(10)))\r\n"
    "print('c11='+str(rcu.GetAICamData(11)))\r\n"
    "print('c12='+str(rcu.GetAICamData(12)))\r\n"
    "print('c13='+str(rcu.GetAICamData(13)))\r\n"
    "print('c14='+str(rcu.GetAICamData(14)))\r\n"
    "print('c15='+str(rcu.GetAICamData(15)))\r\n"
)
out = paste_code(code, wait=8)
for line in out.split('\r\n'):
    line = line.strip()
    if line.startswith('c'):
        print(f"  {line}")

# Step 4: Also test mode 2 for comparison
print("\nStep 4: Switch to mode 2, poll cmd 0-7...")
code = (
    "import rcu,utime\r\n"
    "rcu.SetWaitForAICamData(2,0)\r\n"
    "utime.sleep_ms(500)\r\n"
    "print('m2_c1='+str(rcu.GetAICamData(1)))\r\n"
    "print('m2_c2='+str(rcu.GetAICamData(2)))\r\n"
    "print('m2_c3='+str(rcu.GetAICamData(3)))\r\n"
    "print('m2_c4='+str(rcu.GetAICamData(4)))\r\n"
)
out = paste_code(code, wait=10)
for line in out.split('\r\n'):
    line = line.strip()
    if line.startswith('m2'):
        print(f"  {line}")

s.close()
print("\nDone.")
