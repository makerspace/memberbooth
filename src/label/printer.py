from typing import Tuple

from brother_ql.backends.helpers import send
from brother_ql.conversion import convert
from brother_ql.raster import BrotherQLRaster
import usb.core

from src.util.logger import get_logger

PRINTER_BACKEND = 'pyusb'
LABEL_TYPE = '62'

logger = get_logger()


def get_printer_config() -> Tuple[str, usb.core.Device]:
    usb_dev_brother_810w = usb.core.find(idVendor=0x04f9, idProduct=0x209b)
    if usb_dev_brother_810w:
        return "QL-810W", usb_dev_brother_810w

    usb_dev_brother_800 = usb.core.find(idVendor=0x04f9, idProduct=0x209c)
    if usb_dev_brother_800:
        return "QL-800", usb_dev_brother_800

    raise RuntimeError("No recognized printer is connected.")


def print_label(label):
    printer_model, printer = get_printer_config()
    print(printer_model, printer)
    qlr = BrotherQLRaster(printer_model)
    qlr = convert(qlr, [label], LABEL_TYPE)

    return send(instructions=qlr, printer_identifier=printer, backend_identifier=PRINTER_BACKEND, blocking=True)
