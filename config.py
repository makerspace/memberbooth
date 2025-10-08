from pathlib import Path

# Program flags
no_printer: bool = False
no_backend: bool = False
development: bool = False

# Common init values of argument parsers
makeradmin_token_filename: str = ".makeradmin_token"
slack_token_filename: str = ".slack_token"
slack_timeout: int = 10
logger_name: str = 'memberbooth'
maker_admin_base_url: str = 'https://api.makerspace.se'

# Nice to have constants
_DIR = Path(__file__).parent.absolute()
RESOURCES_PATH = _DIR.joinpath('resources/')
LOGOTYPE_PATH = str(RESOURCES_PATH.joinpath('sms_logotype_gui.png'))
SMS_LOGOTYPE_PATH = str(RESOURCES_PATH.joinpath('sms_logotype_label.png'))
FLAMMABLE_ICON_PATH = str(RESOURCES_PATH.joinpath('flammable_icon.png'))
ROTATING_ICON_PATH = str(RESOURCES_PATH.joinpath('rotating_icon.png'))
FONT_PATH = str(RESOURCES_PATH.joinpath('BebasNeue-Regular.ttf'))
LIST_ARDUINO_SERIAL_DEVICES_PATH = str(_DIR.joinpath("list_arduino_serial_devices.sh"))
