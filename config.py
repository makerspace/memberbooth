from pathlib import Path

no_backend = False
no_printer = False

_DIR = Path(__file__).parent.absolute()
RESOURCES_PATH = _DIR.joinpath('src/resources/')
LOGOTYPE_PATH = str(RESOURCES_PATH.joinpath('sms_logotype_gui.png'))
SMS_LOGOTYPE_PATH = str(RESOURCES_PATH.joinpath('sms_logotype_label.png'))
FONT_PATH = str(RESOURCES_PATH.joinpath('BebasNeue-Regular.ttf'))
