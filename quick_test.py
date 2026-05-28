"""Quick E2E test: Arduino + AI-10, no API."""
import csv, queue, threading, time, sys
from collections import namedtuple

PORT_AI10 = "COM3"
PORT_ARD = "COM6"
SYNC = bytes([0xEF, 0xAA])

def calc_checksum(data):
    r = 0
    for b in data: r ^= b
    return r & 0xFF

def send_frame(ser, cmd, data=b''):
    size = len(data)
    payload = bytes([cmd, (size>>8)&0xFF, size&0xFF]) + data
    ser.write(SYNC + payload + bytes([calc_checksum(payload)]))

# Load athletes
athletes = {}
with open("athletes.csv", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        bib = row["bib"].strip()
        athletes[bib] = {"name": row["name"].strip(), "student_id": row.get("student_id","").strip()}

print(f"Loaded {len(athletes)} athletes")

# Open serial
import serial
ser_ai10 = serial.Serial(PORT_AI10, 115200, timeout=0.1)
ser_ard = None
try:
    ser_ard = serial.Serial(PORT_ARD, 115200, timeout=1.0)
    ser_ard.reset_input_buffer()
    print(f"[OK] Arduino on {PORT_ARD}")
except Exception as e:
    print(f"[WARN] Arduino not available: {e}")

# Face buffer
FaceEvent = namedtuple("FaceEvent", ["face_id", "timestamp"])
buffer_lock = threading.Lock()
face_buffer = []

def add_face(bib):
    global face_buffer
    now = time.perf_counter()
    with buffer_lock:
        face_buffer.append(FaceEvent(bib, now))
        face_buffer = [e for e in face_buffer if now - e.timestamp < 10.0]

def get_closest_face(ref_time):
    with buffer_lock:
        recent = [e for e in face_buffer if abs(e.timestamp - ref_time) < 10.0]
        if not recent:
            return None
        recent.sort(key=lambda e: abs(e.timestamp - ref_time))
        return recent[0].face_id

# AI-10 polling thread
def ai10_poll():
    buf = b''
    while alive[0]:
        send_frame(ser_ai10, 0x12, bytes([0x00, 0x03]))
        deadline = time.time() + 4
        while time.time() < deadline and alive[0]:
            try:
                chunk = ser_ai10.read(256)
            except:
                break
            if not chunk:
                continue
            buf += chunk
            while len(buf) >= 6:
                i = buf.find(SYNC)
                if i < 0: buf = buf[-4:]; break
                buf = buf[i:]
                if len(buf) < 6: break
                sz = (buf[3]<<8)|buf[4]
                end = 5+sz+1
                if len(buf) < end: break
                d = buf[5:5+sz]
                if calc_checksum(buf[2:5+sz]) == buf[5+sz]:
                    if buf[2] == 0x00 and len(d) >= 36 and d[0]==0x12 and d[1]==0:
                        uid = (d[2]<<8)|d[3]
                        name = d[4:36].rstrip(b'\x00').decode('utf-8', errors='ignore').strip()
                        add_face(name)
                        if name in athletes:
                            print(f"[FACE] bib={name}", flush=True)
                        else:
                            print(f"[FACE] uid={uid} name='{name}'", flush=True)
                buf = buf[end:]
        time.sleep(0.1)

alive = [True]
threading.Thread(target=ai10_poll, daemon=True).start()
time.sleep(2)

# Arduino reader thread
arduino_buf = b''
arduino_queue = queue.Queue()

def ard_reader():
    global arduino_buf
    while alive[0] and ser_ard:
        try:
            line = ser_ard.readline().decode("ascii", errors="ignore").strip()
            if not line:
                continue
            now = time.perf_counter()
            if line == "TRIGGER:START":
                arduino_queue.put(("start", now))
                print(f"\n[RACE START]", flush=True)
            elif line == "TRIGGER:FINISH":
                arduino_queue.put(("finish", now))
                print(f"\n[FINISH TRIGGER]", flush=True)
            elif line == "READY":
                print("[Arduino] READY")
        except:
            if alive[0]:
                print("[WARN] Arduino disconnected")
            break

threading.Thread(target=ard_reader, daemon=True).start()

print("\n" + "="*50)
print("  站立在摄像头前，按 Enter 开始比赛")
print("  碰 D3 线 = 冲过终点")
print("  Q = 退出")
print("="*50 + "\n")

input("Press Enter to start...")
start_time = time.perf_counter()

import msvcrt
race_started = True
print(f"[RACE START] {time.strftime('%H:%M:%S')}\n")

# Process finish triggers
while True:
    try:
        source, ts = arduino_queue.get(timeout=0.1)
        lap_time = ts - start_time
        bib = get_closest_face(ts)
        with buffer_lock:
            times = [f"{e.face_id}@{e.timestamp-start_time:.1f}s" for e in face_buffer]
        print(f"  Buffer: {times if times else 'EMPTY'}", flush=True)

        if bib:
            print(f"[{lap_time:.1f}s] >>> {bib} ({athletes[bib]['name']})", flush=True)
        else:
            print(f"[{lap_time:.1f}s] No face match. Trigger discarded.", flush=True)
            print("  (Make sure you're facing the AI-10 camera!)", flush=True)

    except queue.Empty:
        pass

    if msvcrt.kbhit():
        ch = msvcrt.getch()
        if ch in (b'q', b'Q'):
            break
        elif ch == b' ':
            now = time.perf_counter()
            arduino_queue.put(("finish", now))
            print(f"\n[MANUAL TRIGGER]", flush=True)

alive[0] = False
ser_ai10.close()
if ser_ard: ser_ard.close()
print("Done.")
