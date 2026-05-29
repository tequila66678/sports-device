"""Export results from E6-RCU after race.
Reads results.txt from E6-RCU flash, saves to CSV.
Usage: python export_results.py
"""

import serial, time, csv, os, sys

PORT = "COM12"
ATHLETES_CSV = "athletes.csv"
RESULTS_CSV = "results_race.csv"

# Load athlete names
athletes = {}
if os.path.exists(ATHLETES_CSV):
    with open(ATHLETES_CSV, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            athletes[row["bib"].strip()] = row["name"].strip()

# Face map (keep synced with E6-RCU code)
face_map = {
    "1": "101", "2": "102", "3": "103",
    "99": "999",
}

print(f"Connecting to E6-RCU on {PORT}...")
try:
    s = serial.Serial(PORT, 115200, timeout=3)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)

time.sleep(0.5)
s.read(4096)
s.write(b'\r\x03\x03')
time.sleep(0.5)
s.read(2048)
s.write(b'\r\x01')
time.sleep(0.3)
s.read(256)

# Read results.txt from E6-RCU flash
print("Reading results.txt from E6-RCU...")
code = (
    "try:\r\n"
    " f=open('results.txt','r')\r\n"
    " print(f.read())\r\n"
    " f.close()\r\n"
    "except Exception as e:\r\n"
    " print('ERR:'+str(e))\r\n"
    "print('--EOF--')\r\n"
)
s.write(code.encode())
time.sleep(0.3)
s.write(b'\x04')
time.sleep(3)
out = s.read(8192)
text = out.decode("ascii", errors="replace")

# Parse results
results = []
race_start = None
for line in text.split("\r\n"):
    line = line.replace("\x04", "").replace(">", "").strip()
    if line.startswith("OK"):
        line = line[2:]
    if line == "--EOF--":
        break
    if "," in line and not line.startswith("ERR"):
        parts = line.split(",")
        if len(parts) >= 3:
            try:
                fid = parts[0]
                dist = parts[1]
                elapsed_ms = int(parts[2])
                lap = parts[3] if len(parts) > 3 else "?"
                bib = face_map.get(fid, "?")
                name = athletes.get(bib, "?")
                if race_start is None:
                    race_start = elapsed_ms
                elapsed_s = elapsed_ms / 1000.0
                results.append({
                    "face_id": fid, "bib": bib, "name": name,
                    "lap": lap, "distance_cm": dist, "elapsed_s": f"{elapsed_s:.1f}",
                })
            except (ValueError, IndexError):
                pass

s.write(b'\r\x03')
s.close()

# Display
print(f"\n{'='*50}")
print(f"RACE RESULTS ({len(results)} records)")
print(f"{'='*50}")
for r in results:
    es = float(r["elapsed_s"])
    m = int(es // 60)
    sd = f"{int(es % 60):02d}.{int((es % 1) * 10)}"
    print(f"  {r['lap']} | bib={r['bib']} {r['name']} | face={r['face_id']} | {m}'{sd} | {r['distance_cm']}cm")

# Save CSV
if results:
    with open(RESULTS_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)
    print(f"\nSaved to {RESULTS_CSV}")
else:
    print("\nNo results found.")
