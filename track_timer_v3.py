"""V3 Smart Running Timer - E6-RCU + BE-1748 + BE-6311.

Architecture:
  BE-6311(ultrasonic P6) detects runner at finish line (< 50cm)
  BE-1748(AI vision P8) recognizes face → face_id
  E6-RCU runs monitoring loop (raw REPL injection), prints events via serial.
  PC reads events, maps face_id → athlete, records timing, saves CSV.

Usage:
  python track_timer_v3.py
"""

import serial
import time
import csv
import os
import threading
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================
E6RCU_PORT = "COM12"
BAUD = 115200
DISTANCE_THRESHOLD = 50       # cm
COOLDOWN_MS = 3000            # ms between consecutive triggers
POLL_INTERVAL_MS = 70         # ms between sensor polls on E6-RCU
LOOP_COUNT = 50000            # ~70min at 70ms+overhead per loop
ATHLETES_CSV = "athletes.csv"
FACE_MAP_CSV = "face_map.csv"
RESULTS_CSV = "results_v3.csv"

# ============================================================
# E6-RCU MicroPython monitoring code (raw REPL)
# ============================================================
MONITOR_CODE = (
    "import rcu,utime\r\n"
    "rcu.SetWaitForAICamData(10,0)\r\n"
    "utime.sleep_ms(800)\r\n"
    "lt=0\r\n"
    "for i in range({loops}):\r\n"
    " d=rcu.GetUltrasound(6)\r\n"
    " f=rcu.GetAICamData(1)\r\n"
    " t=utime.ticks_ms()\r\n"
    " if d>0 and d<{thresh} and f!=0:\r\n"
    "  if utime.ticks_diff(t,lt)>{cooldown} or lt==0:\r\n"
    "   lt=t\r\n"
    "   print('T|'+str(t)+'|'+str(f)+'|'+str(d))\r\n"
    " utime.sleep_ms({poll})\r\n"
    "print('LOOP_END')\r\n"
).format(loops=LOOP_COUNT, thresh=DISTANCE_THRESHOLD,
         cooldown=COOLDOWN_MS, poll=POLL_INTERVAL_MS)


def load_athletes(path):
    athletes = {}
    if not os.path.exists(path):
        print(f"[WARN] {path} not found")
        return athletes
    with open(path, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            bib = row["bib"].strip()
            athletes[bib] = {
                "name": row["name"].strip(),
                "project": row["project"].strip(),
                "student_id": row["student_id"].strip(),
            }
    print(f"Loaded {len(athletes)} athletes from {path}")
    return athletes


def load_face_map(path):
    face_map = {}
    if not os.path.exists(path):
        print(f"[WARN] {path} not found — register faces first with face_register.py")
        return face_map
    with open(path, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            face_map[row["face_id"].strip()] = row["bib"].strip()
    print(f"Loaded {len(face_map)} face mappings from {path}")
    return face_map


def inject_monitor_raw_repl(s):
    """Inject monitoring code via raw REPL (Ctrl-A)."""
    s.reset_input_buffer()
    s.reset_output_buffer()

    # Interrupt any running code
    s.write(b'\r\x03\x03')
    time.sleep(0.5)
    s.read(2048)

    # Enter raw REPL
    s.write(b'\r\x01')
    time.sleep(0.5)
    resp = s.read(1024)
    if b'raw REPL' not in resp:
        print(f"[WARN] Raw REPL entry unexpected: {resp[:80]}")
    print("  Raw REPL entered.")

    # Send code + Ctrl-D
    s.write(MONITOR_CODE.encode())
    time.sleep(0.3)
    s.write(b'\x04')
    time.sleep(1.0)

    # Read the "OK" acknowledgment
    ack = s.read(256)
    if b'OK' in ack:
        print("  Code accepted. Monitor running.")
    else:
        print(f"  [WARN] No OK ack: {ack[:80]}")


class FinishEvent:
    def __init__(self, e6_time_ms, face_id, distance_cm):
        self.e6_time_ms = e6_time_ms
        self.face_id = face_id
        self.distance_cm = distance_cm
        self.pc_time = datetime.now()
        self.bib = None
        self.athlete = None

    def __repr__(self):
        if self.athlete:
            return (f"FINISH | bib={self.bib} {self.athlete['name']} "
                    f"({self.athlete['project']}) face={self.face_id} dist={self.distance_cm}cm")
        return f"FINISH | face_id={self.face_id} (unknown) dist={self.distance_cm}cm"


def clean_line(line):
    """Strip raw REPL noise: OK prefix, \\x04 bytes, > prompts."""
    # Remove raw REPL artifacts
    line = line.replace('\x04', '').replace('>', '').strip()
    # Remove "OK" prefix (raw REPL prepends this to first output line)
    if line.startswith('OK'):
        line = line[2:]
    return line


def serial_reader(s, stop_event, event_queue):
    """Thread: read serial, parse T| events, push to queue."""
    buf = ""
    while not stop_event.is_set():
        try:
            data = s.read(128)
            if data:
                buf += data.decode("ascii", errors="replace")
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    line = clean_line(line)
                    if not line:
                        continue
                    if line.startswith("T|"):
                        parts = line.split("|")
                        if len(parts) == 4:
                            try:
                                t_ms = int(parts[1])
                                face_id = parts[2]
                                dist = int(parts[3])
                                event_queue.append(FinishEvent(t_ms, face_id, dist))
                            except ValueError:
                                pass
                    elif "LOOP_END" in line:
                        event_queue.append("LOOP_END")
        except Exception as e:
            if not stop_event.is_set():
                print(f"\n[Serial error: {e}]")
            break


def main():
    print("=" * 60)
    print("V3 Smart Running Timer")
    print("E6-RCU + BE-1748(AI P8) + BE-6311(Ultrasonic P6)")
    print(f"Threshold: {DISTANCE_THRESHOLD}cm | Cooldown: {COOLDOWN_MS}ms")
    print("=" * 60)

    athletes = load_athletes(ATHLETES_CSV)
    face_map = load_face_map(FACE_MAP_CSV)

    if not athletes:
        print("ERROR: No athletes found.")
        return

    # Connect to E6-RCU
    print(f"\nConnecting to {E6RCU_PORT}...")
    try:
        s = serial.Serial(E6RCU_PORT, BAUD, timeout=1)
    except Exception as e:
        print(f"ERROR: {e}")
        return

    time.sleep(0.5)
    s.read(4096)

    # Inject code via raw REPL
    print("Injecting monitor code...")
    inject_monitor_raw_repl(s)

    # Start reader thread
    stop_event = threading.Event()
    event_queue = []
    reader_thread = threading.Thread(
        target=serial_reader, args=(s, stop_event, event_queue), daemon=True
    )
    reader_thread.start()

    # Race state
    race_start = None
    results = []
    seen_faces = set()

    print("\nCommands: [s]tart race  [r]eset  [q]uit")
    print("Waiting for race start...\n")

    try:
        while True:
            while event_queue:
                event = event_queue.pop(0)

                if event.face_id in face_map:
                    event.bib = face_map[event.face_id]
                    event.athlete = athletes.get(event.bib)

                if race_start and event.bib and event.face_id not in seen_faces:
                    seen_faces.add(event.face_id)
                    elapsed = (event.pc_time - race_start).total_seconds()
                    elapsed_str = (f"{int(elapsed // 60)}'"
                                   f"{int(elapsed % 60):02d}.{int((elapsed % 1) * 10)}")
                    print(f"  >>> {event}")
                    print(f"      Elapsed: {elapsed_str}")

                    results.append({
                        "time": event.pc_time.strftime("%H:%M:%S"),
                        "bib": event.bib,
                        "name": event.athlete["name"] if event.athlete else "?",
                        "project": event.athlete["project"] if event.athlete else "?",
                        "face_id": event.face_id,
                        "distance_cm": event.distance_cm,
                        "elapsed": f"{elapsed:.1f}",
                    })
                elif not race_start:
                    print(f"  [PRE-START] {event}")
                elif event.face_id in seen_faces:
                    print(f"  [DUPE] {event}")

            # Keyboard input (Windows)
            import msvcrt
            if msvcrt.kbhit():
                key = msvcrt.getch().decode("utf-8", errors="replace").lower()
                if key == 's' and race_start is None:
                    race_start = datetime.now()
                    print(f"\n=== RACE STARTED {race_start.strftime('%H:%M:%S')} ===\n")
                elif key == 'r':
                    print("\n=== RESET ===")
                    race_start = None
                    seen_faces.clear()
                    results.clear()
                elif key == 'q':
                    break

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\nInterrupted.")

    finally:
        stop_event.set()
        reader_thread.join(timeout=2)
        # Try to stop the loop on E6-RCU
        s.write(b'\r\x03\x03')
        time.sleep(0.3)
        s.close()

        if results:
            print(f"\n=== RESULTS: {len(results)} finishes ===")
            for r in results:
                print(f"  {r['time']} | bib={r['bib']} {r['name']} | "
                      f"{r['project']} | {r['elapsed']}s")

            with open(RESULTS_CSV, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=results[0].keys())
                writer.writeheader()
                writer.writerows(results)
            print(f"\nSaved to {RESULTS_CSV}")
        else:
            print("\nNo results recorded.")


if __name__ == "__main__":
    main()
