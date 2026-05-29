"""Test each person's face ID one by one."""
import serial, time

s = serial.Serial('COM12', 115200, timeout=3)
time.sleep(0.5)
s.read(4096)

def test_face():
    s.write(b'\r\x03\x03')
    time.sleep(0.3)
    s.read(1024)
    s.write(b'\r\x01')
    time.sleep(0.3)
    s.read(256)

    code = (
        'import rcu,utime\r\n'
        'rcu.SetWaitForAICamData(10,0)\r\n'
        'utime.sleep_ms(500)\r\n'
        'print(str(rcu.GetAICamData(1)))\r\n'
        'utime.sleep_ms(400)\r\n'
        'print(str(rcu.GetAICamData(1)))\r\n'
        'utime.sleep_ms(400)\r\n'
        'print(str(rcu.GetAICamData(1)))\r\n'
        'print("END")\r\n'
    )
    s.write(code.encode())
    time.sleep(0.2)
    s.write(b'\x04')
    time.sleep(5)
    out = s.read(4096)
    text = out.decode('ascii', errors='replace')
    ids = []
    for line in text.split('\r\n'):
        line = line.strip().replace('\x04','').replace('>','').replace('OK','')
        if line.isdigit():
            ids.append(int(line))
    return ids

for person in ['PERSON_1', 'PERSON_2', 'PERSON_3']:
    input(f'\n>>> {person}: stand in front of camera. Press Enter...')
    ids = test_face()
    unique = [x for x in ids if x > 0]
    if unique:
        print(f'  Face IDs: {unique} (most common: {max(set(unique), key=unique.count)})')
    else:
        print('  Face IDs: all 0 - NOT RECOGNIZED')

s.write(b'\r\x03')
s.close()
print('\nDone.')
