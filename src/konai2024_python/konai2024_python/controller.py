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
        # print(str(key))
        # print(type(str(key)))

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
        elif key == keyboard.Key.enter:
            ros2_main.inject()
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
        executor.submit(lambda: controller.check_controller_connection(
            controller()))  # コントローラーの死活監視
        future = executor.submit(ros)
        future.result()         # 全てのタスクが終了するまで待つ


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

                    if ros2_main != None:
                        ros2_main.stop()

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
                {"axes": list(joy.axes),
                 "buttons": list(joy.buttons)}
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
        self.subscription  # prevent unused variable warning
        self.get_logger().info("ROS2MainNode初期化完了")
        self.timer_0001 = self.create_timer(0.01, self.timer_callback_001)
        # self.timer_0016 = self.create_timer(0.065, self.timer_callback_0033) # 同期式
        self.timer_0016 = self.create_timer(
            0.016, self.timer_callback_0033)  # DMA

        self.get_logger().info("ROS2MainNodeタイマー初期化完了")

    def timer_callback_001(self):
        pass

    def joy0_listener_callback(self, joy):
        controller.joy_setup(controller(), "joy0", joy)

    def joy1_listener_callback(self, joy):
        controller.joy_setup(controller(), "joy1", joy)


if __name__ == '__main__':
    main()
