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

user_count = 0
reception_json = {}
last_received_time = None


@app.route('/')
def index():
    return render_template('sp.html')


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
def connect(json_data):
    global reception_json, last_received_time
    reception_json = json_data
    current_time = datetime.now()
    time_difference = current_time - last_received_time
    hertz = 1 / time_difference.total_seconds()
    print(f"{json_data} {hertz:.0f} Hz")
    last_received_time = current_time


def flask_socketio_run():
    print("flask_socketio_run起動", flush=True)
    cert_path = '/cert.pem'
    key_path = '/key.pem'
    socketio.run(app, host='0.0.0.0', port=5001, debug=True,
                 ssl_context=(cert_path, key_path), use_reloader=False)


def publish():
    global reception_json
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        try:
            sock.sendto(json.dumps(reception_json).encode(
                'utf-8'), ('127.0.0.1', 5010))
            print(json.dumps(reception_json).encode('utf-8'))
            time.sleep(0.002)

        except KeyboardInterrupt:
            print('closing socket')
            sock.close()
            print('done')
            break


if __name__ == '__main__':
    threading.Thread(target=flask_socketio_run).start()
    threading.Thread(target=publish).start()
