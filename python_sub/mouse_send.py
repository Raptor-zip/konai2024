import evdev
import socket

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # デバイス名がLogitech G PRO Gaming Mouseのときのdevice.pathをevdev.InputDeviceにぶち込む
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    device_path: str = None
    # デバイス一のリストを検査する
    for device in devices:
        # print(device.path, device.name, device.phys)
        if device.name == "Logitech G PRO Gaming Mouse":
            print(device.path)
            device_path = device.path
    if device_path:
        device = evdev.InputDevice(device_path)
        # イベントが来たら、ポート5020にUDP送信 x軸のイベントが来たら-1,0で、y軸のイベントが来たら0,2とか
        for event in device.read_loop():
            if event.type == evdev.ecodes.EV_REL:
                if event.code == evdev.ecodes.REL_X:
                    data = ','.join([str(event.value * -1), '0']).encode('utf-8')
                    sock.sendto(data, ('127.0.0.1', 5020))
                    print(data)

                elif event.code == evdev.ecodes.REL_Y:
                    data = ','.join(['0', str(event.value)]).encode('utf-8')
                    sock.sendto(data, ('127.0.0.1', 5020))
                    print(data)
    else:
        print("エラー  Logitech G PRO Gaming Mouseを検出できませんでした")


if __name__ == "__main__":
    main()
