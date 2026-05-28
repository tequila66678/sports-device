"""Read BE-1743 boot.py and find face recognition code."""
import serial, time

s = serial.Serial('COM10', 115200, timeout=2)
time.sleep(0.5)
s.reset_input_buffer()

# Stop any running program
s.write(b'\x03')
time.sleep(2.0)
s.read(4096)

# Send multiple read commands, capture output carefully
s.write(b'\x05')  # Ctrl-E paste mode
time.sleep(0.3)
s.read(256)

# Read first 50 lines of boot.py
code = (
    "try:\r\n"
    "    f=open('boot.py')\r\n"
    "    for i in range(50):\r\n"
    "        l=f.readline()\r\n"
    "        if not l:\r\n"
    "            break\r\n"
    "        print(str(i)+':'+l.rstrip())\r\n"
    "    f.close()\r\n"
    "except Exception as e:\r\n"
    "    print('ERR:',e)\r\n"
)
s.write(code.encode())
s.write(b'\x04')  # Ctrl-D
time.sleep(3.0)
out = s.read(8192)
print("=== boot.py (first 50 lines) ===")
print(out.decode('ascii', errors='replace'))

s.close()
