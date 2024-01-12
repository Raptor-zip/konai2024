#include <IcsSoftSerialClass.h>
// 1/11 ピン配置
// D0 ESPTX
// D1 ESPRX
// D6 Motor5 PWM
// D8 Motor5 AIN
// D7 Motor5 BIN
// D10 STX//S=Servo
// D11 SRX
// D12 SIO
// A4 SDA
// A5 SCL
const int LED_PIN = 13;
const int S_RX_PIN = 12;
const int S_TX_PIN = 11;
const int EN_PIN = 10; /////////////////////////////////////////////////////////////////////////あとでかえる///////////////////////////////////////////
const long BAUDRATE = 115200;  // 上げたらどうなるのか確かめる
const int TIMEOUT = 200;       // softSerialは通信失敗する可能性があるため短めに

String received_strings;  // for incoming serial data

int temp = 0;

String cmds[2] = { "\0" };  // 分割された文字列を格納する配列
// char cmds[2][10] = { "" };

IcsSoftSerialClass krs(S_RX_PIN, S_TX_PIN, EN_PIN, BAUDRATE, TIMEOUT);  // インスタンス＋ENピン(2番ピン)およびUARTの設定、softSerial版

typedef struct
{
  int PWM;
  int INA;
  int INB;
} dataDictionary;

const dataDictionary PIN_array[]{
  { 6, 8, 7 }
};

void setup() {
  krs.begin();  // サーボモータの通信初期設定
  krs.setStrc(0, 60);
  krs.setSpd(0, 127);  // MAX127

  pinMode(LED_PIN, OUTPUT);

  for (int i = 0; i < 1; i++) {
    pinMode(PIN_array[i].PWM, OUTPUT);
    pinMode(PIN_array[i].INA, OUTPUT);
    pinMode(PIN_array[i].INB, OUTPUT);
  }
  Serial.setTimeout(1);  // 1msでシリアル通信タイムアウト 本当はもう少し小さくしたいかも
  Serial.begin(115200);
}



void loop() {
  received_strings = Serial.readStringUntil('\n');
  // Serial.print("I received: ");
  // Serial.println(received_strings);
  if (received_strings.length() > 2) {
    for (int i = 0; i < 2; i++) {
      cmds[i] = "";
    }
    int index = split(received_strings, ',', cmds);
    Serial.println(cmds[0]);

    switch (cmds[0].toInt()) {
      case 5:
        PWM(1, cmds[1].toInt());

      case 6:
        Serial.println(cmds[1]);

        if (cmds[1].toInt() == 999) {
          // フリーにする バッテリーの低電圧を検知したときに送られる
          digitalWrite(LED_PIN, HIGH);
          krs.setFree(0);  ////ID:0 をフリー状態に
        } else {
          // バッテリー電圧が問題ないとき
          if (cmds[1].toInt() == 135) {
            digitalWrite(LED_PIN, HIGH);
          } else {
            digitalWrite(LED_PIN, LOW);
          }

          krs.setPos(0, krs.degPos(cmds[1].toInt()));
        }
    }
  }

  // サーボの状態を取得する timeout:約200ms
  int cur = krs.getCur(0);  //ID0 の電流値を読み取ります
  if (cur != -1) {
    int tmp = krs.getTmp(0);          //ID0 の温度値を読み取ります
    int pos = krs.getPos(0);          //ID0 の現在のポジションデータを読み取ります
    float got_deg = krs.posDeg(pos);  //度数法に変換
    // サーボの状態を送信する
    Serial.println("{\"servo_tmp\":" + String(tmp) + ",\"servo_cur\":" + String(cur) + ",\"servo_deg\":" + String(got_deg) + "}");
  }else{
    // サーボの状態を送信する
    Serial.println("{\"servo_tmp\":999,\"servo_cur\":999,\"servo_deg\":999}");
  }
}

void PWM(int motor_id, int duty) {
  temp = 0;
  if (duty == 0) {
    // VCCブレーキ
    digitalWrite(PIN_array[motor_id - 1].INA, HIGH);
    digitalWrite(PIN_array[motor_id - 1].INB, HIGH);
  } else if (duty > 0) {
    // 正転
    digitalWrite(PIN_array[motor_id - 1].INA, HIGH);
    digitalWrite(PIN_array[motor_id - 1].INB, LOW);
  } else if (duty < 0) {
    // 逆転
    digitalWrite(PIN_array[motor_id - 1].INA, LOW);
    digitalWrite(PIN_array[motor_id - 1].INB, HIGH);
  }
  analogWrite(PIN_array[motor_id - 1].PWM, abs(duty));
}

int split(String data, char delimiter, String *dst) {
  int index = 0;
  int datalength = data.length();

  for (int i = 0; i < datalength; i++) {
    char tmp = data.charAt(i);
    if (tmp == delimiter) {
      index++;
    } else
      dst[index] += tmp;
  }

  return (index + 1);
}


// void loop() {
//   // シリアル通信が利用可能かどうかを確認
//   if (Serial.available() > 0) {
//     // シリアルバッファから1バイト読み込む
//     char receivedChar = Serial.read();

//     // 改行（'\n'）が受信されたら、printlnで改行して内容を表示
//     if (receivedChar == '\n') {
//       Serial.println();
//     } else {
//       // 受信した文字を表示
//       Serial.print(receivedChar);
//     }
//   }
// }