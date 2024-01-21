#include <WiFi.h>
#include <WiFiUdp.h>
#include <ArduinoJson.h>
#include <Wire.h>
// #include "SSD1306.h" //ディスプレイ用ライブラリを読み込み

#define LED_BUILTIN 2

unsigned long last_receive_time;              // 最後にパソコンから受信したmillis
unsigned long startTime, stopTime;            // プログラムの遅延を確認するためにmicros
unsigned int performInfrequentTask_count = 0; // 500回に1回実行するためのカウント
unsigned char low_battery_voltage_count = 0;  // 6回以上1〜9Vの間だったらモーター強制停止するためのカウント
int battery_voltage_PIN = 35;                 // バッテリー電圧を測定するためのピンの番号
bool low_battery_voltage = false;             // バッテリー低電圧時にモーターを強制停止させるときにtrueになる
const char *ssid = "明志-2g";                 // WiFiのSSID
const char *password = "nitttttc";            // WiFiのパスワード
//////////////////////////////////////////////////////////////////////////////////////
// const char *python_ip = "192.168.28.68";
// const char *python_ip = "192.168.107.68";
// const char *python_ip = "192.168.35.68";
// const char *python_ip = "192.168.126.68";
const char *python_ip = "192.168.126.189";
//////////////////////////////////////////////////////////////////////////////////////
const int python_port = 12346; // UDP通信で送信時に使うポート

// 本体裏側0x78に接続→0x3C 0x7A→0x3A
// SSD1306 display(0x3c, 21, 22); // SSD1306インスタンスの作成（I2Cアドレス,SDA,SCL）
WiFiUDP udp;

typedef struct
{
  int PWM_channels;
  int PWM;
  int INA;
  int INB;
} dataDictionary;

const dataDictionary PIN_array[]{
    {0, 25, 32, 33},
    {1, 26, 14, 27},
    {2, 12, 23, 19},
    {3, 13, 4, 18}};

void setup()
{
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(battery_voltage_PIN, INPUT);

  Serial.begin(921600);
  Serial2.setTimeout(1); // 1msでシリアル通信タイムアウト 本当はもう少し小さくしたいかも もしかしたらserial2だと意味ないかも
  Serial2.begin(115200);

  // display.init();                    // ディスプレイを初期化
  // display.setFont(ArialMT_Plain_16); // フォントを設定

  delay(1000);

  connectToWiFi();

  for (int i = 0; i < 4; i++)
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
  int packetSize = udp.parsePacket();
  if (packetSize)
  {
    char packetData[255];
    udp.read(packetData, sizeof(packetData));
    packetData[packetSize] = '\0'; // 文字列の終端を追加

    // 受信したデータを変数に保存
    String json = String(packetData);

    // Serial.print("Received data: ");
    // Serial.print(json);

    // udp.beginPacket(python_ip, python_port);
    // udp.print(json);
    // udp.endPacket();

    startTime = micros();

    // json = "{'motor1':{'speed':-128},'motor2':{'speed':-128},'motor3':{'speed':-128}";

    // JSON用の固定バッファを確保。
    StaticJsonDocument<300> doc; // deserializeJson() failed: NoMemory とSerialで流れたらここの値を大きくする

    // Deserialize the JSON document
    DeserializationError error = deserializeJson(doc, json);

    if (error)
    {
      Serial.print(F("deserializeJson() failed: "));
      Serial.println(error.f_str());
      return;
    }
    last_receive_time = millis();

    if (low_battery_voltage == false)
    { // バッテリーが低電圧でないなら
      if (doc.containsKey("motor1"))
      {
        // Serial.println(String(doc["motor1"].as<float>()));
        PWM(1, doc["motor1"]);
        // analogWrite(LED_BUILTIN, abs(int(doc["motor1"])));
      }
      if (doc.containsKey("motor2"))
      {
        // Serial.println(String(doc["motor2"].as<float>()));
        PWM(2, doc["motor2"]);
        analogWrite(LED_BUILTIN, abs(int(doc["motor2"])));
      }
      if (doc.containsKey("motor3"))
      {
        // Serial.println(String(doc["motor3"].as<float>()));
        PWM(3, doc["motor3"]);
      }
      if (doc.containsKey("motor4"))
      {
        // Serial.println(String(doc["motor3"].as<float>()));
        PWM(4, doc["motor4"]);
      }
      if (doc.containsKey("motor5"))
      {
        Serial2.println("5," + String(doc["motor5"].as<int>()));
        Serial.println("5," + String(doc["motor5"].as<int>()));
      }
      if (doc.containsKey("servo"))
      {
        Serial2.println("6," + String(doc["servo"].as<int>()));
        Serial.println("6," + String(doc["servo"].as<int>()));
        // analogWrite(LED_BUILTIN, abs(int(doc["servo"])));
      }
    }

    // const char* motor1 = doc["motor1"];

    stopTime = micros();
    // Serial.print(stopTime - startTime);
    // Serial.println("us");
  }

  // // Arduinoからサーボの情報を読み取る
  // String received_strings = Serial2.readStringUntil('\n');
  // if (received_strings.length() > 2)
  // { // 5文字以上あるなら = 空でないなら
  //   Serial.print("I received: " + String(received_strings));
  //   udp.beginPacket(python_ip, python_port);
  //   udp.print(received_strings);
  //   udp.endPacket();
  // }

  performInfrequentTask_count++;
  if (performInfrequentTask_count > 500)
  {
    performInfrequentTask_count = 0;
    // 電圧監視
    float battery_voltage = analogRead(battery_voltage_PIN) * 4.034 * 3.3 / 4096;
    if (1 < battery_voltage && battery_voltage < 9) // センサー9Vのとき電源装置9.5V
    {
      if (low_battery_voltage_count > 4)
      { // 6であってるのか検証！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！１
        low_battery_voltage = true;
        // 全てのDCモーターにブレーキをかける and 全てのサーボモーターをフリーにする
        for (int i = 0; i < 4; i++)
        {
          digitalWrite(PIN_array[i].INA, HIGH); // 両方ともLOWのほうがインじゃなかったっけ？バッテリーすくないときは！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！
          digitalWrite(PIN_array[i].INB, HIGH);
        }
        Serial2.println("5,0");
        Serial.println("5,0");
        Serial2.println("6,999");
        Serial.println("6,999");
      }
      low_battery_voltage_count++;
    }
    else
    {
      low_battery_voltage_count = 0;
      low_battery_voltage = false;
    }

    // 500ms以上パソコンからデータを受信できなかったら全てのモーターを強制停止
    if (millis() - last_receive_time > 500)
    {
      for (int i = 0; i < 3; i++)
      {
        digitalWrite(PIN_array[i].INA, HIGH);
        digitalWrite(PIN_array[i].INB, HIGH);
      }
    }

    // バッテリー電圧をパソコンに送信
    udp.beginPacket(python_ip, python_port);
    String jsonString = "{\"battery_voltage\":" + String(battery_voltage, 2) + "}";
    udp.print(jsonString);
    udp.endPacket();

    // WiFiが途切れたら再接続する
    if (WiFi.status() != WL_CONNECTED)
    {
      connectToWiFi();
    }
  }

  delay(1);
}

void PWM(int motor_id, int duty)
{
  if (duty == 0)
  {
    // VCCブレーキ
    digitalWrite(PIN_array[motor_id - 1].INA, HIGH);
    digitalWrite(PIN_array[motor_id - 1].INB, HIGH);
  }
  else if (duty > 0)
  {
    // 正転
    digitalWrite(PIN_array[motor_id - 1].INA, HIGH);
    digitalWrite(PIN_array[motor_id - 1].INB, LOW);
  }
  else if (duty < 0)
  {
    // 逆転
    digitalWrite(PIN_array[motor_id - 1].INA, LOW);
    digitalWrite(PIN_array[motor_id - 1].INB, HIGH);
  }
  ledcWrite(PIN_array[motor_id - 1].PWM_channels, abs(duty));
}

void connectToWiFi()
{
  Serial.println("Connecting to WiFi");
  // display.drawString(15, 0, "Connect WiFi");
  // display.display(); // 指定された情報を描画
  WiFi.begin(ssid, password);
  byte i = 0;
  while (WiFi.status() != WL_CONNECTED)
  {
    Serial.print(".");
    i++;
    if (i > 10 * 10)
    {                // 10秒経ったら
      ESP.restart(); // 再起動する
    }

    delay(100);
  }
  Serial.println("\nConnected to WiFi");
  Serial.print("IP address:");
  Serial.println(WiFi.localIP());
  delay(1000);
  udp.begin(12345); // Choose any available local port
  // display.setFont(ArialMT_Plain_24);
  // display.drawString(25, 40, String(WiFi.localIP()[2]) + "." + String(WiFi.localIP()[3]));
  // display.display(); // 指定された情報を描画
}