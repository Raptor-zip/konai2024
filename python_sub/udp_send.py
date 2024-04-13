from socket import socket, AF_INET, SOCK_DGRAM

HOST = ''
PORT = 5000
ADDRESS = "127.0.0.1"  # 自分に送信

s = socket(AF_INET, SOCK_DGRAM)
# ブロードキャストする場合は、ADDRESSを
# ブロードキャスト用に設定して、以下のコメントを外す
# s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

while True:
    msg = input("> ")
    # 送信
    s.sendto(msg.encode(), (ADDRESS, PORT))

s.close()
