#include <ESP32Servo.h>

Servo esc_1;
Servo esc_2;
Servo esc_3;

void setup() {
  Serial.begin(115200);
  Serial.println("Program begin...");

  esc_1.attach(15);
  esc_2.attach(2);
  esc_3.attach(4);
  Serial.println("2000にする");
  esc_1.writeMicroseconds(2000);
  esc_2.writeMicroseconds(2000);
  esc_3.writeMicroseconds(2000);
  Serial.println("Wait 2 seconds.");
  delay(2000);
  esc_1.writeMicroseconds(1000);
  esc_2.writeMicroseconds(1000);
  esc_3.writeMicroseconds(1000);
  delay(2000);
}

void loop() {
  esc_1.writeMicroseconds(1500);
  esc_2.writeMicroseconds(1500);
  esc_3.writeMicroseconds(1500);
}