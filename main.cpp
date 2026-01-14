#include <Arduino.h>

// Dein reales Mapping:
#define LED_YELLOW 12
#define LED_GREEN  13
#define LED_RED    14

String cmd;

void allOff() {
  digitalWrite(LED_RED, LOW);
  digitalWrite(LED_YELLOW, LOW);
  digitalWrite(LED_GREEN, LOW);
}

void setup() {
  Serial.begin(115200);
  delay(200);

  pinMode(LED_RED, OUTPUT);
  pinMode(LED_YELLOW, OUTPUT);
  pinMode(LED_GREEN, OUTPUT);

  allOff();

  Serial.println("ESP32 LED Controller ready");
  Serial.println("Commands: red_on, red_off, yellow_on, yellow_off, green_on, green_off, all_off");
}

void loop() {
  if (!Serial.available()) return;

  cmd = Serial.readStringUntil('\n');
  cmd.trim();

  if (cmd == "red_on") {
    digitalWrite(LED_RED, HIGH);
    Serial.println("RED ON");
  } else if (cmd == "red_off") {
    digitalWrite(LED_RED, LOW);
    Serial.println("RED OFF");
  } else if (cmd == "yellow_on") {
    digitalWrite(LED_YELLOW, HIGH);
    Serial.println("YELLOW ON");
  } else if (cmd == "yellow_off") {
    digitalWrite(LED_YELLOW, LOW);
    Serial.println("YELLOW OFF");
  } else if (cmd == "green_on") {
    digitalWrite(LED_GREEN, HIGH);
    Serial.println("GREEN ON");
  } else if (cmd == "green_off") {
    digitalWrite(LED_GREEN, LOW);
    Serial.println("GREEN OFF");
  } else if (cmd == "all_off") {
    allOff();
    Serial.println("ALL OFF");
  } else if (cmd == "all_on") {
   digitalWrite(LED_GREEN, HIGH); 
   digitalWrite(LED_YELLOW, HIGH);
   digitalWrite(LED_RED, HIGH);
    Serial.println("ALL ON");
  }  else {
    Serial.print("Unknown command: ");
    Serial.println(cmd);
  }
}
