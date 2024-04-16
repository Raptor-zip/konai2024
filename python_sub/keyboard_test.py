from pynput import keyboard
import time


class MonKeyBoard:
    def on_press(self, key):
        print('press: {}'.format(key))
        # try:
        #     print('press: {}'.format(key.char))
        # except AttributeError:
        #     print('spkey press: {}'.format(key))

    def on_release(self, key):
        print('release: {}'.format(key))
        if (key == keyboard.Key.esc):
            print("StopKey")
            self.listener.stop()
            self.listener = None

    def start(self):
        self.listener = keyboard.Listener(
            on_press=self.on_press, on_release=self.on_release)
        self.listener.start()

    def getstatus(self):
        if (self.listener == None):
            return False
        return True


monitor = MonKeyBoard()
monitor.start()

while (True):
    time.sleep(1)
    # status = monitor.getstatus()
    # # print(str(status))
    # if (status == False):
    #     print("break")
    #     break
