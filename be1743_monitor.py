"""Monitor BE-1743 serial output without stopping boot.py."""
import serial, time

s = serial.Serial('COM10', 115200, timeout=0.5)
time.sleep(1)
s.reset_input_buffer()

print("Monitoring BE-1743 serial output (let boot.py run)...")
print("Stand in front of camera. Press Ctrl+C to stop.\n")

try:
    while True:
        data = s.read(4096)
        if data:
            # Print raw bytes that look like data
            text = data.decode('ascii', errors='replace')
            if text.strip():
                print(f"[{time.strftime('%H:%M:%S')}] {text.strip()[:200]}")
        time.sleep(0.2)
except KeyboardInterrupt:
    print("\nDone")
finally:
    s.close()
