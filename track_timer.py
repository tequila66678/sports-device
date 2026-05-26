"""
Smart Track Timer v2.1 - AI Face Recognition (Serial) + Dual IR Sensors
==================================================================
Hardware:
  - AI-10 module: face recognition via USB-TTL serial -> PC
  - Arduino Uno: dual IR sensors (START + FINISH) -> USB Serial
  - Button: manual backup trigger

Architecture:
  AI-10 (USB-TTL) --Serial--> PC (AI10Serial COM4) --> FaceBuffer
  Arduino (USB) --Serial--> PC (SerialListener COM3) --> TriggerQueue
  Main loop: drain triggers -> correlate with recent faces -> record laps

Graceful degradation:
  - No AI-10 -> manual bib entry on each trigger
  - No Arduino -> SPACE key for manual trigger
  - No hardware at all -> fully manual (original SPACE+Enter mode)
"""
import csv
import json
import os
import queue
import re
import sys
import threading
import time
import urllib.request
import urllib.error
from collections import namedtuple

# ==================== Configuration ====================

API_BASE = "https://sports-dhju.onrender.com"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Serial (Arduino - IR sensors)
SERIAL_PORT = "COM6"
SERIAL_BAUD = 115200

# AI-10 Face Recognition (USB-TTL serial)
AI10_SERIAL_PORT = "COM4"
AI10_SERIAL_BAUD = 115200
FACE_WINDOW_SECONDS = 3.0        # How far back to look for faces before a trigger

# Timing
TRIGGER_DEBOUNCE_MS = 500         # PC-side minimum interval between finish triggers
START_DEBOUNCE_MS = 2000          # Minimum interval between START triggers

# ==================== Event Mapping ====================

EVENT_MAP = {
    "1000m": 2,
    "800m": 1,
}

PROJECT_RULES = {
    "1000m": {"start_offset": 200, "lap_distance": 400, "total": 1000},
    "800m":  {"start_offset": 0,   "lap_distance": 400, "total": 800},
    "1500m": {"start_offset": 300, "lap_distance": 400, "total": 1500},
    "400m":  {"start_offset": 0,   "lap_distance": 400, "total": 400},
    "1000米": "1000m",
    "800米":  "800m",
    "1500米": "1500m",
    "400米":  "400m",
}

# ==================== Data Types ====================

TriggerEvent = namedtuple("TriggerEvent", ["timestamp", "source"])  # source: "start" | "finish" | "manual"
FaceEvent = namedtuple("FaceEvent", ["face_id", "timestamp"])


def gbk_safe(s):
    """Strip characters that can't be encoded in GBK (Windows terminal)."""
    return s.encode("gbk", errors="replace").decode("gbk")


def safe_print(*args, **kwargs):
    """Print without crashing on GBK-incompatible characters."""
    parts = []
    for a in args:
        parts.append(gbk_safe(str(a)))
    print(*parts, **kwargs)


# ==================== API Client ====================

def api_call(method, path, token=None, body=None):
    url = f"{API_BASE}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8") if e.fp else str(e)
        raise RuntimeError(f"API error {e.code}: {detail}")


def login():
    resp = api_call("POST", "/api/auth/login", body={
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD
    })
    token = resp["access_token"]
    safe_print(f"[OK] Logged in: {resp['admin']['display_name']}")
    return token


def resolve_students(token, athletes):
    mapping = {}
    student_ids = {a["student_id"] for a in athletes.values() if a["student_id"]}

    for sid in student_ids:
        resp = api_call("GET", f"/api/students?search={sid}", token=token)
        matched = [s for s in resp if s["student_id"] == sid]
        if not matched:
            raise RuntimeError(f"Student {sid} not found in system")
        mapping[sid] = matched[0]["id"]
        safe_print(f"  {sid} -> internalID={matched[0]['id']} ({matched[0]['name']})")
    return mapping


def submit_scores(token, athletes, student_id_map, test_date):
    entries = []
    for bib, rec in athletes.items():
        if rec["status"] != "finished":
            continue
        sid_str = rec["student_id"]
        internal_id = student_id_map.get(sid_str)
        if internal_id is None:
            continue

        project_key = rec["project"]
        resolved = PROJECT_RULES.get(project_key, project_key)
        if isinstance(resolved, str):
            project_key = resolved
        event_id = EVENT_MAP.get(project_key)

        raw_value = sec_to_time_ms(rec["final_time"])
        entries.append({
            "student_id": internal_id,
            "event_id": event_id,
            "raw_value": raw_value,
            "test_date": test_date
        })

    if not entries:
        return []

    resp = api_call("POST", "/api/scores/batch", token=token, body={"scores": entries})
    return resp


# ==================== Athlete Management ====================

def load_athletes(filepath="athletes.csv"):
    athletes = {}
    with open(filepath, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            bib = row["bib"].strip()
            athletes[bib] = {
                "name": row["name"].strip(),
                "project": row["project"].strip(),
                "student_id": row.get("student_id", "").strip(),
                "lap_count": 0,
                "lap_times": [],
                "final_time": None,
                "status": "racing",
            }
    return athletes


def get_rule(project):
    key = PROJECT_RULES.get(project, project)
    if isinstance(key, str):
        key = PROJECT_RULES.get(key)
    if not isinstance(key, dict):
        raise ValueError(f"Unknown event: {project}")
    return key


def calc_distance(lap_count, rule):
    if lap_count == 0:
        return 0
    if lap_count == 1:
        return rule["start_offset"]
    return rule["start_offset"] + (lap_count - 1) * rule["lap_distance"]


def sec_to_time_ms(seconds):
    total = round(seconds)
    m = total // 60
    s = total % 60
    return f"{m}'{s:02d}"


# ==================== Face Buffer (AI-10 -> PC) ====================

class FaceBuffer:
    """Thread-safe buffer of recent face recognition events from AI-10."""

    def __init__(self, max_age_seconds=3.0):
        self.buffer = []  # list of FaceEvent
        self.max_age = max_age_seconds
        self.lock = threading.Lock()

    def add(self, face_id, timestamp=None):
        """Called by AIFaceServer when AI-10 reports a recognized face."""
        if timestamp is None:
            timestamp = time.perf_counter()
        with self.lock:
            self.buffer.append(FaceEvent(face_id, timestamp))
            # Purge events older than max_age
            cutoff = timestamp - self.max_age
            self.buffer = [e for e in self.buffer if e.timestamp > cutoff]

    def get_closest(self, reference_time):
        """Return the face event closest to reference_time within the window,
           or None if no recent faces."""
        with self.lock:
            cutoff = reference_time - self.max_age
            recent = [e for e in self.buffer if cutoff <= e.timestamp <= reference_time]
            if not recent:
                return None
            recent.sort(key=lambda e: abs(e.timestamp - reference_time))
            return recent[0]

    def get_recent(self, reference_time):
        """Return all face events near reference_time, sorted by proximity."""
        with self.lock:
            cutoff = reference_time - self.max_age
            recent = [e for e in self.buffer if cutoff <= e.timestamp <= reference_time]
            recent.sort(key=lambda e: abs(e.timestamp - reference_time))
            return recent


# ==================== AI-10 Serial Communication (USB-TTL -> PC) ====================

class AI10Serial:
    """Communicates with HLK AI-10 face recognition module via USB-TTL serial.

    Protocol:
      Frame: EF AA | CMD(1B) | SIZE(2B, big-endian) | DATA(NB) | CHECKSUM(1B)
      Checksum: XOR of all bytes from CMD through DATA.

    Key commands:
      0x10 RESET
      0x12 VERIFY (auto recognition mode)
      0x13 ENROLL (interactive face registration)
      0x1D ENROLL_SINGLE (single-frame registration)
      0x20 DELETEUSER
      0x21 DELETEALL

    Response messages:
      0x00 REPLY  (response to commands)
      0x01 NOTE   (async notification: ready, face state, recognition result)

    NOTE types (nid):
      0x00 NID_READY        - module initialized
      0x01 NID_FACE_STATE   - face position/state update
      0x0A NID_AUTO_VERIFY  - auto recognition result

    Recognition result (NID_AUTO_VERIFY, nid=0x0A):
      data[0] = 0x01 (recognition result available)
      data[1] = 0x00 (MR_SUCCESS)
      data[2] = user_id_high_byte
      data[3] = user_id_low_byte
    """

    SYNC_WORD = bytes([0xEF, 0xAA])
    MID_REPLY = 0x00
    MID_NOTE = 0x01
    CMD_RESET = 0x10
    CMD_VERIFY = 0x12
    CMD_ENROLL = 0x13
    CMD_DELETE_ALL = 0x21

    NID_READY = 0x00
    NID_AUTO_VERIFY = 0x0A

    MR_SUCCESS = 0x00

    def __init__(self, port, baud=115200):
        self.port = port
        self.baud = baud
        self.ser = None
        self.face_buffer = None
        self.alive = False
        self._thread = None
        self._stop = threading.Event()

    def calc_checksum(self, data):
        """XOR of all bytes in data."""
        result = 0
        for b in data:
            result ^= b
        return result & 0xFF

    def send_frame(self, cmd_id, data=b''):
        """Send a frame to the AI-10 module."""
        size = len(data)
        payload = bytes([cmd_id, (size >> 8) & 0xFF, size & 0xFF]) + data
        checksum = self.calc_checksum(payload)
        frame = self.SYNC_WORD + payload + bytes([checksum])
        self.ser.write(frame)

    # Time between single-shot verify attempts
    VERIFY_INTERVAL = 0.2  # seconds

    def _run(self):
        """Polling loop: send single-shot VERIFY, parse reply, buffer recognized faces."""
        buffer = b''
        while not self._stop.is_set():
            # Send single-shot verify: at_verify=0, timeout=5s
            self.send_frame(self.CMD_VERIFY, bytes([0x00, 0x05]))
            deadline = time.time() + 6.0

            while time.time() < deadline and not self._stop.is_set():
                try:
                    chunk = self.ser.read(256)
                except (OSError, Exception):
                    if not self._stop.is_set():
                        self.alive = False
                        safe_print("[WARN] AI-10 serial disconnected")
                    break

                if not chunk:
                    continue
                buffer += chunk

                # Search for sync word and parse frames
                while len(buffer) >= 8:
                    idx = buffer.find(self.SYNC_WORD)
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
                    expected_chk = buffer[5 + size]
                    actual_chk = self.calc_checksum(buffer[2:5 + size])

                    if actual_chk == expected_chk:
                        if cmd == self.MID_NOTE and len(data) >= 1 and data[0] == self.NID_READY:
                            safe_print("  [AI-10] READY")
                        elif cmd == self.MID_REPLY and len(data) >= 2:
                            mid, result = data[0], data[1]
                            if mid == self.CMD_VERIFY and result == self.MR_SUCCESS and len(data) >= 36:
                                name_bytes = data[4:36].rstrip(b'\x00')
                                bib = name_bytes.decode('utf-8', errors='ignore').strip()
                                if bib and bib in self.athletes:
                                    if self.face_buffer:
                                        self.face_buffer.add(bib)
                                        safe_print(f"  [AI-10] Recognized: bib={bib}")
                                elif bib:
                                    safe_print(f"  [AI-10] Unknown bib: '{bib}'")

                    buffer = buffer[frame_end:]

            time.sleep(self.VERIFY_INTERVAL)

    def start(self, face_buffer, athletes):
        """Open serial port and start background thread."""
        self.face_buffer = face_buffer
        self.athletes = athletes  # bib -> athlete mapping
        try:
            import serial
        except ImportError:
            safe_print("[WARN] pyserial not installed, AI-10 disabled")
            return False

        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=0.5)
            self.alive = True
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
            time.sleep(1.5)  # Wait for READY
            return True
        except Exception as e:
            safe_print(f"[WARN] AI-10 serial {self.port} not available: {e}")
            return False

    def stop(self):
        """Close serial port and stop thread."""
        self._stop.set()
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
            except Exception:
                pass


# ==================== Serial Listener (Arduino -> PC) ====================

class SerialListener:
    """Background thread: reads Arduino serial, enqueues trigger events.

    Supports dual sensors:
      - "TRIGGER:START"  -> race start (START line sensor)
      - "TRIGGER:FINISH" -> athlete crossing (FINISH line sensor)
    """

    def __init__(self, port, baud, event_queue):
        self.port = port
        self.baud = baud
        self.queue = event_queue
        self.alive = False
        self.ser = None
        self._stop = threading.Event()
        self._thread = None

    def start(self):
        try:
            import serial
        except ImportError:
            safe_print("[WARN] pyserial not installed")
            return False

        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=1.0)
            time.sleep(2)  # Wait for Arduino reset
            self.ser.reset_input_buffer()
            self.alive = True
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
            return True
        except Exception as e:
            safe_print(f"[WARN] Serial {self.port} not available: {e}")
            return False

    def _run(self):
        while not self._stop.is_set():
            try:
                line = self.ser.readline().decode("ascii", errors="ignore").strip()
                if not line:
                    continue

                now = time.perf_counter()

                if line == "READY":
                    safe_print("[Arduino] READY - dual IR sensors online")
                elif line == "TRIGGER:START":
                    self.queue.put(TriggerEvent(now, "start"))
                elif line == "TRIGGER:FINISH":
                    self.queue.put(TriggerEvent(now, "finish"))
                elif line == "TRIGGER":
                    # Legacy single-sensor firmware
                    self.queue.put(TriggerEvent(now, "finish"))
                else:
                    safe_print(f"[Arduino] Unknown: {line}")

            except (OSError, Exception):
                if self._stop.is_set():
                    break
                self.alive = False
                safe_print("[WARN] Serial disconnected")
                break

    def stop(self):
        self._stop.set()
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
            except Exception:
                pass


# ==================== Trigger Processing ====================

def record_lap(bib, lap_time, athletes):
    """Record a lap/finish for an athlete. Returns display message."""
    rec = athletes[bib]
    rule = get_rule(rec["project"])
    rec["lap_count"] += 1
    rec["lap_times"].append(lap_time)
    distance = calc_distance(rec["lap_count"], rule)

    if distance >= rule["total"]:
        rec["final_time"] = lap_time
        rec["status"] = "finished"
        return f"FINISHED: {rec['name']}({bib}) time={lap_time:.1f}s"
    else:
        return f"LAP: {rec['name']}({bib}) lap#{rec['lap_count']} ({distance}m/{rule['total']}m)"


def resolve_bib_from_face(face_buffer, trigger_time, athletes):
    """Try to determine which athlete crossed based on recent face detections.

    Returns (bib, method) where method is "face" or None.
    """
    event = face_buffer.get_closest(trigger_time)
    if event is None:
        return None, None

    face_id = event.face_id
    time_diff = trigger_time - event.timestamp

    # Direct match: face_id IS the bib number (recommended registration method)
    if face_id in athletes and athletes[face_id]["status"] == "racing":
        return face_id, f"face ({time_diff:.1f}s ago)"

    # The face_id might be a student_id - try matching
    for bib, rec in athletes.items():
        if rec["student_id"] == face_id and rec["status"] == "racing":
            return bib, f"face->student_id ({time_diff:.1f}s ago)"

    return None, None


def process_trigger(event, face_buffer, athletes, start_time):
    """Handle a trigger: determine bib via AI-10 face buffer or manual entry."""
    lap_time = event.timestamp - start_time

    if event.source == "start":
        safe_print(f"\n[RACE START] {lap_time:.1f}s - Race begins!")
        return

    # FINISH or manual trigger
    safe_print(f"\n[TRIGGER:{event.source.upper()}] {lap_time:.1f}s")

    # --- Try AI-10 face recognition ---
    bib = None
    method = None

    if face_buffer is not None:
        bib, method = resolve_bib_from_face(face_buffer, event.timestamp, athletes)
        if bib:
            safe_print(f"  [AI-10] -> {bib} ({athletes[bib]['name']}) via {method}")

    # --- Manual fallback ---
    if bib is None:
        safe_print("  [AI-10] No recent face detected")
        while bib is None:
            raw = input("  Enter bib (or 'skip' to discard): ").strip()
            if raw.lower() == "skip":
                safe_print("  Trigger discarded")
                return
            if raw in athletes:
                if athletes[raw]["status"] != "racing":
                    safe_print(f"  WARN: {athletes[raw]['name']} already finished")
                    continue
                bib = raw
            else:
                safe_print(f"  WARN: bib '{raw}' not found")

    # --- Validate ---
    if bib not in athletes:
        safe_print(f"  WARN: bib {bib} not found, skip")
        return
    if athletes[bib]["status"] != "racing":
        safe_print(f"  WARN: {athletes[bib]['name']}({bib}) already finished, skip")
        return

    # --- Record ---
    msg = record_lap(bib, lap_time, athletes)
    safe_print(f"  {msg}")


# ==================== Main ====================

def main():
    safe_print("Track Timer v2.0 (AI-10 Face + Dual IR)")
    safe_print("-" * 50)

    # --- Load athletes ---
    athletes = load_athletes()
    safe_print(f"Loaded {len(athletes)} athletes")

    # --- API login ---
    token = None
    student_id_map = {}
    try:
        token = login()
        student_id_map = resolve_students(token, athletes)
    except Exception as e:
        safe_print(f"[WARN] API unavailable: {e}")
        safe_print("[WARN] Running offline — results saved to CSV only")
    safe_print("-" * 50)

    # --- Initialize hardware (best-effort) ---
    event_queue = queue.Queue()
    serial_listener = SerialListener(SERIAL_PORT, SERIAL_BAUD, event_queue)
    serial_ok = serial_listener.start()

    face_buffer = FaceBuffer(FACE_WINDOW_SECONDS)
    ai10_serial = AI10Serial(AI10_SERIAL_PORT, AI10_SERIAL_BAUD)
    ai10_ok = ai10_serial.start(face_buffer, athletes)

    # --- Status ---
    safe_print(f"Arduino (IR):  {'OK' if serial_ok else 'N/A - manual SPACE mode'}")
    safe_print(f"AI-10 Serial:  {'OK - auto recognition active' if ai10_ok else 'N/A - manual bib entry'}")
    safe_print("-" * 50)

    input("Press Enter when ready (athletes at start line)...")

    start_time = time.perf_counter()
    test_date = time.strftime("%Y-%m-%d")
    last_finish_time = -999999.0
    last_start_time = -999999.0
    race_started = False

    safe_print(f"\nWaiting for START signal...")
    safe_print("(IR start sensor, or press SPACE for manual start)")
    safe_print("S: status   |   Q: quit")
    safe_print("-" * 50)

    # --- Main event loop ---
    try:
        import msvcrt
        has_msvcrt = True
    except ImportError:
        has_msvcrt = False

    while True:
        # 1. Drain all pending triggers
        while True:
            try:
                event = event_queue.get_nowait()

                if event.source == "start":
                    if event.timestamp - last_start_time >= START_DEBOUNCE_MS / 1000.0:
                        last_start_time = event.timestamp
                        if not race_started:
                            race_started = True
                            start_time = event.timestamp
                            safe_print(f"\n[RACE START] Automatic start!")
                            safe_print(f"Base time: {time.strftime('%H:%M:%S')}")
                            safe_print("-" * 50)
                        else:
                            safe_print("  [IGNORE] Duplicate START signal")
                elif event.source in ("finish", "manual"):
                    if race_started:
                        if event.timestamp - last_finish_time >= TRIGGER_DEBOUNCE_MS / 1000.0:
                            last_finish_time = event.timestamp
                            process_trigger(event, face_buffer, athletes, start_time)
                    else:
                        safe_print("  [IGNORE] Finish trigger before race start")

            except queue.Empty:
                break

        # 2. Keyboard input (non-blocking)
        if has_msvcrt and msvcrt.kbhit():
            ch = msvcrt.getch()
            now = time.perf_counter()

            if ch == b' ':
                if not race_started:
                    # SPACE = manual race start
                    if now - last_start_time >= START_DEBOUNCE_MS / 1000.0:
                        last_start_time = now
                        race_started = True
                        start_time = now
                        safe_print(f"\n[RACE START] Manual start!")
                        safe_print(f"Base time: {time.strftime('%H:%M:%S')}")
                        safe_print("-" * 50)
                else:
                    # SPACE = manual finish trigger
                    if now - last_finish_time >= TRIGGER_DEBOUNCE_MS / 1000.0:
                        last_finish_time = now
                        event_queue.put(TriggerEvent(now, "manual"))

            elif ch in (b'q', b'Q'):
                break
            elif ch in (b's', b'S'):
                racing = sum(1 for a in athletes.values() if a["status"] == "racing")
                finished = sum(1 for a in athletes.values() if a["status"] == "finished")
                elapsed = time.perf_counter() - start_time if race_started else 0
                faces = len(face_buffer.buffer) if face_buffer else 0
                safe_print(f"\n  Racing: {racing}  Finished: {finished}  Elapsed: {elapsed:.0f}s  Faces: {faces}")

        # 3. Check if all finished
        if race_started:
            racing_count = sum(1 for a in athletes.values() if a["status"] == "racing")
            if racing_count == 0:
                safe_print("\nAll finished!")
                break

    # --- Cleanup ---
    serial_listener.stop()
    ai10_serial.stop()

    # --- Submit to API ---
    print("\n" + "=" * 50)
    print("Submitting results...")
    print("=" * 50)

    try:
        results = submit_scores(token, athletes, student_id_map, test_date)
        for r in results:
            safe_print(f"  [OK] student={r['student_id']} event={r['event_id']} "
                       f"raw={r['raw_value']} score={r['earned_score']}")
        if results:
            safe_print(f"\n[OK] {len(results)} scores synced to management system")
    except Exception as e:
        safe_print(f"  [FAIL] Submit error: {e}")

    # --- Local CSV ---
    print("\n" + "=" * 50)
    print("Results")
    print("=" * 50)

    with open("results.csv", "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["bib", "name", "student_id", "event", "time(s)", "time_ms", "status", "laps"])
        for bib, rec in sorted(athletes.items()):
            time_str = f"{rec['final_time']:.1f}" if rec["final_time"] else "N/A"
            time_ms = sec_to_time_ms(rec["final_time"]) if rec["final_time"] else "N/A"
            writer.writerow([bib, rec["name"], rec["student_id"], rec["project"],
                           time_str, time_ms, rec["status"], rec["lap_count"]])
            mark = "DONE" if rec["status"] == "finished" else "DNF"
            safe_print(f"{mark} {bib} {rec['name']} | {rec['project']} | {time_str}s ({time_ms})")

    safe_print(f"\nSaved to results.csv")
    safe_print("Go to https://sports-dhju.onrender.com to view scores")


if __name__ == "__main__":
    main()
