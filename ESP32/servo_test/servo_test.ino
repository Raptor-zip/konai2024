#include <IcsHardSerialClass.h>

const byte EN_PIN = 2;
const long BAUDRATE = 115200;
const int TIMEOUT = 1000; // 通信できてないか確認用にわざと遅めに設定

IcsHardSerialClass krs(&Serial2, EN_PIN, BAUDRATE, TIMEOUT); // インスタンス＋ENピン(2番ピン)およびUARTの指定

void setup()
{
    Serial.begin(921600);
    krs.begin(); // サーボモータの通信初期設定
    krs.setStrc(0, 60);
    krs.setSpd(0, 127); // MAX127
}

void loop()
{
    int deg = -90;
    // krs.setPos(0, 9000);
    krs.setPos(0, krs.degPos(int(deg)));

    // delay(0);
    // int cur = krs.getCur(0); // ID0 の電流値を読み取ります
    // int tmp = krs.getTmp(0); // ID0 の温度値を読み取ります
    // int pos = krs.getPos(0); // ID0 の現在のポジションデータを読み取ります
    // float got_deg = krs.posDeg(pos);
    // Serial.print("温度");
    // Serial.print(tmp);
    // Serial.print("電流");
    // Serial.print(cur);
    // Serial.print("角度");
    // Serial.println(got_deg);
    delay(1000);

    deg = 90;
    krs.setPos(0, krs.degPos(int(deg)));

    delay(1000);
}