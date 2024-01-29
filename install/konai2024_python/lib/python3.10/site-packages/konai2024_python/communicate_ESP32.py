import copy  # 辞書型をコピーする用
import matplotlib.pyplot as plt
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import Joy
import json  # jsonを使うため
from concurrent.futures import ThreadPoolExecutor  # threadPoolExecutor
import playsound  # バッテリー低電圧保護ブザー用
import subprocess  # SSID取得用
import time
import serial
import ipget  # IPアドレス取得用
import socket  # UDP通信用
import math
import evdev
from matplotlib import pyplot as plt  # 描画用ライブラリ
# import matplotlib
# matplotlib.use('agg')
reception_json = {
    "raw_angle": 0,
    "servo_tmp": 999,
    "servo_cur": 999,
    "servo_deg": 999,
    "battery_voltage": 0,
    "wifi_signal_strength": 0
}

ser = None

accuracy_angle = 0

# UDPソケットの作成
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sp_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sp_udp_socket.bind(('127.0.0.1', 5010))  # 本当は5002
sp_udp_socket.settimeout(1.0)  # タイムアウトを1秒に設定

mouse_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
mouse_udp_socket.bind(('127.0.0.1', 5020))  # 本当は5002
mouse_udp_socket.settimeout(1.0)  # タイムアウトを1秒に設定

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
    with ThreadPoolExecutor(max_workers=6) as executor:
        executor.submit(sp_udp_reception)
        executor.submit(battery_alert)
        executor.submit(serial_reception)
        executor.submit(odometry)
        executor.submit(graph)
        future = executor.submit(ros)
        future.result()         # 全てのタスクが終了するまで待つ


DEVICE_PATH = "/dev/input/event6"  # Specify your device path here
MAX_ARRAY_LENGTH = 1000  # Maximum length for x_coords and y_coords arrays
# MAX_ARRAY_LENGTH = 2  # Maximum length for x_coords and y_coords arrays

coordinates = [[1,1],[2,2]]

def graph():
    global coordinates
    while True:
        # print(coordinates[0],coordinates[1],flush=True)
        plt.clf()
        plt.plot(coordinates[0], coordinates[1], color='red', linewidth=3)
        # plt.axhline(0, color='black', linewidth=1)
        # plt.axvline(0, color='black', linewidth=1)
        plt.xlim(-50000,50000)
        plt.ylim(-50000,50000)
        plt.title(f"mouse odometry")
        plt.grid(True)
        plt.gca().set_aspect('equal', adjustable='box')
        plt.pause(0.01)


def odometry():
    global coordinates
    global accuracy_angle
    while True:
        try:
            message, cli_addr = mouse_udp_socket.recvfrom(1024)
            # print(f"Received: {message.decode('utf-8')}", flush=True)
            mouse_displacement = [int(value)
                                  for value in message.decode("utf-8").split(",")]
            # print(mouse_displacement, flush=True)
            # angle = MinimalSubscriber.current_angle  # 角度（度）
            angle = accuracy_angle
            # print(
            #     f"           角度{angle}", flush=True)
            # 角度をラジアンに変換
            angle = math.radians(angle) * -1

            x_new = math.cos(
                angle)*mouse_displacement[0] - math.sin(angle)*mouse_displacement[1]
            y_new = math.sin(
                angle)*mouse_displacement[0] + math.cos(angle)*mouse_displacement[1]

            # 本当はintにしてから代入したい！！！！！！！！！！！！！！！！!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            coordinates[0].append(coordinates[0][-1] - x_new)
            coordinates[1].append(coordinates[1][-1] - y_new)
            # print(coordinates, flush=True)

            if len(coordinates[0]) > MAX_ARRAY_LENGTH:
                coordinates[0].pop(0)
            if len(coordinates[1]) > MAX_ARRAY_LENGTH:
                coordinates[1].pop(0)
        except Exception as e:
            print(
                f"\n\n\n\n\n\n\n    マウス の読み取りに失敗: {e}\n\n\n\n\n\n\n", flush=True)


def serial_connection():
    global ser
    global serial_reception_text
    print("253kitaaaaaa",flush=True)
    # while True:
    i = 0
    while i > -1:
        try:
            ser = serial.Serial(f'/dev/ttyUSB{i}', 921600, timeout=3)
            print(f"{i}マイコンとSerial接続成功", flush=True)
            i = -1  # Serialが正常に開かれた場合はループを抜ける
        except Exception as e:
            print(f"{i}マイコンとSerial接続失敗: {e}", flush=True)
            time.sleep(0.2)  # 0.2秒待って再試行
            if i<5:
                i += 1  # 例外が発生した場合もiをインクリメントして次のポートを試す
            else:
                i=0

def serial_reception():
    global ser
    global serial_reception_text
    while True:
        try:
            line = ser.readline()
            # line = ser.readline().decode('utf-8')
            # print(line, flush=True)
            # \n消したほうがいい気が
        except UnicodeDecodeError as e:
            # print("エンコードエラー")
            # print(line)
            print(f"デコードエラー:{e}", flush=True)
        except Exception as e:
            print("マイコンと接続失敗",flush=True)
            serial_connection()
        # serial_reception_text.insert(0, line)
        # if len(serial_reception_text) > 100:
        #     del serial_reception_text[-1]
        time.sleep(0.002) # これないとCPU使用率が増える


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
            print(
                f"\n\n\n\n\n\n\n    スマホ からの受信に失敗: {e}\n\n\n\n\n\n\n", flush=True)

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
    motor_speed = [0, 0, 0, 0, 0]
    servo_angle = 0

    turn_P_gain = 5  # 旋回中に角度センサーにかけられるPゲインーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーー
    # Initialize PID parameters
    kp = 4  # Proportional gain
    ki = 0.1  # Integral gain
    kd = 20  # Derivative gain
    # Pの項：基本要素として必須。これをベースに、必要に応じて他の項を追加する
    # Iの項：出力が目標値に留まるのを邪魔する、何らかの作用がシステムに働く場合に追加する
    # Dの項：システムに振動を抑制する要素が十分にない場合に追加する
    prev_error = 0  # Initialize previous error for derivative term
    integral = 0  # Initialize integral term

    angle_adjust = 0
    current_angle = 0
    angle_control_count = 0

    angle_when_turn = []
    time_when_turn = []

    joy_now = {}
    joy_past = {}

    start_time = 0
    turn_start_time = 0

    controller = ["DS3"]

    def __init__(self):
        global reception_json
        super().__init__('command_subscriber')
        self.publisher_ESP32_to_Webserver = self.create_publisher(
            String, 'ESP32_to_Webserver', 10)
        self.subscription = self.create_subscription(
            Joy,
            "joy0",
            self.joy0_listener_callback,
            10)
        self.subscription = self.create_subscription(
            Joy,
            "joy1",
            self.joy1_listener_callback,
            10)
        self.subscription = self.create_subscription(
            String, 'Web_to_Main', self.Web_to_Main_listener_callback, 10)
        self.subscription  # prevent unused variable warning

        self.timer_0001 = self.create_timer(0.01, self.timer_callback_001)
        self.timer_0016 = self.create_timer(0.033, self.timer_callback_0033)

    def Web_to_Main_listener_callback(self, json_string):
        _json = json.loads(json_string.data)
        if "p" in _json:
            self.kp = float(_json["p"])
        if "i" in _json:
            self.ki = float(_json["i"])
        if "d" in _json:
            self.kd = float(_json["d"])

    def timer_callback_0033(self):
        global wifi_ssid

        msg = String()
        send_json = {
            "state": self.state,
            "ubuntu_ssid": wifi_ssid,
            # "ubuntu_ip": ipget.ipget().ipaddr("wlp2s0"),
            "ubuntu_ip": "aiueo",
            "esp32_ip": "/dev/ttyUSB0",
            "battery_voltage": reception_json["battery_voltage"],
            # "battery_voltage": 6,
            "wifi_signal_strength": reception_json["wifi_signal_strength"],
            "motor_speed": [int(speed) for speed in self.motor_speed],
            "servo_angle": int(self.servo_angle),
            "servo_tmp": reception_json["servo_tmp"],
            "servo_cur": reception_json["servo_cur"],
            "servo_deg": reception_json["servo_deg"],
            "angle_value": self.current_angle,
            "start_time": self.start_time,
            "joy": self.joy_now
        }
        msg.data = json.dumps(send_json)
        self.publisher_ESP32_to_Webserver.publish(msg)

    def timer_callback_001(self):
        global reception_json
        global accuracy_angle
        global ser
        try:
            self.current_angle = reception_json["raw_angle"] + \
                self.angle_adjust
            if self.current_angle < 0:
                self.current_angle = 360 + self.current_angle

            # print(reception_json["raw_angle"],self.angle_adjust,self.current_angle,flush=True)

            accuracy_angle = self.current_angle

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
            turn_minus1to1 += self.joy_now["joy0"]["axes"][0]

            self.motor_speed[:4] = [
                turn_minus1to1 * 255 * -1,
                turn_minus1to1 * 255,
                turn_minus1to1 * 255 * -1,
                turn_minus1to1 * 255]

            normalized_angle = (
                1 - (math.atan2(self.joy_now["joy0"]["axes"][2], self.joy_now["joy0"]["axes"][3])) / (2 * math.pi)) % 1
            distance = math.sqrt(
                self.joy_now["joy0"]["axes"][2]**2 + self.joy_now["joy0"]["axes"][3]**2)
            distance = min(distance, 1)

            # 制御関数の呼び出し
            front_left, front_right, rear_left, rear_right = self.control_mecanum_wheels(
                normalized_angle, distance)  # 0から1の範囲で指定（北を0、南を0.5として時計回りに）

            # 旋回と合わせる
            self.motor_speed[:4] = [speed + value for speed, value in zip(
                self.motor_speed[:4], [front_left, front_right, rear_left, rear_right])]

            # 255を超えた場合、比率を保ったまま255以下にする
            max_motor_speed = max(map(abs, self.motor_speed[:4]))
            if max_motor_speed > 255:
                self.motor_speed[:4] = [int(speed * 255 / max_motor_speed)
                                        for speed in self.motor_speed[:4]]

            # モータースピードが絶対値16未満の値を削除 (ジョイコンの戻りが悪いときでもブレーキを利かすため)
            self.motor_speed = [
                0 if abs(i) < 16 else i for i in self.motor_speed]

            print(self.state,
                  *[int(speed) for speed in self.motor_speed],
                  int(self.servo_angle),
                  flush=True)

            send_ESP32_data = [
                int(self.motor_speed[0]),
                int(self.motor_speed[1]),
                int(self.motor_speed[2]),
                int(self.motor_speed[3]),
                int(self.motor_speed[4]),
                int(self.servo_angle),
                ]
            # send_ESP32_data = [1,2,3,4]
            # json_str = ','.join(send_ESP32_data) + "\n"
            json_str = ','.join(map(str, send_ESP32_data)) + "\n"
            print(json_str,flush=True)
            try:
                ser.write(json_str.encode()) # 書き込む
            except Exception as e:
                print(
                    f"\n\n\n\n\n\n\n    ESP32 への送信に失敗: {e}\n\n\n\n\n\n\n", flush=True)
                serial_connection()
        except KeyError as e:
            print(f"コントローラー の読み取りに失敗: {e}", flush=True)

    def joy0_listener_callback(self, joy):
        global reception_json
        global coordinates

        self.joy_now.update({
            "joy0":
            {"axes": list(joy.axes),
             "buttons": list(joy.buttons)}
        })
        self.joy_past.setdefault(
            "joy0",
            {"axes": [0] * len(joy.axes), "buttons": [0] * len(joy.buttons)}
        )

        # self.motor5_speed = int(self.joy_now["joy0"]["axes"][1]*255)

        if self.joy_now["joy0"]["buttons"][2] == 1:  # Xボタン
            # 0°に旋回
            self.state = 1
            self.turn_start_time = time.time()
            self.angle_when_turn = []
            self.time_when_turn = []
            self.angle_control_count = 0
        if self.joy_now["joy0"]["buttons"][1] == 1:  # Aボタン
            # 90°に旋回
            self.state = 2
            self.turn_start_time = time.time()
            self.angle_when_turn = []
            self.time_when_turn = []
            self.angle_control_count = 0
        if self.joy_now["joy0"]["buttons"][0] == 1:  # Bボタン
            # 180°に旋回
            self.state = 3
            self.turn_start_time = time.time()
            self.angle_when_turn = []
            self.time_when_turn = []
            self.angle_control_count = 0
        if self.joy_now["joy0"]["buttons"][3] == 1:  # Yボタン
            # 270°に旋回
            self.state = 4
            self.turn_start_time = time.time()
            self.angle_when_turn = []
            self.time_when_turn = []
            self.angle_control_count = 0
        if self.joy_past["joy0"]["buttons"][13] == 0 and self.joy_now["joy0"]["buttons"][13] == 1:  # upボタン
            # 排出蓋を閉じる
            self.servo_angle = -135
        if self.joy_past["joy0"]["buttons"][14] == 0 and self.joy_now["joy0"]["buttons"][14] == 1:  # downボタン
            # 排出蓋を開く
            self.servo_angle = 135

        # LボタンとRボタン同時押し
        if self.joy_past["joy0"]["buttons"][4] == 0 and self.joy_now["joy0"]["buttons"][5] == 1:
            # 角度リセット
            if reception_json["raw_angle"] < 0:
                # マイナスのとき
                self.angle_adjust = - 180 - reception_json["raw_angle"]
            else:
                self.angle_adjust = -1 * reception_json["raw_angle"]
            # 座標リセット
                coordinates = [[1,1],[2,2]]

        if self.joy_past["joy0"]["buttons"][10] == 0 and self.joy_now["joy0"]["buttons"][10] == 1:  # homeボタン
            # タイマースタート
            self.start_time = time.time()

        if self.joy_now["joy0"]["buttons"][6] == 1 or self.joy_now["joy0"]["buttons"][7] == 1:  # ZRボタンまたはZLボタン
            # 走行補助強制停止
            self.state = 0
            self.motor_speed = [0] * 5

        self.joy_past["joy0"] = self.joy_now["joy0"]

    def joy1_listener_callback(self, joy):
        self.joy_now.update({
            "joy1":
            {"axes": list(joy.axes),
             "buttons": list(joy.buttons)}
        })
        self.joy_past.setdefault(
            "joy1",
            {"axes": [0] * len(joy.axes), "buttons": [0] * len(joy.buttons)}
        )

        # 回収機構のモーター
        self.motor_speed[4] = int(self.joy_now["joy1"]["axes"][1] * 255)

        if self.joy_now["joy1"]["buttons"][6] == 1 or self.joy_now["joy1"]["buttons"][7]:
            # 走行補助強制停止
            self.state = 0
            self.motor_speed = [0] * 5

        self.joy_past["joy1"] = self.joy_now["joy1"]

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
        # print(self.current_angle, target_angle, flush=True)

        # ラジアンにして、来週的に度数法に直せばよくね？   ーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーー
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

        self.angle_when_turn.append(angle_difference)
        self.time_when_turn.append(time.time() - self.turn_start_time)

        if abs(angle_difference) < 2:
            if self.angle_control_count > 50:
                # 止まる
                temp = 0
                self.state = 0

                print(self.time_when_turn, flush=True)
                print(self.angle_when_turn, flush=True)
                plt.clf()
                plt.plot(self.time_when_turn, self.angle_when_turn,
                         color='red', linewidth=2)
                plt.title(f"PID P:{self.kp} I:{self.ki} D:{self.kd}")
                plt.xlabel("second")
                plt.ylabel("degree")
                plt.grid(True)
                # プロットしたグラフをファイルsin.pngに保存する
                plt.savefig(f"turn_{int(time.time())}.png")

            self.angle_control_count += 1
            temp = 0
        else:
            # P制御
            # temp = angle_difference/360 * self.turn_P_gain

            #  PID制御する
            error = angle_difference
            self.integral += error
            # 微分項の計算
            derivative = error - self.prev_error

            # PID制御出力の計算
            temp = self.kp * error + self.ki * self.integral + self.kd * derivative

            print(self.kp, self.ki, self.kd, flush=True)

            # 制御出力が -1 から 1 の範囲に収まるようにクリップ
            temp = max(min(temp, 1), -1)

            # 更新
            self.prev_error = error

        return temp


if __name__ == '__main__':
    main()
