"""Test BE-1743 via E6-RCU - poll all data fields."""
import serial, time

s = serial.Serial('COM9', 115200, timeout=2)
time.sleep(0.5)
s.read(4096)

def repl(cmd, wait=1):
    s.write((cmd + '\r\n').encode())
    time.sleep(wait)
    out = s.read(4096)
    return out.decode('ascii', errors='replace')

# Import and setup
repl('import ai')
repl('import rcu')

# Set mode 2 (as per SB3 example) on port 6
print("Setting mode...")
repl('ai.SetAICamData(6,2)', 2)
print("Mode set")

# Poll all 14 data fields
print("\nPolling all data fields (cmd 1-14)...")
print("Put face in front of BE-1743!\n")

for cmd in range(1, 15):
    r = repl(f'ai.GetAICamData({cmd})', 0.5)
    # Extract result value
    lines = r.split('\r\n')
    for l in lines:
        l = l.strip()
        if l and '>>>' not in l and 'GetAICamData' not in l and 'import' not in l:
            if l != '0':
                print(f'  cmd={cmd}: {l} (HEX: 0x{int(l):02X})' if l.isdigit() or (l.startswith('-') and l[1:].isdigit()) else f'  cmd={cmd}: {l}')

# Also try SetAICamData with mode 8 (face recognition)
print("\n\nTrying mode 8 (face recognition learning)...")
repl('ai.SetAICamData(6,8)', 2)

for cmd in range(1, 15):
    r = repl(f'ai.GetAICamData({cmd})', 0.5)
    lines = r.split('\r\n')
    for l in lines:
        l = l.strip()
        if l and '>>>' not in l and 'GetAICamData' not in l and 'import' not in l:
            if l != '0':
                print(f'  cmd={cmd}: {l}')

s.close()
print("\nDone")
