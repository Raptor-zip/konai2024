#include <ESP32Servo.h>

#define ESC_PIN 15  //ESCへの出力ピン
int volume = 0;  //可変抵抗の値を入れる変数
char message[50];  //シリアルモニタへ表示する文字列を入れる変数

Servo esc;  //Servoオブジェクトを作成する．今回はESCにPWM信号を送るので，`esc`と命名している．

void setup() {
  Serial.begin(115200);
  Serial.println("Program begin...");

  esc.attach(ESC_PIN);  //ESCへの出力ピンをアタッチします
  Serial.println("2000にする");
  esc.writeMicroseconds(2000);  //ESCへ最小のパルス幅を指示します
  Serial.println("Wait 2 seconds.");
  delay(2000);
  esc.writeMicroseconds(1000);  //ESCへ最小のパルス幅を指示します
  delay(2000);
}

void loop() {
  volume = 1120;
  sprintf(message, "%d micro sec", volume);  //シリアルモニタに表示するメッセージを作成
  Serial.println(message);  //可変抵抗の値をシリアルモニタに表示
  esc.writeMicroseconds(volume);  // パルス幅 `volume` のPWM信号を送信する
}