#include <Wire.h>
#include <MadgwickAHRS.h> // https://github.com/arduino-libraries/MadgwickAHRS
Madgwick MadgwickFilter;

#define MPU6050_WHO_AM_I     0x75  // Read Only
#define MPU6050_PWR_MGMT_1   0x6B
#define MPU_ADDRESS  0x68

uint32_t tick;

int32_t c_x,c_y,c_z;

void setup() {
  Wire.begin();
  Serial.begin(115200); //115200bps

  Wire.beginTransmission(MPU_ADDRESS);
  Wire.write(MPU6050_WHO_AM_I);  //MPU6050_PWR_MGMT_1
  Wire.write(0x00);
  Wire.endTransmission();

  Wire.beginTransmission(MPU_ADDRESS);
  Wire.write(MPU6050_PWR_MGMT_1);  //MPU6050_PWR_MGMT_1レジスタの設定
  Wire.write(0x00);
  Wire.endTransmission();

  MadgwickFilter.begin(100); //100Hz

  delay(1000);
  calib(100);

  tick = micros();
}

void loop() {
  Wire.beginTransmission(0x68);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  delay(1);
  Wire.requestFrom(0x68, 14, true);
  unsigned long startTime = millis();
    while (Wire.available() < 14) {
        if (millis() - startTime > 1000) { // 1秒間データが揃わない場合
            // タイムアウト処理
            break;
        }
        Serial.println("test");
    }
  int16_t axRaw, ayRaw, azRaw, gxRaw, gyRaw, gzRaw, Temperature;

  axRaw = Wire.read() << 8 | Wire.read();
  ayRaw = Wire.read() << 8 | Wire.read();
  azRaw = Wire.read() << 8 | Wire.read();
  Temperature = Wire.read() << 8 | Wire.read();
  gxRaw = Wire.read() << 8 | Wire.read();
  gyRaw = Wire.read() << 8 | Wire.read();
  gzRaw = Wire.read() << 8 | Wire.read();

  // 加速度値を分解能で割って加速度(G)に変換する
  float acc_x = axRaw / 16384.0;  //FS_SEL_0 16,384 LSB / g
  float acc_y = ayRaw / 16384.0;
  float acc_z = azRaw / 16384.0;

  // 角速度値を分解能で割って角速度(degrees per sec)に変換する
  float gyro_x = (gxRaw - c_x) / 131.0;  // (度/s)
  float gyro_y = (gyRaw - c_y) / 131.0;
  float gyro_z = (gzRaw - c_z) / 131.0;

  MadgwickFilter.updateIMU(gyro_x, gyro_y, gyro_z, acc_x, acc_y, acc_z);

  //PRYの計算結果を取得する
  float roll  = MadgwickFilter.getRoll();
  float pitch = MadgwickFilter.getPitch();
  float yaw   = MadgwickFilter.getYaw() - 180;

  Serial.println(yaw);

  tick += 10000;
  delayMicroseconds(tick - micros());
}

void calib(uint16_t n){
  c_x = 0;
  c_y = 0;
  c_z = 0;

  int16_t axRaw, ayRaw, azRaw, gxRaw, gyRaw, gzRaw, Temperature;
  for(int i = 0; i < n; i ++){
    Wire.beginTransmission(0x68);
    Wire.write(0x3B);
    Wire.endTransmission(false);
    Wire.requestFrom(0x68, 14, true);
    while (Wire.available() < 14);
    axRaw = Wire.read() << 8 | Wire.read();
    ayRaw = Wire.read() << 8 | Wire.read();
    azRaw = Wire.read() << 8 | Wire.read();
    Temperature = Wire.read() << 8 | Wire.read();
    gxRaw = Wire.read() << 8 | Wire.read();
    gyRaw = Wire.read() << 8 | Wire.read();
    gzRaw = Wire.read() << 8 | Wire.read();
    c_x += gxRaw;
    c_y += gyRaw;
    c_z += gzRaw;
    delay(1);
  }
  c_x /= n;
  c_y /= n;
  c_z /= n;
}