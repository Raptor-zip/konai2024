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

# TODO ちゃんと動作してるかのしらんけど治す
try:
    result = subprocess.check_output(
        ['iwgetid', '-r'], universal_newlines=True)
    wifi_ssid = result.strip()
    # wifi_ssid= bytes(result.strip(), 'utf-8').decode('unicode-escape')
except subprocess.CalledProcessError:
    wifi_ssid = "エラー"

def location(depth:int=0) -> tuple:
    frame = inspect.currentframe().f_back
    return os.path.basename(frame.f_code.co_filename), frame.f_code.co_name, frame.f_lineno

def main() -> None:
    with ThreadPoolExecutor(max_workers=6) as executor:
        executor.submit(lambda: Serial.receive_serial(Serial(), "ESP32"))
        # ROS2MainNode.get_logger(ROS2MainNode).debug("ESP32との通信開始")
        # executor.submit(Serial.receive_serial("STM32"))
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
        future.result()         # 全てのタスクが終了するまで待つ

class Serial:
    def connect_serial(self) -> None: # TODO　これもreceiveみたいに並列にしてもインじゃない？
        global micon_dict

        while True:
            for micon_name, micon_values in micon_dict.items():
                micon_dict["STM32"]["is_connected"] = True # TODO これなおす
                if micon_values["is_connected"]:
                    continue

                candidates_port_list = [info.device for info in list_ports.comports()]
                connected_ports = [m["serial_port"] for m in micon_dict.values() if m["is_connected"]]
                available_ports = [port for port in candidates_port_list if port not in connected_ports]

                if not available_ports:
                    logger.critical(f"{micon_name}がUSBに接続されていない")
                    # ROS2MainNode.get_logger().error(f"{micon_name}がUSBに接続されていない")
                    continue

                for port in available_ports:
                    try:
                        subprocess.run(f"sudo -S chmod 777 {port}".split(), input=("robocon471" + '\n').encode())
                        micon_values["serial_obj"] = serial.Serial(port, 500000, timeout=1)
                        micon_values["serial_port"] = port
                        micon_values["is_connected"] = True
                        logger.info(f"{micon_name}とSerial接続成功 {port}")
                        # ROS2MainNode.get_logger().info(f"{micon_name}とSerial接続成功 {port}")
                    except Exception as e:
                        logger.critical(f"{micon_name}とSerial接続失敗: {e}")
                        # ROS2MainNode.get_logger().error(f"{micon_name}とSerial接続失敗: {e}")

                time.sleep(0.1)


    def receive_serial(self, micon_id:str) -> None:
        global micon_dict

        while True:
            each_micon_dict_values:dict = micon_dict[micon_id]
            # logger.info(f"{location()}")
            # ROS2MainNode.get_logger().error(f"{location()}")
            if each_micon_dict_values["serial_obj"] is not None:
                try:
                    received_bytes: bytes = each_micon_dict_values["serial_obj"].readline()
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

        logger.info(f"{each_micon_dict_key}から:{received_message}")
        # ROS2MainNode.get_logger().error(f"{each_micon_dict_key}から:{received_message}")

        try:
            received_message: str = received_message.decode('utf-8')[:-2]  # \r\nを消す
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

# TODO コントローラーの変換とかの処理がくそめんどい気がする importすればいっか　importするか、もう一回joyノードをパブリッシュする

# TODO パブサブが無限に増えるのを危惧してるけど、多孔線とかはセンサー1個ごとにパブサブしてるから　それよりかはまし？　石川先輩は
# TODO パブサブ通信の遅延しりたいよね UDPなら全然いい　あとゼロコピーでもぜんぜんいい

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
        self.publisher_ESP32_to_Webserver = self.create_publisher(
            String, 'ESP32_to_Webserver', 10)
        self.subscription = self.create_subscription(
            Joy,
            "joy0",
            self.joy0_listener_callback,
            10)
        self.subscription = self.create_subscription(
            String, 'serial_write', self.serial_write, 10)
        self.subscription  # prevent unused variable warning

        self.timer_0001 = self.create_timer(0.01, self.timer_callback_001)
        # TODO キューにいれる関数書くけど、ROSで自動でできるのか、並列処理でかかないといけないのか調べる

    def serial_write(self, json_string):
        # 100hzで制御するんじゃなくて、普通にサブスクライブしたときに書き込み

        # HACK bytearray型？で受信する　でもパブリッシュのデータ見てるときに、ぱっとみでわからんのだるいから intとfloat　でおくる？独自？

        self.get_logger.debug(json_string);
        pass

    def joy0_listener_callback(self):
        # TODO 安全装置のプログラムを挿入する
        # どこかのボタンが押されているならコマンドを送信しない　など でも間違えて押された場合事故るから
        pass

    def timer_callback_001(self):
        # バッテリー保護
        # if battery.battery_dict["battery_4cell"]["state"] == "much_low" or battery.battery_dict["battery_4cell"]["state"] == "abnormality":
        #     # 4セルで動かすものは メカナムと回収機構
        #     self.DCmotor_speed = [0] * len(self.DCmotor_speed)
        #     logger.critical(f"4セルバッテリーが危険:{battery.battery_dict['battery_4cell']['state']}")
        # if battery.battery_dict["battery_3cell"]["state"] == "much_low" or battery.battery_dict["battery_3cell"]["state"] == "abnormality":
        #     # 3セルで動かすものは ブラシレスモーター
        #     self.BLmotor_speed = [0] * len(self.BLmotor_speed)
        #     logger.critical(f"3セルバッテリーが危険:{battery.battery_dict['battery_3cell']['state']}")

        for micon_dict_key, micon_dict_values in micon_dict.items():
            if micon_dict_values["reboot"] == True:
                micon_dict_values["reboot"] = False

        self.uart_prev_count:bytes = (self.uart_prev_count + 1) & 0xFF # 0から255までの値を繰り返す

        data_tuple:tuple = (self.uart_prev_count,-32767,16384,-24576,255)

        self.get_logger().info(f"{data_tuple}")

        data = bytearray()
        for x in data_tuple:
            data.extend(x.to_bytes(2, byteorder='big', signed=True))

        # data = bytearray([0x10, 0x20])

        # TODO 安全装置のプログラム入れる -255〜255とかの判別とか　バッテリー電圧の予備とか これによって安全装置が作動して値が変更されたかの返り値必要？
        # TODO バッテリーの管理どのファイルでやる？
        # TODO 送るマイコンもパブサブする


        # crc16_bytes:bytes = crc16(data, 0, len(data)).to_bytes(2, byteorder='big')
        crc16_bytes:bytes = crc16(data, 0, len(data))
        data.extend(crc16_bytes.to_bytes(2, byteorder='big'))
        # print(hex(crc16_bytes),flush=True)
        # data.extend(crc16_bytes)
        # print(hex(crc16(data, 0, len(data))),flush=True)

        json_str: str = ','.join(map(str, self.send_ESP32_data)) + "\n"
        data.extend(b'\x0d')  # 改行文字を追加 キャリッジリターン（CR：ASCIIコード0x0d）は \r       改行文字（CR）を追加します # ラインフィード(b'\x0a')（LF：ASCIIコード0x0a）は \nはいらない
        
        if self.count_print % 1 == 0:  # 15回に1回実行
            # self.get_logger().info(json_str.encode().hex())
            self.get_logger().info(data.hex())
            pass
        self.count_print += 1

        try:
            # each_micon_dict_values["serial_obj"].write(
            #     json_str.encode())
            each_micon_dict_values["serial_obj"].write(data)
            # print(f"{each_micon_dict_key}への送信成功", flush=True)
        except Exception as e:
            # logger.critical(f"{each_micon_dict_key}への送信に失敗: {e}")
            each_micon_dict_values["is_connected"] = False
            # TODO 片方のマイコンが途切れたときに、詰まるから、このやり方よくない 非同期にするか、connect_serialを並行処理でずっとwhileしといて、bool変数がTrueになったら接続処理するとか

if __name__ == '__main__':
    main()
