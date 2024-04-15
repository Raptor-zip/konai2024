import pyudev

# USBデバイスの物理パスを設定
usb_device_path = "/devices/pci0000:00/0000:00:08.1/0000:04:00.3/usb1/1-4/1-4:1.1"
usb_device_path = "/devices/pci0000:00/0000:00:08.1/0000:04:00.3/usb1/1-3/1-3:1.3"

# pyudevコンテキストを作成
context = pyudev.Context()

# デバイスオブジェクトを取得
# usb_device = context.device_by_path(usb_device_path)
usb_device = context.device_path()

# USBバス情報を取得
usb_bus_info = usb_device.attributes.asstring('busnum')
print("USB Bus Number:", usb_bus_info)

# USBホストコントローラのインデックスを取得
usb_host_index = usb_device.attributes.asstring('devnum')
print("USB Host Controller Index:", usb_host_index)

# USBポートの識別子を取得
usb_port_id = usb_device.attributes.asstring('devpath')
print("USB Port Identifier:", usb_port_id)
