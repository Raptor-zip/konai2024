// パソコンとシリアル通信して、センサー情報を送信したり、回収装填用モーターを制御する。
/*
制御するもの
ダクテッドファン1個
回収・装填用モーター2個
距離センサー たくさん
*/
#include <Wire.h>       // I2Cを制御する
#include <ESP32Servo.h> //サーボではなく、ダクテッドファンのESCを制御する
#include <VL53L1X.h>    // 距離センサー VL53L1Xを制御する

TaskHandle_t thp[3]; // マルチスレッドのタスクハンドル格納用

String incomingStrings = ""; // for incoming serial data

Servo ducted_fan;
Servo GM6020;

// 距離センサー
const uint8_t sensor_count = 3;
const uint8_t xshutPins[sensor_count] = {4, 5, 6};
VL53L1X sensors[sensor_count];

// ブラシレスモーターのキャリブレーション
boolean calibrate_ducted_fan_enabled_now = false;
boolean calibrate_ducted_fan_enabled_old = false;
boolean is_calibrating_ducted_fan = false;

#define LED_BUILTIN 2

unsigned long last_receive_time = 0;          // 最後にパソコンから受信したmillis
unsigned long startTime, stopTime = 0;        // プログラムの遅延を確認するためにmicros
unsigned int performInfrequentTask_count = 0; // 500回に1回実行するためのカウント
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
    {0, 25, 32, 33},
    {1, 26, 14, 27}};

size_t amount_motor = sizeof(PIN_array) / sizeof(PIN_array[0]);

void setup()
{
    xTaskCreatePinnedToCore(Core0a_calibrate_ducted_fan, "Core0a_calibrate_ducted_fan", 4096, NULL, 1, &thp[0], 0);
    // xTaskCreatePinnedToCore(Core0b_calibrate_GM6020, "Core0b_calibrate_GM6020", 4096, NULL, 2, &thp[1], 0);
    pinMode(LED_BUILTIN, OUTPUT);
    pinMode(12, OUTPUT);
    pinMode(13, OUTPUT);
    pinMode(23, OUTPUT);

    Serial.begin(921600);
    // Serial2.setTimeout(1); // 1msでシリアル通信タイムアウト 本当はもう少し小さくしたいかも もしかしたらserial2だと意味ないかも
    // Serial2.begin(921600);

    Wire.begin();
    Wire.setClock(400000); // use 400 kHz I2C

    // ICに信号いれる
    for (uint8_t i = 0; i < sensor_count; i++)
    {
        pinMode(xshutPins[i], OUTPUT);
        digitalWrite(xshutPins[i], LOW);
    }

    // 1つずつセンサーをスタートする
    for (uint8_t i = 0; i < sensor_count; i++)
    {
        // Stop driving this sensor's XSHUT low. This should allow the carrier
        // board to pull it high. (We do NOT want to drive XSHUT high since it is
        // not level shifted.) Then wait a bit for the sensor to start up.
        pinMode(xshutPins[i], INPUT);
        delay(10);

        sensors[i].setTimeout(500);
        if (!sensors[i].init())
        {
            Serial.print("Failed to detect and initialize sensor ");
            Serial.println(i);
            while (1) ///////////////////////////////////////////////////////////////While1ってなってるけど、これだと抜け出せないよね？緊急時に抜け出せるようにする
                ;
        }

        sensors[i].setAddress(0x2A + i); // 各センサーのアドレスを、0x2Aから順にカウントアップする
        sensors[i].setDistanceMode(VL53L1X::Short);
        sensors[i].setMeasurementTimingBudget(30000); // マイクロ秒 最小20000
        sensors[i].setROISize(4, 4);
        sensors[i].setROICenter(199);
        sensors[i].startContinuous(50); // 測定間隔30msで連続読み取り開始。これはタイミングバジェット以上に長くする必要がある
    }

    ducted_fan.attach(12);
    GM6020.attach(13);
    // Serial.setRxBufferSize(512); // 送受信バッファサイズを変更。デフォルト:256バイト
    // Serial.setRxBufferSize(64); // これ変更しても影響ない？気がする
    while (!Serial)
    {
        ; // シリアル通信ポートが正常に接続されるまで抜け出さない
    }
    // Serial.setTimeout(10); // milliseconds for Serial.readString
    Serial.setTimeout(1000); // milliseconds for Serial.readString
    Serial.println(" ");
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

    Serial.println("GM6020 キャリブレーション 最大");
    GM6020.writeMicroseconds(2000);
    delay(2000);
    Serial.println("GM6020 キャリブレーション 最小");
    GM6020.writeMicroseconds(1000);
    delay(2000);
    Serial.println("GM6020 キャリブレーション 完了");
}

void Core0a_calibrate_ducted_fan(void *args)
{ // スレッド
    delay(100);
    while (1)
    {
        digitalWrite(LED_BUILTIN, HIGH);
        if (calibrate_ducted_fan_enabled_now == true && calibrate_ducted_fan_enabled_old == false)
        {
            ducted_fan.attach(12);
            digitalWrite(LED_BUILTIN, LOW);
            is_calibrating_ducted_fan = true;
            Serial.println("ダクテッドファン キャリブレーション 最大");
            ducted_fan.writeMicroseconds(2000);
            delay(2000);
            Serial.println("ダクテッドファン キャリブレーション 最小");
            ducted_fan.writeMicroseconds(1000);
            delay(2000);
            Serial.println("ダクテッドファン キャリブレーション 完了");
            is_calibrating_ducted_fan = false;
        }
        calibrate_ducted_fan_enabled_old = calibrate_ducted_fan_enabled_now;
        delay(1);
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
            const int maxElements = 15; // 配列の最大要素数 多分ぴったりだとうまく行かない気がする
            int intArray[maxElements];  // 整数の配列
            int count = parseStringToArray(incomingStrings, intArray, maxElements);

            // PWM(0, intArray[5]);
            // PWM(1, intArray[6]);

            GM6020.writeMicroseconds(intArray[8]);
            Serial.println("これは着てるよね？");
            if (intArray[10] == 1)
            {
                // digitalWrite(LED_BUILTIN, LOW);
                digitalWrite(23, HIGH);
                calibrate_ducted_fan_enabled_now = true;

                // キャリブレーション中でないなら 若しくは キャリブレーション後なら
                if (is_calibrating_ducted_fan == false)
                {
                    Serial.println("false");
                    ducted_fan.writeMicroseconds(intArray[7]);
                }
                else
                {
                    Serial.println("true");
                }
            }
            else
            {
                // digitalWrite(LED_BUILTIN, HIGH);
                digitalWrite(23, LOW);
                calibrate_ducted_fan_enabled_now = false;

                // キャリブレーション中でないなら 若しくは キャリブレーション後なら
                // if (is_calibrating_ducted_fan == false)
                // {
                digitalWrite(12, LOW);
                ducted_fan.detach(); // 接続解除
                                     // ducted_fan.writeMicroseconds(0);
                                     // }
            }
            // analogWrite(LED_BUILTIN, abs(intArray[4]));
        }
        else
        {
            Serial.println("シリアル通信エラー105");
        }
    }

    // ESP32_2からサーボの情報を読み取る
    // String received_strings = Serial2.readStringUntil('\n');
    // if (received_strings.length() > 2)
    // { // 5文字以上あるなら = 空でないなら
    //   Serial.println(received_strings);
    // }

    //  距離センサーを読む
    for (uint8_t i = 0; i < sensor_count; i++)
    {
        Serial.print(sensors[i].read());
        if (sensors[i].timeoutOccurred())
        {
            Serial.print(" TIMEOUT");
        }
        Serial.print('\t');
    }

    performInfrequentTask_count++;
    if (performInfrequentTask_count > 200)
    {
        performInfrequentTask_count = 0;
        // 500ms以上パソコンからデータを受信できなかったら全てのモーターを強制停止
        if (millis() - last_receive_time > 100)
        {
            digitalWrite(23, LOW); // リレーにつながってるブラシレス2個停止
            for (int i = 0; i < amount_motor - 1; i++)
            {
                digitalWrite(PIN_array[i].INA, HIGH);
                digitalWrite(PIN_array[i].INB, HIGH);
            }

            // digitalWrite(LED_BUILTIN, HIGH);
        }

        // 3セルバッテリー電圧をパソコンに送信
        float battery_voltage = analogRead(34) * 4.034 * 3.3 / 4096;
        String strings = "2," + String(battery_voltage, 2) + "";
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