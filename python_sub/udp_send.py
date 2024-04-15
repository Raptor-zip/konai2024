from socket import socket, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_BROADCAST

HOST = ''
PORT = 5123
ADDRESS = "192.168.168.255"  # 自分に送信
ADDRESS = "192.168.3.255"  # 自分に送信

# s = socket(AF_INET, SOCK_DGRAM)

# ブロードキャストする場合は、ADDRESSをブロードキャスト用に設定して、以下のコメントを外す
s = socket(AF_INET, SOCK_DGRAM)
s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
s.bind((HOST, PORT))

while True:
    msg = input("> ")
    # 送信
    s.sendto(msg.encode(), (ADDRESS, PORT))

s.close()
