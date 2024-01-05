#include <IcsSoftSerialClass.h>

const byte S_RX_PIN = 2;  // あとで変更する
const byte S_TX_PIN = 3;  // あとで変更する
const byte EN_PIN = 4;    // あとで変更する
const long BAUDRATE = 115200;
const int TIMEOUT = 200;  // softSerialは通信失敗する可能性があるため短めに

const int LED_PIN = 13;

String received_strings;  // for incoming serial data

bool low_battery_voltage = false;

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
  { "D6", "D8", "D7" },
  { "D5", "D4", "D3" }
};

void setup() {
  krs.begin();  // サーボモータの通信初期設定

  pinMode(LED_PIN, OUTPUT);

  for (int i = 0; i < 2; i++) {
    pinMode(PIN_array[i].PWM, OUTPUT);
    pinMode(PIN_array[i].INA, OUTPUT);
    pinMode(PIN_array[i].INB, OUTPUT);
  }
  Serial.begin(9600);
}

void loop() {
  // シリアル通信が利用可能かどうかを確認
  if (Serial.available() > 0) {
    // シリアルバッファから1バイト読み込む
    char receivedChar = Serial.read();

    // 改行（'\n'）が受信されたら、printlnで改行して内容を表示
    if (receivedChar == '\n') {
      Serial.println();
    } else {
      // 受信した文字を表示
      Serial.print(receivedChar);
    }
  }
}

// void loop() {
//   received_strings = Serial.readStringUntil('\n');
//   Serial.print("I received: ");
//   Serial.println(received_strings);
//   for (int i = 0; i < 2; i++) {
//     cmds[i] = "";
//   }
//   int index = split(received_strings, ',', cmds);
//   Serial.println(cmds[0]);
//   if (cmds[0].toInt() == 7) {
//     Serial.println(cmds[1]);
//     if(cmds[1].toInt() == 135){
//       digitalWrite(LED_PIN, HIGH);
//     }else{
//       digitalWrite(LED_PIN, LOW);
//     }
//     krs.setPos(0, krs.degPos100(cmds[1].toInt() * 100));
//   // } else if (cmds[0] == "motor5") {
//   }else if (cmds[0].toInt() == 5) {
//     PWM(1, cmds[1].toInt());
//   // } else if (cmds[0] == "motor6") {
//   }else if (cmds[0].toInt() == 6) {
//     PWM(2, cmds[1].toInt());
//   } else {
//     Serial.println("エラー64");
//   }
// }

void PWM(int motor_id, int duty) {
  if (low_battery_voltage == false) {
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
  } else {
    temp = temp + 1;
    if (temp > 100) {
      for (int i = 0; i < 3; i++) {
        digitalWrite(PIN_array[i].INA, HIGH);
        digitalWrite(PIN_array[i].INB, HIGH);
      }
    }
  }
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