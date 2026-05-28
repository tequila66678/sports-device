"""Live single-shot face recognition - continuous polling."""
import serial, time, threading

PORT = "COM3"
BAUD = 115200
SYNC = bytes([0xEF, 0xAA])

def checksum(data):
    r = 0
    for b in data: r ^= b
    return r & 0xFF

def send_frame(ser, cmd, data=b''):
    size = len(data)
    payload = bytes([cmd, (size>>8)&0xFF, size&0xFF]) + data
    ser.write(SYNC + payload + bytes([checksum(payload)]))

ser = serial.Serial(PORT, BAUD, timeout=0.1)
buf = b''
buf_lock = threading.Lock()
alive = [True]

def reader():
    global buf
    while alive[0]:
        try:
            chunk = ser.read(256)
            if chunk:
                with buf_lock: buf += chunk
        except: break
threading.Thread(target=reader, daemon=True).start()

# Wait for READY
t0 = time.time()
while time.time() - t0 < 3:
    with buf_lock:
        while len(buf) >= 6:
            i = buf.find(SYNC)
            if i < 0: buf = buf[-4:]; break
            buf = buf[i:]
            if len(buf) < 6: break
            sz = (buf[3]<<8)|buf[4]
            end = 5+sz+1
            if len(buf) < end: break
            d = buf[5:5+sz]
            if checksum(buf[2:5+sz]) == buf[5+sz] and buf[2]==0x01 and len(d)>=1 and d[0]==0x00:
                print("[OK] READY")
                t0 = -999; break
            buf = buf[end:]
    if t0 == -999: break
    time.sleep(0.1)

print("Live recognition started. Stand in front of camera!\n")

last_uid = None
while alive[0]:
    send_frame(ser, 0x12, bytes([0x00, 0x03]))
    deadline = time.time() + 4
    while time.time() < deadline:
        with buf_lock:
            while len(buf) >= 6:
                i = buf.find(SYNC)
                if i < 0: buf = buf[-4:]; break
                buf = buf[i:]
                if len(buf) < 6: break
                sz = (buf[3]<<8)|buf[4]
                end = 5+sz+1
                if len(buf) < end: break
                d = buf[5:5+sz]
                if checksum(buf[2:5+sz]) == buf[5+sz]:
                    if buf[2] == 0x00 and len(d) >= 4 and d[0]==0x12 and d[1]==0:
                        uid = (d[2]<<8)|d[3]
                        name = d[4:].rstrip(b'\x00').decode('utf-8', errors='ignore')
                        if uid != last_uid:
                            print(f">>> RECOGNIZED: UserID={uid} name={name}")
                            last_uid = uid
                        deadline = 0
                buf = buf[end:]
        time.sleep(0.02)
    time.sleep(0.1)
