import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import Joy
import json  # jsonを使うため
from concurrent.futures import ThreadPoolExecutor  # threadPoolExecutor
import playsound  # バッテリー低電圧保護ブザー用
import subprocess  # SSID取得用
import time
import ipget
import socket
import math
motor_speed = [0, 0, 0, 0]
reception_json = {
    "raw_angle": 0,
    "battery_voltage": 0,
    "wifi_signal_strength": 0
}

# ESP32のIPアドレスとポート番号
# esp32_ip = "192.168.211.78"
esp32_ip = "192.168.211.241"
esp32_port = 12345

# UDPソケットの作成
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sp_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sp_udp_socket.bind(('127.0.0.1', 5003)) ####################################################################本当は5002
sp_udp_socket.settimeout(1.0)  # タイムアウトを1秒に設定

local_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
local_udp_socket.bind(('0.0.0.0', 12346))
local_udp_socket.settimeout(1.0)  # タイムアウトを1秒に設定

try:
    result = subprocess.check_output(
        ['iwgetid', '-r'], universal_newlines=True)
    wifi_ssid = result.strip()
    # wifi_ssid= bytes(result.strip(), 'utf-8').decode('unicode-escape')
except subprocess.CalledProcessError:
    wifi_ssid = "エラー"


def main():
    with ThreadPoolExecutor(max_workers=4) as executor:
        # executor.submit(sp_udp_reception)
        executor.submit(udp_reception)
        executor.submit(battery_alert)
        future = executor.submit(ros)
        future.result()         # 全てのタスクが終了するまで待つ


def sp_udp_reception():
    global sp_udp_socket
    global reception_json
    while True:
        try:
            message, cli_addr = sp_udp_socket.recvfrom(1024)
            # print(f"Received: {message.decode('utf-8')}", flush=True)
            reception_json_temp = json.loads(message.decode('utf-8'))
            reception_json.update(reception_json_temp)
        except Exception as e:
            print(f"               スマホから受信に失敗: {e}", flush=True)
            print(f"               スマホから受信に失敗: {e}", flush=True)
            print(f"               スマホから受信に失敗: {e}", flush=True)
            print(f"               スマホから受信に失敗: {e}", flush=True)
            print(f"               スマホから受信に失敗: {e}", flush=True)
            print(f"               スマホから受信に失敗: {e}", flush=True)
            print(f"               スマホから受信に失敗: {e}", flush=True)
            print(f"               スマホから受信に失敗: {e}", flush=True)


def udp_reception():
    global local_udp_socket
    global reception_json
    while True:
        try:
            # データを受信
            data, addr = local_udp_socket.recvfrom(1024)
            print(f"           {data.decode('utf-8')}", flush=True)
            reception_json_temp = json.loads(data.decode('utf-8'))
            reception_json.update(reception_json_temp)
        except Exception as e:
            print(f"               ESP32から受信に失敗: {e}", flush=True)
            print(f"               ESP32から受信に失敗: {e}", flush=True)
            print(f"               ESP32から受信に失敗: {e}", flush=True)
            print(f"               ESP32から受信に失敗: {e}", flush=True)
            print(f"               ESP32から受信に失敗: {e}", flush=True)
            print(f"               ESP32から受信に失敗: {e}", flush=True)
            print(f"               ESP32から受信に失敗: {e}", flush=True)
            print(f"               ESP32から受信に失敗: {e}", flush=True)
            reception_json["battery_voltage"] = 0


def battery_alert():
    global reception_json
    temp = 0
    while True:
        if reception_json["battery_voltage"] < 10 and reception_json["battery_voltage"] > 5:
            temp += 1
            if temp > 3:
                playsound.playsound("battery_alert.mp3")
        else:
            temp = 0
        time.sleep(0.2)  # 無駄にCPUを使わないようにする


def ros(args=None):
    rclpy.init(args=args)

    minimal_subscriber = MinimalSubscriber()

    rclpy.spin(minimal_subscriber)

    minimal_subscriber.destroy_node()
    rclpy.shutdown()


class MinimalSubscriber(Node):
    state = 0
    motor1_speed = 0
    motor2_speed = 0
    motor3_speed = 0
    motor4_speed = 0
    motor5_speed = 0
    motor6_speed = 0
    servo_angle = 0
    normal_max_motor_speed = 230  # 自動運転時の最高速度

    turn_P_gain = 4  # 旋回中に角度センサーにかけられるPゲイン
    angle_adjust = 0
    current_angle = 0

    axes_0 = 0
    axes_1 = 0
    axes_2 = 0
    axes_3 = 0

    buttons_L = 0
    buttons_R = 0
    buttons_ZL = 0
    buttons_ZR = 0
    buttons_home = 0
    buttons_X = 0
    buttons_A = 0
    buttons_B = 0
    buttons_Y = 0
    buttons_up = 0
    buttons_left = 0
    buttons_down = 0
    buttons_right = 0

    start_time = 0

    def __init__(self):
        global reception_json
        print("Subscriber", flush=True)
        super().__init__('command_subscriber')
        self.publisher_ESP32_to_Webserver = self.create_publisher(
            String, 'ESP32_to_Webserver', 10)
        self.subscription = self.create_subscription(
            Joy,
            "joy1",
            self.joy1_listener_callback,
            10)
        self.subscription = self.create_subscription(
            Joy,
            "joy2",
            self.joy2_listener_callback,
            10)
        self.subscription  # prevent unused variable warning

        # 0.001でも試す！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！
        self.timer_0001 = self.create_timer(0.01, self.timer_callback_001)
        self.timer_0016 = self.create_timer(0.033, self.timer_callback_0033)

    def timer_callback_0033(self):
        global wifi_ssid, esp32_ip

        msg = String()
        send_json = {
            "state": self.state,
            "ubuntu_ssid": wifi_ssid,
            "ubuntu_ip": ipget.ipget().ipaddr("wlp2s0"),
            "esp32_ip": esp32_ip,
            "battery_voltage": reception_json["battery_voltage"],
            "wifi_signal_strength": reception_json["wifi_signal_strength"],
            "motor1_speed": self.motor1_speed,
            "motor2_speed": self.motor2_speed,
            "motor3_speed": self.motor3_speed,
            "motor4_speed": self.motor4_speed,
            "motor5_speed": self.motor5_speed,
            "motor6_speed": self.motor6_speed,
            "servo_angle":self.servo_angle,
            "angle_value": self.current_angle,
            "start_time": self.start_time
        }
        msg.data = json.dumps(send_json)
        self.publisher_ESP32_to_Webserver.publish(msg)

    def timer_callback_001(self):
        global motor_speed
        global reception_json
        self.current_angle = reception_json["raw_angle"] + self.angle_adjust
        if self.current_angle < 0:
            self.current_angle = 360 + self.current_angle

        # print(reception_json["raw_angle"],self.angle_adjust,self.current_angle,flush=True)

        if self.state == 0:
            # 走行補助がオフなら
            turn_minus1to1 = 0
        elif self.state == 1:
            turn_minus1to1 = self.turn(0)
        elif self.state == 2:
            turn_minus1to1 = self.turn(90)
        elif self.state == 3:
            turn_minus1to1 = self.turn(180)
        elif self.state == 4:
            turn_minus1to1 = self.turn(270)

        # 手動旋回と自動旋回を合わせる
        turn_minus1to1 += self.axes_0
        self.motor1_speed = turn_minus1to1 * 256 * -1
        self.motor2_speed = turn_minus1to1 * 256
        self.motor3_speed = turn_minus1to1 * 256 * -1
        self.motor4_speed = turn_minus1to1 * 256

        normalized_angle = (1 - (math.atan2(self.axes_2, self.axes_3)) / (2 * math.pi)) % 1
        distance = math.sqrt(self.axes_2**2 + self.axes_3**2)
        if distance > 1:
            distance = 1

        # 制御関数の呼び出し
        front_left, front_right, rear_left, rear_right = self.control_mecanum_wheels(
            normalized_angle, distance)  # 0から1の範囲で指定（北を0、南を0.5として時計回りに）

        # 旋回と合わせる
        self.motor1_speed += front_left
        self.motor2_speed += front_right
        self.motor3_speed += rear_left
        self.motor4_speed += rear_right

        # 255を超えた場合、比率を保ったまま255以下にする
        max_motor_speed = max([abs(self.motor1_speed), abs(self.motor2_speed),
                            abs(self.motor3_speed), abs(self.motor4_speed)])
        if max_motor_speed > 255:
            self.motor1_speed = int(self.motor1_speed * 255 / max_motor_speed)
            self.motor2_speed = int(self.motor2_speed * 255 / max_motor_speed)
            self.motor3_speed = int(self.motor3_speed * 255 / max_motor_speed)
            self.motor4_speed = int(self.motor4_speed * 255 / max_motor_speed)

        print(self.state,
              int(self.motor1_speed),
              int(self.motor2_speed),
              int(self.motor3_speed),
              int(self.motor4_speed),
              int(self.servo_angle),
              flush=True)

        serialCommand = f"{{'motor1':{{'speed':{int(self.motor1_speed)}}},'motor2':{{'speed':{int(self.motor2_speed)}}},'motor3':{{'speed':{int(self.motor3_speed)}}},'motor4':{{'speed':{int(self.motor4_speed)}}},'motor5':{{'speed':{int(self.motor5_speed)}}},'motor6':{{'speed':{int(self.motor6_speed)}}},'servo':{{'angle':{int(self.servo_angle)}}}}}\n"

        serialCommand = serialCommand.encode()
        try:
            udp_socket.sendto(serialCommand, (esp32_ip, esp32_port))
        except Exception as e:
            print(f"                UDP送信エラー: {e}", flush=True)
            print(f"                UDP送信エラー: {e}", flush=True)
            print(f"                UDP送信エラー: {e}", flush=True)
            print(f"                UDP送信エラー: {e}", flush=True)
            print(f"                UDP送信エラー: {e}", flush=True)
            print(f"                UDP送信エラー: {e}", flush=True)
            print(f"                UDP送信エラー: {e}", flush=True)
            print(f"                UDP送信エラー: {e}", flush=True)
        # print(f"Sent {esp32_ip}:{esp32_port} {serialCommand}",flush=True)

    def joy1_listener_callback(self, joy):
        global reception_json
        self.axes_0 = joy.axes[0]
        self.axes_1 = joy.axes[1]
        self.axes_2 = joy.axes[2]
        self.axes_3 = joy.axes[3]

        if joy.buttons[6] == 1 or joy.buttons[7] == 1:
            # 走行補助強制停止
            self.state = 0
            self.motor1_speed = 0
            self.motor2_speed = 0
            self.motor3_speed = 0
            self.motor4_speed = 0

        if self.buttons_X == 0 and joy.buttons[2] == 1:
            # 0°に旋回
            self.state = 1
        if self.buttons_A == 0 and joy.buttons[1] == 1:
            # 90°に旋回
            self.state = 2
        if self.buttons_B == 0 and joy.buttons[0] == 1:
            # 180°に旋回
            self.state = 3
        if self.buttons_Y == 0 and joy.buttons[3] == 1:
            # 270°に旋回
            self.state = 4
        if self.buttons_up == 0 and joy.buttons[13] == 1:
            # 排出蓋を閉じる
            self.servo_angle = 0
        if self.buttons_down == 0 and joy.buttons[14] == 1:
            # 排出蓋を開く
            self.servo_angle = 270

        if self.buttons_L == 1 and self.buttons_R == 1:
            # 角度リセット
            if reception_json["raw_angle"] < 0:
                # マイナスのとき
                self.angle_adjust = - 180 - reception_json["raw_angle"]
            else:
                self.angle_adjust = -1 * reception_json["raw_angle"]

        if self.buttons_home == 0 and joy.buttons[10] == 1:
            # タイマースタート
            self.start_time = time.time()

        self.buttons_L = joy.buttons[4]
        self.buttons_R = joy.buttons[5]
        self.buttons_ZL = joy.buttons[6]
        self.buttons_ZR = joy.buttons[7]
        self.buttons_home = joy.buttons[10]
        self.buttons_X = joy.buttons[2]
        self.buttons_A = joy.buttons[1]
        self.buttons_B = joy.buttons[0]
        self.buttons_Y = joy.buttons[3]
        self.buttons_up = joy.buttons[13]
        self.buttons_left = joy.buttons[16]
        self.buttons_down = joy.buttons[14]
        self.buttons_right = joy.buttons[15]

    def joy2_listener_callback(self, joy):
        # 回収機構のモーター
        self.motor5_speed = int(joy.axes[1]*256)
        self.motor6_speed = int(joy.axes[3]*256)

        if joy.buttons[6] == 1 or joy.buttons[7] == 1:
            # 走行補助強制停止
            self.state = 0
            self.motor1_speed = 0
            self.motor2_speed = 0
            self.motor3_speed = 0
            self.motor4_speed = 0

    def control_mecanum_wheels(self, direction, speed):
        # ラジアンに変換
        angle = direction * 2.0 * math.pi

        # 回転数を255から-255の範囲に変換
        front_left = math.sin(angle + math.pi / 4.0) * 255
        front_right = math.cos(angle + math.pi / 4.0) * 255
        rear_left = math.cos(angle + math.pi / 4.0) * 255
        rear_right = math.sin(angle + math.pi / 4.0) * 255
        adjust = 255 / max([abs(front_left), abs(front_right),
                           abs(rear_left), abs(rear_right)])
        front_left = int(front_left * adjust * speed)
        front_right = int(front_right * adjust * speed)
        rear_left = int(rear_left * adjust * speed)
        rear_right = int(rear_right * adjust * speed)

        return front_left, front_right, rear_left, rear_right

    def turn(self, target_angle):
        target_plus_180 = target_angle + 180
        if target_plus_180 > 360:
            target_plus_180 = 360 - target_angle
        angle_difference = abs(self.current_angle - target_angle)
        if angle_difference > 180:
            angle_difference = 360 - abs(self.current_angle-target_angle)
        if target_angle > 180:
            if target_plus_180 <= self.current_angle <= target_angle:
                angle_difference = angle_difference*-1
        else:
            if target_angle <= self.current_angle <= target_plus_180:
                pass
            else:
                angle_difference = angle_difference*-1

        if abs(angle_difference) < 2:  # この判定ゆるくする！！！！！！！！！！！！！！！！
            # 止まる
            temp = 0
            self.state = 0
        else:
            temp = angle_difference/360 * self.turn_P_gain
            if temp > 1:
                temp = 1
            if temp < -1:
                temp = -1
        return temp


if __name__ == '__main__':
    main()
