#include <Arduino.h>

#if __has_include(<esp_arduino_version.h>)
#include <esp_arduino_version.h>
#endif

constexpr uint8_t PIN_IR_TX = 25;
constexpr uint8_t PIN_IR_RX = 26;
constexpr uint8_t PIN_STATUS = 27;
constexpr uint8_t PIN_PAIR = 33;
constexpr uint32_t IR_CARRIER_HZ = 38000;

#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
void carrierBegin() {
  ledcAttach(PIN_IR_TX, IR_CARRIER_HZ, 8);
}
void carrier(bool on) {
  ledcWrite(PIN_IR_TX, on ? 128 : 0);
}
#else
constexpr uint8_t IR_PWM_CHANNEL = 0;
void carrierBegin() {
  ledcSetup(IR_PWM_CHANNEL, IR_CARRIER_HZ, 8);
  ledcAttachPin(PIN_IR_TX, IR_PWM_CHANNEL);
}
void carrier(bool on) {
  ledcWrite(IR_PWM_CHANNEL, on ? 128 : 0);
}
#endif

void irBurst(uint16_t milliseconds) {
  carrier(true);
  delay(milliseconds);
  carrier(false);
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_STATUS, OUTPUT);
  pinMode(PIN_PAIR, INPUT_PULLUP);
  pinMode(PIN_IR_RX, INPUT_PULLUP);
  carrierBegin();
  carrier(false);
  Serial.println("IR Blaster REV4 factory test");
  Serial.println("PAIR press = 100 ms 38 kHz burst");
}

void loop() {
  static bool lastPair = HIGH;
  static bool lastRx = HIGH;
  static uint32_t lastHeartbeat = 0;

  const bool pair = digitalRead(PIN_PAIR);
  const bool rx = digitalRead(PIN_IR_RX);

  if (lastPair == HIGH && pair == LOW) {
    Serial.println("PAIR pressed; transmitting IR burst");
    digitalWrite(PIN_STATUS, HIGH);
    irBurst(100);
    digitalWrite(PIN_STATUS, LOW);
  }
  if (rx != lastRx) {
    Serial.printf("IR_RX=%d\n", rx);
    lastRx = rx;
  }
  if (millis() - lastHeartbeat >= 1000) {
    lastHeartbeat = millis();
    digitalWrite(PIN_STATUS, !digitalRead(PIN_STATUS));
    Serial.printf("alive pair=%d rx=%d\n", pair, rx);
  }

  lastPair = pair;
  delay(5);
}
