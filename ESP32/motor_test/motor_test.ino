// パソコンとシリアル通信して、センサー情報を送信したり、回収装填用モーターを制御する。
/*
制御するもの
ダクテッドファン1個
回収・装填用モーター2個
距離センサー たくさん
*/
#include <Wire.h> // I2Cを制御する

String incomingStrings = ""; // for incoming serial data

// モーターのピン
typedef struct
{
    int PWM_channels;
    int PWM;
    int INA;
    int INB;
} dataDictionary;

const dataDictionary PIN_array[]{
    {3, 25, 32, 33},
    {4, 26, 14, 27}};

size_t amount_motor = sizeof(PIN_array) / sizeof(PIN_array[0]);

void setup()
{

    Serial.begin(921600);
    Serial.println(" ");
    Serial.println("ESP32_2起動");
    // Serial2.setTimeout(1); // 1msでシリアル通信タイムアウト 本当はもう少し小さくしたいかも もしかしたらserial2だと意味ないかも
    // Serial2.begin(921600);
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
    PWM(0, 255);
    PWM(1, 255);

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