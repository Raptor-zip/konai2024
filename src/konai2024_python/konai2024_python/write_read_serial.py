import inspect  # 実行中の行数を取得 logger用
import os
import sys
import struct  # floatをbytesに変換するため
from re import T
from turtle import distance  # どのESP32を識別するためにls使うよう
import matplotlib.pyplot as plt
from sympy import false
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray, String  # main ⇔ write_read_serial
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
from queue import Queue

serial_queue = Queue()
# serial_queue = Queue(maxsize=100)

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


def main() -> None:
    with ThreadPoolExecutor(max_workers=6) as executor:
        executor.submit(lambda: Serial.connect_serial(Serial()))
        executor.submit(lambda: Serial.write_serial(Serial(), "ESP32"))
        # executor.submit(lambda: Serial.receive_serial(Serial(), "ESP32"))
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

        future = executor.submit(ros)
        future.result()         # 全てのタスクが終了するまで待つ


micon_dict: dict[str, dict] = {
    "ESP32": {"is_connected": False,  # パソコンと接続しているか
              "serial_port": None,  # ポート 例:/dev/ttyUSB0
              "serial_obj": None,  # シリアルオブジェクト
              "reboot": False},  # 再起動命令がでているか
    "STM32": {"is_connected": False,
              "serial_port": None,
              "serial_obj": None,
              "reboot": False}}


# micon_dictのキーに対応するキューを作成
micon_write_queues = {micon_key: Queue() for micon_key in micon_dict.keys()}


reception_json: dict = {
    "raw_angle": 0
}


class DeviceControl:
    DCmotor: dict = {
        "motor1": {
            "is_allowed_to_run": True,
            "duty": 0,
            "duty_min": -256,
            "duty_max": 256
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

    def joy_convert(self, joy_id: str, received_joy: Joy) -> None:
        self.joy_past.setdefault(  # 初回のみ実行 上書き不可
            joy_id,
            {"axes": [0] * 4, "buttons": [0] * 17}
        )

        # 　一周期前のデータを保存
        if joy_id in self.joy_now:
            self.joy_past[joy_id] = self.joy_now[joy_id]

        joy: dict = {"axes": received_joy.axes,
                     "buttons": received_joy.buttons}

        # 旋回が逆になるから無理やり合わせる
        joy["axes"][0] = joy["axes"][0] * -1

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

                # USBがついているときは接続しない
                available_ports = [
                    port for port in available_ports if "USB" not in port]

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

    def write_serial(self, micon_name: str) -> None:
        global mipon_dict, micon_write_queues
        uart_prev_count = 0
        count_print = 0

        while True:
            if micon_write_queues[micon_name].empty():
                # logger.info("キューが空")
                time.sleep(0.01)
                # continue

            else:

                # キューから取り出す
                send_float_array = micon_write_queues[micon_name].get()

                data = bytearray()

                # 同じ値が送られてきてないか確認するためのカウンタ
                uart_prev_count += 1
                if uart_prev_count > 255:
                    uart_prev_count = 1
                data.extend(uart_prev_count.to_bytes(
                    1, byteorder='big', signed=False))

                # コマンドID
                command_id = send_float_array["command_id"]
                data.extend(command_id.to_bytes(
                    2, byteorder='big', signed=False))

                # コマンド内容
                command_content = send_float_array["command_content"]
                data.extend(struct.pack('>f', command_content))
                # logger.info(command_content)

                # crc16_bytes:bytes = crc16(data, 0, len(data)).to_bytes(2, byteorder='big')
                # crc16_bytes: bytes = crc16(data, 0, len(data))
                # data.extend(crc16_bytes.to_bytes(2, byteorder='big'))
                # print(hex(crc16_bytes),flush=True)
                # data.extend(crc16_bytes)
                # print(hex(crc16(data, 0, len(data))),flush=True)

                # data.extend(b'\x0d')
                # data.extend(b'\x0a')

                # self.get_logger().info(f"{data_tuple}")
                # logger.info(f"{data_tuple}")

                logger.info(len(data))

                if len(data) != 7:
                    logger.info(
                        "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\nああああ\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")
                    logger.info(len(data))

                logger.info(micon_write_queues[micon_name].qsize())  # キューのサイズ

                if count_print % 1 == 0:  # 15回に1回実行
                    # self.get_logger().info(data.hex())
                    # self.get_logger().info(data2.hex())
                    logger.info(data.hex())
                    # logger.info(data2.hex())
                    pass
                count_print += 1

                try:
                    # logger.debug(location())
                    micon_dict[micon_name]["serial_obj"].write(bytes(data))
                    # logger.debug(location())
                    pass
                except Exception as e:
                    logger.critical(f"{micon_name}への送信に失敗: {e}")
                    micon_dict[micon_name]["is_connected"] = False
                    # TODO 片方のマイコンが途切れたときに、詰まるから、このやり方よくない 非同期にするか、connect_serialを並行処理でずっとwhileしといて、bool変数がTrueになったら接続処理するとか

            # time.sleep(0.015)  # DMA 0.002# DMA 0.01 #同期だと0.015が限界 0.01だめで0.02は大丈夫
            # DMA 0.002# DMA 0.01 #同期だと0.015が限界 0.01だめで0.02は大丈夫
            time.sleep(0.001)

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
        super().__init__('main')
        # self.publisher_ESP32_to_Webserver = self.create_publisher(
        #     String, 'ESP32_to_Webserver', 10)
        self.subscription = self.create_subscription(
            Float64MultiArray, 'serial_write', self.serial_write, 10)
        self.subscription  # prevent unused variable warning
        # TODO キューにいれる関数書くけど、ROSで自動でできるのか、並列処理でかかないといけないのか調べる

    def serial_write(self, received_float_array):
        global micon_write_queues
        micon_name = "ESP32"
        micon_write_queues[micon_name].put({"command_id": int(
            received_float_array.data[1]), "command_content": float(received_float_array.data[2])})
        # logger.debug(received_float_array.data);
        pass
# TODO 書き込みはrosのclass外で、回す　それぞれのマイコンに付き一つの関数で動かす


if __name__ == '__main__':
    main()
