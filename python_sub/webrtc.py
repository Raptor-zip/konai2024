import argparse
import asyncio
import logging
import time
import aioconsole  # Added for asynchronous console input

from aiortc import RTCIceCandidate, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.signaling import BYE, add_signaling_arguments, create_signaling


def channel_log(channel, t, message):
    print("channel(%s) %s %s" % (channel.label, t, message))


# データチャネルを介してメッセージを送信するための関数。
def channel_send(channel, message):
    channel_log(channel, ">", message)
    channel.send(message)

# シグナリングを受信し、RTCSessionDescription や RTCIceCandidate を処理するための非同期関数。
async def consume_signaling(pc, signaling):
    while True:
        obj = await signaling.receive()

        if isinstance(obj, RTCSessionDescription):
            await pc.setRemoteDescription(obj)

            if obj.type == "offer":
                # send answer
                await pc.setLocalDescription(await pc.createAnswer())
                await signaling.send(pc.localDescription)
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
            print("Received message:", message)  # Modified to print received messages

    await consume_signaling(pc, signaling)

# offer の役割を担当し、ローカルパーティーによって作成されたデータチャネルを処理し、offer を送信する非同期関数。
async def run_offer(pc, signaling):
    await signaling.connect() #シグナリングを確立するために、シグナリングサーバーとの接続を確立します。

    channel = pc.createDataChannel("chat") #offer 側でデータチャネルを作成し、"chat" というラベルを持つデータチャネルを作成します。
    channel_log(channel, "-", "created by local party") #データチャネルが offer 側によって作成されたことをログに記録します。

    async def send_input(): # ユーザーからの入力を待ち受け、入力されたメッセージをデータチャネルを介して送信する非同期関数を定義します。
        while True:
            message = await aioconsole.ainput("Message: ")
            channel_send(channel, message)

    @channel.on("open") # データチャネルが開かれたときに実行されるイベントハンドラを定義します。send_input() 関数を非同期で実行します。
    def on_open():
        asyncio.ensure_future(send_input())

    @channel.on("message") # データチャネルからメッセージを受信したときに実行されるイベントハンドラを定義します。ただし、このコードではメッセージを受信した際の処理がコメントアウトされています。
    def on_message(message):
        pass
        # channel_log(channel, "<", message)

    await pc.setLocalDescription(await pc.createOffer()) # ローカルのセッション記述を作成し、offer を生成します。
    await signaling.send(pc.localDescription) # 作成した offer をシグナリングサーバーを介して送信します。

    await consume_signaling(pc, signaling) # シグナリングを介して受信した情報を処理するための非同期関数 consume_signaling を実行します。


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Data channels ping/pong") # argparse を使用してコマンドライン引数を処理し、"role" と "--verbose" の引数を受け入れます。
    parser.add_argument("role", choices=["offer", "answer"])
    parser.add_argument("--verbose", "-v", action="count")
    add_signaling_arguments(parser) # add_signaling_arguments(parser) 関数を呼び出して、シグナリングに関する引数を追加します。

    args = parser.parse_args() # パースされた引数を取得し、verbose フラグが設定されている場合はデバッグレベルのログを有効にします。

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    signaling = create_signaling(args) # create_signaling(args) を使用してシグナリングを作成し、RTCPeerConnection オブジェクトを作成します。
    pc = RTCPeerConnection()
    # print(args.role)
    if args.role == "offer":
        coro = run_offer(pc, signaling) # run_offer(pc, signaling) 関数を呼び出して、offer の役割での処理を開始します。
    else:
        coro = run_answer(pc, signaling)

    # # run event loop
    loop = asyncio.get_event_loop() # 最後に、イベントループを実行して通信を確立し、キーボード割り込みが発生した場合には graceful に終了処理を行います。
    try:
        loop.run_until_complete(coro)
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(pc.close())
        loop.run_until_complete(signaling.close())