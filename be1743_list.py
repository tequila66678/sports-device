"""List files on BE-1743 and check face recognition capabilities."""
import serial, time

s = serial.Serial('COM10', 115200, timeout=2)
time.sleep(0.5)
s.read(4096)

# List files on flash
s.write(b"import os\r\n")
time.sleep(0.3)
s.read(1024)

s.write(b"os.listdir('/')\r\n")
time.sleep(1.0)
out = s.read(2048)
print("=== FILES ON FLASH ===")
print(out.decode('ascii', errors='replace'))

s.write(b"os.listdir('/sd')\r\n")
time.sleep(1.0)
out = s.read(2048)
print("=== SD CARD ===")
print(out.decode('ascii', errors='replace'))

# Check if face model files exist
for path in ['/face_model.kmodel', '/sd/face_model.kmodel', 'face_model.kmodel',
             '/detect.kmodel', '/sd/detect.kmodel']:
    s.write(f"try:\r\n    os.stat('{path}')\r\n    print('EXISTS: {path}')\r\nexcept:\r\n    pass\r\n".encode())
    time.sleep(0.5)
    out = s.read(512)
    r = out.decode('ascii', errors='replace')
    for ln in r.split('\r\n'):
        if 'EXISTS' in ln:
            print(ln.strip())

# Also try to import face recognition specific modules
for mod in ['face', 'face_recognition', 'face_detect', 'ai', 'zmrobo']:
    s.write(f"try:\r\n    import {mod}\r\n    print('IMPORT OK: {mod}')\r\nexcept Exception as e:\r\n    print(e)\r\n".encode())
    time.sleep(0.5)
    out = s.read(512)
    r = out.decode('ascii', errors='replace')
    for ln in r.split('\r\n'):
        ln = ln.strip()
        if 'IMPORT' in ln or ('Error' in ln and len(ln) < 100):
            print(ln.strip())

s.close()
print("Done")
