"""AI-10 test: face recognition + enrollment via serial."""
import serial
import sys
import threading
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
    return frame

print(f"Opening {PORT}...")
try:
    ser = serial.Serial(PORT, BAUD, timeout=0.1)
    print("[OK] Serial opened")
except Exception as e:
    print(f"[FAIL] {e}")
    input("Press Enter to exit...")
    exit(1)

buffer = b''
buffer_lock = threading.Lock()
alive = [True]

def serial_reader():
    while alive[0]:
        try:
            chunk = ser.read(256)
            if chunk:
                with buffer_lock:
                    global buffer
                    buffer += chunk
        except:
            if alive[0]:
                print("[WARN] Serial read error")
            break

reader_thread = threading.Thread(target=serial_reader, daemon=True)
reader_thread.start()

def process_messages(quiet=True):
    """Parse all complete frames in buffer, return list of parsed messages.
    If quiet=True, suppresses face detection spam and prints only important events."""
    global buffer
    results = []
    with buffer_lock:
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
                if not quiet:
                    results.append((cmd, data))
                else:
                    # Only keep important messages (not face position spam)
                    if cmd == 0x01:
                        nid = data[0] if len(data) >= 1 else None
                        if nid == 0x0A:  # Recognition result
                            results.append((cmd, data))
                        elif nid == 0x00:  # READY
                            results.append((cmd, data))
                        # Skip nid=0x01 (face position) - too much spam
                    else:
                        results.append((cmd, data))
            buffer = buffer[frame_end:]
    return results

def wait_for(match_fn, timeout=5.0):
    """Wait for a message matching match_fn. Returns (cmd, data) or (None, None)."""
    start = time.time()
    while time.time() - start < timeout:
        for cmd, data in process_messages():
            if cmd == 0x01 and len(data) >= 1 and data[0] == 0x01:
                continue  # Skip face position spam
            if match_fn(cmd, data):
                return (cmd, data)
            if cmd == 0x01 and len(data) >= 1:
                nid = data[0]
                if nid == 0x0A:
                    if len(data) >= 3 and data[1] == 0x01:
                        if data[2] == 0x00 and len(data) >= 5:
                            uid = (data[3] << 8) | data[4]
                            print(f"  >>> RECOGNIZED: UserID={uid}")
                        elif data[2] == 0x08:
                            print(f"  [Unknown face]")
        time.sleep(0.05)
    return (None, None)

# Wait for READY
print("Waiting for AI-10...")
wait_for(lambda c, d: c == 0x01 and len(d) >= 1 and d[0] == 0x00, 5)
print("[OK] AI-10 ready")

# Reset
send_frame(ser, 0x10)
time.sleep(0.5)
process_messages()

# Start auto recognition
send_frame(ser, 0x12, bytes([0x01, 0xFF]))
print("[OK] Auto recognition started")

print("""
========================================
  Commands (type and press Enter):
    r 101   - Register face for bib 101
    d 101   - Delete user 101
    v       - Re-start auto verify
    q       - Quit
========================================
""")

try:
    import msvcrt
    has_kb = True
except ImportError:
    has_kb = False

cmd_buffer = ""
last_display = 0

while alive[0]:
    # Process incoming messages
    for cmd, data in process_messages(quiet=True):
        if cmd == 0x01:
            nid = data[0]
            if nid == 0x0A and len(data) >= 4 and data[1] == 0x01 and data[2] == 0x00:
                uid = (data[3] << 8) | data[4]
                print(f">>> RECOGNIZED: UserID={uid}")
        elif cmd == 0x00 and len(data) >= 2:
            mid, result = data[0], data[1]
            rname = {0:"OK",1:"REJECTED",8:"NOT_FOUND",10:"ALREADY_EXISTS",13:"TIMEOUT"}.get(result, f"ERR={result}")
            if mid in (0x13, 0x1D):
                if result == 0 and len(data) >= 4:
                    print(f">>> ENROLL OK! UserID={(data[2]<<8)|data[3]}")
                else:
                    print(f"[ENROLL] {rname}")
            elif mid == 0x20:
                print(f"[DELETE] {rname}")

    # Keyboard input
    if has_kb:
        while msvcrt.kbhit():
            ch = msvcrt.getch()
            if ch in (b'\r', b'\n'):
                parts = cmd_buffer.strip().split()
                cmd_buffer = ""
                if not parts:
                    continue
                if parts[0] == 'q':
                    alive[0] = False
                    break
                elif parts[0] == 'r' and len(parts) >= 2:
                    try:
                        uid = int(parts[1])
                    except:
                        print("Invalid ID")
                        continue
                    print(f"\nRegistering face for ID={uid}...")
                    print("  Stand in front of camera, look straight ahead")
                    # Stop auto verify
                    send_frame(ser, 0x10)
                    time.sleep(0.3)
                    process_messages()
                    # Enroll
                    name = str(uid).encode('utf-8')[:32].ljust(32, b'\x00')
                    data = bytes([0x00]) + name + bytes([0xFD, 15])
                    send_frame(ser, 0x13, data)
                    # Wait for result
                    def is_enroll_reply(c, d):
                        return c == 0x00 and len(d) >= 2 and d[0] in (0x13, 0x1D)
                    c, d = wait_for(is_enroll_reply, 18)
                    if c is None:
                        print("  [TIMEOUT] No response from AI-10")
                    # Restart auto verify
                    time.sleep(0.5)
                    send_frame(ser, 0x12, bytes([0x01, 0xFF]))
                    print("  Auto recognition restarted")
                elif parts[0] == 'd' and len(parts) >= 2:
                    try:
                        uid = int(parts[1])
                    except:
                        print("Invalid ID")
                        continue
                    print(f"\nDeleting user ID={uid}...")
                    send_frame(ser, 0x10)
                    time.sleep(0.2)
                    process_messages()
                    send_frame(ser, 0x20, bytes([(uid >> 8) & 0xFF, uid & 0xFF]))
                    time.sleep(0.5)
                    send_frame(ser, 0x12, bytes([0x01, 0xFF]))
                    print("  Done")
                elif parts[0] == 'v':
                    send_frame(ser, 0x10)
                    time.sleep(0.3)
                    process_messages()
                    send_frame(ser, 0x12, bytes([0x01, 0xFF]))
                    print("  Auto recognition restarted")
                else:
                    print(f"  Unknown command: {parts[0]}")
                print("> ", end='', flush=True)
            else:
                try:
                    cmd_buffer += ch.decode('ascii')
                    print(ch.decode('ascii'), end='', flush=True)
                except:
                    pass
    else:
        cmd = input("> ").strip().split()
        if cmd:
            if cmd[0] == 'q':
                alive[0] = False
                break
            elif cmd[0] == 'r' and len(cmd) >= 2:
                uid = int(cmd[1])
                print(f"Registering face for ID={uid}...")
                send_frame(ser, 0x10)
                time.sleep(0.3)
                process_messages()
                name = str(uid).encode('utf-8')[:32].ljust(32, b'\x00')
                send_frame(ser, 0x13, bytes([0x00]) + name + bytes([0xFD, 15]))
                wait_for(lambda c, d: c == 0x00 and len(d) >= 2 and d[0] in (0x13, 0x1D), 18)
                send_frame(ser, 0x12, bytes([0x01, 0xFF]))

    time.sleep(0.05)

print("\nDone.")
alive[0] = False
ser.close()
