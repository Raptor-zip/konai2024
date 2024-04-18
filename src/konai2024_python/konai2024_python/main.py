import inspect  # 実行中の行数を取得 logger用
import os
from sqlite3 import Time
import sys
import struct  # floatをbytesに変換するため
from re import T
from turtle import distance
from xmlrpc.client import Boolean
from keyboard import is_pressed  # どのESP32を識別するためにls使うよう
import matplotlib.pyplot as plt
from sympy import false
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from std_msgs.msg import Float64MultiArray  # main ⇔ write_read_serial
from sensor_msgs.msg import Joy
import json  # jsonを使うため
from concurrent.futures import ThreadPoolExecutor  # threadPoolExecutor
import playsound  # バッテリー低電圧保護ブザー用
import subprocess  # SSID取得用
import time
import datetime
import serial  # シリアル通信用
from serial.tools import list_ports  # シリアル通信用
import ipget  # IPアドレス取得用
import socket  # UDP通信用
import asyncio  # 非同期関数を実行するため
import math
import evdev
from matplotlib import pyplot as plt  # 描画用ライブラリ
from logging import getLogger, handlers, DEBUG
import logging
from pynput import keyboard
# import matplotlib
# matplotlib.use('agg')

# ロガーを作成
logger = getLogger(__name__)
logger.setLevel(DEBUG)
# ログファイルの設定
# ログファイルを保存するフォルダのパス
log_folder = "python_log"
# フォルダが存在しない場合は作成する
if not os.path.exists(log_folder):
    os.makedirs(log_folder)
log_filename: str = os.path.join(
    log_folder, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S.log"))
handler = handlers.RotatingFileHandler(
    log_filename, maxBytes=1000000, backupCount=10)
logger.addHandler(handler)
# コンソールにログを出力するハンドラを追加
handler_console = logging.StreamHandler(sys.stdout)
logger.addHandler(handler_console)

# TODO ちゃんと動作してるかのしらんけど治す
try:
    result = subprocess.check_output(
        ['iwgetid', '-r'], universal_newlines=True)
    wifi_ssid = result.strip()
    # wifi_ssid= bytes(result.strip(), 'utf-8').decode('unicode-escape')
except subprocess.CalledProcessError:
    wifi_ssid = "エラー"


def location(depth: int = 0) -> tuple:
    frame = inspect.currentframe().f_back
    return os.path.basename(frame.f_code.co_filename), frame.f_code.co_name, frame.f_lineno


ros2_main = None


class MonitorKeyboard:
    def __init__(self):
        self.key_pressed = {}

    def on_press(self, key):
        print(str(key))
        # print(type(str(key)))

        if str(key) == "'1'":
            ros2_main.joy_id = "joy0"
        elif str(key) == "'2'":
            ros2_main.joy_id = "joy1"
        elif str(key) == "'3'":
            ros2_main.joy_id = "joy2"

        if str(key) == "'u'":
            ros2_main.VESC_adjust[0] += 500
        elif str(key) == "'h'":
            ros2_main.servo_adjust[1] += -5
        elif str(key) == "'j'":
            ros2_main.VESC_adjust[0] += -500
        elif str(key) == "'k'":
            ros2_main.servo_adjust[1] += 5
        elif str(key) == "'v'":
            ros2_main.servo_setup = True

            command = Float64MultiArray()
            # CyberGear_speedの値を浮動小数点数に変換してリストに格納
            command.data = [float(1), float(27), float(1)]
            ros2_main.publisher_serial_write.publish(command)
        elif str(key) == "'b'":
            ros2_main.time_pushed_antiJammedServo_button = time.time()
            ros2_main.servo_raw[2] = -100
        elif str(key) == "'n'":
            # タイマースタート
            ros2_main.start_time = time.time()
        elif key == keyboard.Key.space:
            ros2_main.inject()
        elif key == keyboard.Key.ctrl:
            if ros2_main.injection_mode > 4:
                ros2_main.injection_mode = 0
            else:
                ros2_main.injection_mode += 1
        else:
            # print(str(key))
            pass

        # 引数で指定されたキーが押されているかどうかを判定
        self.key_pressed[str(key)] = True
        logger.debug(self.key_pressed)

    def on_release(self, key):
        # print('release: {}'.format(key))
        # 指定されたキーが離されたら状態をリセット
        if str(key) in self.key_pressed:
            del self.key_pressed[str(key)]

        if (key == keyboard.Key.esc):
            print("StopKey")
            self.listener.stop()
            self.listener = None

    def start(self):
        self.listener = keyboard.Listener(
            on_press=self.on_press, on_release=self.on_release)
        self.listener.start()

    def getstatus(self):
        if (self.listener == None):
            return False
        return True

    def is_pressed(self, key: str) -> bool:
        return self.key_pressed.get(key, False)


monitor = MonitorKeyboard()
monitor.start()


def main() -> None:
    with ThreadPoolExecutor(max_workers=6) as executor:
        # executor.submit(receive_udp_sp)
        # executor.submit(receive_udp_webserver)
        # executor.submit(receive_udp_webrtc)
        # executor.submit(battery.battery_alert)
        executor.submit(lambda: controller.check_controller_connection(
            controller()))  # コントローラーの死活監視
        executor.submit(lambda: Serial.receive_serial(Serial(), "ESP32"))
        # ROS2MainNode.get_logger(ROS2MainNode).debug("ESP32との通信開始")

#         import threading
# import serial

# # シリアルポートとロックの初期化
# ser = serial.Serial('COM1', 9600)
# lock = threading.Lock()

# def send_data(data):
#     with lock:
#         ser.write(data.encode())

# # スレッドの作成と実行
# thread1 = threading.Thread(target=send_data, args=("Hello",))
# thread2 = threading.Thread(target=send_data, args=("World",))
# thread1.start()
# thread2.start()
# こういう感じに動作させる

        executor.submit(lambda: Serial.connect_serial(Serial()))
        future = executor.submit(ros)
        executor.submit(lambda: DeviceControl.servo_2_control(DeviceControl()))
        future.result()         # 全てのタスクが終了するまで待つ


micon_dict: dict[str, dict] = {
    "ESP32": {"is_connected": False,  # パソコンと接続しているか
              "serial_port": None,  # ポート 例:/dev/ttyUSB0
              "serial_obj": None,  # シリアルオブジェクト
              "reboot": False},  # 再起動命令がでているか
    "STM32": {"is_connected": False,
              "serial_port": None,
              "serial_obj": None,
              "reboot": False}
}


reception_json: dict = {
    "raw_angle": 0
}


class DeviceControl:
    DCmotor: dict = {
        "motor1": {
            "is_allowed_to_run": True,
            "duty": 0,
            "duty_min": -256,
            "duty_max": 256,
            "duty_normal": 0
        },

        "motor2": {
            "is_allowed_to_run": True,
            "duty": 0,
            "duty_min": -256,
            "duty_max": 256
        }
    }

    BLmotor: dict = {
        "motor1": {
            "is_allowed_to_run": False,
            "speed": 0,
            "speed_min": 1000,
            "speed_max": 2000
        }
    }

    solenoid: dict = {
        "solenoid1": {
            "is_allowed_to_run": False,
            "is_open": False
        }
    }

    distance_sensors: list[int] = [-1, -1, -1, -1]

    limit_switch: bool = False


class controller:
    joy_now: dict = {}
    joy_past: dict = {}

    def check_controller_connection(self) -> None:
        while True:
            # 0.1秒に1回コントローラーの接続を確認
            time.sleep(0.1)
            # コントローラーの接続を確認
            for joy_id, joy_value in controller.joy_now.items():
                if time.time() - joy_value["time"] > 1:
                    logger.error(f"{joy_id}が接続されていません")

                    joy_value["state"] = "disconnected"
                    joy_value["axes"] = [0] * len(joy_value["axes"])
                    joy_value["buttons"] = [0] * len(joy_value["buttons"])

                    # if ros2_main != None:
                    #     ros2_main.stop()

    def joy_setup(self, joy_id: str, received_joy: Joy) -> None:
        self.joy_past.setdefault(  # 初回のみ実行 上書き不可
            joy_id,
            {"axes": [0] * 4, "buttons": [0] * 17}
        )

        # 一周期前のデータを保存
        if joy_id in self.joy_now:
            self.joy_past[joy_id] = self.joy_now[joy_id]

        joy: dict = {"axes": received_joy.axes,
                     "buttons": received_joy.buttons}

        # 各axesが0.3未満の場合に0に設定する
        joy["axes"] = [
            0 if abs(each_axes) < 0.3 else each_axes for each_axes in joy["axes"]]

        _len_axes: int = len(joy["axes"])  # axesの数
        _len_buttons: int = len(joy["buttons"])  # buttonsの数

        # ボタンの数が違うので、それぞれのコントローラーに合わせて変換する
        if _len_axes == 4 and _len_buttons == 17:
            self.joy_now.update({
                joy_id:
                {"axes": list(joy["axes"]),
                 "buttons": list(joy["buttons"])}
            })
        if _len_axes == 6 and _len_buttons == 17:
            self.joy_now.update({joy_id: self.convert_PS3_to_WiiU(joy)})
        elif _len_axes == 6 and _len_buttons == 16:
            self.joy_now.update({joy_id: self.convert_PS4_to_WiiU(joy)})
        elif _len_axes == 8 and _len_buttons == 13:
            self.joy_now.update({joy_id: self.convert_PS4_other_to_WiiU(joy)})
        else:
            logger.error("コントローラーのボタン数が違う")

        # 時刻を保存 死活監視のため
        self.joy_now[joy_id].update({
            "time": time.time(),
            "state": "connected"})

    def convert_PS3_to_WiiU(self, joy_before: dict) -> dict:
        joy_after: dict = {"buttons": joy_before["buttons"],
                           "axes": [joy_before["axes"][0], joy_before["axes"][1], joy_before["axes"][3], joy_before["axes"][4]]}
        return joy_after

    def convert_PS4_to_WiiU(self, joy_before: dict) -> dict:
        joy_after: dict = {"axes": [joy_before["axes"][0], joy_before["axes"][1], joy_before["axes"][2], joy_before["axes"][3]],
                           "buttons": [
            joy_before["buttons"][0],
            joy_before["buttons"][1],
            joy_before["buttons"][3],
            joy_before["buttons"][2],
            joy_before["buttons"][9],
            joy_before["buttons"][10],
            joy_before["axes"][4],
            joy_before["axes"][5],
            joy_before["buttons"][4],
            joy_before["buttons"][6],
            joy_before["buttons"][5],
            joy_before["buttons"][7],
            joy_before["buttons"][8],
            joy_before["buttons"][11],
            joy_before["buttons"][12],
            joy_before["buttons"][13],
            joy_before["buttons"][14]]}
        # リマッピングする
        # print(joy_before,flush=True)

        if joy_after["buttons"][6] == -1:
            joy_after["buttons"][6] = 1
        else:
            joy_after["buttons"][6] = 0

        if joy_after["buttons"][7] == -1:
            joy_after["buttons"][7] = 1
        else:
            joy_after["buttons"][7] = 0
        # joy_before["buttons"][15]はタッチパッドおしこみ

        # L2 [4]
        # R2 [5]
        # print(joy_after,flush=True)
        return joy_after

    def convert_PS4_other_to_WiiU(self, joy_before: dict) -> dict:
        joy_after: dict = {"buttons": [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]}
        # リマッピングする
        # print(joy_before,flush=True)

        joy_after["buttons"][:13] = joy_before["buttons"][:13]

        if joy_before["axes"][7] < 0:
            joy_after["buttons"][13] = 0
            joy_after["buttons"][14] = 1
        elif joy_before["axes"][7] > 0:
            joy_after["buttons"][13] = 1
            joy_after["buttons"][14] = 0
        else:
            joy_after["buttons"][13] = 0
            joy_after["buttons"][14] = 0

        if joy_before["axes"][6] < 0:  # トリガー　しきい値
            joy_after["buttons"][15] = 0
            joy_after["buttons"][16] = 1
        elif joy_before["axes"][6] > 0:  # トリガー　しきい値
            joy_after["buttons"][15] = 1
            joy_after["buttons"][16] = 0
        else:
            joy_after["buttons"][15] = 0
            joy_after["buttons"][16] = 0

        joy_after.setdefault("axes", [joy_before["axes"][0], joy_before["axes"]
                                      [1], joy_before["axes"][3], joy_before["axes"][4]])
        # L2 [2]
        # R2 [5]
        # print(joy_after,flush=True)
        return joy_after


class battery:
    # stateには 以下のものが入る dictにはstrが入る send_ESPにはintが入る
    # -1:エラー 以下のものではない
    # 0:normal
    # 1:low
    # 2:much_low
    # 3:not_exit
    # 4:abnormality
    # 5:undefined
    battery_dict: dict[str, dict] = {
        "battery_4cell": {
            "cell_number": 4,
            "voltage_history": [],
            "average_voltage": None,
            "state": None},
        "battery_3cell": {
            "cell_number": 3,
            "voltage_history": [],
            "average_voltage": None,
            "state": None},
    }

    # HACK はじめからintをdictにいれるほうがいい　定数で宣言する
    def convert_battery_state_to_binary(self, battery_state_str: str) -> int:
        if battery_state_str == "normal":
            return 0
        elif battery_state_str == "low":
            return 1
        elif battery_state_str == "much_low":
            return 2
        elif battery_state_str == "not_exit":
            return 3
        elif battery_state_str == "abnormality":
            return 4
        elif battery_state_str == None:
            return 5
        else:
            logger.error("battery_stateが既定のものではない")
            return -1

    def battery_alert(self) -> None:
        while True:
            for each_battery_dict_key, each_battery_dict_value in battery.battery_dict.items():
                if each_battery_dict_value["state"] == "low":
                    playsound.playsound("battery_alert.mp3")

                elif each_battery_dict_value["state"] == "much_low":
                    # 音声読み上げでやりたいけど妥協
                    playsound.playsound("battery_alert.mp3")
                elif each_battery_dict_value["state"] == "abnormality":
                    playsound.playsound("battery_alert.mp3")
                # 1:low
                # 2:much_low
                # 3:not_exit
                # 4:abnormality
            time.sleep(0.2)  # 無駄にCPUを使わないようにする


class Serial:
    def connect_serial(self) -> None:  # TODO　これもreceiveみたいに並列にしてもインじゃない？
        global micon_dict

        while True:
            for micon_name, micon_values in micon_dict.items():
                time.sleep(0.1)
                micon_dict["STM32"]["is_connected"] = True  # TODO これなおす
                if micon_values["is_connected"]:
                    continue

                candidates_port_list = [
                    info.device for info in list_ports.comports()]
                connected_ports = [m["serial_port"]
                                   for m in micon_dict.values() if m["is_connected"]]
                available_ports = [
                    port for port in candidates_port_list if port not in connected_ports]

                # ACMがついているときは接続しない
                available_ports = [
                    port for port in available_ports if "ACM" not in port]

                if not available_ports:
                    logger.critical(f"{micon_name}がUSBに接続されていない")
                    # ROS2MainNode.get_logger().error(f"{micon_name}がUSBに接続されていない")
                    continue

                for port in available_ports:
                    try:
                        subprocess.run(
                            f"sudo -S chmod 777 {port}".split(), input=("robocon471" + '\n').encode())
                        micon_values["serial_obj"] = serial.Serial(
                            port, 500000, timeout=1)
                        micon_values["serial_port"] = port
                        micon_values["is_connected"] = True
                        logger.info(f"{micon_name}とSerial接続成功 {port}")
                        # ROS2MainNode.get_logger().info(f"{micon_name}とSerial接続成功 {port}")
                    except Exception as e:
                        logger.critical(f"{micon_name}とSerial接続失敗: {e}")
                        # ROS2MainNode.get_logger().error(f"{micon_name}とSerial接続失敗: {e}")

    def receive_serial(self, micon_id: str) -> None:
        global micon_dict

        while True:
            each_micon_dict_values: dict = micon_dict[micon_id]
            # logger.info(f"{location()}")
            # ROS2MainNode.get_logger().error(f"{location()}")
            if each_micon_dict_values["serial_obj"] is not None:
                try:
                    received_bytes: bytes = each_micon_dict_values["serial_obj"].readline(
                    )
                    # HACK なにもマイコンから受信しなくてもタイムアウトで、空を受け取ったふうになるから注意

                    # ROS2MainNode.get_logger().error(f"{micon_id}から:{received_bytes}")
                    logger.info(f"{micon_id}から:{received_bytes}")
                    # self.received_command(received_bytes, micon_id)
                # except AttributeError as e:
                #     logger.error(f"{micon_id}への接続失敗 読み取り試行時:{e}")
                    # TODO falseにする動作ついか
                    # continue
                except Exception as e:
                    logger.error(f"{micon_id}への接続失敗 読み取り試行時:{e}")
                    # ROS2MainNode.get_logger().error(f"{micon_id}への接続失敗 読み取り試行時:{e}")
                    continue
            else:
                each_micon_dict_values["is_connected"] = False
                time.sleep(0.01)  # 無駄にCPUを使わないようにする

    def received_command(self, received_message: bytes, each_micon_dict_key: str) -> None:

        def convert_value(value):
            if value.isdigit():  # 整数値の場合
                return int(value)
            try:
                return float(value)  # 浮動小数点数の場合
            except ValueError:
                return value  # その他の場合は文字列として返す

        logger.info(
            f"{each_micon_dict_key}から:{received_message.decode('utf-8', 'ignore')}")
        # ROS2MainNode.get_logger().error(f"{each_micon_dict_key}から:{received_message}")

        try:
            received_message: str = received_message.decode(
                'utf-8')[:-2]  # \r\nを消す
        except UnicodeDecodeError as e:
            print(f"{each_micon_dict_key}から受信時のデコードエラー:{e}", flush=True)

        if received_message[0] == "$":
            # print(
            # f"\n                                       {each_micon_dict_key}からz$:{received_message}\n", flush=True)
            received_message = received_message[1:]  # 先頭の$を除く
            received_message_array: list = [convert_value(
                x) for x in received_message.split(",")]  # 文字列を,で区切ってstr、int、floatに変換して配列に入れる

            # 送受信できているか確認するよう 通常時は送らない
            if received_message_array[1] == 0:
                print(
                    f"\n\n\n\n\n折り返された{received_message}\n\n\n\n\n", flush=True)

            # マイコンのsetupの開始と完了を検知
            elif received_message_array[1] == 1:
                #    micon_dictとかにstatusとしていれたい
                if received_message_array[2] == 1:
                    print(
                        f"\n\n\n\n\nESP32_{received_message_array[0]} setup開始\n\n\n\n\n", flush=True)
                elif received_message_array[2] == 2:
                    print(
                        f"\n\n\n\n\nESP32_{received_message_array[0]} setup完了\n\n\n\n\n", flush=True)
                else:
                    print("\n\n\n\n\nエラー\n\n\n\n\n", flush=True)

            # バッテリーの処理
            elif received_message_array[1] == 2:  # 4セルバッテリー
                battery.battery_dict["battery_4cell"]["voltage_history"].insert(
                    0, received_message_array[2])  # listの先頭にボルト追加
                # 先頭から7個以降を削除 だいたい2秒の平均
                battery.battery_dict["battery_4cell"]["voltage_history"] = battery.battery_dict["battery_4cell"]["voltage_history"][:6]

            elif received_message_array[1] == 3:  # 3セルバッテリー
                battery.battery_dict["battery_3cell"]["voltage_history"].insert(
                    0, received_message_array[2])  # listの先頭にボルト追加
                # 先頭から7個以降を削除 だいたい2秒の平均
                battery.battery_dict["battery_3cell"]["voltage_history"] = battery.battery_dict["battery_3cell"]["voltage_history"][:6]

            # 距離センサーのデータが来たときの処理
            elif received_message_array[1] == 4:
                DeviceControl.distance_sensors = [
                    int(received_message_array[2]),
                    int(received_message_array[3]),
                    int(received_message_array[4]),
                    int(received_message_array[5])]

            # デコードエラーが来たときの処理
            elif received_message_array[1] == 5:
                print(
                    f"\nESP32_{received_message_array[0]}デコードエラー:{received_message_array[2]}\n", flush=True)

            # リセット命令を受信したときの処理
            elif received_message_array[1] == 6:
                print(
                    f"\n\n\n\n\n\nESP32_{received_message_array[0]}をソフトウェアリセットします\n\n\n\n\n", flush=True)

            # 回収機構のリミットスイッチが来たときの処理
            # elif received_message_array[1] == 7:
            #     DeviceControl.limit_switch = bool(received_message_array[2])

            elif received_message_array[0] == 1 and received_message_array[1] == 8:
                # ジャイロセンサーのデータが来たときの処理
                pass

        else:
            # デバッグ用メッセージ
            # print(
            #     f"\n                                       {each_micon_dict_key}から:{received_message}\n", flush=True)
            pass

            # serial_reception_text.insert(0, line)
            # if len(serial_reception_text) > 100:
            #     del serial_reception_text[-1]

        # バッテリー保護
        # TODO 場所を適切なところに移す
        for each_battery in battery.battery_dict.values():
            if each_battery["voltage_history"] != []:
                each_battery["average_voltage"] = round(
                    sum(each_battery["voltage_history"]) / len(each_battery["voltage_history"]), 2)
                cell_voltage: float = round(
                    each_battery["average_voltage"] / each_battery["cell_number"], 2)

                if cell_voltage < 1:
                    each_battery["state"] = "not_exit"
                elif cell_voltage < 3:
                    each_battery["state"] = "much_low"
                elif cell_voltage < 3.5:
                    each_battery["state"] = "low"
                elif cell_voltage < 4.3:
                    each_battery["state"] = "normal"
                else:
                    each_battery["state"] = "abnormality"


def ros(args=None):
    global ros2_main

    rclpy.init(args=args)

    ros2_main = ROS2MainNode()

    rclpy.spin(ros2_main)

    ros2_main.destroy_node()
    rclpy.shutdown()


class ROS2MainNode(Node):
    state: int = 0
    CyberGear_speed: list[float] = [0, 0, 0, 0]  # rpm -30〜30
    DCmotor_speed: list[int] = [0, 0]  # -256〜256 符号あり
    BLmotor_speed: list[int] = [0]  # 射出用ダクテッドファンと仰角調整用GM6020

    VESC_rpm: list[int] = [0]  # VESC
    VESC_adjust: list[int] = [0]
    VESC_raw: list[int] = [0]

    servo_angle: list[int] = [0, 0, 0]
    servo_adjust: list[int] = [0, 0, 0]
    servo_raw: list[int] = [0, 0, 0]

    is_slow_speed: bool = False

    time_pushed_load_button = 0  # 装填ボタンが押された時間
    time_pushed_antiJammedServo_button = 0
    time_pushed_antiJammed_loadServo_button = 0

    # controller_list: list[str] = ["joy0", "joy1"]
    joy_id: str = "joy0"

    # TODO Initialize PID parameters dict型にしたい！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！
    kp: float = 0.01  # Proportional gain 基本要素として必須。これをベースに、必要に応じて他の項を追加する
    ki: float = 0  # Integral gain 出力が目標値に留まるのを邪魔する、何らかの作用がシステムに働く場合に追加する
    kd: float = 0  # Derivative gain システムに振動を抑制する要素が十分にない場合に追加する

    prev_error = 0  # Initialize previous error for derivative term
    integral: float = 0  # Initialize integral term

    angle_adjust: int = 0
    current_angle: int = 0
    angle_control_count: int = 0

    angle_when_turn: list = []
    time_when_turn: list = []

    injection_mode: int = 0  # 0停止 1左下かご 2左上かご 3右下かご 4右上かご 5Vゴール

    start_time: float = 0  # 試合開始時刻(ホームボタン押下時の時刻)
    turn_start_time: float = 0  # 旋回の開始時刻

    count_print: int = 0  # 15回に1回デバッグ用のprintを出力するためのカウンタ

    servo_setup: bool = False

    send_ESP32_data: str = ""

    def __init__(self):
        global reception_json
        super().__init__('main')
        self.publisher_ESP32_to_Webserver = self.create_publisher(
            String, 'ESP32_to_Webserver', 10)
        self.publisher_serial_write = self.create_publisher(
            Float64MultiArray, 'serial_write', 10)
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
            Joy,
            "joy2",
            self.joy2_listener_callback,
            10)
        self.subscription = self.create_subscription(
            String, 'Web_to_Main', self.Web_to_Main_listener_callback, 10)
        self.subscription  # prevent unused variable warning
        self.get_logger().info("ROS2MainNode初期化完了")
        self.timer_0001 = self.create_timer(0.01, self.timer_callback_001)
        # self.timer_0016 = self.create_timer(0.065, self.timer_callback_0033) # 同期式
        self.timer_0016 = self.create_timer(
            0.016, self.timer_callback_0033)  # DMA

        self.get_logger().info("ROS2MainNodeタイマー初期化完了")

    def Web_to_Main_listener_callback(self, json_string):
        # ロボット制御からきたデータの処理
        # この処理雑くていろわろし
        _json = json.loads(json_string.data)
        if "p" in _json:
            self.kp = float(_json["p"])
        if "i" in _json:
            self.ki = float(_json["i"])
        if "d" in _json:
            self.kd = float(_json["d"])

    def timer_callback_0033(self):
        global wifi_ssid, micon_dict

        temp_micon_dict: dict = {"ESP32": {
            "is_connected": micon_dict["ESP32"]["is_connected"],
            "serial_id": micon_dict["ESP32"]["serial_port"]
        },
            "STM32": {
            "is_connected": micon_dict["STM32"]["is_connected"],
            "serial_id": micon_dict["STM32"]["serial_port"]
        }, }

        # temp_micon_dict:dict = micon_dict
        # print(temp_micon_dict["ESP32_1"],flush=True)
        # print(temp_micon_dict["ESP32_1"]["serial_obj"],flush=True)
        # print(temp_micon_dict["ESP32_1"]["serial_obj"].port,flush=True)
        # temp_micon_dict["ESP32_1"].pop("serial_obj")
        # temp_micon_dict["ESP32_2"].pop("serial_obj")

        try:
            _ubuntu_ip: str = ipget.ipget().ipaddr("wlp2s0")
        except ValueError as e:
            _ubuntu_ip: str = "WiFiエラー"

        msg = String()
        send_json: dict = {
            "state": self.state,
            "ubuntu_ssid": wifi_ssid,
            "ubuntu_ip": _ubuntu_ip,
            # "ubuntu_ip": "aiueo",
            # "battery_voltage": battery_dict["average_voltage"],
            # "battery_voltage": 6,
            "battery": battery.battery_dict,
            "limited_switch": DeviceControl.limit_switch,
            # "micon":micon_dict,
            "micon": temp_micon_dict,
            "wifi_signal_strength": 0,  # wifiのウブンツの強度を読み取る
            "DCmotor_speed": [int(speed) for speed in self.DCmotor_speed],
            "BLmotor_speed": [int(speed) for speed in self.BLmotor_speed],
            "servo_angle": [int(angle) for angle in self.servo_angle],
            "angle_value": self.current_angle,
            "start_time": self.start_time,
            "joy": controller.joy_now,
            "serial_str": self.send_ESP32_data
        }

        # send_json: dict = {
        #     # "DCmotor_speed": [int(speed) for speed in self.DCmotor_speed],
        #     # "BLmotor_speed": [int(speed) for speed in self.BLmotor_speed],
        #     "servo_angle": [int(angle) for angle in self.servo_angle],
        #     # "start_time": self.start_time,
        #     "joy": controller.joy_now,
        # }
        msg.data = json.dumps(send_json)  # エンコード
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(json.dumps(msg.data).encode(
            'utf-8'), ('127.0.0.1', 5002))
        # print(json.dumps(reception_json).encode('utf-8'))
        self.publisher_ESP32_to_Webserver.publish(msg)

        if self.joy_id in controller.joy_now:
            if controller.joy_now[self.joy_id]["buttons"][4] == 1:
                self.stop()

        command = Float64MultiArray()
        # CyberGear_speedの値を浮動小数点数に変換してリストに格納
        command.data = [float(1), float(22), float(self.CyberGear_speed[0])]
        self.publisher_serial_write.publish(command)

        command = Float64MultiArray()
        # CyberGear_speedの値を浮動小数点数に変換してリストに格納
        command.data = [float(1), float(24), float(self.CyberGear_speed[1])]
        self.publisher_serial_write.publish(command)

        command = Float64MultiArray()
        # CyberGear_speedの値を浮動小数点数に変換してリストに格納
        command.data = [float(1), float(26), float(self.CyberGear_speed[2])]
        self.publisher_serial_write.publish(command)

        command = Float64MultiArray()
        # CyberGear_speedの値を浮動小数点数に変換してリストに格納
        command.data = [float(1), float(28), float(self.CyberGear_speed[3])]
        self.publisher_serial_write.publish(command)

    def timer_callback_001(self):
        global reception_json, micon_dict
        self.current_angle = reception_json["raw_angle"] + \
            self.angle_adjust
        if self.current_angle < 0:
            self.current_angle = 360 + self.current_angle

        # self.get_logger().info(
        #     f"ESP32からの角度:{reception_json['raw_angle']} 補正後の角度:{self.current_angle}")

        # print(reception_json["raw_angle"],self.angle_adjust,self.current_angle,flush=True)

        if controller.joy_now[self.joy_id]["buttons"][8] == 1 and controller.joy_past["joy0"]["buttons"][9] == 0:
            self.DCmotor_speed[0] = -255
        elif controller.joy_now["joy0"]["buttons"][9] == 1 and controller.joy_past["joy0"]["buttons"][8] == 0:
            self.DCmotor_speed[0] = 255
        else:
            if "joy1" in controller.joy_now:
                if abs(controller.joy_now["joy1"]["axes"][1]) > 0.1:
                    self.DCmotor_speed[0] = 0
            else:
                self.DCmotor_speed[0] = 0

        if self.joy_id in controller.joy_now:
            # 回収モーター
            if controller.joy_now[self.joy_id]["buttons"][6] == 1 and controller.joy_now[self.joy_id]["buttons"][7] == 0:
                self.DCmotor_speed[0] = -255
            elif controller.joy_now[self.joy_id]["buttons"][7] == 1 and controller.joy_now[self.joy_id]["buttons"][6] == 0:
                self.DCmotor_speed[0] = 255
            else:
                if monitor.is_pressed("'y'"):
                    self.DCmotor_speed[0] = -255
                elif monitor.is_pressed("'i'"):
                    self.DCmotor_speed[0] = 255
                else:
                    self.DCmotor_speed[0] = 0

        else:
            if monitor.is_pressed("'y'"):
                self.DCmotor_speed[0] = -255
            elif monitor.is_pressed("'i'"):
                self.DCmotor_speed[0] = 255
            else:
                self.DCmotor_speed[0] = 0

        turn_minus1to1: float = 0
        _distance: float = 0
        _angle_rad: float = 0

        # if self.state == 0:
        #     # 走行補助がオフなら
        #     turn_minus1to1 = 0
        # elif self.state == 1:
        #     turn_minus1to1 = self.turn(0)
        # elif self.state == 2:
        #     turn_minus1to1 = self.turn(90)
        # elif self.state == 3:
        #     turn_minus1to1 = self.turn(180)
        # elif self.state == 4:
        #     turn_minus1to1 = self.turn(270)

        if monitor.is_pressed("'q'"):
            turn_minus1to1 += -1
        if monitor.is_pressed("'e'"):
            turn_minus1to1 += 1

        if monitor.is_pressed("'w'") and monitor.is_pressed("'a'"):
            _angle_rad += math.pi * 7 / 4
            _distance += 1
        elif monitor.is_pressed("'w'") and monitor.is_pressed("'d'"):
            _angle_rad += math.pi * 1 / 4
            _distance += 1
        elif monitor.is_pressed("'s'") and monitor.is_pressed("'a'"):
            _angle_rad += math.pi * 5 / 4
            _distance += 1
        elif monitor.is_pressed("'s'") and monitor.is_pressed("'d'"):
            _angle_rad += math.pi * 3 / 4
            _distance += 1
        elif monitor.is_pressed("'w'"):
            _distance += 1
        elif monitor.is_pressed("'s'"):
            _angle_rad += math.pi * 4 / 4
            _distance += 1
        elif monitor.is_pressed("'a'"):
            _angle_rad += math.pi * 6 / 4
            _distance += 1
        elif monitor.is_pressed("'d'"):
            _angle_rad += math.pi * 2 / 4
            _distance += 1

        if self.joy_id in controller.joy_now:
            # 手動旋回と自動旋回を合わせる
            turn_minus1to1 += controller.joy_now[self.joy_id]["axes"][0]

            # ジョイスティックの傾きの大きさを求める(最大1最小0)
            _distance += min(math.sqrt(
                controller.joy_now[self.joy_id]["axes"][2]**2 + controller.joy_now[self.joy_id]["axes"][3]**2), 1)

            if controller.joy_now[self.joy_id]["axes"][2]**2 + controller.joy_now[self.joy_id]["axes"][3]**2 > 0.1:
                _angle_rad = math.atan2(
                    controller.joy_now[self.joy_id]["axes"][3], controller.joy_now[self.joy_id]["axes"][2]) - math.pi / 2

        else:
            # logger.critical(f"joy0の読み取りに失敗")
            # self.get_logger().error("joy0の読み取りに失敗") // TODO コメントアウト外す
            turn_minus1to1 = 0

        turn_minus1to1 = min(max(turn_minus1to1, -1), 1)
        _distance = min(max(_distance, 0), 1)

        self.CyberGear_speed[:4] = [
            turn_minus1to1 * 30 * -1,
            turn_minus1to1 * 30,
            turn_minus1to1 * 30 * -1,
            turn_minus1to1 * 30]

        # 旋回と十字移動合わせる
        self.CyberGear_speed[:4] = [speed + value for speed, value in zip(
            self.CyberGear_speed[:4], control_mecanum_wheels(_angle_rad, _distance))]
        # front_left, front_right, rear_left, rear_right

        # 絶対値が30を超えた場合、比率を保ったまま30以下にする
        _max_motor_speed: float = max(map(abs, self.CyberGear_speed[:4]))
        if _max_motor_speed > 30:
            self.CyberGear_speed[:4] = [speed * 30 / _max_motor_speed
                                        for speed in self.CyberGear_speed[:4]]

        self.CyberGear_speed = [
            self.CyberGear_speed[0] * -1,
            self.CyberGear_speed[1],
            self.CyberGear_speed[3],
            self.CyberGear_speed[2] * -1
        ]

        # 低速モードの処理
        # Rボタン
        if self.joy_id in controller.joy_now:
            if controller.joy_now[self.joy_id]["buttons"][5]:
                self.is_slow_speed = True
            else:
                self.is_slow_speed = monitor.is_pressed("Key.shift")
        else:
            self.is_slow_speed = monitor.is_pressed("Key.shift")

        # logger.info(self.is_slow_speed)

        if self.is_slow_speed >= 1:
            self.CyberGear_speed[:4] = [speed * 0.2
                                        for speed in self.CyberGear_speed[:4]]

        # モータースピードが絶対値16未満の値を削除 (ジョイコンの戻りが悪いときでもブレーキを利かすため)
        # self.DCmotor_speed = [
        #     0 if abs(i) < 16 else i for i in self.DCmotor_speed]
        # self.CyberGear_speed = [
        #     0 if abs(i) < 1 else i for i in self.CyberGear_speed]

        # 射出モード
        PREV_ANGLE = 15
        if self.injection_mode == 0:  # 停止
            self.VESC_raw[0] = 0
            self.servo_raw[1] = 0

        elif self.injection_mode == 1:  # 左下かご
            self.VESC_raw[0] = 14000
            if self.servo_raw[0] < PREV_ANGLE:
                self.servo_raw[1] = -70

        elif self.injection_mode == 2:  # 左上かご
            self.VESC_raw[0] = 32500
            if self.servo_raw[0] < PREV_ANGLE:
                self.servo_raw[1] = -50

        elif self.injection_mode == 3:  # 右下かご
            self.VESC_raw[0] = 21500
            if self.servo_raw[0] < PREV_ANGLE:
                self.servo_raw[1] = -70

        elif self.injection_mode == 4:  # 右上かご
            self.VESC_raw[0] = 37500
            if self.servo_raw[0] < PREV_ANGLE:
                self.servo_raw[1] = -50

        elif self.injection_mode == 5:  # Vゴール
            self.VESC_raw[0] = 30500
            if self.servo_raw[0] < PREV_ANGLE:
                self.servo_raw[1] = -45

        # VESC
        self.VESC_rpm[0] = self.VESC_raw[0] + self.VESC_adjust[0]

        # 装填サーボの処理
        if self.time_pushed_load_button != 0 and (time.time() - self.time_pushed_load_button) > 1.2:
            # 1.2sで0°に戻る
            self.servo_raw[0] = -40
            self.time_pushed_load_button = 0

        if self.time_pushed_antiJammed_loadServo_button != 0 and (time.time() - self.time_pushed_antiJammed_loadServo_button) > 0.4:
            # 0.4sで0°に戻る
            self.servo_raw[0] = -40
            self.time_pushed_antiJammed_loadServo_button = 0

        # 玉詰まりサーボの処理
        if self.time_pushed_antiJammedServo_button != 0 and (time.time() - self.time_pushed_antiJammedServo_button) > 1.5:
            # 1.2sで0°に戻る
            self.servo_raw[2] = 0
            self.time_pushed_antiJammedServo_button = 0

        for i in range(len(self.servo_angle)):
            self.servo_angle[i] = self.servo_raw[i] + self.servo_adjust[i]

        if self.joy_id in controller.joy_now:
            if controller.joy_now[self.joy_id]["buttons"][4] == 1:
                self.stop()

        # バッテリー保護
        # if battery.battery_dict["battery_4cell"]["state"] == "much_low" or battery.battery_dict["battery_4cell"]["state"] == "abnormality":
        #     # 4セルで動かすものは メカナムと回収機構
        #     self.DCmotor_speed = [0] * len(self.DCmotor_speed)
        #     logger.critical(f"4セルバッテリーが危険:{battery.battery_dict['battery_4cell']['state']}")
        # if battery.battery_dict["battery_3cell"]["state"] == "much_low" or battery.battery_dict["battery_3cell"]["state"] == "abnormality":
        #     # 3セルで動かすものは ブラシレスモーター
        #     self.BLmotor_speed = [0] * len(self.BLmotor_speed)
        #     logger.critical(f"3セルバッテリーが危険:{battery.battery_dict['battery_3cell']['state']}")

        # command = Float64MultiArray()
        # # CyberGear_speedの値を浮動小数点数に変換してリストに格納
        # command.data = [float(1), float(22), float(self.CyberGear_speed[0])]
        # self.publisher_serial_write.publish(command)

        # command = Float64MultiArray()
        # # CyberGear_speedの値を浮動小数点数に変換してリストに格納
        # command.data = [float(1), float(24), float(self.CyberGear_speed[1])]
        # self.publisher_serial_write.publish(command)

        # command = Float64MultiArray()
        # # CyberGear_speedの値を浮動小数点数に変換してリストに格納
        # command.data = [float(1), float(26), float(self.CyberGear_speed[2])]
        # self.publisher_serial_write.publish(command)

        # command = Float64MultiArray()
        # # CyberGear_speedの値を浮動小数点数に変換してリストに格納
        # command.data = [float(1), float(28), float(self.CyberGear_speed[3])]
        # self.publisher_serial_write.publish(command)

        self.send_ESP32_data: list[int] = [
            int(self.DCmotor_speed[0]),  # 0 回収装填
            int(self.DCmotor_speed[1]),  # 1 回収装填
            int(self.BLmotor_speed[0]),  # 2 ダクテッドファン
            int(max(min(self.servo_angle[0], 135), -135)),  # 3 サーボ
            int(max(min(self.servo_angle[1], 135), -135)),  # 4 サーボ
            int(max(min(self.servo_angle[2], 135), -135)),  # 5 サーボ
            # 6 ESP32を再起動するか 0 or 1
            int(convert_to_binary(micon_dict["ESP32"]["reboot"])),
            int(max(min(self.VESC_rpm[0], 40000), 0)),   # 7 VESC
            int(0),  # 8 LEDテープの装填アニメーションの合図 0 or 1
            int(convert_to_binary(self.servo_setup))  # 9 サーボの初期設定 0 or 1
        ]

        for micon_dict_key, micon_dict_values in micon_dict.items():
            if micon_dict_values["reboot"] == True:
                micon_dict_values["reboot"] = False

        self.servo_setup = False

        # logger.debug(f"{self.VESC_rpm[0]}    {self.servo_angle[1]}")

        logger.info(self.send_ESP32_data)
        logger.info(self.CyberGear_speed)

        json_str: str = ','.join(map(str, self.send_ESP32_data))
        # self.get_logger().info(json_str)
        # logger.info(json_str)
        data: bytearray = bytearray(json_str.encode())

        data.extend(b'\x0d')

        # logger.info(data.hex())

        if self.count_print % 1 == 0:  # 15回に1回実行
            # self.get_logger().info(data.hex())
            # logger.info(data.hex())
            pass
        self.count_print += 1
        try:
            micon_dict["ESP32"]["serial_obj"].write(bytes(data))
            # each_micon_dict_values["serial_obj"].write(json_str_2.encode())
            # print(f"{each_micon_dict_key}への送信成功", flush=True)
            pass
        except Exception as e:
            logger.critical(f"ESP32 への送信に失敗: {e}")
            micon_dict["ESP32"]["is_connected"] = False
            # TODO 片方のマイコンが途切れたときに、詰まるから、このやり方よくない 非同期にするか、connect_serialを並行処理でずっとwhileしといて、bool変数がTrueになったら接続処理するとか

    def joy_all_listener_callback(self):
        global reception_json, micon_dict
        if self.joy_id in controller.joy_now:
            # Lボタン
            if controller.joy_now[self.joy_id]["buttons"][4] == 1:
                self.stop()

            # Rボタン
            if controller.joy_now[self.joy_id]["buttons"][5] == 1:
                # 低速モード
                self.is_slow_speed = True
            else:
                self.is_slow_speed = False

            # リセット
            # + / options
            if controller.joy_now[self.joy_id]["buttons"][9] == 1:
                self.time_pushed_antiJammed_loadServo_button = time.time()  # エポック秒
                self.servo_raw[0] = abs(
                    self.servo_raw[1] + self.servo_adjust[1]) + 14

                # # 角度リセット
                # if reception_json["raw_angle"] < 0:
                #     # マイナスのとき
                #     self.angle_adjust = - 180 - reception_json["raw_angle"]
                # else:
                #     self.angle_adjust = -1 * reception_json["raw_angle"]
                # # 座標リセット
                #     coordinates = [[1, 1], [2, 2]]

            # PS/homeボタン
            if controller.joy_past[self.joy_id]["buttons"][10] == 0 and controller.joy_now[self.joy_id]["buttons"][10] == 1:
                # タイマースタート
                self.start_time = time.time()

            # 射出
            # ↑ボタン
            if controller.joy_now[self.joy_id]["buttons"][13] == 1:
                self.inject()

            # 初期化
            # ↓ボタン
            if controller.joy_now[self.joy_id]["buttons"][14] == 1 and controller.joy_past[self.joy_id]["buttons"][14] == 0:
                self.servo_setup = True

                command = Float64MultiArray()
                # CyberGear_speedの値を浮動小数点数に変換してリストに格納
                command.data = [float(1), float(27), float(1)]
                self.publisher_serial_write.publish(command)

            # たまづまりサーボ
            # ←ボタン
            if controller.joy_now[self.joy_id]["buttons"][15] == 1:
                self.time_pushed_antiJammedServo_button = time.time()
                self.servo_raw[2] = -100

            # →ボタン
            if controller.joy_past[self.joy_id]["buttons"][16] == 0 and controller.joy_now[self.joy_id]["buttons"][16] == 1:
                if self.injection_mode > 4:
                    self.injection_mode = 0
                else:
                    self.injection_mode += 1

            # VESC
            # △ボタン
            if controller.joy_now[self.joy_id]["buttons"][2] == 1 and controller.joy_past[self.joy_id]["buttons"][2] == 0:
                self.VESC_adjust[0] += 500

            # ×ボタン
            elif controller.joy_now[self.joy_id]["buttons"][0] == 1 and controller.joy_past[self.joy_id]["buttons"][0] == 0:
                self.VESC_adjust[0] += -500

            # 仰角サーボ
            # ◯ボタン
            if controller.joy_now[self.joy_id]["buttons"][1] == 1 and controller.joy_past[self.joy_id]["buttons"][1] == 0:
                self.servo_adjust[1] += 5

            # □ボタン
            elif controller.joy_now[self.joy_id]["buttons"][3] == 1 and controller.joy_past[self.joy_id]["buttons"][3] == 0:
                self.servo_adjust[1] += -5

            # 左ジョイスティック
            if controller.joy_past[self.joy_id]["buttons"][11] == 0 and controller.joy_now[self.joy_id]["buttons"][11] == 1:
                # ESP32_1のソフトウェアリセット
                micon_dict["ESP32"]["reboot"] = True
                # 送信後に False に戻す

            # 右ジョイスティック
            if controller.joy_past[self.joy_id]["buttons"][12] == 0 and controller.joy_now[self.joy_id]["buttons"][12] == 1:
                # STM32のソフトウェアリセット
                micon_dict["STM32"]["reboot"] = True
                # 送信後に False に戻す

        else:
            logger.error(f"{self.joy_id}の読み取りに失敗")

    def joy0_listener_callback(self, joy):
        controller.joy_setup(controller(), "joy0", joy)

        self.joy_all_listener_callback()

    def joy1_listener_callback(self, joy):
        controller.joy_setup(controller(), "joy1", joy)

        self.joy_all_listener_callback()

    def joy2_listener_callback(self, joy):
        controller.joy_setup(controller(), "joy2", joy)

        self.joy_all_listener_callback()

    def inject(self):
        self.time_pushed_load_button = time.time()  # エポック秒
        self.servo_raw[0] = abs(
            self.servo_raw[1] + self.servo_adjust[1]) + 14

    def turn(self, target_angle: float) -> float:
        # TODO ラジアンにして、来週的に度数法に直せばよくね？   ーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーー
        target_plus_180 = target_angle + 180
        if target_plus_180 > 360:
            target_plus_180 = 360 - target_angle
        angle_difference: float = abs(self.current_angle - target_angle)
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

        turn_amount: float = 0

        if abs(angle_difference) < 2:
            if self.angle_control_count > 50:
                # 止まる
                turn_amount = 0
                self.state = 0

                # print(self.time_when_turn, flush=True)
                # print(self.angle_when_turn, flush=True)
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
            turn_amount = 0
        else:
            #  PID制御する
            error = angle_difference
            self.integral += error
            # 微分項の計算
            derivative = error - self.prev_error

            # PID制御出力の計算
            turn_amount = self.kp * error + self.ki * self.integral + self.kd * derivative

            print("                                     ",
                  self.kp, self.ki, self.kd, flush=True)

            # 制御出力が -1 から 1 の範囲に収まるようにクリップ
            turn_amount = max(min(turn_amount, 1), -1)

            # 更新
            self.prev_error = error

        return turn_amount

    def straight(self, target_angle):
        return
        # if self.current_distance > self.straight_distance_to_wall:
        #     distance = self.current_distance * self.straight_P_gain
        #     if distance > self.normal_max_motor_speed:
        #         distance = self.normal_max_motor_speed

        #     distance_1 = distance - self.axes_3
        #     if distance_1 > 255:
        #         distance_1 = 255
        #     self.motor1_speed = distance_1

        #     distance_2 = distance - self.axes_1
        #     if distance_2 > 255:
        #         distance_2 = 255
        #     self.motor2_speed = distance_2

        #     target_plus_180 = target_angle + 180
        #     if target_plus_180 > 360:
        #         target_plus_180 = 360 - target_angle
        #     angle_difference = abs(self.current_angle - target_angle)
        #     if angle_difference > 180:
        #         angle_difference = 360 - abs(self.current_angle-target_angle)
        #     if target_angle > 180:
        #         if target_plus_180 <= self.current_angle <= target_angle:
        #             angle_difference = angle_difference*-1
        #     else:
        #         if target_angle <= self.current_angle <= target_plus_180:
        #             pass
        #         else:
        #             angle_difference = angle_difference*-1

        #     # print(angle_difference,flush=True)

        #     if abs(angle_difference) > 2:  # 単位:° パラメーター調整必要
        #         # 壁と平行じゃないなら
        #         if angle_difference > 0:
        #             # 右に傾いているなら
        #             self.motor1_speed = self.motor1_speed - angle_difference * \
        #                 self.straight_turn_P_gain
        #         else:
        #             # 左に傾いているなら
        #             self.motor2_speed = self.motor2_speed + \
        #                 angle_difference * self.straight_turn_P_gain

        #         if self.motor1_speed > 255:
        #             self.motor1_speed = 255
        #         elif self.motor1_speed < -1 * 255:
        #             self.motor1_speed = -1 * 255
        #         if self.motor2_speed > 255:
        #             self.motor2_speed = 255
        #         elif self.motor2_speed < -1 * 255:
        #             self.motor2_speed = -1 * 255
        # else:
        #     self.motor1_speed = 0
        #     self.motor2_speed = 0
        #     self.state = 0

    def stop(self):
        # 強制停止
        self.state = 0
        self.injection_mode = 0
        self.CyberGear_speed = [0] * len(self.CyberGear_speed)
        self.DCmotor_speed = [0] * len(self.DCmotor_speed)
        self.BLmotor_speed = [0] * len(self.BLmotor_speed)
        self.VESC_rpm = [0] * len(self.VESC_rpm)
        self.VESC_adjust = [0] * len(self.VESC_adjust)
        self.VESC_raw = [0] * len(self.VESC_raw)
        self.servo_angle = [0] * len(self.servo_angle)
        self.servo_adjust = [0] * len(self.servo_adjust)
        # self.servo_raw = [0] * len(self.servo_raw)
        self.servo_raw = [14, 0, 0]

# def stop():
#     # 強制停止
#     ROS2MainNode.state = 0
#     ROS2MainNode.CyberGear_speed = [0] * len(ROS2MainNode.CyberGear_speed)
#     ROS2MainNode.DCmotor_speed = [0] * len(ROS2MainNode.DCmotor_speed)
#     ROS2MainNode.BLmotor_speed = [0] * len(ROS2MainNode.BLmotor_speed)
#     ROS2MainNode.VESC_rpm = [0] * len(ROS2MainNode.VESC_rpm)
#     ROS2MainNode.VESC_adjust = [0] * len(ROS2MainNode.VESC_adjust)
#     ROS2MainNode.VESC_raw = [0] * len(ROS2MainNode.VESC_raw)
#     ROS2MainNode.servo_angle = [0] * len(ROS2MainNode.servo_angle)
#     ROS2MainNode.servo_adjust = [0] * len(ROS2MainNode.servo_adjust)
#     ROS2MainNode.servo_raw = [0] * len(ROS2MainNode.servo_raw)


# ros2_main = ROS2MainNode()


def control_mecanum_wheels(angle_rad: float, speed: float) -> list[float]:
    # 回転数を-30から30の範囲に変換
    front_left: float = math.sin(angle_rad + math.pi / 4.0) * 30
    front_right: float = math.cos(angle_rad + math.pi / 4.0) * 30
    rear_left: float = math.cos(angle_rad + math.pi / 4.0) * 30
    rear_right: float = math.sin(angle_rad + math.pi / 4.0) * 30

    adjust = 30 / max([abs(front_left), abs(front_right),
                       abs(rear_left), abs(rear_right)])
    front_left = front_left * adjust * speed
    front_right = front_right * adjust * speed
    rear_left = rear_left * adjust * speed
    rear_right = rear_right * adjust * speed

    return [front_left, front_right, rear_left, rear_right]


def convert_to_binary(boolean_value: bool) -> int:
    if boolean_value:
        return 1
    else:
        return 0


def crc16(data: bytearray, offset, length: int) -> int:
    # CRC-16/CCITT-FALSE
    # define CRC16_CCITT_FALSE_POLYNOME  0x1021
    # define CRC16_CCITT_FALSE_INITIAL   0xFFFF
    # define CRC16_CCITT_FALSE_XOR_OUT   0x0000
    # define CRC16_CCITT_FALSE_REV_IN    false
    # define CRC16_CCITT_FALSE_REV_OUT   false
    # https://stackoverflow.com/questions/35205702/calculating-crc16-in-python
    if data is None or offset < 0 or offset > len(data) - 1 and offset+length > len(data):
        return 0
    crc = 0xFFFF
    for i in range(0, length):
        crc ^= data[offset + i] << 8
        for j in range(0, 8):
            if (crc & 0x8000) > 0:
                crc = (crc << 1) ^ 0x1021
            else:
                crc = crc << 1
    return crc & 0xFFFF


# def receive_udp_sp() -> None:
#     global reception_json
#     # UDPソケットの作成
#     sp_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     sp_udp_socket.bind(('127.0.0.1', 5010))
#     sp_udp_socket.settimeout(0.1)  # タイムアウトを0.1秒に設定
#     while True:
#         try:
#             message, cli_addr = sp_udp_socket.recvfrom(1024)
#             # print(f"Received: {message.decode('utf-8')}", flush=True)
#             reception_json_temp = json.loads(message.decode('utf-8'))
#             reception_json.update(reception_json_temp)
#         except Exception as e:
#             print(
#                 f"スマホ からの受信に失敗: {e}", flush=True)


def receive_udp_webserver() -> None:
    global reception_json
    # UDPソケットの作成
    udp_socket_webserver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket_webserver.bind(('127.0.0.1', 5003))
    udp_socket_webserver.settimeout(1.0)  # タイムアウトを1秒に設定
    while True:
        try:
            message, cli_addr = udp_socket_webserver.recvfrom(1024)
            # print(f"Received: {message.decode('utf-8')}", flush=True)
            reception_json_temp = json.loads(message.decode('utf-8'))
            reception_json.update(reception_json_temp)
        except Exception as e:
            print(
                f"\n\n\n\n\n\n\n    Webserver からの受信に失敗: {e}\n\n\n\n\n\n\n", flush=True)


def receive_udp_webrtc() -> None:
    global reception_json
    # UDPソケットの作成
    udp_socket_webserver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket_webserver.bind(('127.0.0.1', 5007))
    udp_socket_webserver.settimeout(1.0)  # タイムアウトを1秒に設定
    while True:
        try:
            message, cli_addr = udp_socket_webserver.recvfrom(1024)
            # print(f"Received: {message.decode('utf-8')}", flush=True)
            reception_json_temp = json.loads(message.decode('utf-8'))
            # reception_json.update({"raw_angle": int(reception_json_temp)})
            print(reception_json, flush=True)
        except Exception as e:
            print(
                f"\n\n\n\n\n\n\n    webrtc からの受信に失敗: {e}\n\n\n\n\n\n\n", flush=True)


if __name__ == '__main__':
    main()
