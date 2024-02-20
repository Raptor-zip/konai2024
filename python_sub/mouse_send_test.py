import socket
import time
import random

while True:
    random_x = random.randint(-10, 100)
    random_y = random.randint(-10, 100)
    data = f"{random_x},{random_y}".encode('utf-8')
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as test_sock:
        print(data)
        test_sock.sendto(data, ('127.0.0.1', 5020))
        time.sleep(0.01)  # データが処理されるのを待つ