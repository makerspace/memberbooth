from pathlib import Path

# Program flags
no_printer = False
development = False

# Common init values of argument parsers
ramdisk_path = 'ramdisk'
makeradmin_token_filename = ".makeradmin_token"
slack_token_filename = ".slack_token"
logger_name = 'memberbooth'
maker_admin_base_url = 'https://api.makerspace.se'

# Nice to have constants
_DIR = Path(__file__).parent.absolute()
RESOURCES_PATH = _DIR.joinpath('resources/')
LOGOTYPE_PATH = str(RESOURCES_PATH.joinpath('sms_logotype_gui.png'))
SMS_LOGOTYPE_PATH = str(RESOURCES_PATH.joinpath('sms_logotype_label.png'))
FLAMMABLE_ICON_PATH = str(RESOURCES_PATH.joinpath('flammable_icon.png'))
ERROR_REPORT_TEMPLATE_PATH = str(RESOURCES_PATH.joinpath('error_report_template.png'))
FONT_PATH = str(RESOURCES_PATH.joinpath('BebasNeue-Regular.ttf'))
LIST_ARDUINO_SERIAL_DEVICES_PATH = str(_DIR.joinpath("list_arduino_serial_devices.sh"))
