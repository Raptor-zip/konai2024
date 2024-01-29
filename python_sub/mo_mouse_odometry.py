import evdev
import matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor
import socket

DEVICE_PATH = "/dev/input/event3"  # Specify your device path here
MAX_ARRAY_LENGTH = 500  # Maximum length for x_coords and y_coords arrays

x_coords, y_coords = [], []


def main():
    with ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(mouse)
        # future = executor.submit(graph)
        # future.result()


def graph():
    global x_coords
    global y_coords
    fig, ax = plt.subplots()

    while True:
        ax.clear()
        ax.scatter(x_coords, y_coords, s=5, color='black')
        ax.plot(x_coords, y_coords, color='red', linewidth=2)
        ax.set_aspect('equal', adjustable='box')
        plt.pause(0.01)


def mouse():
    global x_coords
    global y_coords

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    for device in devices:
        print(device.path, device.name, device.phys)

    device = evdev.InputDevice(DEVICE_PATH)

    for event in device.read_loop():
        if event.type == evdev.ecodes.EV_REL:
            if event.code == evdev.ecodes.REL_X:
                x_coords.append(
                    x_coords[-1] + event.value) if x_coords else x_coords.append(event.value)
                y_coords.append(
                    y_coords[-1]) if y_coords else y_coords.append(0)

                data = ','.join([str(event.value * -1), '0']).encode('utf-8')
                sock.sendto(data, ('127.0.0.1', 5020))
                print(data)

            elif event.code == evdev.ecodes.REL_Y:
                x_coords.append(
                    x_coords[-1]) if x_coords else x_coords.append(0)
                y_coords.append(
                    y_coords[-1] - event.value) if y_coords else y_coords.append(event.value)

                data = ','.join(['0', str(event.value)]).encode('utf-8')
                sock.sendto(data, ('127.0.0.1', 5020))
                print(data)

            if len(x_coords) > MAX_ARRAY_LENGTH:
                x_coords.pop(0)
            if len(y_coords) > MAX_ARRAY_LENGTH:
                y_coords.pop(0)


if __name__ == "__main__":
    main()
