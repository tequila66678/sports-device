"""Upload boot.py to E6-RCU for standalone operation."""
import serial, time

PORT = "COM12"
BOOT_CODE = """f=open('boot.py','w')
f.write('import rcu,utime'+chr(10))
f.write('rcu.SetDisplayString(1,"BOOT_OK",0xFFE0,0x0000)'+chr(10))
f.write('print("AUTO_RUN")'+chr(10))
f.close()
print('BOOT_WRITTEN')"""

s = serial.Serial(PORT, 115200, timeout=2)
time.sleep(0.5)
s.read(4096)

# Enter raw REPL
s.write(b'\r\x03\x03')
time.sleep(0.5)
s.read(2048)
s.write(b'\r\x01')
time.sleep(0.5)
resp = s.read(256)
print(f"REPL: {resp[:60]}")

# Send code
print("Sending boot.py...")
s.write(BOOT_CODE.encode())
time.sleep(0.3)
s.write(b'\x04')
time.sleep(3)

out = s.read(4096)
text = out.decode('ascii', errors='replace')
print(f"Output: {text}")

# Verify
s.write(b'\r\x03')
time.sleep(0.3)
s.read(256)
s.write(b'\r\x01')
time.sleep(0.3)
s.read(256)

verify = (
    "f=open('boot.py','r')\r\n"
    "print('CONTENT:'+repr(f.read()[:200]))\r\n"
    "f.close()\r\n"
)
s.write(verify.encode())
time.sleep(0.2)
s.write(b'\x04')
time.sleep(2)
out = s.read(4096)
print(out.decode('ascii', errors='replace'))

s.write(b'\r\x03')
s.close()
print("\nDone. Power-cycle E6-RCU to test auto-run.")
