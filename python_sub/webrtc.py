import argparse
import asyncio
import logging
import time
import aioconsole  # Added for asynchronous console input
import socket  # UDP localhostで
import threading

from aiortc import RTCIceCandidate, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.signaling import BYE, add_signaling_arguments, create_signaling


got_sdp: str = ""


def channel_log(channel, t, message):
    print("channel(%s) %s %s" % (channel.label, t, message))


# データチャネルを介してメッセージを送信するための関数。
def channel_send(channel, message):
    channel_log(channel, ">", message)
    channel.send(message)

# シグナリングを受信し、RTCSessionDescription や RTCIceCandidate を処理するための非同期関数。


async def consume_signaling(pc, signaling):
    global got_sdp
    while True:
        # while len(got_sdp) < 2:
        #     await asyncio.sleep(1)

        #     # 予め定義されたstr変数からRTCSessionDescriptionオブジェクトを取得する例
        #     # ここではdummy_dataという変数に予め定義されたデータを使用しています

        # dummy_data: str = "v=0\r\no=- 3918648610 3918648610 IN IP4 0.0.0.0\r\ns=-\r\nt=0 0\r\na=group:BUNDLE 0\r\na=msid-semantic:WMS *\r\nm=application 51316 DTLS/SCTP 5000\r\nc=IN IP4 192.168.229.68\r\na=mid:0\r\na=sctpmap:5000 webrtc-datachannel 65535\r\na=max-message-size:65536\r\na=candidate:a163705e00d9330ae8de17c9be20477e 1 udp 2130706431 192.168.229.68 51316 typ host\r\na=candidate:580b5f32035da7f14a30ea7a8d826c67 1 udp 2130706431 172.17.0.1 36489 typ host\r\na=candidate:d3134823d160adfc9a8a8f9c89d14550 1 udp 1694498815 133.106.222.116 51316 typ srflx raddr 192.168.229.68 rport 51316\r\na=candidate:0ad8db753210ce9554cf251a9e51e792 1 udp 1694498815 133.106.222.116 36489 typ srflx raddr 172.17.0.1 rport 36489\r\na=end-of-candidates\r\na=ice-ufrag:Jk3h\r\na=ice-pwd:4UYEkRHxeFWXtF0dGoxQry\r\na=fingerprint:sha-256 A9:2E:5D:38:7B:23:D7:BB:D3:BC:83:A0:C7:BE:82:D9:27:1C:7C:50:C2:1C:0A:A4:1C:A3:BD:51:78:9F:F8:D8\r\na=setup:actpass\r\n"

        # dummy_data = got_sdp

        # # dummy_dataを使用してRTCSessionDescriptionオブジェクトを作成する
        # obj = RTCSessionDescription(sdp=dummy_data, type='offer')

        obj = await signaling.receive()  # signalingから受信したオブジェクトを待機します。
        # これがconsoleの入力だわ

        if isinstance(obj, RTCSessionDescription):  # 受信したオブジェクトがRTCSessionDescriptionの場合
            await pc.setRemoteDescription(obj)  # pcのリモート記述を設定

            if obj.type == "offer":
                # send answer
                # "offer"の場合は"answer"を作成
                await pc.setLocalDescription(await pc.createAnswer())
                await signaling.send(pc.localDescription)  # 送信
        # 受信したオブジェクトがRTCIceCandidateの場合、pcにIceCandidateを追加します。
        elif isinstance(obj, RTCIceCandidate):
            await pc.addIceCandidate(obj)
        elif obj is BYE:
            print("Exiting")
            break

# answer の役割を担当し、リモートパーティーによって作成されたデータチャネルを処理する非同期関数。


async def run_answer(pc, signaling):
    await signaling.connect()

    @pc.on("datachannel")
    def on_datachannel(channel):
        channel_log(channel, "-", "created by remote party")

        @channel.on("message")
        def on_message(message):
            # Modified to print received messages
            print("Received message:", message)

    await consume_signaling(pc, signaling)

# offer の役割を担当し、ローカルパーティーによって作成されたデータチャネルを処理し、offer を送信する非同期関数。


async def run_offer(pc, signaling):
    await signaling.connect()  # シグナリングを確立するために、シグナリングサーバーとの接続を確立します。

    # offer 側でデータチャネルを作成し、"chat" というラベルを持つデータチャネルを作成します。
    channel = pc.createDataChannel("chat")
    # データチャネルが offer 側によって作成されたことをログに記録します。
    channel_log(channel, "-", "created by local party")

    async def send_input():  # ユーザーからの入力を待ち受け、入力されたメッセージをデータチャネルを介して送信する非同期関数を定義します。
        while True:
            message = await aioconsole.ainput("Message: ")
            channel_send(channel, message)

    # データチャネルが開かれたときに実行されるイベントハンドラを定義します。send_input() 関数を非同期で実行します。
    @channel.on("open")
    def on_open():
        asyncio.ensure_future(send_input())

    # データチャネルからメッセージを受信したときに実行されるイベントハンドラを定義します。ただし、このコードではメッセージを受信した際の処理がコメントアウトされています。
    @channel.on("message")
    def on_message(message):
        pass
        channel_log(channel, "<", message)
        # get_angleからのデータを取得できた
        # UDPでmainに渡す
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(message.encode(
            'utf-8'), ('127.0.0.1', 5007))  # 角度データのみを送信

    # ローカルのセッション記述を作成し、offer を生成します。
    await pc.setLocalDescription(await pc.createOffer())

    # await signaling.send(pc.localDescription) # 作成した offer をシグナリングサーバーを介して送信します。

    temp = pc.localDescription
    await signaling.send(temp)  # 作成した offer をシグナリングサーバーを介して送信します。

    print("korekita")
    print(temp.sdp)
    # 変にjson化しないで、そのままwebsocketする
    print("korekita")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(temp.sdp.encode(
        'utf-8'), ('127.0.0.1', 5005))  # 角度データのみを送信

    sock.sendto(temp.sdp.encode(
        'utf-8'), ('192.168.229.80', 5005))  # 角度データのみを送信

    # ＃＃＃＃＃＃＃＃＃＃＃＃＃＃＃＃＃＃＃＃＃＃＃＃＃＃＃＃＃ユーザーの出力を待つやつかな？？
    # シグナリングを介して受信した情報を処理するための非同期関数 consume_signaling を実行します。
    await consume_signaling(pc, signaling)


def webrtc():
    # argparse を使用してコマンドライン引数を処理し、"role" と "--verbose" の引数を受け入れます。
    parser = argparse.ArgumentParser(description="Data channels ping/pong")
    parser.add_argument("role", choices=["offer", "answer"])
    parser.add_argument("--verbose", "-v", action="count")
    # add_signaling_arguments(parser) 関数を呼び出して、シグナリングに関する引数を追加します。
    add_signaling_arguments(parser)

    args = parser.parse_args()  # パースされた引数を取得し、verbose フラグが設定されている場合はデバッグレベルのログを有効にします。

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    # create_signaling(args) を使用してシグナリングを作成し、RTCPeerConnection オブジェクトを作成します。
    signaling = create_signaling(args)
    pc = RTCPeerConnection()
    # print(args.role)
    if args.role == "offer":
        # run_offer(pc, signaling) 関数を呼び出して、offer の役割での処理を開始します。
        coro = run_offer(pc, signaling)
    else:
        coro = run_answer(pc, signaling)

    # # run event loop
    # 最後に、イベントループを実行して通信を確立し、キーボード割り込みが発生した場合には graceful に終了処理を行います。
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(coro)
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(pc.close())
        loop.run_until_complete(signaling.close())


def receive_udp_from_main():
    # UDPソケットの作成
    received_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    received_udp.bind(('127.0.0.1', 5006))
    received_udp.settimeout(1.0)  # タイムアウトを1秒に設定
    while True:
        try:
            message, cli_addr = received_udp.recvfrom(1024)
            # print(f"Received: {message.decode('utf-8')}")
            received_json_temp: str = message.decode('utf-8')
            # socketio.emit("send_control_data", received_json_temp, namespace='/')
            # デコードエラーの処理もつける？？！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！
        except Exception as e:
            print(
                f"main からの受信に失敗: {e}")


def receive_udp_from_get_angle():
    global got_sdp
    # UDPソケットの作成
    received_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    received_udp.bind(('127.0.0.1', 5004))
    received_udp.settimeout(1.0)  # タイムアウトを1秒に設定
    while True:
        try:
            message, cli_addr = received_udp.recvfrom(1024)
            print(f"Received: {message.decode('utf-8')}")
            received_json_temp: str = message.decode('utf-8')
            got_sdp = received_json_temp
            # socketio.emit("send_control_data", received_json_temp, namespace='/')
            # デコードエラーの処理もつける？？！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！
        except Exception as e:
            pass
            # print(
            #     f"get_angle からの受信に失敗: {e}")


if __name__ == "__main__":
    # threading.Thread(target=receive_udp_from_main).start()
    threading.Thread(target=receive_udp_from_get_angle).start()

    # asyncio.run(receive_udp())

    asyncio.run(webrtc())
    # threading.Thread(target=webrtc).start()
