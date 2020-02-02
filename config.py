from pathlib import Path

no_backend = False
no_printer = False
development = False
token_path = "ramdisk/.token"

_DIR = Path(__file__).parent.absolute()
RESOURCES_PATH = _DIR.joinpath('resources/')
LOGOTYPE_PATH = str(RESOURCES_PATH.joinpath('sms_logotype_gui.png'))
SMS_LOGOTYPE_PATH = str(RESOURCES_PATH.joinpath('sms_logotype_label.png'))
FONT_PATH = str(RESOURCES_PATH.joinpath('BebasNeue-Regular.ttf'))
LIST_ARDUINO_SERIAL_DEVICES_PATH = str(_DIR.joinpath("list_arduino_serial_devices.sh"))
