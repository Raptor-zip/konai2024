#include <ESP32Servo.h>

Servo esc;

void setup() {
  Serial.begin(115200);
  Serial.println("Program begin...");

  esc.attach(15);
  Serial.println("2000にする");
  esc.writeMicroseconds(2000);
  Serial.println("Wait 2 seconds.");
  delay(2000);
  esc.writeMicroseconds(1000);
  delay(2000);

  for(int i=1000; i < 1250; i++){
    esc.writeMicroseconds(i);
    delay(4);
  }
}

void loop() {
}