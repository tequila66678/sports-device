/*
 * Smart Track Timer - Dual IR Beam Trigger
 * Target: Arduino Nano / Uno
 *
 * Two independent laser beam sensors:
 *   - START line sensor (D2): detects race start
 *   - FINISH line sensor (D3): detects each athlete crossing
 *
 * Wiring:
 *   D2  -> START line LDR receiver (LOW = beam broken)
 *   D3  -> FINISH line LDR receiver (LOW = beam broken)
 *   D5  -> Green LED (START alignment indicator, ON = beam aligned)
 *   D6  -> Green LED (FINISH alignment indicator, ON = beam aligned)
 *   D13 -> Red LED (built-in, flashes on trigger)
 *   D9  -> Buzzer (optional)
 */

const int START_SENSOR_PIN   = 2;
const int FINISH_SENSOR_PIN  = 3;
const int START_LED_PIN      = 5;   // Green: ON = aligned
const int FINISH_LED_PIN     = 6;   // Green: ON = aligned
const int STATUS_LED_PIN     = 13;  // Red: flash on trigger
const int BUZZER_PIN         = 9;

const unsigned long DEBOUNCE_MS = 200;
const unsigned long BEEP_MS     = 150;

bool start_broken  = false;
bool finish_broken = false;
unsigned long last_start  = 0;
unsigned long last_finish = 0;

void setup() {
  Serial.begin(115200);

  pinMode(START_SENSOR_PIN, INPUT_PULLUP);
  pinMode(FINISH_SENSOR_PIN, INPUT_PULLUP);
  pinMode(START_LED_PIN, OUTPUT);
  pinMode(FINISH_LED_PIN, OUTPUT);
  pinMode(STATUS_LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  digitalWrite(STATUS_LED_PIN, LOW);

  // Blink twice -> ready
  for (int i = 0; i < 2; i++) {
    digitalWrite(STATUS_LED_PIN, HIGH);
    delay(100);
    digitalWrite(STATUS_LED_PIN, LOW);
    delay(100);
  }

  Serial.println("READY");
}

void loop() {
  unsigned long now = millis();

  // --- START line ---
  int start_state = digitalRead(START_SENSOR_PIN);
  digitalWrite(START_LED_PIN, start_state);  // HIGH = beam intact = LED on

  if (start_state == LOW && !start_broken) {
    start_broken = true;
    if (now - last_start >= DEBOUNCE_MS) {
      last_start = now;
      Serial.println("TRIGGER:START");
      digitalWrite(STATUS_LED_PIN, HIGH);
      tone(BUZZER_PIN, 800, BEEP_MS);
      delay(50);
      digitalWrite(STATUS_LED_PIN, LOW);
    }
  }
  if (start_state == HIGH && start_broken) {
    start_broken = false;
  }

  // --- FINISH line ---
  int finish_state = digitalRead(FINISH_SENSOR_PIN);
  digitalWrite(FINISH_LED_PIN, finish_state);  // HIGH = beam intact = LED on

  if (finish_state == LOW && !finish_broken) {
    finish_broken = true;
    if (now - last_finish >= DEBOUNCE_MS) {
      last_finish = now;
      Serial.println("TRIGGER:FINISH");
      digitalWrite(STATUS_LED_PIN, HIGH);
      tone(BUZZER_PIN, 1200, BEEP_MS);
      delay(50);
      digitalWrite(STATUS_LED_PIN, LOW);
    }
  }
  if (finish_state == HIGH && finish_broken) {
    finish_broken = false;
  }

  delay(1);
}
