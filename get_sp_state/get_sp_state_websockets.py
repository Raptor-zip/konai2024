from flask import Flask, render_template, request
import socket
import threading
import json
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
# ユーザー数
user_count = 0

reception_json = {}


@app.route('/')
def index():
    return render_template('index.html')


@app.route("/stream", methods=["POST"])
def streamcallfromajax():
    inputData = request.json
    # print(inputData)
    print(inputData['raw_angle'])

    # p = request
    # print(p, flush=True)

    if request.method == "POST":
        # ここにPythonの処理を書く
        dict = {
            "data": "aiueoookk"
        }

    return json.dumps(dict)             # 辞書をJSONにして返す]


def flask_socketio_run():
    print("flask_socketio_run起動", flush=True)
    cert_path = '/cert.pem'
    key_path = '/key.pem'
    app.run(host='0.0.0.0', debug=True, port=5001,
            ssl_context=(cert_path, key_path), use_reloader=False)
    # socketio.run(app, host='0.0.0.0', port=5001, debug=True,
    #              ssl_context=(cert_path, key_path), use_reloader=False)


def publish():
    global reception_json
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(json.dumps(reception_json).encode(
                'utf-8'), ('127.0.0.1', 5002))
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
