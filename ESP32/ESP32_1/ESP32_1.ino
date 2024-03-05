/*
制御するもの
メカナムホイール4輪
バッテリー電圧取得
ステータススピーカー
*/
#include <Wire.h>  // 現状I2C使ってないけどw
#include <IcsHardSerialClass.h>

const byte EN_PIN = 2;
const long BAUDRATE = 115200;
const int TIMEOUT = 1000;  // 通信できてないか確認用にわざと遅めに設定

IcsHardSerialClass krs(&Serial2, EN_PIN, BAUDRATE, TIMEOUT);  // インスタンス＋ENピン(2番ピン)およびUARTの指定

TaskHandle_t thp[3];  // マルチスレッドのタスクハンドル格納用

String incomingStrings = "";  // for incoming serial data

// #define LED_BUILTIN 2

unsigned long last_receive_time = 0;           // 最後にESP32_2から受信したmillis
unsigned long startTime, stopTime = 0;         // プログラムの遅延を確認するためにmicros
unsigned int performInfrequentTask_count = 0;  // 500回に1回実行するためのカウント

boolean state_boolean_array[300];

bool low_battery_voltage = false;  // バッテリー低電圧時にモーターを強制停止させるときにtrueになる

// モーターのピン
typedef struct
{
  int PWM_channels;
  int PWM;
  int INA;
  int INB;
} dataDictionary;

const dataDictionary PIN_array[]{
  { 1, 25, 32, 33 },
  { 2, 26, 14, 27 },
  { 3, 12, 23, 19 },
  { 4, 13, 4, 18 }
};

size_t amount_motor = sizeof(PIN_array) / sizeof(PIN_array[0]);

void setup() {
  xTaskCreatePinnedToCore(Core0a_speaker,
                          "Core0a_speaker", 4096, NULL, 1, &thp[0], 0);
  pinMode(35, INPUT);
  // pinMode(8, OUTPUT);
  Serial.begin(921600);  // PCとUSB接続
  // Serial.setRxBufferSize(512); // 送受信バッファサイズを変更。デフォルト:256バイト
  // Serial.setRxBufferSize(64); // これ変更しても影響ない？気がする
  while (!Serial) {
    ;  // シリアル通信ポートが正常に接続されるまで抜け出さない
  }
  Serial.setTimeout(1000);  // milliseconds for Serial.readString
  Serial.println(" ");
  Serial.println("ESP32_1起動");
  Serial.println("$1,1.1");

  // 配列をfalseで初期化
  for (int i = 0; i < 300; i++) {
    state_boolean_array[i] = false;
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

  // ステータススピーカーのピン設定
  ledcSetup(0, 12000, 8);
  ledcAttachPin(15, 0);

  // サーボモーターの設定
  krs.begin();  // サーボモータの通信初期設定
  krs.setStrc(0, 60);
  krs.setSpd(0, 127);  // MAX127

  Serial.println("$1,1.2");
}

void Core0a_speaker(void *args) {
  const u_int16_t green = 600;
  const u_int16_t yellow = 1300;
  const u_int16_t red = 2000;
  delay(100);
  // 起動音
  ledcWriteTone(0, green);
  delay(100);
  ledcWriteTone(0, yellow);
  delay(100);
  ledcWriteTone(0, red);
  delay(400);
  ledcWriteTone(0, 0);
  delay(1000);

  while (1) {
    delay(1);
    // 最初にtrueになるインデックスを見つける
    int firstTrueIndex = findFirstTrueIndex(state_boolean_array);
    Serial.print("スピーカー");
    Serial.println(firstTrueIndex);
    switch (firstTrueIndex) {
      case 1:
        ledcWriteTone(0, red);
        delay(1000);
        break;
      case 2:
        ledcWriteTone(0, red);
        delay(1000);
        break;
      case 3:
        ledcWriteTone(0, red);
        delay(100);
        ledcWriteTone(0, 0);
        delay(900);
        break;
      case 4:
        ledcWriteTone(0, red);
        delay(100);
        ledcWriteTone(0, 0);
        delay(100);
        ledcWriteTone(0, red);
        delay(100);
        ledcWriteTone(0, 0);
        delay(800);
        break;
      case 5:
        ledcWriteTone(0, red);
        delay(250);
        ledcWriteTone(0, yellow);
        delay(250);
        ledcWriteTone(0, red);
        delay(250);
        ledcWriteTone(0, yellow);
        delay(250);
        break;
      case 6:
        ledcWriteTone(0, red);
        delay(250);
        ledcWriteTone(0, green);
        delay(250);
        ledcWriteTone(0, red);
        delay(250);
        ledcWriteTone(0, green);
        delay(250);
        break;
      case 101:
        ledcWriteTone(0, red);
        delay(500);
        ledcWriteTone(0, yellow);
        delay(500);
        break;
      case 102:
        ledcWriteTone(0, red);
        delay(500);
        ledcWriteTone(0, green);
        delay(500);
        break;
      case 201:
        ledcWriteTone(0, green);
        delay(100);
        ledcWriteTone(0, 0);
        delay(900);
        break;
      case 202:
        ledcWriteTone(0, green);
        delay(100);
        ledcWriteTone(0, 0);
        delay(100);
        ledcWriteTone(0, green);
        delay(100);
        ledcWriteTone(0, 0);
        delay(800);
        break;
      default:
        Serial.println(firstTrueIndex);
        Serial.println("1ステータススピーカーのcaseがおかしい");
    }
  }
}

void loop() {
  stopTime = micros();
  // Serial.println(stopTime - startTime);
  // Serial.println("us");

  startTime = micros();

  if (Serial.available() > 0) {
    // read the incoming byte:
    startTime = micros();
    incomingStrings = Serial.readStringUntil('\n');
    // Serial.print("I received: ");
    // Serial.println(incomingStrings);
    if (incomingStrings.length() > 5) {
      const int maxElements = 10;  // 配列の最大要素数
      int intArray[maxElements];   // 整数の配列
      int count = parseStringToArray(incomingStrings, intArray, maxElements);
      last_receive_time = millis();

      if (intArray[12] == 1) {
        ESP.restart();
      }

      // バッテリーのステータススピーカーの処理
      if (intArray[13] == 2) {
        state_boolean_array[101] = true;
      } else {
        state_boolean_array[101] = false;
      }
      if (intArray[13] == 3 || intArray[13] == 4 || intArray[13] == 5) {
        state_boolean_array[5] = true;
      } else {
        state_boolean_array[5] = false;
      }
      if (intArray[14] == 2) {
        state_boolean_array[102] = true;
      } else {
        state_boolean_array[102] = false;
      }
      if (intArray[14] == 3 || intArray[14] == 4 || intArray[14] == 5) {
        state_boolean_array[6] = true;
      } else {
        state_boolean_array[6] = false;
      }

      // DCモーターの処理
      PWM(0, intArray[1]);
      PWM(1, intArray[2]);
      PWM(2, intArray[3]);
      PWM(3, intArray[4]);

      state_boolean_array[201] = true;

      // サーボモーターの処理
      krs.setPos(0, krs.degPos(int(intArray[9])));
    } else {
      Serial.println("シリアル通信エラー105");
      Serial.println("$1,5," + String(incomingStrings));
    }
  }

  // int pos = krs.getPos(0);  // ID0 の現在のポジションデータを読み取ります
  // // float got_deg = krs.posDeg(pos);
  // Serial.println("");
  // Serial.print("1角度");
  // Serial.println(pos);
  // Serial.println(got_deg);

  // 100ms以上パソコンからデータを受信できなかったら全てのモーターを強制停止
  if (millis() - last_receive_time > 100) {
    state_boolean_array[2] = true;

    for (int i = 0; i < amount_motor; i++)  // -1いるかも！！！！！！！！！！！！１１
    {
      digitalWrite(PIN_array[i].INA, HIGH);
      digitalWrite(PIN_array[i].INB, HIGH);
    }
    // ステータススピーカーの処理をするーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーー
  } else {
    state_boolean_array[2] = false;
  }

  performInfrequentTask_count++;
  if (performInfrequentTask_count > 200) {
    performInfrequentTask_count = 0;

    // 4セルバッテリー電圧をパソコンに送信
    float battery_voltage = analogRead(35) * 7.0609 * 3.3 / 4096;
    Serial.println("$1,2," + String(battery_voltage, 2));
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

int findFirstTrueIndex(boolean arr[]) {
  for (int i = 0; i < 300; i++) {
    if (arr[i] == true) {
      return i;
    }
  }
  return -1;  // trueが見つからない場合は-1を返す
}