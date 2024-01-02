from flask import Flask, render_template, request # Flaskを使うため
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room, rooms, disconnect
# ユーザー数
user_count = 0
# 現在のテキスト
text = ""
serial_reception_text = [""]
img_str = "data:image/jpeg;base64だよ"

# webbrowser.open(url, 0)# デフォルトブラウザでWebサイトを新しいタブで開く
app = Flask(__name__)
            # template_folder="../../../../../../src/experiment_python/experiment_python/flask/templates",
            # static_folder="../../../../../../src/experiment_python/experiment_python/flask/static") #Flaskが実行されるディレクトリがきもい
app.config['SECRET_KEY'] = 'secret!'

# cors_allowed_originは本来適切に設定するべき
# socketio = SocketIO(app, cors_allowed_origins='*')
socketio = SocketIO(app, cors_allowed_origins='*') # , async_mode='eventlet'


@socketio.event
def image_ud():
    global img_str
    try:
        emit('image_update', {'image': img_str}, broadcast=True)
        emit('count_update', {'user_count': 20}, broadcast=True)
    except Exception as e:
        print(f"67エラー:{e}", flush=True)

def main():
    print("flask_socketio_run起動", flush=True)
    # socketio.run(app, debug=True, host="0.0.0.0", port=5000use_reloader=False,  allow_unsafe_werkzeug=True)
    # 非同期処理に使用するライブラリの指定
    # `threading`, `eventlet`, `gevent`から選択可能
    # socketio.run(app, host="0.0.0.0", port=5000,) # , threaded=Trueやると起動しない  async_mode="threading"
    socketio.run(app, host='192.168.10.68', port=5000, ssl_context=('/cert.pem', '/key.pem'), ) # , threaded=Trueやると起動しない  async_mode="threading"


    # スレッドを格納するためのグローバル変数


class Data: # クラスを作成する
    def __init__(self, motor_1, motor_2, motor_3):
        self.motor_1 = motor_1
        self.motor_2 = motor_2
        self.motor_3 = motor_3

@app.route("/")
def index():
    data = Data(motor_1='190', motor_2=180, motor_3=100) # インスタンスの作成
    return render_template('index.html', gafa=data) # インスタンスをテンプレートに渡す

# ユーザーが新しく接続すると実行
@socketio.on('connect')
def connect(auth):
    print("connctされた")
    global user_count, text, img_str
    user_count += 1
    # 接続者数の更新（全員向け）
    emit('count_update', {'user_count': user_count}, broadcast=True)
    image_ud()
    # テキストエリアの更新
    # emit('text_update', {'text': text})/


# ユーザーの接続が切断すると実行
@socketio.on('disconnect')
def disconnect():
    global user_count
    user_count -= 1
    # 接続者数の更新（全員向け）
    emit('count_update', {'user_count': user_count}, broadcast=True)
    image_ud()

@socketio.on("my ping")
def ping():
    emit('my pong', {}, broadcast=True)


# テキストエリアが変更されたときに実行
@socketio.on('text_update_request')
def text_update_request(json):
    global text
    text = json["text"]
    # 変更をリクエストした人以外に向けて送信する
    # 全員向けに送信すると入力の途中でテキストエリアが変更されて日本語入力がうまくできない
    emit('text_update', {'text': text}, broadcast=True, include_self=False)
    image_ud()

# subscribeしたデータに合わせてflaskを更新する
# @app.route("/stream_call_from_ajax", methods = ["POST"])
# def streamcallfromajax():
#     global serial_reception_text
#     global img_str

#     if request.method == "POST":
#         # ここにPythonの処理を書く
#         try:
#             message = serial_reception_text
#             # message = "aiueo"
#         except Exception as e:
#             message = str(e)
#         dict = {
#             # "data": message,
#             "image": img_str
#                 }

        # いるかわからないけど
        # スマホが何台か増えたときに負担が増えすぎるから困る
        # serialCommand = f"{{'motor1':{{'speed':{global_value}}}}}+\n"
        # ser.write(serialCommand.encode())

    # return json.dumps(dict)             # 辞書をJSONにして返す]


if __name__ == '__main__':
    main()