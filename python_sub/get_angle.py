from flask import Flask, render_template, request
from flask_socketio import SocketIO, send, emit
import socket
import threading
import json
import time
from engineio.payload import Payload
from datetime import datetime

Payload.max_decode_packets = 1000

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

socketio = SocketIO(app, cors_allowed_origins='*')

user_count: int = 0
reception_json: dict = {}
last_received_time: datetime

@app.route('/')
def got_index():
    return render_template('index.html')

@app.route('/angle_sp')
def got_angle_sp():
    return render_template('angle_sp.html')

@app.route('/control_sp')
def got_control_sp():
    return render_template('control_sp.html')

# ipadとかのwebrtc繋がずに、websocketだけで見るバージョンも作る？!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

@app.route('/pc') # angleとcontrol両方とも受信する
def got_pc():
    return render_template('pc.html')

@socketio.on('connect')
def connect(auth):
    global user_count, last_received_time
    user_count += 1
    emit('count_update', {'user_count': user_count}, broadcast=True)
    last_received_time = datetime.now()


@socketio.on('disconnect')
def disconnect():
    global user_count
    user_count -= 1
    emit('count_update', {'user_count': user_count}, broadcast=True)


@socketio.on('state')
def state(json_data):
    global reception_json, last_received_time
    reception_json = json_data
    current_time: datetime = datetime.now()
    time_difference = current_time - last_received_time
    hertz = 1 / time_difference.total_seconds()
    print(f"{json_data} {hertz:.0f} Hz")
    last_received_time = current_time


@socketio.on("angle_sp_localSDP")
def sp_localSDP(received_localSDP_str):
    print(f"angle_sp SDP受信:{received_localSDP_str}")
    emit("send_angle_sp_localSDP", {
         "sp_localSDP":  received_localSDP_str}, broadcast=True)

@socketio.on("control_sp_localSDP")
def sp_localSDP(received_localSDP_str):
    print(f"control_sp SDP受信:{received_localSDP_str}")
    emit("send_control_sp_localSDP", {
         "sp_localSDP":  received_localSDP_str}, broadcast=True)

@socketio.on("angle_pc_localSDP")
def angle_pc_localSDP(received_localSDP_str):
    print(f"angle_pc SDP受信:{received_localSDP_str}")
    emit("send_angle_pc_localSDP", {
         "pc_localSDP":  received_localSDP_str}, broadcast=True)

@socketio.on("control_pc_localSDP")
def control_pc_localSDP(received_localSDP_str):
    print(f"control_pc SDP受信:{received_localSDP_str}")
    emit("send_control_pc_localSDP", {
         "pc_localSDP":  received_localSDP_str}, broadcast=True)


def flask_socketio_run():
    print("flask_socketio_run起動", flush=True)
    cert_path = '/cert.pem'
    key_path = '/key.pem'
    socketio.run(app, host='0.0.0.0', port=5001, debug=True,
                 ssl_context=(cert_path, key_path), use_reloader=False)
    # socketio.run(app, host='0.0.0.0', port=5001, debug=False, use_reloader=False)


def send_udp_to_main():
    global reception_json
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        try:
            sock.sendto(json.dumps(reception_json).encode(
                'utf-8'), ('127.0.0.1', 5010)) # 角度データのみを送信
            # print(json.dumps(reception_json).encode('utf-8'))
            time.sleep(0.02)

        except KeyboardInterrupt:
            print('closing socket')
            sock.close()
            print('done')
            break

def receive_udp_from_main():
    # UDPソケットの作成
    received_udp_from_main = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    received_udp_from_main.bind(('127.0.0.1', 5002))
    received_udp_from_main.settimeout(1.0)  # タイムアウトを1秒に設定
    while True:
        try:
            message, cli_addr = received_udp_from_main.recvfrom(1024)
            # print(f"Received: {message.decode('utf-8')}")
            received_json_temp:str = message.decode('utf-8')
            socketio.emit("send_control_data", received_json_temp, namespace='/')
            # デコードエラーの処理もつける？？！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！
        except Exception as e:
            print(
                f"main からの受信に失敗: {e}")

def receive_udp_from_webrtc():
    # UDPソケットの作成
    received_udp_from_webrtc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    received_udp_from_webrtc.bind(('127.0.0.1', 5005))
    received_udp_from_webrtc.settimeout(1.0)  # タイムアウトを1秒に設定
    while True:
        try:
            message, cli_addr = received_udp_from_webrtc.recvfrom(1024)
            # print(f"Received: {message.decode('utf-8')}")
            received_json_temp:str = message.decode('utf-8')
            # webrtcで生成したlocal?SDP
            socketio.emit("send_control_pc_localSDP", received_json_temp, namespace='/')
            # デコードエラーの処理もつける？？！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！
        except Exception as e:
            print(
                f"webrtc からの受信に失敗: {e}")

if __name__ == '__main__':
    threading.Thread(target=flask_socketio_run).start()
    threading.Thread(target=send_udp_to_main).start()
    threading.Thread(target=receive_udp_from_webrtc).start()
    threading.Thread(target=receive_udp_from_main).start()

