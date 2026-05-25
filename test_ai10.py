"""Quick test: AI-10 serial communication."""
import serial
import time

PORT = "COM6"
BAUD = 115200

SYNC = bytes([0xEF, 0xAA])

def calc_checksum(data):
    result = 0
    for b in data:
        result ^= b
    return result & 0xFF

def send_frame(ser, cmd_id, data=b''):
    size = len(data)
    payload = bytes([cmd_id, (size >> 8) & 0xFF, size & 0xFF]) + data
    checksum = calc_checksum(payload)
    frame = SYNC + payload + bytes([checksum])
    ser.write(frame)
    print(f"  SEND: {frame.hex()}")

print(f"Opening {PORT}...")
try:
    ser = serial.Serial(PORT, BAUD, timeout=0.5)
    print("[OK] Serial opened")
except Exception as e:
    print(f"[FAIL] {e}")
    input("Press Enter to exit...")
    exit(1)

print("Waiting for AI-10 READY message...")
buffer = b''
start = time.time()
ready = False

while time.time() - start < 5:
    chunk = ser.read(256)
    if chunk:
        buffer += chunk
        # Search for frames
        while len(buffer) >= 6:
            idx = buffer.find(SYNC)
            if idx < 0:
                buffer = buffer[-4:]
                break
            buffer = buffer[idx:]
            if len(buffer) < 6:
                break
            cmd = buffer[2]
            size = (buffer[3] << 8) | buffer[4]
            frame_end = 5 + size + 1
            if len(buffer) < frame_end:
                break
            data = buffer[5:5 + size]
            chk = buffer[5 + size]
            actual = calc_checksum(buffer[2:5 + size])
            if chk == actual:
                if cmd == 0x01 and len(data) >= 1 and data[0] == 0x00:
                    print("[OK] AI-10 READY!")
                    ready = True
                elif cmd == 0x01 and len(data) >= 1 and data[0] == 0x0A:
                    print(f"  AUTO_VERIFY: {data[1:].hex()}")
                    if len(data) >= 4 and data[1] == 0x01 and data[2] == 0x00:
                        user_id = (data[3] << 8) | data[4]
                        print(f"  >>> RECOGNIZED: user_id={user_id}")
                elif cmd == 0x01:
                    print(f"  NOTE: nid={data[0]:02X} data={data[1:].hex()}")
                elif cmd == 0x00:
                    print(f"  REPLY: {data.hex()}")
                else:
                    print(f"  CMD={cmd:02X}: {data.hex()}")
            else:
                pass
            buffer = buffer[frame_end:]
    if ready:
        break
    time.sleep(0.05)

if not ready:
    print("[WARN] No READY received. Trying RESET command...")
    send_frame(ser, 0x10)
    time.sleep(1)

# Start auto recognition
print("Starting auto recognition mode...")
send_frame(ser, 0x12, bytes([0x01, 0xFF]))  # at_verify=1, timeout=infinite

print("\nListening for face recognition... (look at camera, Ctrl+C to quit)\n")

try:
    while True:
        chunk = ser.read(256)
        if chunk:
            buffer += chunk
            while len(buffer) >= 6:
                idx = buffer.find(SYNC)
                if idx < 0:
                    buffer = buffer[-4:]
                    break
                buffer = buffer[idx:]
                if len(buffer) < 6:
                    break
                cmd = buffer[2]
                size = (buffer[3] << 8) | buffer[4]
                frame_end = 5 + size + 1
                if len(buffer) < frame_end:
                    break
                data = buffer[5:5 + size]
                chk = buffer[5 + size]
                actual = calc_checksum(buffer[2:5 + size])
                if chk == actual:
                    if cmd == 0x01 and len(data) >= 1 and data[0] == 0x0A:
                        if len(data) >= 4 and data[1] == 0x01 and data[2] == 0x00:
                            user_id = (data[3] << 8) | data[4]
                            print(f"  >>> MATCH: UserID={user_id}")
                        else:
                            print(f"  AUTO_VERIFY: {data[1:].hex()}")
                    elif cmd == 0x01:
                        print(f"  NOTE: nid={data[0]:02X} data={data[1:].hex()}")
                buffer = buffer[frame_end:]
        time.sleep(0.01)
except KeyboardInterrupt:
    print("\nDone.")
    ser.close()
