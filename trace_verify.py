"""Sniff what PC tool sends for auto-recognition."""
import serial, time

PORT = "COM3"
BAUD = 115200
SYNC = bytes([0xEF, 0xAA])

def calc_checksum(data):
    r = 0
    for b in data: r ^= b
    return r & 0xFF

ser = serial.Serial(PORT, BAUD, timeout=0.1)
print("[OK] Listening... (start recognition in PC tool now)")
print("      Then close PC tool and watch for recognition here.\n")

buf = b''
last_hex = None
try:
    while True:
        buf += ser.read(256)
        while len(buf) >= 6:
            i = buf.find(SYNC)
            if i < 0: buf = buf[-4:]; break
            buf = buf[i:]
            if len(buf) < 6: break
            sz = (buf[3] << 8) | buf[4]
            end = 5 + sz + 1
            if len(buf) < end: break
            d = buf[5:5+sz]
            chk = buf[5+sz]
            actual = calc_checksum(buf[2:5+sz])
            if chk == actual:
                h = buf[:end].hex()
                cmd = buf[2]
                label = ""
                if cmd == 0x00 and len(d) >= 2:
                    label = f"  REPLY mid=0x{d[0]:02X} result={d[1]}"
                elif cmd == 0x01 and len(d) >= 1:
                    label = f"  NOTE nid=0x{d[0]:02X}"
                    if d[0] == 0x0A and len(d) >= 3:
                        label += f" status={d[1]} result={d[2]}"
                        if d[2] == 0 and len(d) >= 5:
                            label += f" UserID={(d[3]<<8)|d[4]}"
                if h != last_hex:
                    print(f"{h}{label}", flush=True)
                    last_hex = h
            buf = buf[end:]
except KeyboardInterrupt:
    print("\nDone.")
    ser.close()
