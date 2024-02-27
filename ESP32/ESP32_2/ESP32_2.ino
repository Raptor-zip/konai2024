// パソコンとシリアル通信して、センサー情報を送信したり、回収装填用モーターを制御する。
/*
制御するもの
ダクテッドファン1個
回収・装填用モーター2個
*/
#include <Wire.h>
#include <ESP32Servo.h> //サーボではなく、ダクテッドファンのESCを制御する

Servo esc;

String incomingStrings; // for incoming serial data

#define LED_BUILTIN 2

unsigned long last_receive_time;              // 最後にパソコンから受信したmillis
unsigned long startTime, stopTime;            // プログラムの遅延を確認するためにmicros
unsigned int performInfrequentTask_count = 0; // 500回に1回実行するためのカウント
// bool low_battery_voltage = false;             // バッテリー低電圧時にモーターを強制停止させるときにtrueになる

typedef struct
{
  int PWM_channels;
  int PWM;
  int INA;
  int INB;
} dataDictionary;

const dataDictionary PIN_array[]{
    {0, 25, 32, 33},
    {1, 26, 14, 27}};

size_t amount_motor = sizeof(PIN_array) / sizeof(PIN_array[0]);

void setup()
{
  pinMode(LED_BUILTIN, OUTPUT);

  Serial.begin(921600);
  Serial2.setTimeout(1); // 1msでシリアル通信タイムアウト 本当はもう少し小さくしたいかも もしかしたらserial2だと意味ないかも
  Serial2.begin(921600);

  // ダクテッドファンの設定
  esc.attach(12);
  Serial.println("ダクテッドファン キャリブレーション 最大");
  esc.writeMicroseconds(2000);
  delay(2000);
  Serial.println("ダクテッドファン キャリブレーション 最小");
  esc.writeMicroseconds(1000);
  delay(2000);

  pinMode(LED_BUILTIN, OUTPUT);
  // Serial.setRxBufferSize(512); // 送受信バッファサイズを変更。デフォルト:256バイト
  // Serial.setRxBufferSize(64); // これ変更しても影響ない？気がする
  while (!Serial)
  {
    ; // シリアル通信ポートが正常に接続されるまで抜け出さない
  }
  // Serial.setTimeout(10); // milliseconds for Serial.readString
  Serial.setTimeout(1000); // milliseconds for Serial.readString
  Serial.println("ESP32_2起動");

  for (int i = 0; i < amount_motor; i++)
  {
    // INA,INBの設定
    pinMode(PIN_array[i].INA, OUTPUT);
    pinMode(PIN_array[i].INB, OUTPUT);
    // PWM初期化
    ledcSetup(PIN_array[i].PWM_channels, 10000, 8); // PWM 周波数: 10kHz 8bit
    ledcAttachPin(PIN_array[i].PWM, PIN_array[i].PWM_channels);
  }
}

void loop()
{

  stopTime = micros();
  // Serial.println(stopTime - startTime);
  // Serial.println("us");

  startTime = micros();

  // analogWrite(0, motor1_speed);
  if (Serial.available() > 0)
  {
    // read the incoming byte:
    startTime = micros();
    incomingStrings = Serial.readStringUntil('\n');
    // Serial.print("I received: ");
    // Serial.println(incomingStrings);
    if (incomingStrings.length() > 5)
    {
      last_receive_time = millis();
      const int maxElements = 10; // 配列の最大要素数
      int intArray[maxElements];  // 整数の配列
      int count = parseStringToArray(incomingStrings, intArray, maxElements);

      PWM(0, intArray[4]);
      PWM(1, intArray[5]);
      esc.writeMicroseconds(intArray[6] + 1000);
      analogWrite(LED_BUILTIN, abs(intArray[0]));
    }
    else
    {
      Serial.println("シリアル通信エラー105");
    }
  }

  // ESP32_2からサーボの情報を読み取る
  String received_strings = Serial2.readStringUntil('\n');
  if (received_strings.length() > 2)
  { // 5文字以上あるなら = 空でないなら
    Serial.println(received_strings);
  }

  performInfrequentTask_count++;
  if (performInfrequentTask_count > 500)
  {
    performInfrequentTask_count = 0;
    // 500ms以上パソコンからデータを受信できなかったら全てのモーターを強制停止
    if (millis() - last_receive_time > 100)
    {
      for (int i = 0; i < amount_motor - 1; i++)
      {
        digitalWrite(PIN_array[i].INA, HIGH);
        digitalWrite(PIN_array[i].INB, HIGH);
      }

      digitalWrite(LED_BUILTIN, HIGH);
      delay(100);
      digitalWrite(LED_BUILTIN, LOW);
      delay(100);
    }
  }

  delay(1);
}

void PWM(int motor_id, int duty)
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

int parseStringToArray(String input, int array[], int maxSize)
{
  int count = 0;
  char *token = strtok(const_cast<char *>(input.c_str()), ",");

  while (token != NULL && count < maxSize)
  {
    array[count] = atoi(token);
    count++;
    token = strtok(NULL, ",");
  }

  return count;
}