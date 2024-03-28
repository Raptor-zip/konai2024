import inspect  # 実行中の行数を取得 logger用
import os
import sys
from re import T
from turtle import distance  # どのESP32を識別するためにls使うよう
import matplotlib.pyplot as plt
from sympy import false
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import Joy
import json  # jsonを使うため
from concurrent.futures import ThreadPoolExecutor  # threadPoolExecutor
import playsound  # バッテリー低電圧保護ブザー用
import subprocess  # SSID取得用
import time
import datetime
import serial # シリアル通信用
from serial.tools import list_ports # シリアル通信用
import ipget  # IPアドレス取得用
import socket  # UDP通信用
import asyncio  # 非同期関数を実行するため
import math
import evdev
from matplotlib import pyplot as plt  # 描画用ライブラリ
from logging import getLogger, handlers, DEBUG
import logging
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
log_filename:str = os.path.join(log_folder, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S.log"))
handler = handlers.RotatingFileHandler(log_filename, maxBytes=1000000, backupCount=10)
logger.addHandler(handler)
# コンソールにログを出力するハンドラを追加
handler_console = logging.StreamHandler(sys.stdout)
logger.addHandler(handler_console)

def location(depth:int=0) -> tuple:
    frame = inspect.currentframe().f_back
    return os.path.basename(frame.f_code.co_filename), frame.f_code.co_name, frame.f_lineno

def main() -> None:
    with ThreadPoolExecutor(max_workers=6) as executor:
        executor.submit(odometry)
        executor.submit(graph)
        future = executor.submit(ros)
        future.result()         # 全てのタスクが終了するまで待つ

def ros(args=None):
    rclpy.init(args=args)

    minimal_subscriber = ROS2MainNode()

    rclpy.spin(minimal_subscriber)

    minimal_subscriber.destroy_node()
    rclpy.shutdown()


class ROS2MainNode(Node):
    def __init__(self):
        global reception_json
        super().__init__('main')
        self.subscription = self.create_subscription(
            Joy,
            "joy0",
            self.joy0_listener_callback,
            10)
        self.subscription  # prevent unused variable warning

        self.timer_0001 = self.create_timer(0.01, self.timer_callback_001)

    def timer_callback_001(self):
        pass

    def joy0_listener_callback(self, joy):
        pass

coordinates: list[list[float]] = [[0, 1], [0, 1]]
accuracy_angle: int = 0


def graph():
    global coordinates
    while True:
        # print(coordinates[0],coordinates[1],flush=True)
        plt.clf()
        plt.plot(coordinates[0], coordinates[1], color='red', linewidth=2)
        plt.plot(coordinates[0][-1], coordinates[1]
                 [-1], marker='x', markersize=15)
        plt.xlim(-50000, 50000)
        plt.ylim(-50000, 50000)
        plt.title(
            f"mouse odometry ( {coordinates[0][-1]} , {coordinates[1][-1]} )")
        plt.grid(True)
        plt.gca().set_aspect('equal', adjustable='box')
        plt.pause(0.01)


def odometry():
    global coordinates, accuracy_angle
    # マウス受信用
    mouse_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    mouse_udp_socket.bind(('127.0.0.1', 5020))  # 本当は5002
    mouse_udp_socket.settimeout(1.0)  # タイムアウトを1秒に設定
    while True:
        try:
            message, cli_addr = mouse_udp_socket.recvfrom(1024)
            # print(f"Received: {message.decode('utf-8')}", flush=True)
            mouse_displacement = [int(value)
                                  for value in message.decode("utf-8").split(",")]
            # print(mouse_displacement, flush=True)
            # angle = ROS2MainNode.current_angle  # 角度（度）
            angle = accuracy_angle
            # print(
            #     f"           角度{angle}", flush=True)
            # 角度をラジアンに変換
            angle = math.radians(angle) * -1

            x_new = math.cos(
                angle)*mouse_displacement[0] - math.sin(angle)*mouse_displacement[1]
            y_new = math.sin(
                angle)*mouse_displacement[0] + math.cos(angle)*mouse_displacement[1]

            x_lateset = coordinates[0][-1] - x_new
            y_lateset = coordinates[1][-1] - y_new

            # 本当はintにしてから代入したい！！！！！！！！！！！！！！！！!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            coordinates[0].append(coordinates[0][-1] - x_new)
            coordinates[1].append(coordinates[1][-1] - y_new)
            # print(coordinates, flush=True)

            if len(coordinates[0]) > 1000:
                # coordinates[0].pop(0)
                # coordinates[1].pop(0)

                coordinates[0].append(coordinates[0][-1])
                coordinates[1].append(coordinates[1][-1])
                coordinates[0] = coordinates[0][:-1][::2]
                coordinates[1] = coordinates[1][:-1][::2]

            coordinates[0].append(x_lateset)
            coordinates[1].append(y_lateset)
        except Exception as e:
            print(
                f"\n\n\n\n\n\n\n    マウス の読み取りに失敗: {e}\n\n\n\n\n\n\n", flush=True)




if __name__ == '__main__':
    main()
