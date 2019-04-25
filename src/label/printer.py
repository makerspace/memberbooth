from brother_ql.backends.helpers import send
from brother_ql.conversion import convert
from brother_ql.raster import BrotherQLRaster
from logger import get_logger

PRINTER_MODEL = 'QL-810W'
PRINTER_BACKEND = 'pyusb'
PRINTER_URL = 'usb://0x04f9:0x209c'
LABEL_TYPE = '62'

logger = get_logger()

def print_label(label):

    qlr = BrotherQLRaster(PRINTER_MODEL)
    qlr = convert(qlr, [label], LABEL_TYPE)

    return send(instructions=qlr, printer_identifier=PRINTER_URL, backend_identifier=PRINTER_BACKEND, blocking=True)

