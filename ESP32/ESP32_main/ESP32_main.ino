/*
制御するもの
サーボ 1台
Flipsky VESC 1台
ブラシレスモーター on 普通のESC 2個
回収・装填用ブラシ付きモーター2個
距離センサー 4個
*/
#include <Wire.h>               // I2Cを制御する
#include <SPI.h>                // 74HC595を制御する
#include <ESP32Servo.h>         //サーボではなく、ダクテッドファンのESCを制御する https://madhephaestus.github.io/ESP32Servo/annotated.html
#include <VescUart.h>           // VESCブラシレスモーターを制御する https://github.com/SolidGeek/VescUart
#include <IcsHardSerialClass.h> // 近藤化学の公式サイトからダウンロード
#include <VL53L1X.h>            // 距離センサー VL53L1Xを制御する https://github.com/pololu/vl53l1x-arduino

// 全般
TaskHandle_t thp[2];                   // マルチスレッドのタスクハンドル格納用
String incomingStrings = "";           // for incoming serial data
#define MAX_ELEMENTS 20                // 配列の最大要素数 多分ぴったりだとうまく行かない気がする
unsigned long last_receive_time = 0;   // 最後にパソコンから受信したmillis
unsigned long startTime, stopTime = 0; // プログラムの遅延を確認するためにmicros

// 内蔵LED
#define LED_BUILTIN 2

// VESCモーター
VescUart UART(10);

// サーボモーター
#define EN_PIN 23
#define BAUDRATE 115200                                      // TODO 速くする？ノイズも怖いけど
#define TIMEOUT 10                                           // TODO [ms] 遅いとタイムアウトするまで待たないといけないからやばい
IcsHardSerialClass krs(&Serial2, EN_PIN, BAUDRATE, TIMEOUT); // インスタンス＋ENピン(2番ピン)およびUARTの指定

// 距離センサー
#define SENSOR_COUNT 4 // センサーの個数
#define PIN_SER 2      // TODO 配列か構造体か何かにする
#define PIN_LATCH 4
#define PIN_CLK 15
byte patterns[] = {
    B00000000,
    B10000000,
    B11000000,
    B11100000,
    B11110000};
VL53L1X distance_sensors[SENSOR_COUNT];
uint8_t can_read_distance_sensors_list[SENSOR_COUNT] = {}; // 使える距離センサーのリスト0〜3
int16_t distance_sensors_result_list[SENSOR_COUNT] = {-1}; // 使える距離センサーのリスト0〜3

// ブラシレスモーター
Servo ducted_fan;
const uint8_t BLmotor_Pin[1] = {12};

// ブラシ付きモーター
typedef struct
{
  uint8_t PWM_channels;
  uint8_t PWM;
  uint8_t INA;
  uint8_t INB;
} dataDictionary;
const dataDictionary PIN_array[]{
    {4, 25, 32, 33},
    {3, 26, 14, 27}};
const uint8_t amount_motor = sizeof(PIN_array) / sizeof(PIN_array[0]);

// LED連携のピン
#define COMMUNICATE_LED_PIN 13

void servo_setup(){
  krs.setStrc(0, 40); // 127
  krs.setSpd(0, 50);
  krs.setStrc(1, 20); // 10
  krs.setSpd(1, 20);
  krs.setStrc(2, 10);
  krs.setSpd(2, 120);
}

void setup()
{
  xTaskCreatePinnedToCore(Core0a_read_distance_sensors, "Core0a_read_distance_sensors", 4096, NULL, 1, &thp[0], 0);

  Wire.begin();
  Wire.setClock(400000); // use 400 kHz I2C

  pinMode(LED_BUILTIN, OUTPUT);    // ESP32内蔵LED
  digitalWrite(LED_BUILTIN, HIGH); // ESP32内蔵LED

  Serial.begin(500000);
  // Serial.setRxBufferSize(512); // 送受信バッファサイズを変更。デフォルト:256バイト 変更しても効果ないきがする
  while (!Serial)
  {
    ; // シリアル通信ポートが正常に接続されるまで抜け出さない
    // TODO このプログラム怖いんだけど
  }
  Serial.setTimeout(100); // milliseconds for Serial.readString
  Serial.println(" ");
  Serial.println("ESP32_2起動");
  Serial.println("$2,1,1");

  // VESCモーターの初期化
  Serial1.begin(115200, SERIAL_8N1, 18, 19, false, 100); // RX,TXの順 // https://github.com/espressif/arduino-esp32/blob/master/cores/esp32/HardwareSerial.cpp#L280
  // Serial1.begin(unsigned long baud, uint32_t config, int8_t rxPin, int8_t txPin, bool invert, unsigned long timeout_ms, uint8_t rxfifo_full_thrhd)
  /** Define which ports to use as UART */
  UART.setSerialPort(&Serial1);

  // サーボモーターの初期化
  krs.begin(); // サーボモータの通信初期設定
  delay(100);
  // krs.setID(2);

  servo_setup();

  // 距離センサーの処理
  pinMode(PIN_SER, OUTPUT);
  pinMode(PIN_LATCH, OUTPUT);
  pinMode(PIN_CLK, OUTPUT);
  for (uint8_t i = 0; i < sizeof(patterns) / sizeof(byte); i++)
  {
    digitalWrite(PIN_LATCH, LOW);
    shiftOut(PIN_SER, PIN_CLK, LSBFIRST, patterns[i]);
    digitalWrite(PIN_LATCH, HIGH);
    delay(100);
  }
  // 1つずつセンサーをスタートする
  for (uint8_t i = 0; i < SENSOR_COUNT; i++)
  {
    // このセンサーのXSHUTをロー駆動するのを止める。これにより、キャリアボードがXSHUTをHighにプルできるようになる。(XSHUTはレベルシフトされていないため、Highにドライブしたくない。) その後、センサーが起動するまで少し待つ。
    // pinMode(xshutPins[i], INPUT);
    delay(10);

    distance_sensors[i].setTimeout(30);
    if (!distance_sensors[i].init())
    {
      Serial.print("距離センサー読み取りに失敗");
      Serial.println(i);
      can_read_distance_sensors_list[i] = 0;
    }
    else
    {
      distance_sensors[i].setAddress(0x2A + i); // 各センサーのアドレスを、0x2Aから順にカウントアップする
      distance_sensors[i].setDistanceMode(VL53L1X::Short);
      distance_sensors[i].setMeasurementTimingBudget(20000); // マイクロ秒 最小20000
      distance_sensors[i].setROISize(4, 4);
      distance_sensors[i].setROICenter(199);
      distance_sensors[i].startContinuous(20); // 測定間隔30msで連続読み取り開始。これはタイミングバジェット以上に長くする必要がある
      can_read_distance_sensors_list[i] = 1;
    }
  }

  // DCモーターの設定
  for (uint8_t i = 0; i < amount_motor; i++)
  {
    // INA,INBの設定
    pinMode(PIN_array[i].INA, OUTPUT);
    pinMode(PIN_array[i].INB, OUTPUT);
    // PWM初期化
    ledcSetup(PIN_array[i].PWM_channels, 10000, 8); // PWM 周波数: 10kHz 8bit
    ledcAttachPin(PIN_array[i].PWM, PIN_array[i].PWM_channels);
  }

  // ブラシレスモーター
  pinMode(BLmotor_Pin[0], OUTPUT);
  ducted_fan.attach(BLmotor_Pin[0]);

  ducted_fan.writeMicroseconds(2000);
  delay(2000);
  ducted_fan.writeMicroseconds(1000);
  delay(2000);

  // LEDの射出との連携
  pinMode(COMMUNICATE_LED_PIN, OUTPUT);
  digitalWrite(COMMUNICATE_LED_PIN, HIGH);

  Serial.println("$2,1,2");
}

void Core0a_read_distance_sensors(void *args)
{
  delay(1000);

  while (1)
  {
    for (uint8_t i = 0; i < SENSOR_COUNT; i++)
    {
      //  距離センサーを読む
      distance_sensors_result_list[i] = distance_sensors[i].read();
      // Serial.println(distance_sensors_result_list[i]);
      if (distance_sensors[i].timeoutOccurred())
      {
        // Serial.print(i);
        // Serial.println(" の読み取りに失敗");
        distance_sensors_result_list[i] = -1;
      }
      delay(1);
    }
  }
}

void loop()
{
  stopTime = micros();
  // Serial.println(stopTime - startTime);
  // Serial.println("us");

  startTime = micros();

  // ducted_fan.writeMicroseconds(2000);

  // delay(2000);

  // ducted_fan.writeMicroseconds(1000);

  // delay(2000);

  // ducted_fan.writeMicroseconds(2000);
  
  // delay(10000);

  if (Serial.available() > 0)
  {
    // read the incoming byte:
    startTime = micros();
    incomingStrings = Serial.readStringUntil('\r');
    if (incomingStrings.length() > 5)
    {
      int32_t intArray[MAX_ELEMENTS]; // 整数の配列
      uint8_t count = parseStringToArray(incomingStrings, intArray, MAX_ELEMENTS);
      last_receive_time = millis();

      // 再起動するかの処理
      if (intArray[6] == 1)
      {
        Serial.println("$2,6");
        delay(200);
        ESP.restart();
      }

      // 回収モーター0のduty制御
      PWM(0, intArray[0]);

      // 回収モーター1のduty制御
      PWM(1, intArray[1]);

      // 装填サーボの制御
      krs.setPos(0, krs.degPos(int(intArray[3]))); // タイムアウトさせとくと、Serial受信(Serial2じゃなくて)と干渉して、途中までしか受信できなくなった intで囲む必要ない

      // 仰角サーボの制御
      krs.setPos(1, krs.degPos(int(intArray[4])));

      // 玉づまりサーボの制御
      krs.setPos(2, krs.degPos(int(intArray[5])));

      // LEDテープの処理 射出時のアニメーションのトリガー
      if (intArray[8] == 1)
      {
        digitalWrite(COMMUNICATE_LED_PIN, LOW);
      }
      else
      {
        digitalWrite(COMMUNICATE_LED_PIN, HIGH);
      }

      // サーボを初期設定する
      if (intArray[9] == 1){
        // サーボモーターの初期化
        krs.begin(); // サーボモータの通信初期設定
        delay(100);
        servo_setup();
      }

      // VESCの制御
      UART.setRPM(float(intArray[7]), 0); // 連続して送らないとタイムアウトで勝手に切れる 安全装置ナイス

      // PWM出力のデバイスの制御
      ducted_fan.writeMicroseconds(intArray[10]);
      Serial.println(intArray[10]);
      // ducted_fan.writeMicroseconds(2000);

      // analogWrite(LED_BUILTIN , intArray[4]* -1);

      // analogWrite(LED_BUILTIN , intArray[10]/10);

      // ducted_fan.detach();  // 接続解除
      // digitalWrite(BLmotor_Pin[0], LOW);  // ブラシレスモーターのPWM停止
    }
    else
    {
      Serial.println("$2,5," + String(incomingStrings));
    }
  }

  // int pos = krs.getPos(0);  // ID0 の現在のポジションデータを読み取ります
  // // float got_deg = krs.posDeg(pos);
  // Serial.println("");
  // Serial.print("1角度");
  // Serial.println(pos);
  // Serial.println(got_deg);

  // Serial.println("$2,4," + String(distance_sensors_result_list[0]) + "," + String(distance_sensors_result_list[1]) + "," + String(distance_sensors_result_list[2]) + "," + String(distance_sensors_result_list[3]));

  // if (UART.getVescValues())
  // {
  //   Serial.print("RPM:");
  //   // Serial.println(UART.data.rpm/14); // 限界突破してる説ある
  //   Serial.println(UART.data.rpm); // 限界突破してる説ある
  //   // Serial.print("ボルト:");
  //   // Serial.println(UART.data.inpVoltage);
  //   // Serial.print("アンペア:");
  //   // Serial.println(UART.data.ampHours); // うまく反応してない説 0.02A
  //   // Serial.print("オドメトリ:");
  //   // Serial.println(UART.data.tachometerAbs);
  // }
  // else
  // {
  //   Serial.println("Failed to get VESC data!");
  // }

  // 100ms以上パソコンからデータを受信できなかったら全てのモーターを強制停止(WatchdogTimerみたいな)
  if (millis() - last_receive_time > 100)
  {
    digitalWrite(LED_BUILTIN, LOW); // ESP32内蔵LED
    // ducted_fan.detach();               // 接続解除
    // digitalWrite(BLmotor_Pin[0], LOW); // PWM停止
    krs.setFree(0); //フリー指令 ID:0 をフリー状態に
    krs.setFree(1); //フリー指令 ID:1 をフリー状態に
    krs.setFree(2); //フリー指令 ID:1 をフリー状態に
    // ducted_fan_2.detach();  // 接続解除
    // digitalWrite(13, LOW);  // PWM停止
    for (uint8_t i = 0; i < amount_motor - 1; i++)
    {
      digitalWrite(PIN_array[i].INA, HIGH);
      digitalWrite(PIN_array[i].INB, HIGH);
    }

    // digitalWrite(LED_BUILTIN, HIGH);
  }

  delay(1);
}

void PWM(uint8_t motor_id, int16_t duty)
{
  if (duty == 0)
  {
    // VCCブレーキ
    digitalWrite(PIN_array[motor_id].INA, HIGH);
    digitalWrite(PIN_array[motor_id].INB, HIGH);
  }
  else if (duty > 0)
  {
    // 正転
    digitalWrite(PIN_array[motor_id].INA, HIGH);
    digitalWrite(PIN_array[motor_id].INB, LOW);
  }
  else if (duty < 0)
  {
    // 逆転
    digitalWrite(PIN_array[motor_id].INA, LOW);
    digitalWrite(PIN_array[motor_id].INB, HIGH);
  }
  ledcWrite(PIN_array[motor_id].PWM_channels, abs(duty));
}

uint8_t parseStringToArray(String input, int32_t array[], uint8_t maxSize)
{
  uint8_t count = 0;
  char *token = strtok(const_cast<char *>(input.c_str()), ",");

  while (token != NULL && count < maxSize)
  {
    array[count] = atoi(token);
    count++;
    token = strtok(NULL, ",");
  }

  return count;
}