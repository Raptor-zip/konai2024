import inspect  # 実行中のぎょうすう取得
import os
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
import serial
import ipget  # IPアドレス取得用
import socket  # UDP通信用
import asyncio  # 非同期関数を実行するため
import math
import evdev
from matplotlib import pyplot as plt  # 描画用ライブラリ
# import matplotlib
# matplotlib.use('agg')


class sensors:
    distance_sensors: list[int] = [-1, -1, -1, -1]
    limit_switch: bool = False


reception_json: dict = {
    "raw_angle": 0
}


class controller:
    joy0: dict = {}

    def convert_PS3_to_WiiU(self, joy_before: dict) -> dict:
        joy_after: dict = {"buttons": joy_before["buttons"],
                           "axes": [joy_before["axes"][0], joy_before["axes"][1], joy_before["axes"][3], joy_before["axes"][4]]}
        return joy_after

    def convert_PS4_to_WiiU(self, joy_before: dict):
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

    def convert_PS4_other_to_WiiU(self, joy_before: dict):
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

        if joy_before["axes"][6] < 0:
            joy_after["buttons"][15] = 0
            joy_after["buttons"][16] = 1
        elif joy_before["axes"][6] > 0:
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


micon_dict: dict[str, dict] = {
    "ESP32_1": {"is_connected": False,  # パソコンと接続しているか
                "number": 1,  # マイコンからデータ来るときに
                "serial_id": None,
                "serial_obj": None,
                "reboot": False},
    "ESP32_2": {"is_connected": False,  # パソコンと接続しているか
                "number": 2,  # マイコンからデータ来るときに やっぱ消す！！！！！！！！！！！！！！！！！！！！！！！！！！
                "serial_id": None,
                "serial_obj": None,
                "reboot": False}}

# これ、クラスの中のほうが良くない？！！！！！！！！！！！！！！！！！！！！！！！！
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

# stateには 以下のものが入る dictにはstrが入る send_ESPにはintが入る
# -1:エラー 以下のものではない
# 0:normal
# 1:low
# 2:much_low
# 3:not_exit
# 4:abnormality
# 5:undefined

accuracy_angle: int = 0

# マウス受信用
mouse_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
mouse_udp_socket.bind(('127.0.0.1', 5020))  # 本当は5002
mouse_udp_socket.settimeout(1.0)  # タイムアウトを1秒に設定

try:
    result = subprocess.check_output(
        ['iwgetid', '-r'], universal_newlines=True)
    wifi_ssid = result.strip()
    # wifi_ssid= bytes(result.strip(), 'utf-8').decode('unicode-escape')
except subprocess.CalledProcessError:
    wifi_ssid = "エラー"


def main():
    with ThreadPoolExecutor(max_workers=6) as executor:
        # executor.submit(sp_udp_reception)
        # executor.submit(receive_udp_webserver)
        executor.submit(receive_udp_webrtc)
        # executor.submit(battery_alert)
        executor.submit(recept_serial)
        executor.submit(recept_serial_2)
        executor.submit(connect_serial)
        # executor.submit(odometry)
        # executor.submit(graph)
        future = executor.submit(ros)
        future.result()         # 全てのタスクが終了するまで待つ


MAX_ARRAY_LENGTH = 1000  # Maximum length for x_coords and y_coords arrays

coordinates: list[list[float]] = [[0, 1], [0, 1]]


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

            x_lateset = coordinates[0][-1] - x_new
            y_lateset = coordinates[1][-1] - y_new

            # 本当はintにしてから代入したい！！！！！！！！！！！！！！！！!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            coordinates[0].append(coordinates[0][-1] - x_new)
            coordinates[1].append(coordinates[1][-1] - y_new)
            # print(coordinates, flush=True)

            if len(coordinates[0]) > MAX_ARRAY_LENGTH:
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


def connect_serial():
    global micon_dict
    while True:
        for micon_name, micon_values in micon_dict.items():
            if micon_values["is_connected"] == False:
                i = 0
                print(f"{micon_name}とシリアル接続を試行", flush=True)
                while i > -1:
                    if micon_values["serial_id"] != None:
                        micon_values["serial_id"] = None
                    exclude_list: list[int] = []

                    for each_micon_dict_values in micon_dict.values():  # micon_dictの各値に対して #なんかきもいねまたmicon_dict参照してるのアホらしい
                        # if each_micon_dict["serial_obj"].in_waiting > 0:
                        #     exclude_list.append(each_micon_dict["serial_id"])

                        try:
                            # ポートがnoneじゃないか確認 絶対もっといい書き方ある！！
                            # なるべく短い文字を送って送信テスト。readlineにするとESP32側がloopで送信しないといけないし、しないにしてもtimeoutまで待たないといけないから不適切
                            each_micon_dict_values["serial_obj"].write(
                                "a".encode())
                            exclude_list.append(
                                each_micon_dict_values["serial_id"])
                        except AttributeError as e:  # 'NoneType' object has no attribute 'readline' このエラーのみを補足するようにして
                            # print(f"ポートがnoneのときに出るエラー。無視して次のポートを試行する:{e}", flush=True)
                            pass
                        except Exception as e:
                            # print(f"書き込みがバグるときに出るエラー。マイコンは存在する:{e}", flush=True)
                            exclude_list.append(
                                each_micon_dict_values["serial_id"])
                            pass

                    if i in exclude_list:
                        i += 1  # iが除外リストに含まれている場合、iをインクリメントする
                    try:
                        subprocess.run(
                            f"sudo -S chmod 777 /dev/ttyUSB{i}".split(), input=("robocon471" + '\n').encode())
                        try:
                            micon_values["serial_obj"] = serial.Serial(
                                f'/dev/ttyUSB{i}', 921600, timeout=1)
                            micon_values["serial_id"] = i
                            print(
                                f"{micon_name}とSerial接続成功 /dev/ttyUSB{i}", flush=True)
                            micon_values["is_connected"] = True
                            i = -1  # Serialが正常に開かれた場合はループを抜ける
                        except Exception as e:
                            print(
                                f"\n\n{micon_name}とSerial接続失敗: {e} \n\n", flush=True)
                            if i < 2:
                                i += 1  # 例外が発生した場合もiをインクリメントして次のポートを試す
                            else:
                                i = 0
                    except Exception as e:
                        print(
                            f"\n\n{micon_name}とSerial接続試行時 /dev/ttyUSB{i} の権限追加に失敗 {e} \n\n", flush=True)

                    time.sleep(0.1)  # 0.2秒待って再試行
        time.sleep(0.1)  # 無駄にCPUを使わないようにする


def location(depth=0):
    frame = inspect.currentframe().f_back
    return os.path.basename(frame.f_code.co_filename), frame.f_code.co_name, frame.f_lineno


def recept_serial():
    global micon_dict, serial_reception_text, battery_dict

    # 自動的にstr、int、floatに変換する 動的型付けになっているので安全ではない
    def convert_value(value):
        if value.isdigit():  # 整数値の場合
            return int(value)
        try:
            return float(value)  # 浮動小数点数の場合
        except ValueError:
            return value  # その他の場合は文字列として返す

    while True:
        each_micon_dict_key = "ESP32_1"
        each_micon_dict_values = micon_dict["ESP32_1"]
        try:
            received_message: str = each_micon_dict_values["serial_obj"].readline(
            ).decode('utf-8')[:-2]  # \r\nを消す
            print(
                f"\n                                                {each_micon_dict_key}から:{received_message}\n", flush=True)
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
                    battery_dict["battery_4cell"]["voltage_history"].insert(
                        0, received_message_array[2])  # listの先頭にボルト追加
                    # 先頭から7個以降を削除 だいたい2秒の平均
                    battery_dict["battery_4cell"]["voltage_history"] = battery_dict["battery_4cell"]["voltage_history"][:6]

                elif received_message_array[1] == 3:  # 3セルバッテリー
                    battery_dict["battery_3cell"]["voltage_history"].insert(
                        0, received_message_array[2])  # listの先頭にボルト追加
                    # 先頭から7個以降を削除 だいたい2秒の平均
                    battery_dict["battery_3cell"]["voltage_history"] = battery_dict["battery_3cell"]["voltage_history"][:6]

                # 距離センサーのデータが来たときの処理
                elif received_message_array[1] == 4:
                    sensors.distance_sensors = [
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
                elif received_message_array[1] == 7:
                    sensors.limit_switch = bool(received_message_array[2])

            else:
                # デバッグ用メッセージ
                # print(
                #     f"\n                                       {each_micon_dict_key}から!:{received_message}\n", flush=True)
                pass

        except UnicodeDecodeError as e:
            print(f"{each_micon_dict_key}から受信時のデコードエラー:{e}", flush=True)
        except Exception as e:
            # print(f"{each_micon_dict_key}への接続失敗 読み取り試行時:{e}", flush=True)
            # each_micon_dict_values["is_connected"] = False
            pass
        # バッテリー保護
        # どこでこれを動作させるべきか考える！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！
        if battery_dict != {}:
            for each_battery in battery_dict.values():
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

        # serial_reception_text.insert(0, line)
        # if len(serial_reception_text) > 100:
        #     del serial_reception_text[-1]
        time.sleep(0.002)  # これないとCPU使用率が増える


def recept_serial_2():
    global micon_dict, serial_reception_text, battery_dict

    # 自動的にstr、int、floatに変換する 動的型付けになっているので安全ではない
    def convert_value(value):
        if value.isdigit():  # 整数値の場合
            return int(value)
        try:
            return float(value)  # 浮動小数点数の場合
        except ValueError:
            return value  # その他の場合は文字列として返す

    while True:
        each_micon_dict_key = "ESP32_2"
        each_micon_dict_values = micon_dict["ESP32_2"]
        try:
            received_message: str = each_micon_dict_values["serial_obj"].readline(
            ).decode('utf-8')[:-2]  # \r\nを消す
            print(
                f"\n                                                {each_micon_dict_key}から:{received_message}\n", flush=True)
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
                    battery_dict["battery_4cell"]["voltage_history"].insert(
                        0, received_message_array[2])  # listの先頭にボルト追加
                    # 先頭から7個以降を削除 だいたい2秒の平均
                    battery_dict["battery_4cell"]["voltage_history"] = battery_dict["battery_4cell"]["voltage_history"][:6]

                elif received_message_array[1] == 3:  # 3セルバッテリー
                    battery_dict["battery_3cell"]["voltage_history"].insert(
                        0, received_message_array[2])  # listの先頭にボルト追加
                    # 先頭から7個以降を削除 だいたい2秒の平均
                    battery_dict["battery_3cell"]["voltage_history"] = battery_dict["battery_3cell"]["voltage_history"][:6]

                # 距離センサーのデータが来たときの処理
                elif received_message_array[1] == 4:
                    sensors.distance_sensors = [
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
                elif received_message_array[1] == 7:
                    sensors.limit_switch = bool(received_message_array[2])

            else:
                # デバッグ用メッセージ
                # print(
                #     f"\n                                       {each_micon_dict_key}から!:{received_message}\n", flush=True)
                pass

        except UnicodeDecodeError as e:
            print(f"{each_micon_dict_key}から受信時のデコードエラー:{e}", flush=True)
        except Exception as e:
            # print(f"{each_micon_dict_key}への接続失敗 読み取り試行時:{e}", flush=True)
            # each_micon_dict_values["is_connected"] = False
            pass
        # バッテリー保護
        # どこでこれを動作させるべきか考える！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！
        if battery_dict != {}:
            for each_battery in battery_dict.values():
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

        # serial_reception_text.insert(0, line)
        # if len(serial_reception_text) > 100:
        #     del serial_reception_text[-1]
        time.sleep(0.002)  # これないとCPU使用率が増える

# def sp_udp_reception():
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


def receive_udp_webserver():
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


def receive_udp_webrtc():
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
            reception_json.update({"raw_angle": int(reception_json_temp)})
            print(reception_json, flush=True)
        except Exception as e:
            print(
                f"\n\n\n\n\n\n\n    webrtc からの受信に失敗: {e}\n\n\n\n\n\n\n", flush=True)


def battery_alert():
    global battery_dict
    while True:
        for each_battery_dict_key, each_battery_dict_value in battery_dict.items():
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


def ros(args=None):
    rclpy.init(args=args)

    minimal_subscriber = MinimalSubscriber()

    rclpy.spin(minimal_subscriber)

    minimal_subscriber.destroy_node()
    rclpy.shutdown()


class MinimalSubscriber(Node):
    state: int = 0
    DCmotor_speed: list[int] = [0, 0, 0, 0, 0, 0]  # 原則% 符号あり
    BLmotor_speed: list[int] = [0, 0]  # 射出用ダクテッドファンと仰角調整用GM6020
    servo_angle: int = 0
    is_run_ducted_fan: bool = False
    is_slow_speed: bool = False

    time_pushed_load_button: int = 0  # 装填ボタンが押された時間

    # Initialize PID parameters dict型にしたい！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！
    kp: float = 0.01  # Proportional gain 基本要素として必須。これをベースに、必要に応じて他の項を追加する
    ki: float = 0  # Integral gain 出力が目標値に留まるのを邪魔する、何らかの作用がシステムに働く場合に追加する
    kd: float = 0  # Derivative gain システムに振動を抑制する要素が十分にない場合に追加する

    prev_error = 0  # Initialize previous error for derivative term
    integral: float = 0  # Initialize integral term

    angle_adjust: int = 0
    current_angle: int = 0
    angle_control_count: int = 0

    low_3cell_battery_voltage: bool = False
    much_low_3cell_voltage: bool = False
    low_4cell_battery_voltage: bool = False
    much_low_4cell_voltage: bool = False

    angle_when_turn: list = []
    time_when_turn: list = []

    joy_now: dict = {}
    joy_past: dict = {}

    joy0_stick1_angle: float = 0
    joy0_stick1_distance: float = 0

    start_time: float = 0  # 試合開始時刻(ホームボタン押下時の時刻)
    turn_start_time: float = 0

    count_print: int = 0

    send_ESP32_data: str = ""

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
        self.timer_0016 = self.create_timer(0.016, self.timer_callback_0033)

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
        global wifi_ssid, battery_dict, micon_dict

        temp_micon_dict: dict = {"ESP32_1": {
            "is_connected": micon_dict["ESP32_1"]["is_connected"],
            "serial_id": micon_dict["ESP32_1"]["serial_id"]
        },
            "ESP32_2": {
            "is_connected": micon_dict["ESP32_2"]["is_connected"],
            "serial_id": micon_dict["ESP32_2"]["serial_id"]
        }, }

        # temp_micon_dict:dict = micon_dict
        # print(temp_micon_dict["ESP32_1"],flush=True)
        # print(temp_micon_dict["ESP32_1"]["serial_obj"],flush=True)
        # print(temp_micon_dict["ESP32_1"]["serial_obj"].port,flush=True)
        # temp_micon_dict["ESP32_1"].pop("serial_obj")
        # temp_micon_dict["ESP32_2"].pop("serial_obj")

        try:
            _ubuntu_ip:str = ipget.ipget().ipaddr("wlp2s0")
        except ValueError as e:
            _ubuntu_ip:str = "WiFiエラー"

        msg = String()
        send_json: dict = {
            "state": self.state,
            "ubuntu_ssid": wifi_ssid,
            "ubuntu_ip": _ubuntu_ip,
            # "ubuntu_ip": "aiueo",
            # "battery_voltage": battery_dict["average_voltage"],
            # "battery_voltage": 6,
            "battery": battery_dict,
            "limited_switch": sensors.limit_switch,
            # "micon":micon_dict,
            "micon": temp_micon_dict,
            "wifi_signal_strength": 0,  # wifiのウブンツの強度を読み取る
            "DCmotor_speed": [int(speed) for speed in self.DCmotor_speed],
            "BLmotor_speed": [int(speed) for speed in self.BLmotor_speed],
            "servo_angle": int(self.servo_angle),
            "angle_value": self.current_angle,
            "start_time": self.start_time,
            "joy": self.joy_now,
            "serial_str": self.send_ESP32_data
        }
        msg.data = json.dumps(send_json)  # エンコード
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(json.dumps(msg.data).encode(
            'utf-8'), ('127.0.0.1', 5002))
        # print(json.dumps(reception_json).encode('utf-8'))
        self.publisher_ESP32_to_Webserver.publish(msg)

    def timer_callback_001(self):
        global reception_json, accuracy_angle, micon_dict, battery_dict
        self.current_angle = reception_json["raw_angle"] + \
            self.angle_adjust
        if self.current_angle < 0:
            self.current_angle = 360 + self.current_angle

        # print(reception_json["raw_angle"],self.angle_adjust,self.current_angle,flush=True)

        accuracy_angle = self.current_angle

        turn_minus1to1: float = 0

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

        if "joy0" in self.joy_now:
            # 手動旋回と自動旋回を合わせる
            turn_minus1to1 += self.joy_now["joy0"]["axes"][0]
        else:
            print(f"joy0の読み取りに失敗", flush=True)

        self.DCmotor_speed[:4] = [
            turn_minus1to1 * 255 * -1,
            turn_minus1to1 * 255,
            turn_minus1to1 * 255 * -1,
            turn_minus1to1 * 255]

        # 制御関数の呼び出し
        front_left, front_right, rear_left, rear_right = self.control_mecanum_wheels(
            self.joy0_stick1_angle, self.joy0_stick1_distance)  # 0から1の範囲で指定（北を0、南を0.5として時計回りに）

        # 旋回と合わせる
        self.DCmotor_speed[:4] = [speed + value for speed, value in zip(
            self.DCmotor_speed[:4], [front_left, front_right, rear_left, rear_right])]

        # 255を超えた場合、比率を保ったまま255以下にする
        max_motor_speed = max(map(abs, self.DCmotor_speed[:4]))
        if max_motor_speed > 255:
            self.DCmotor_speed[:4] = [int(speed * 255 / max_motor_speed)
                                      for speed in self.DCmotor_speed[:4]]

        self.DCmotor_speed[3] = max(
            min(255, self.DCmotor_speed[3] * 1.5), -255)

        #   装填サーボの処理
        if self.time_pushed_load_button != 0 and int(time.time() * 1000) - self.time_pushed_load_button > 700:
            # 1500msで0°に戻る
            self.servo_angle = 0
            self.time_pushed_load_button = 0

        # 回収機構のリミットスイッチの処理
        # リミットスイッチが押されているかつ、巻き取る方向に動かそうとしているならモーター停止。リミットスイッチが押されていても、展開方向に動かそうとすることはできる
        if sensors.limit_switch and self.DCmotor_speed[4] > 0:
            self.DCmotor_speed[4] = 0

        # 低速モードの処理
        if self.is_slow_speed:
            self.DCmotor_speed[:4] = [int(speed * 0.3)
                                      for speed in self.DCmotor_speed[:4]]

        # モータースピードが絶対値16未満の値を削除 (ジョイコンの戻りが悪いときでもブレーキを利かすため)
        self.DCmotor_speed = [
            0 if abs(i) < 16 else i for i in self.DCmotor_speed]

        # バッテリー保護
        if "battery_4cell" in battery_dict:
            if battery_dict["battery_4cell"]["state"] == "much_low" or battery_dict["battery_4cell"]["state"] == "abnormality":
                # 4セルで動かすものは メカナムと回収機構
                self.DCmotor_speed = [0] * len(self.DCmotor_speed)
        if "battery_3cell" in battery_dict:
            if battery_dict["battery_3cell"]["state"] == "much_low" or battery_dict["battery_3cell"]["state"] == "abnormality":
                # 3セルで動かすものは ブラシレスモーター
                self.is_run_ducted_fan = False  # リレーを非通電状態に
                self.BLmotor_speed = [0] * len(self.BLmotor_speed)
                print(
                    "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n", flush=True)

        self.send_ESP32_data: list[int] = [
            int(self.state),  # 0 状態
            int(self.DCmotor_speed[0]),  # 1 メカナム
            int(self.DCmotor_speed[1]),  # 2 メカナム
            int(self.DCmotor_speed[2]),  # 3 メカナム
            int(self.DCmotor_speed[3]),  # 4 メカナム
            int(self.DCmotor_speed[4]),  # 5 回収装填
            int(self.DCmotor_speed[5]),  # 6 回収装填
            int(self.BLmotor_speed[0]),  # 7 ダクテッドファン
            int(self.BLmotor_speed[1]),  # 8 ダクテッドファン2
            int(self.servo_angle),  # 9 サーボ
            # 10 ダクテッドファンのリレー 0 or 1
            int(convert_to_binary(self.is_run_ducted_fan)),
            # 11 ESP32_1を再起動するか 0 or 1
            int(convert_to_binary(micon_dict["ESP32_1"]["reboot"])),
            # 12 ESP32_2を再起動するか 0 or 1
            int(convert_to_binary(micon_dict["ESP32_2"]["reboot"])),
            # 13 4セルリポバッテリーのstate
            int(convert_battery_state_to_binary(
                battery_dict["battery_4cell"]["state"])),
            # 14 3セルリポバッテリーのstate
            int(convert_battery_state_to_binary(
                battery_dict["battery_3cell"]["state"])),
        ]

        micon_dict["ESP32_1"]["reboot"] = False
        micon_dict["ESP32_2"]["reboot"] = False

        # データの作成
        target_angle = 32768  # ターゲット角度 (0～65535)
        target_velocity = 16384  # 目標角速度 (0～65535)
        Kp = 24576  # Kp (0～65535)
        Kd = 40960  # Kd (0～65535)

        # データをバイト列にパック
        data = target_angle.to_bytes(2, byteorder='big') + \
            target_velocity.to_bytes(2, byteorder='big') + \
            Kp.to_bytes(2, byteorder='big') + \
            Kd.to_bytes(2, byteorder='big')

        print(data,flush=True)

        json_str: str = ','.join(map(str, self.send_ESP32_data)) + "\n"
        if self.count_print % 15 == 0:  # 15回に1回実行
            print(self.send_ESP32_data, flush=True)
            pass
        self.count_print += 1
        for each_micon_dict_key, each_micon_dict_values in micon_dict.items():
            try:
                each_micon_dict_values["serial_obj"].write(
                    json_str.encode())
                # print(f"{each_micon_dict_key}への送信成功", flush=True)
            except Exception as e:
                # print(
                #     f"{each_micon_dict_key}への送信に失敗: {e}", flush=True)
                each_micon_dict_values["is_connected"] = False
                # 片方のマイコンが途切れたときに、詰まるから、このやり方よくない 非同期にするか、connect_serialを並行処理でずっとwhileしといて、bool変数がTrueになったら接続処理するとか

    def joy0_listener_callback(self, joy):
        global reception_json, coordinates, exclude_list, micon_dict
        self.joy_now.update({  # 上書きOK
            "joy0":
            {"axes": list(joy.axes),
             "buttons": list(joy.buttons)}
        })
        if len(self.joy_now["joy0"]["axes"]) == 6 and len(self.joy_now["joy0"]["buttons"]) == 17:
            self.joy_now["joy0"] = controller.convert_PS3_to_WiiU(
                self, self.joy_now["joy0"])
        elif len(self.joy_now["joy0"]["axes"]) == 6 and len(self.joy_now["joy0"]["buttons"]) == 16:
            self.joy_now["joy0"] = controller.convert_PS4_to_WiiU(
                self, self.joy_now["joy0"])
        elif len(self.joy_now["joy0"]["axes"]) == 8 and len(self.joy_now["joy0"]["buttons"]) == 13:
            self.joy_now["joy0"] = controller.convert_PS4_other_to_WiiU(
                self, self.joy_now["joy0"])
        # 旋回が逆になるから無理やり合わせる
        self.joy_now["joy0"]["axes"][0] = self.joy_now["joy0"]["axes"][0] * -1
        # 各axesが0.3未満の場合に0に設定する
        for i in range(len(self.joy_now["joy0"]["axes"])):
            if abs(self.joy_now["joy0"]["axes"][i]) < 0.3:
                self.joy_now["joy0"]["axes"][i] = 0
        self.joy_past.setdefault(  # 初回のみ実行 上書き不可
            "joy0",
            {"axes": [0] * len(joy.axes), "buttons": [0] * len(joy.buttons)}
        )

        self.joy0_stick1_angle = (
            1 - (math.atan2(self.joy_now["joy0"]["axes"][2], self.joy_now["joy0"]["axes"][3])) / (2 * math.pi)) % 1

        self.joy0_stick1_distance = min(math.sqrt(
            self.joy_now["joy0"]["axes"][2]**2 + self.joy_now["joy0"]["axes"][3]**2), 1)  # ジョイスティックの傾きの大きさを求める(最大1最小0) # これよりも、割る1.4141356のほうがよくね？

        # Bボタン
        if self.joy_past["joy0"]["buttons"][0] == 0 and self.joy_now["joy0"]["buttons"][0] == 1:
            self.BLmotor_speed[0] = 1100

        # Aボタン
        if self.joy_past["joy0"]["buttons"][1] == 0 and self.joy_now["joy0"]["buttons"][1] == 1:
            self.BLmotor_speed[0] = 1500

        if self.joy_now["joy0"]["buttons"][2] == 1:  # Xボタン
            # 0°に旋回
            self.state = 1
            self.turn_start_time = time.time()
            self.angle_when_turn = []
            self.time_when_turn = []
            self.angle_control_count = 0
        # if self.joy_now["joy0"]["buttons"][1] == 1:  # Aボタン
        #     # 90°に旋回
        #     self.state = 2
        #     self.turn_start_time = time.time()
        #     self.angle_when_turn = []
        #     self.time_when_turn = []
        #     self.angle_control_count = 0
        # if self.joy_now["joy0"]["buttons"][0] == 1:  # Bボタン
        #     # 180°に旋回
        #     self.state = 3
        #     self.turn_start_time = time.time()
        #     self.angle_when_turn = []
        #     self.time_when_turn = []
        #     self.angle_control_count = 0
        if self.joy_now["joy0"]["buttons"][3] == 1:  # Yボタン
            # 270°に旋回
            self.state = 4
            self.turn_start_time = time.time()
            self.angle_when_turn = []
            self.time_when_turn = []
            self.angle_control_count = 0

        # Rボタン
        if self.joy_now["joy0"]["buttons"][4] == 1:
            # 走行補助強制停止
            self.state = 0
            self.DCmotor_speed = [0] * len(self.DCmotor_speed)
            self.BLmotor_speed = [0] * len(self.BLmotor_speed)

        # Lボタン
        if self.joy_now["joy0"]["buttons"][5] == 1:
            # 低速モード
            self.is_slow_speed = True
        else:
            self.is_slow_speed = False

        # ダクテッドのリレー
        # ZL
        if self.joy_past["joy0"]["buttons"][6] == 0 and self.joy_now["joy0"]["buttons"][6] == 1:
            if self.is_run_ducted_fan == True:
                self.is_run_ducted_fan = False
            else:
                self.is_run_ducted_fan = True

        # サーボの制御
        # self.servo_angle = int(self.joy_now["joy0"]["axes"][1]*174)
        # ZR装填 サーボ初期位置
        if self.joy_now["joy0"]["buttons"][7] == 1:
            self.time_pushed_load_button = int(time.time() * 1000)  # エポックミリ秒
            self.servo_angle = 45

        if self.joy_now["joy0"]["buttons"][8] == 1:
            micon_dict = {
                "ESP32_1": {"is_connected": False,  # パソコンと接続しているか
                            "number": 1,  # マイコンからデータ来るときに
                            "serial_id": None,
                            "serial_obj": None,
                            "reboot": False},
                "ESP32_2": {"is_connected": False,  # パソコンと接続しているか
                            "number": 2,  # マイコンからデータ来るときに やっぱ消す！！！！！！！！！！！！！！！！！！！！！！！！！！
                            "serial_id": None,
                            "serial_obj": None,
                            "reboot": False}}

        # リセット
        # + / options
        if self.joy_now["joy0"]["buttons"][9] == 1:
            # if self.joy_now["joy0"]["buttons"][4] == 1 and self.joy_now["joy0"]["buttons"][5] == 1:
            # 角度リセット
            if reception_json["raw_angle"] < 0:
                # マイナスのとき
                self.angle_adjust = - 180 - reception_json["raw_angle"]
            else:
                self.angle_adjust = -1 * reception_json["raw_angle"]
            # 座標リセット
                coordinates = [[1, 1], [2, 2]]

        if self.joy_past["joy0"]["buttons"][10] == 0 and self.joy_now["joy0"]["buttons"][10] == 1:  # PS/homeボタン
            # タイマースタート
            self.start_time = time.time()

        # ダクテッドファン
        if self.joy_now["joy0"]["buttons"][13] == 1 and self.joy_past["joy0"]["buttons"][13] == 0:
            # ↑
            self.BLmotor_speed[0] = max(
                1000, min(1500, self.BLmotor_speed[0] + 10))
        elif self.joy_now["joy0"]["buttons"][14] == 1 and self.joy_past["joy0"]["buttons"][14] == 0:
            # ↓
            self.BLmotor_speed[0] = min(
                1500, max(1000, self.BLmotor_speed[0] - 10))

        # 回収モーター
        # if self.joy_now["joy0"]["buttons"][15] == 1:
        #     # 左ジョイスティック 回収機構 展開
        #     self.DCmotor_speed[4] = -255
        # elif self.joy_now["joy0"]["buttons"][16] == 1:
        #     # 右ジョイスティック 回収機構 巻取り
        #     self.DCmotor_speed[4] = 255
        # else:
        #     self.DCmotor_speed[4] = 0

        if self.joy_past["joy0"]["buttons"][11] == 0 and self.joy_now["joy0"]["buttons"][11] == 1:
            # ESP32_1のソフトウェアリセット
            micon_dict["ESP32_1"]["reboot"] = True
            # 送信後に False に戻す

        if self.joy_past["joy0"]["buttons"][12] == 0 and self.joy_now["joy0"]["buttons"][12] == 1:
            # ESP32_2のソフトウェアリセット
            micon_dict["ESP32_2"]["reboot"] = True
            # 送信後に False に戻す

        self.joy_past["joy0"] = self.joy_now["joy0"]

    def joy1_listener_callback(self, joy):
        global reception_json, coordinates, exclude_list, micon_dict
        self.joy_now.update({  # 上書きOK
            "joy1":
            {"axes": list(joy.axes),
             "buttons": list(joy.buttons)}
        })
        if len(self.joy_now["joy1"]["axes"]) == 6 and len(self.joy_now["joy1"]["buttons"]) == 17:
            self.joy_now["joy1"] = controller.convert_PS3_to_WiiU(
                self, self.joy_now["joy1"])
        elif len(self.joy_now["joy1"]["axes"]) == 6 and len(self.joy_now["joy1"]["buttons"]) == 16:
            self.joy_now["joy1"] = controller.convert_PS4_to_WiiU(
                self, self.joy_now["joy1"])
        elif len(self.joy_now["joy1"]["axes"]) == 8 and len(self.joy_now["joy1"]["buttons"]) == 13:
            self.joy_now["joy1"] = controller.convert_PS4_other_to_WiiU(
                self, self.joy_now["joy1"])
        # 旋回が逆になるから無理やり合わせる
        self.joy_now["joy1"]["axes"][0] = self.joy_now["joy1"]["axes"][0] * -1
        # 各axesが0.3未満の場合に0に設定する
        for i in range(len(self.joy_now["joy1"]["axes"])):
            if abs(self.joy_now["joy1"]["axes"][i]) < 0.3:
                self.joy_now["joy1"]["axes"][i] = 0
        self.joy_past.setdefault(  # 初回のみ実行 上書き不可
            "joy1",
            {"axes": [0] * len(joy.axes), "buttons": [0] * len(joy.buttons)}
        )

        # サーボの制御
        # R装填 サーボ初期位置
        if self.joy_now["joy1"]["buttons"][5] == 1:
            self.time_pushed_load_button = int(time.time() * 1000)  # エポックミリ秒
            self.servo_angle = 45

        # ダクテッドファン
        # if self.joy_now["joy1"]["buttons"][13] == 1 and self.joy_past["joy1"]["buttons"][13] == 0:
        #     # ↑
        #     self.BLmotor_speed[0] = max(1000,min(1500,self.BLmotor_speed[0] + 10))
        # elif self.joy_now["joy1"]["buttons"][14] == 1 and self.joy_past["joy1"]["buttons"][14] == 0:
        #     # ↓
        #     self.BLmotor_speed[0] = min(1500,max(1000,self.BLmotor_speed[0] - 10))

        # 回収モーター
        if self.joy_now["joy1"]["buttons"][15] == 1:
            # 左ジョイスティック 回収機構 展開
            self.DCmotor_speed[4] = -255
        elif self.joy_now["joy1"]["buttons"][16] == 1:
            # 右ジョイスティック 回収機構 巻取り
            self.DCmotor_speed[4] = 255
        else:
            self.DCmotor_speed[4] = 0

        if self.joy_past["joy1"]["buttons"][10] == 0 and self.joy_now["joy1"]["buttons"][10] == 1:  # PS/homeボタン
            # タイマースタート
            self.start_time = time.time()

        self.joy_past["joy1"] = self.joy_now["joy1"]

    def control_mecanum_wheels(self, direction, speed) -> list[int]:
        # ラジアンに変換
        angle: float = direction * 2.0 * math.pi

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

    def turn(self, target_angle: float) -> float:
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
            temp = 0
        else:
            #  PID制御する
            error = angle_difference
            self.integral += error
            # 微分項の計算
            derivative = error - self.prev_error

            # PID制御出力の計算
            temp = self.kp * error + self.ki * self.integral + self.kd * derivative

            print("                                     ",
                  self.kp, self.ki, self.kd, flush=True)

            # 制御出力が -1 から 1 の範囲に収まるようにクリップ
            temp = max(min(temp, 1), -1)

            # 更新
            self.prev_error = error

        return temp

    def straight(self, target_angle):

        if self.current_distance > self.straight_distance_to_wall:
            distance = self.current_distance * self.straight_P_gain
            if distance > self.normal_max_motor_speed:
                distance = self.normal_max_motor_speed

            distance_1 = distance - self.axes_3
            if distance_1 > 255:
                distance_1 = 255
            self.motor1_speed = distance_1

            distance_2 = distance - self.axes_1
            if distance_2 > 255:
                distance_2 = 255
            self.motor2_speed = distance_2

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

            # print(angle_difference,flush=True)

            if abs(angle_difference) > 2:  # 単位:° パラメーター調整必要
                # 壁と平行じゃないなら
                if angle_difference > 0:
                    # 右に傾いているなら
                    self.motor1_speed = self.motor1_speed - angle_difference * \
                        self.straight_turn_P_gain
                else:
                    # 左に傾いているなら
                    self.motor2_speed = self.motor2_speed + \
                        angle_difference * self.straight_turn_P_gain

                if self.motor1_speed > 255:
                    self.motor1_speed = 255
                elif self.motor1_speed < -1 * 255:
                    self.motor1_speed = -1 * 255
                if self.motor2_speed > 255:
                    self.motor2_speed = 255
                elif self.motor2_speed < -1 * 255:
                    self.motor2_speed = -1 * 255
        else:
            self.motor1_speed = 0
            self.motor2_speed = 0
            self.state = 0


def convert_to_binary(boolean_value: bool) -> int:
    if boolean_value:
        return 1
    else:
        return 0


def convert_battery_state_to_binary(battery_state_str: str) -> int:
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
        print("エラー battery_stateが既定のものではない", flush=True)
        return -1


if __name__ == '__main__':
    main()
