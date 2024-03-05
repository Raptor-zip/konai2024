from threading import Lock  # これ消していいよね？
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room, rooms, disconnect
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import Joy
from concurrent.futures import ThreadPoolExecutor  # threadPoolExecutor
import json
from flask import Flask, render_template, request  # Flaskを使うため
import logging  # Flaskのログを削除する
from engineio.payload import Payload
Payload.max_decode_packets = 10000

thread_lock = Lock()  # これ消していいよね？

# うけとったデータ
received_json = {"test": -1}

# ユーザー数
user_count = 0

reception_json = {
    "state": 0
}

# l = logging.getLogger()
# l.addHandler(logging.FileHandler("/dev/null"))
app = Flask(__name__,
            template_folder="../../../../../../src/konai2024_python/konai2024_python/flask/templates",
            static_folder="../../../../../../src/konai2024_python/konai2024_python/flask/static")  # Flaskが実行されるディレクトリがきもい
app.config['SECRET_KEY'] = 'secret!'

socketio = SocketIO(app, cors_allowed_origins='*')  # , async_mode='eventlet'


@socketio.event  # これ消していいよね?
def main():
    with ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(publish)
        future = executor.submit(flask_socketio_run)
        future.result()         # 全てのタスクが終了するまで待つ

##############################################################


def publish(args=None):
    rclpy.init(args=args)

    minimal_subscriber = MinimalSubscriber()

    rclpy.spin(minimal_subscriber)

    minimal_subscriber.destroy_node()
    rclpy.shutdown()


class MinimalSubscriber(Node):
    def __init__(self):
        print("Subscriber", flush=True)
        super().__init__('command_subscriber')
        self.publisher_Web_to_Main = self.create_publisher(
            String, 'Web_to_Main', 10)
        self.timer_0001 = self.create_timer(0.01, self.timer_callback_001)

        self.subscription = self.create_subscription(
            String,
            "ESP32_to_Webserver",
            self.listener_callback,
            10)
        # self.subscription = self.create_subscription(
        #     Joy,
        #     "joy1",
        #     self.joy1_listener_callback,
        #     10)
        # self.subscription = self.create_subscription(
        #     Joy,
        #     "joy2",
        #     self.joy2_listener_callback,
        #     10)
        self.subscription  # prevent unused variable warning

    def listener_callback(self, msg):
        global reception_json
        # print(msg.data, flush=True)
        try:
            reception_json = json.loads(msg.data)
            # print(reception_json, flush=True)
        except Exception as e:
            print(f'エラー: {e}', flush=True)

    def timer_callback_001(self):
        global received_json
        msg = String()
        msg.data = json.dumps(received_json)
        self.publisher_Web_to_Main.publish(msg)

    # def joy1_listener_callback(self, msg):
    #     print("女医北", flush=True)

    # def joy2_listener_callback(self, msg):
    #     print("女医北", flush=True)


#############################################################

def flask_socketio_run():
    print("flask_socketio_run起動", flush=True)
    # socketio.run(app, debug=True, host="0.0.0.0", port=5000use_reloader=False,  allow_unsafe_werkzeug=True)
    # 非同期処理に使用するライブラリの指定
    # `threading`, `eventlet`, `gevent`から選択可能
    # , threaded=Trueやると起動しない  async_mode="threading"
    socketio.run(app, host="0.0.0.0", port=5000)


@app.route("/")
def index():
    # data = Data(motor_1='190', motor_2=180, motor_3=100) # インスタンスの作成
    return render_template('index.html')  # インスタンスをテンプレートに渡す , gafa=data

# ユーザーが新しく接続すると実行


@socketio.on('connect')
def connect(auth):
    print("connctされた")
    global user_count
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


@socketio.on('json_request')
def json_request():
    global reception_json  # しなくていいの?
    print(reception_json, flush=True)
    emit('json_receive', reception_json)


@socketio.on("send_web_data")
def send_web_data(json):
    global received_json
    received_json = json


@socketio.on("my ping")
def ping():
    emit('my pong', {})


if __name__ == '__main__':
    main()
