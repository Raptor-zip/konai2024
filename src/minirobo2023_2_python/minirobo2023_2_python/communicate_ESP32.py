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
    "raw_distance": 1000,
    "raw_angle": 0,
    "battery_voltage": 0,
    "wifi_signal_strength": 0
}

# ESP32のIPアドレスとポート番号
esp32_ip = "192.168.211.78"
esp32_port = 12345

# UDPソケットの作成
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sp_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sp_udp_socket.bind(('127.0.0.1', 5002))
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
        # executor.submit(udp_reception)
        # executor.submit(battery_alert)
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
    normal_max_motor_speed = 230  # 自動運転時の最高速度

    straight_P_gain = 1  # 直進中に距離センサーにかけられるPゲイン
    straight_turn_P_gain = 1  # 直進中に補助するときに回転するときのPゲイン
    straight_distance_to_wall = 30  # 止まるときの壁までの距離
    turn_P_gain = 1.5  # 旋回中に角度センサーにかけられるPゲイン
    distance_adjust = -10  # ロボットの前面から距離センサーまでの距離 (マイナス)
    current_distance = 0
    angle_adjust = 0
    current_angle = 0

    axes_1 = 0
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
        # self.timer_0001 = self.create_timer(0.01, self.timer_callback_001)
        # self.timer_0016 = self.create_timer(0.033, self.timer_callback_0033)

    def control_mecanum_wheels(self, direction, speed):
        # print(direction * 360)

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
            "distance_value": reception_json["raw_distance"] + self.distance_adjust,
            "angle_value": self.current_angle,
            "start_time": self.start_time
        }
        msg.data = json.dumps(send_json)
        self.publisher_ESP32_to_Webserver.publish(msg)

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
            self.motor1_speed = 0
            self.motor2_speed = 0
            self.state = 0
        elif angle_difference < 0:
            # 右旋回
            print("右旋回", flush=True)
            self.motor1_speed = angle_difference * self.turn_P_gain * -1
            self.motor2_speed = angle_difference * self.turn_P_gain
            if self.motor1_speed < -1 * self.normal_max_motor_speed:
                self.motor1_speed = -1 * self.normal_max_motor_speed - self.axes_3 + self.axes_1
                if self.motor1_speed < -1 * 255:
                    self.motor1_speed = -1 * 255
            elif self.motor1_speed > self.normal_max_motor_speed:
                self.motor1_speed = self.normal_max_motor_speed - self.axes_3 + self.axes_1
                if self.motor1_speed > 255:
                    self.motor1_speed = 255

            if self.motor2_speed > self.normal_max_motor_speed:
                self.motor2_speed = self.normal_max_motor_speed + self.axes_1 - self.axes_3
                if self.motor2_speed > 255:
                    self.motor2_speed = 255
            elif self.motor2_speed < -1 * self.normal_max_motor_speed:
                self.motor2_speed = -1 * self.normal_max_motor_speed + self.axes_1 - self.axes_3
                if self.motor2_speed < -1*255:
                    self.motor2_speed = -1*255

        else:
            # 左旋回
            print("左旋回", flush=True)
            self.motor1_speed = angle_difference * self.turn_P_gain * -1
            self.motor2_speed = angle_difference * self.turn_P_gain
            if self.motor1_speed > self.normal_max_motor_speed:
                self.motor1_speed = self.normal_max_motor_speed + self.axes_3 - self.axes_1
                if self.motor1_speed > 255:
                    self.motor1_speed = 255
            elif self.motor1_speed < -1*self.normal_max_motor_speed:
                self.motor1_speed = -1*self.normal_max_motor_speed + self.axes_3 - self.axes_1
                if self.motor1_speed < -1*255:
                    self.motor1_speed = -1*255

            if self.motor2_speed < -1*self.normal_max_motor_speed:
                self.motor2_speed = -1*self.normal_max_motor_speed - self.axes_1 + self.axes_3
                if self.motor2_speed < -1*255:
                    self.motor2_speed = -1*255
            elif self.motor2_speed > self.normal_max_motor_speed:
                self.motor2_speed = self.normal_max_motor_speed - self.axes_1 + self.axes_3
                if self.motor2_speed > 255:
                    self.motor2_speed = 255

    def timer_callback_001(self):
        global motor_speed
        global reception_json
        # print(reception_json["raw_angle"],flush=True)
        self.current_angle = reception_json["raw_angle"] + self.angle_adjust
        if self.current_angle < 0:
            self.current_angle = 360 + self.current_angle

        # print(reception_json["raw_angle"],self.angle_adjust,self.current_angle,flush=True)

###################################################################################################
        self.current_distance = reception_json["raw_distance"] + \
            self.distance_adjust
        # self.current_distance = 50
###################################################################################################

        if self.state == 1:
            self.turn(0)
        if self.state == 2:
            self.turn(90)
        if self.state == 3:
            self.turn(180)
        if self.state == 4:
            self.turn(270)

        print(self.state, self.motor1_speed,
              self.motor2_speed, self.motor3_speed, flush=True)

        serialCommand = f"{{'motor1':{{'speed':{int(self.motor1_speed)}}},'motor2':{{'speed':{int(self.motor2_speed)}}},'motor3':{{'speed':{int(self.motor3_speed)}}}}}\n"

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
        self.axes_1 = int(joy.axes[1]*64)
        self.axes_3 = int(joy.axes[3]*64)

        self.axes_2 = int(joy.axes[2])
        self.axes_3 = int(joy.axes[3])

        angle = math.atan2(joy.axes[2], joy.axes[3])
        normalized_angle = (1 - angle / (2 * math.pi)) % 1
        distance = math.sqrt(joy.axes[2]**2 + joy.axes[3]**2)
        if distance > 1:
            distance = 1

        # print(distance,flush=True)

        # 方向と速さの設定
        direction = normalized_angle  # 0から1の範囲で指定（北を0、南を0.5として時計回りに）
        speed = distance      # 速さを指定
        # speed = 1

        # 制御関数の呼び出し
        front_left, front_right, rear_left, rear_right = self.control_mecanum_wheels(
            direction, speed)

        # 結果の表示
        print("Motor Speed :", front_left,front_right,rear_left,rear_right,flush=True)

        if self.state == 0:
            # 走行補助がオフなら
            self.motor1_speed = int(joy.axes[1]*256*0.5)
            self.motor2_speed = int(joy.axes[3]*256*0.5)

        if joy.buttons[6] == 1:
            # 走行補助強制停止
            self.state = 0
            self.motor1_speed = 0
            self.motor2_speed = 0
            self.motor3_speed = 0

        if joy.buttons[7] == 1:
            # 走行補助強制停止
            self.state = 0
            self.motor1_speed = 0
            self.motor2_speed = 0
            self.motor3_speed = 0

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
        self.motor3_speed = int(joy.axes[1]*256)

        if joy.buttons[6] == 1:
            # 走行補助強制停止
            self.state = 0
            self.motor1_speed = 0
            self.motor2_speed = 0
            self.motor3_speed = 0

        if joy.buttons[7] == 1:
            # 走行補助強制停止
            self.state = 0
            self.motor1_speed = 0
            self.motor2_speed = 0
            self.motor3_speed = 0


if __name__ == '__main__':
    main()
