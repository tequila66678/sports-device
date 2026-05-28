"""Single-shot face verification - simpler protocol."""
import serial, time

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
    chk = checksum(payload)
    frame = SYNC + payload + bytes([chk])
    ser.write(frame)
    return frame

ser = serial.Serial(PORT, BAUD, timeout=0.1)
print(f"Opened {PORT}")

buf = b''
# Wait for READY
t0 = time.time()
while time.time() - t0 < 5:
    buf += ser.read(256)
    while len(buf) >= 6:
        i = buf.find(SYNC)
        if i < 0: buf = buf[-4:]; break
        buf = buf[i:]
        if len(buf) < 6: break
        sz = (buf[3]<<8)|buf[4]
        end = 5+sz+1
        if len(buf) < end: break
        d = buf[5:5+sz]
        ck = checksum(buf[2:5+sz])
        if ck == buf[5+sz] and buf[2] == 0x01 and len(d) >= 1 and d[0] == 0x00:
            print("[OK] READY")
            t0 = -999; break
        buf = buf[end:]
    if t0 == -999: break
    time.sleep(0.1)

print("\nAttempting one-shot verification every 8 seconds.")
print("Stand in front of camera!\n")

for attempt in range(5):
    print(f"\n--- Attempt {attempt+1} ---")
    # Single-shot verify: at_verify=0, timeout=5
    send_frame(ser, 0x12, bytes([0x00, 0x05]))

    buf = b''
    t0 = time.time()
    while time.time() - t0 < 6:
        buf += ser.read(256)
        while len(buf) >= 6:
            i = buf.find(SYNC)
            if i < 0: buf = buf[-4:]; break
            buf = buf[i:]
            if len(buf) < 6: break
            sz = (buf[3]<<8)|buf[4]
            end = 5+sz+1
            if len(buf) < end: break
            d = buf[5:5+sz]
            ck = checksum(buf[2:5+sz])
            if ck == buf[5+sz]:
                cmd = buf[2]
                hexstr = buf[:end].hex()
                label = ""
                if cmd == 0x00 and len(d) >= 2:
                    mid, result = d[0], d[1]
                    label = f" REPLY mid=0x{mid:02X} result={result}"
                    if mid == 0x12 and result == 0 and len(d) >= 4:
                        uid = (d[2]<<8)|d[3]
                        label += f" >>> UserID={uid} <<<"
                elif cmd == 0x01 and len(d) >= 1:
                    label = f" NOTE nid=0x{d[0]:02X}"
                print(f"  {hexstr}{label}", flush=True)
            buf = buf[end:]
        time.sleep(0.05)

    time.sleep(2)

ser.close()
print("\nDone.")
