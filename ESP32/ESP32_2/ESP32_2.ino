/*
制御するもの
ダクテッドファン1個
回収・装填用モーター2個
距離センサー たくさん
*/
#include <Wire.h>        // I2Cを制御する
#include <ESP32Servo.h>  //サーボではなく、ダクテッドファンのESCを制御する
#include <VL53L1X.h>     // 距離センサー VL53L1Xを制御する

TaskHandle_t thp[6];  // マルチスレッドのタスクハンドル格納用

String incomingStrings = "";  // for incoming serial data

// 距離センサー
const uint8_t sensor_count = 4;
const uint8_t xshutPins[sensor_count] = { 19, 18, 5, 4 };
VL53L1X distance_sensors[sensor_count];
uint8_t can_read_distance_sensors_list[sensor_count] = {};                // 使える距離センサーのリスト0〜3
int16_t distance_sensors_result_list[sensor_count] = { -1, -1, -1, -1 };  // 使える距離センサーのリスト0〜3

// ブラシレスモーター
Servo ducted_fan_1;
Servo ducted_fan_2;
boolean calibrate_ducted_fan_enabled_now = false;
boolean calibrate_ducted_fan_enabled_old = false;
boolean is_calibrating_ducted_fan = false;

#define LED_BUILTIN 2

unsigned long last_receive_time = 0;             // 最後にパソコンから受信したmillis
unsigned long startTime, stopTime = 0;           // プログラムの遅延を確認するためにmicros
unsigned int performInfrequentTask_count = 0;    // 500回に1回実行するためのカウント
unsigned int performInfrequentTask_count_2 = 0;  // 10回に1回実行するためのカウント
// bool low_battery_voltage = false;             // バッテリー低電圧時にモーターを強制停止させるときにtrueになる

// モーターのピン
typedef struct
{
  int PWM_channels;
  int PWM;
  int INA;
  int INB;
} dataDictionary;

const dataDictionary PIN_array[]{
  { 4, 25, 32, 33 },
  { 3, 26, 14, 27 }
};

size_t amount_motor = sizeof(PIN_array) / sizeof(PIN_array[0]);

void setup() {
  xTaskCreatePinnedToCore(Core0a_calibrate_ducted_fan, "Core0a_calibrate_ducted_fan", 4096, NULL, 1, &thp[0], 0);
  xTaskCreatePinnedToCore(Core0b_read_distance_sensors, "Core0b_read_distance_sensors", 4096, NULL, 2, &thp[1], 0);
  pinMode(LED_BUILTIN, OUTPUT);  // ESP32内蔵LED
  pinMode(34, INPUT);
  pinMode(35, INPUT);
  pinMode(23, OUTPUT);    // ブラシレスのリレー
  digitalWrite(23, LOW);  // ブラシレスのリレーをOFF

  Serial.begin(921600);
  // Serial.setRxBufferSize(512); // 送受信バッファサイズを変更。デフォルト:256バイト
  // Serial.setRxBufferSize(64); // これ変更しても影響ない？気がする
  while (!Serial) {
    ;  // シリアル通信ポートが正常に接続されるまで抜け出さない
  }
  Serial.setTimeout(1000);  // milliseconds for Serial.readString
  Serial.println(" ");
  Serial.println("ESP32_2起動");
  Serial.println("$2,1,1");
  // Serial2.setTimeout(1); // 1msでシリアル通信タイムアウト 本当はもう少し小さくしたいかも もしかしたらserial2だと意味ないかも
  // Serial2.begin(921600);

  // ICに信号いれる
  for (uint8_t i = 0; i < sensor_count; i++) {
    pinMode(xshutPins[i], OUTPUT);
    digitalWrite(xshutPins[i], LOW);
  }

  // 1つずつセンサーをスタートする
  for (uint8_t i = 0; i < sensor_count; i++) {
    // このセンサーのXSHUTをロー駆動するのを止める。これにより、キャリアボードがXSHUTをHighにプルできるようになる。(XSHUTはレベルシフトされていないため、Highにドライブしたくない。) その後、センサーが起動するまで少し待つ。
    pinMode(xshutPins[i], INPUT);
    delay(10);

    distance_sensors[i].setTimeout(30);
    if (!distance_sensors[i].init()) {
      Serial.print("距離センサー読み取りに失敗");
      Serial.println(i);
      can_read_distance_sensors_list[i] = 0;
    } else {
      distance_sensors[i].setAddress(0x2A + i);  // 各センサーのアドレスを、0x2Aから順にカウントアップする
      distance_sensors[i].setDistanceMode(VL53L1X::Short);
      distance_sensors[i].setMeasurementTimingBudget(20000);  // マイクロ秒 最小20000
      distance_sensors[i].setROISize(4, 4);
      distance_sensors[i].setROICenter(199);
      distance_sensors[i].startContinuous(20);  // 測定間隔30msで連続読み取り開始。これはタイミングバジェット以上に長くする必要がある
      can_read_distance_sensors_list[i] = 1;
    }
  }

  // DCモーターの設定
  for (int i = 0; i < amount_motor; i++) {
    // INA,INBの設定
    pinMode(PIN_array[i].INA, OUTPUT);
    pinMode(PIN_array[i].INB, OUTPUT);
    // PWM初期化
    ledcSetup(PIN_array[i].PWM_channels, 10000, 8);  // PWM 周波数: 10kHz 8bit
    ledcAttachPin(PIN_array[i].PWM, PIN_array[i].PWM_channels);
  }

  // ダクテッドファンの設定
  pinMode(12, OUTPUT);
  pinMode(13, OUTPUT);
  ducted_fan_1.attach(12);
  ducted_fan_2.attach(13);

  Serial.println("$2,1,2");
}

void Core0a_calibrate_ducted_fan(void *args) {  // スレッド
  delay(100);
  while (1) {
    // digitalWrite(LED_BUILTIN, HIGH);
    if (calibrate_ducted_fan_enabled_now == true && calibrate_ducted_fan_enabled_old == false) {
      ducted_fan_1.attach(12);
      ducted_fan_2.attach(13);
      digitalWrite(LED_BUILTIN, LOW);
      is_calibrating_ducted_fan = true;
      // Serial.println("ダクテッドファン キャリブレーション 最大");
      ducted_fan_1.writeMicroseconds(2000);
      ducted_fan_2.writeMicroseconds(2000);
      delay(2000);
      // Serial.println("ダクテッドファン キャリブレーション 最小");
      ducted_fan_1.writeMicroseconds(1000);
      ducted_fan_2.writeMicroseconds(1000);
      delay(2000);
      // Serial.println("ダクテッドファン キャリブレーション 完了");
      is_calibrating_ducted_fan = false;
    }
    calibrate_ducted_fan_enabled_old = calibrate_ducted_fan_enabled_now;
    delay(1);
  }
}

void Core0b_read_distance_sensors(void *args) {
  delay(1000);
  Wire.begin();
  Wire.setClock(400000);  // use 400 kHz I2C

  while (1) {
    for (uint8_t i = 0; i < sensor_count; i++) {
      //  距離センサーを読む
      distance_sensors_result_list[i] = distance_sensors[i].read();
      Serial.println(distance_sensors_result_list[i]);
      if (distance_sensors[i].timeoutOccurred()) {
        // Serial.print(i);
        // Serial.println(" の読み取りに失敗");
        distance_sensors_result_list[i] = -1;
      }
      delay(1);
    }
  }
}

void loop() {

  stopTime = micros();
  // Serial.println(stopTime - startTime);
  // Serial.println("us");

  startTime = micros();

  // analogWrite(0, motor1_speed);
  if (Serial.available() > 0) {
    // read the incoming byte:
    startTime = micros();
    incomingStrings = Serial.readStringUntil('\n');
    // Serial.print("I received: ");
    // Serial.println(incomingStrings);
    if (incomingStrings.length() > 3) {
      const int maxElements = 15;  // 配列の最大要素数 多分ぴったりだとうまく行かない気がする
      int intArray[maxElements];   // 整数の配列
      int count = parseStringToArray(incomingStrings, intArray, maxElements);
      last_receive_time = millis();

      // リスタートするかの処理
      if (intArray[12] == 1) {
        ESP.restart();
      }

      PWM(0, intArray[5]);
      PWM(1, intArray[6]);

      if (intArray[10] == 1) {
        // digitalWrite(LED_BUILTIN, LOW);
        digitalWrite(23, HIGH);
        calibrate_ducted_fan_enabled_now = true;

        // キャリブレーション中でないなら 若しくは キャリブレーション後なら
        if (is_calibrating_ducted_fan == false) {
          // Serial.println("false");
          // analogWrite(LED_BUILTIN, int(intArray[7]* (255/2000)));
          ducted_fan_1.writeMicroseconds(intArray[7]);
          ducted_fan_2.writeMicroseconds(intArray[8]);
        } else {
          // Serial.println("true");
        }
      } else {
        // digitalWrite(LED_BUILTIN, HIGH);
        calibrate_ducted_fan_enabled_now = false;
        digitalWrite(23, LOW);  // リレーオフ
        ducted_fan_1.detach();  // 接続解除
        ducted_fan_2.detach();  // 接続解除
        digitalWrite(12, LOW);  // PWM停止
        digitalWrite(13, LOW);  // PWM停止
      }
      // analogWrite(LED_BUILTIN, abs(intArray[4]));
    } else {
      Serial.println("シリアル通信エラー105");
      Serial.println("$2,5," + String(incomingStrings));
    }
  }

  // ESP32_2からサーボの情報を読み取る
  // String received_strings = Serial2.readStringUntil('\n');
  // if (received_strings.length() > 2)
  // { // 5文字以上あるなら = 空でないなら
  //   Serial.println(received_strings);
  // }

  // Serial.println("$2,4," + String(distance_sensors_result_list[0]) + "," + String(distance_sensors_result_list[1]) + "," + String(distance_sensors_result_list[2]) + "," + String(distance_sensors_result_list[3]));

  // 回収機構のリミットスイッチの状態を取得
  performInfrequentTask_count_2++;
  if (performInfrequentTask_count_2 > 20) {
    performInfrequentTask_count_2 = 0;
    Serial.println("$2,7," + String(digitalRead(35)));
  }

  // 100ms以上パソコンからデータを受信できなかったら全てのモーターを強制停止
  if (millis() - last_receive_time > 100) {
    calibrate_ducted_fan_enabled_now = false;
    digitalWrite(23, LOW);  // リレーオフ
    ducted_fan_1.detach();  // 接続解除
    ducted_fan_2.detach();  // 接続解除
    digitalWrite(12, LOW);  // PWM停止
    digitalWrite(13, LOW);  // PWM停止
    for (int i = 0; i < amount_motor - 1; i++) {
      digitalWrite(PIN_array[i].INA, HIGH);
      digitalWrite(PIN_array[i].INB, HIGH);
    }

    // digitalWrite(LED_BUILTIN, HIGH);
  }

  performInfrequentTask_count++;
  if (performInfrequentTask_count > 200) {
    performInfrequentTask_count = 0;

    // 3セルバッテリー電圧をパソコンに送信
    float battery_voltage = analogRead(34) * 4.034 * 3.3 / 4096;
    Serial.println("$2,3," + String(battery_voltage, 2));
  }

  delay(1);
}

void PWM(int motor_id, int duty) {
  if (duty == 0) {
    // VCCブレーキ
    digitalWrite(PIN_array[motor_id].INA, HIGH);
    digitalWrite(PIN_array[motor_id].INB, HIGH);
  } else if (duty > 0) {
    // 正転
    digitalWrite(PIN_array[motor_id].INA, HIGH);
    digitalWrite(PIN_array[motor_id].INB, LOW);
  } else if (duty < 0) {
    // 逆転
    digitalWrite(PIN_array[motor_id].INA, LOW);
    digitalWrite(PIN_array[motor_id].INB, HIGH);
  }
  ledcWrite(PIN_array[motor_id].PWM_channels, abs(duty));
}

int parseStringToArray(String input, int array[], int maxSize) {
  int count = 0;
  char *token = strtok(const_cast<char *>(input.c_str()), ",");

  while (token != NULL && count < maxSize) {
    array[count] = atoi(token);
    count++;
    token = strtok(NULL, ",");
  }

  return count;
}