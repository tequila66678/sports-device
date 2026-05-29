"""Quick end-to-end test: inject monitor, catch events, show results."""
import serial, time, csv, os

PORT = "COM12"
FACE_MAP_CSV = "face_map.csv"
ATHLETES_CSV = "athletes.csv"

def clean_line(line):
    line = line.replace('\x04', '').replace('>', '').strip()
    if line.startswith('OK'):
        line = line[2:]
    return line

# Load face map
face_map = {}
if os.path.exists(FACE_MAP_CSV):
    with open(FACE_MAP_CSV, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            face_map[row["face_id"].strip()] = row["bib"].strip()
print(f"Face map: {face_map}")

# Load athletes
athletes = {}
if os.path.exists(ATHLETES_CSV):
    with open(ATHLETES_CSV, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            athletes[row["bib"].strip()] = row["name"].strip()

# Connect
s = serial.Serial(PORT, 115200, timeout=1)
time.sleep(0.5)
s.read(4096)

# Raw REPL inject
s.write(b'\r\x03\x03')
time.sleep(0.5)
s.read(2048)
s.write(b'\r\x01')
time.sleep(0.5)
s.read(1024)

# Monitor: 100 loops = ~10s
code = (
    "import rcu,utime\r\n"
    "rcu.SetWaitForAICamData(10,0)\r\n"
    "utime.sleep_ms(800)\r\n"
    "lt=0\r\n"
    "for i in range(100):\r\n"
    " d=rcu.GetUltrasound(6)\r\n"
    " f=rcu.GetAICamData(1)\r\n"
    " t=utime.ticks_ms()\r\n"
    " if d>0 and d<50 and f!=0:\r\n"
    "  if utime.ticks_diff(t,lt)>3000 or lt==0:\r\n"
    "   lt=t\r\n"
    "   print('T|'+str(t)+'|'+str(f)+'|'+str(d))\r\n"
    " utime.sleep_ms(90)\r\n"
    "print('END')\r\n"
)
s.write(code.encode())
time.sleep(0.3)
s.write(b'\x04')

print("Monitor running for ~12s. Stand in front of camera + near ultrasonic!")
time.sleep(2)

# Read events
buf = ""
events = []
deadline = time.time() + 12
while time.time() < deadline:
    data = s.read(128)
    if data:
        buf += data.decode("ascii", errors="replace")
        while "\n" in buf:
            line, buf = buf.split("\n", 1)
            line = clean_line(line)
            if line.startswith("T|"):
                parts = line.split("|")
                if len(parts) == 4:
                    events.append({
                        "t_ms": parts[1],
                        "face_id": parts[2],
                        "dist": parts[3],
                    })
                    bib = face_map.get(parts[2], "?")
                    name = athletes.get(bib, "?")
                    print(f"  >>> FINISH! face_id={parts[2]} → bib={bib} ({name}) dist={parts[3]}cm")
            elif "END" in line:
                print("  [Loop complete]")

# Ctrl-C to stop
s.write(b'\r\x03\x03')
time.sleep(0.3)
s.close()

print(f"\nTotal events: {len(events)}")
for e in events:
    print(f"  face={e['face_id']} dist={e['dist']}cm")
