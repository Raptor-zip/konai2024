// パソコンとシリアル通信して、メカナムなどを動かす。
/*
制御するもの
メカナムホイール4輪
バッテリー電圧取得
サーボ 射出筒の仰角調整
ステータススピーカー
*/
#include <Wire.h> // 現状I2C使ってないけどw

TaskHandle_t thp[3]; // マルチスレッドのタスクハンドル格納用

String incomingStrings = ""; // for incoming serial data

#define LED_BUILTIN 2

unsigned long last_receive_time = 0;          // 最後にESP32_2から受信したmillis
unsigned long startTime, stopTime = 0;        // プログラムの遅延を確認するためにmicros
unsigned int performInfrequentTask_count = 0; // 500回に1回実行するためのカウんと

bool low_battery_voltage = false; // バッテリー低電圧時にモーターを強制停止させるときにtrueになる

typedef struct
{
    int PWM_channels;
    int PWM;
    int INA;
    int INB;
} dataDictionary;

const dataDictionary PIN_array[]{
    {1, 25, 32, 33},
    {2, 26, 14, 27},
    {3, 12, 23, 19},
    {4, 13, 4, 18}};

size_t amount_motor = sizeof(PIN_array) / sizeof(PIN_array[0]);

void setup()
{
    xTaskCreatePinnedToCore(Core0a_speaker,
                            "Core0a_speaker", 4096, NULL, 1, &thp[0], 0);
    pinMode(LED_BUILTIN, OUTPUT);
    pinMode(35, INPUT);
    // pinMode(8, OUTPUT);
    Serial.begin(921600); // PCとUSB接続
    // Serial.setRxBufferSize(512); // 送受信バッファサイズを変更。デフォルト:256バイト
    // Serial.setRxBufferSize(64); // これ変更しても影響ない？気がする
    while (!Serial)
    {
        ; // シリアル通信ポートが正常に接続されるまで抜け出さない
    }
    Serial.setTimeout(1000); // milliseconds for Serial.readString
    Serial.println(" ");
    Serial.println("ESP32_1起動");
    Serial.println("$1,0,1");

    for (int i = 0; i < amount_motor; i++)
    {
        // INA,INBの設定
        pinMode(PIN_array[i].INA, OUTPUT);
        pinMode(PIN_array[i].INB, OUTPUT);
        // PWM初期化
        ledcSetup(PIN_array[i].PWM_channels, 10000, 8); // PWM 周波数: 10kHz 8bit
        ledcAttachPin(PIN_array[i].PWM, PIN_array[i].PWM_channels);
    }

    // ステータススピーカーのピン設定
    ledcSetup(0, 12000, 8);
    ledcAttachPin(15, 0);
}

void Core0a_speaker(void *args)
{
    delay(100);
    // 起動音
    ledcWriteTone(0, 700);
    delay(100);
    ledcWriteTone(0, 900);
    delay(100);
    ledcWriteTone(0, 2000);
    delay(400);
    ledcWriteTone(0, 0);
    delay(1000);
    while (1)
    {
        ledcWriteTone(0, 800);
        delay(100);
        ledcWriteTone(0, 0);
        delay(900);
    }
}

void loop()
{
    stopTime = micros();
    // Serial.println(stopTime - startTime);
    // Serial.println("us");

    startTime = micros();

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

            PWM(0, intArray[1]);
            PWM(1, intArray[2]);
            PWM(2, intArray[3]);
            PWM(3, intArray[4]);
            analogWrite(LED_BUILTIN, abs(intArray[0]));
        }
        else
        {
            Serial.println("シリアル通信エラー105");
        }
    }

    performInfrequentTask_count++;
    if (performInfrequentTask_count > 200)
    {
        performInfrequentTask_count = 0;
        // 500ms以上パソコンからデータを受信できなかったら全てのモーターを強制停止
        if (millis() - last_receive_time > 100)
        {
            for (int i = 0; i < amount_motor; i++) // -1いるかも！！！！！！！！！！！！１１
            {
                digitalWrite(PIN_array[i].INA, HIGH);
                digitalWrite(PIN_array[i].INB, HIGH);
            }
            // ステータススピーカーの処理をするーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーー
        }

        // 4セルバッテリー電圧をパソコンに送信
        float battery_voltage = analogRead(35) * 7.0609 * 3.3 / 4096;
        String strings = "$1," + String(battery_voltage, 2) + ",0";
        Serial.println(strings);
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