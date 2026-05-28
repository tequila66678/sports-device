"""Try SmartEye functions for BE-1743 on E6-RCU P6."""
import serial, time

s = serial.Serial('COM9', 115200, timeout=2)
time.sleep(0.5)
s.read(4096)

def repl(cmd, wait=1):
    s.write((cmd + '\r\n').encode())
    time.sleep(wait)
    out = s.read(2048)
    return out.decode('ascii', errors='replace')

repl('import sensor')
repl('import rcu')

# Try SmartEye functions
tests = [
    ('sensor.SetSmartEyeMode(6, 1)', 'Set SmartEye mode 1'),
    ('sensor.SetSmartEyeMode(6, 2)', 'Set SmartEye mode 2'),
    ('sensor.SetSmartEyeMode(6, 8)', 'Set SmartEye mode 8'),
    ('sensor.GetSmartEyeDist(6)', 'Get SmartEye dist'),
    ('sensor.GetSmartEyeIRcode(6)', 'Get SmartEye IR code'),
    ('sensor.SetSmartEyeAllLed(6, 1)', 'Set SmartEye LED on'),
    ('sensor.GetScanCamera(6)', 'Get Scan Camera'),
    # Also try with port numbers as different parameters
    ('rcu.GetSmartEyeDist(6)', 'RCU SmartEye dist'),
    ('rcu.GetSmartEyeIRcode(6)', 'RCU SmartEye IR'),
]

print("Trying SmartEye & camera functions on P6...\n")
for cmd, desc in tests:
    r = repl(cmd, 0.8)
    lines = r.split('\r\n')
    for l in lines:
        l = l.strip()
        if l and '>>>' not in l and cmd.split('(')[0] not in l:
            if 'Error' in l or 'Traceback' in l:
                print(f'  {desc}: ERROR - {l[:80]}')
            elif l != '0':
                print(f'  {desc}: {l}')
    # Print grouped by function
print("\nDone. If SmartEye functions error, BE-1743 uses different API.")
s.close()
