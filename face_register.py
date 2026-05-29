"""BE-1748 face registration helper.

After registering a face on BE-1748 (screen+buttons), run this to discover
the assigned face_id and map it to an athlete bib.

Usage:
  python face_register.py
  - Register face on BE-1748 module
  - Enter athlete bib when prompted
  - Show face to camera → captures face_id
  - Saves mapping to face_map.csv
"""

import serial
import time
import csv
import os

E6RCU_PORT = "COM12"
BAUD = 115200
FACE_MAP_CSV = "face_map.csv"
ATHLETES_CSV = "athletes.csv"


def paste_code(s, code, wait=8):
    s.reset_input_buffer()
    s.write(b'\x05')
    time.sleep(0.3)
    s.read(256)
    s.write(code.encode())
    time.sleep(0.3)
    s.write(b'\x04')
    time.sleep(wait)
    out = s.read(4096)
    return out.decode('ascii', errors='replace')


def load_athletes():
    athletes = {}
    if os.path.exists(ATHLETES_CSV):
        with open(ATHLETES_CSV, "r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                athletes[row["bib"].strip()] = row["name"].strip()
    return athletes


def load_face_map():
    face_map = {}
    if os.path.exists(FACE_MAP_CSV):
        with open(FACE_MAP_CSV, "r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                face_map[row["face_id"].strip()] = row["bib"].strip()
    return face_map


def save_face_map(face_map):
    with open(FACE_MAP_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["face_id", "bib"])
        for fid, bib in sorted(face_map.items(), key=lambda x: int(x[0])):
            writer.writerow([fid, bib])


def main():
    athletes = load_athletes()
    face_map = load_face_map()
    registered_faces = set(face_map.keys())

    print("=" * 60)
    print("BE-1748 Face Registration Helper")
    print("=" * 60)
    print(f"Athletes loaded: {len(athletes)}")
    print(f"Faces already mapped: {len(face_map)}")
    if face_map:
        for fid, bib in sorted(face_map.items(), key=lambda x: int(x[0])):
            name = athletes.get(bib, "?")
            print(f"  face_id={fid} → bib={bib} ({name})")

    # Connect
    print(f"\nConnecting to E6-RCU on {E6RCU_PORT}...")
    try:
        s = serial.Serial(E6RCU_PORT, BAUD, timeout=3)
    except Exception as e:
        print(f"ERROR: {e}")
        return
    time.sleep(0.5)
    s.read(4096)

    # Init mode 10
    print("Initializing face recognition (mode 10)...")
    code = "import rcu\r\nrcu.SetWaitForAICamData(10,0)\r\nprint('ok')\r\n"
    out = paste_code(s, code, wait=8)
    if 'ok' not in out:
        print("ERROR: Init failed!")
        s.close()
        return
    print("Ready.\n")

    while True:
        bib = input("Enter athlete bib (or 'q' to quit): ").strip()
        if bib.lower() == 'q':
            break
        if not bib:
            continue

        if bib in face_map.values():
            print(f"  bib={bib} already mapped!")
            continue

        name = athletes.get(bib, "UNKNOWN")
        print(f"  Athlete: {name}")
        print(f"  [Step 1] Register face on BE-1748 screen+buttons")
        input(f"  [Step 2] Press Enter when ready to scan face...")

        # Poll face ID
        print(f"  Scanning... Show face to camera!", end="", flush=True)
        found_id = None
        for attempt in range(30):
            time.sleep(0.3)
            print(".", end="", flush=True)
            code = "import rcu\r\nr=rcu.GetAICamData(1)\r\nprint('F'+str(r))\r\n"
            out = paste_code(s, code, wait=3)
            for line in out.split('\r\n'):
                line = line.strip()
                if line.startswith('F') and len(line) > 1:
                    val = line[1:]
                    try:
                        val = int(val)
                        if val > 0:
                            found_id = str(val)
                            break
                    except ValueError:
                        pass
            if found_id:
                break

        if found_id:
            print(f"\n  >>> Face ID: {found_id}")
            if found_id in face_map:
                existing = face_map[found_id]
                exist_name = athletes.get(existing, "?")
                print(f"  WARNING: face_id={found_id} already mapped to bib={existing} ({exist_name})!")
                confirm = input("  Overwrite? (y/n): ").strip().lower()
                if confirm != 'y':
                    continue
            face_map[found_id] = bib
            registered_faces.add(found_id)
            save_face_map(face_map)
            print(f"  ✓ Saved: face_id={found_id} → bib={bib} ({name})")
        else:
            print(f"\n  No face detected. Try again.")

    s.close()
    print(f"\nTotal faces mapped: {len(face_map)}")
    print(f"Face map saved to {FACE_MAP_CSV}")


if __name__ == "__main__":
    main()
