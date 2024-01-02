from flask import Flask, render_template, request
from flask_socketio import SocketIO, send, emit
import socket
import threading
import json
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

# cors_allowed_originは本来適切に設定するべき
socketio = SocketIO(app, cors_allowed_origins='*')

# ユーザー数
user_count = 0

reception_json = {}

@app.route('/')
def index():
    return render_template('sp.html')

# ユーザーが新しく接続すると実行
@socketio.on('connect')
def connect(auth):
    global user_count, text
    user_count += 1
    # 接続者数の更新（全員向け）
    emit('count_update', {'user_count': user_count}, broadcast=True)

# ユーザーの接続が切断すると実行
@socketio.on('disconnect')
def disconnect():
    global user_count
    user_count -= 1
    # 接続者数の更新（全員向け）
    emit('count_update', {'user_count': user_count}, broadcast=True)

@socketio.on('state')
def connect(json):
    global reception_json
    reception_json = json
    print(json)
    # print(json["raw_angle"])
    # print(json["sp_battery_level"])

def flask_socketio_run():
    print("flask_socketio_run起動", flush=True)
    cert_path = '/cert.pem'
    key_path = '/key.pem'
    socketio.run(app,host='0.0.0.0', port=5001, debug=True,ssl_context=(cert_path, key_path),use_reloader=False)

def publish():
    global reception_json
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(json.dumps(reception_json).encode('utf-8'), ('127.0.0.1', 5002))
            # print(reception_json)
            # print(json.dumps(reception_json))
            time.sleep(0.002)

        except KeyboardInterrupt:
            print('closing socket')
            sock.close()
            print('done')
            break

if __name__ == '__main__':
    threading.Thread(target=flask_socketio_run).start()
    threading.Thread(target=publish).start()

