from typing import Any, Tuple

from brother_ql.backends.helpers import send
from brother_ql.conversion import convert
from brother_ql.raster import BrotherQLRaster
from brother_ql.devicedependent import label_type_specs
from PIL import Image
import usb.core

from src.util.logger import get_logger

PRINTER_BACKEND = 'pyusb'
LABEL_TYPE = '62'

logger = get_logger()


class PrinterNotFoundError(RuntimeError):
    pass


def get_printer_config() -> Tuple[str, usb.core.Device]:
    usb_dev_brother_810w = usb.core.find(idVendor=0x04f9, idProduct=0x209b)
    if usb_dev_brother_810w:
        return "QL-810W", usb_dev_brother_810w

    usb_dev_brother_800 = usb.core.find(idVendor=0x04f9, idProduct=0x209c)
    if usb_dev_brother_800:
        return "QL-800", usb_dev_brother_800

    raise PrinterNotFoundError()


def print_label(label: Image.Image) -> dict[str, Any]:
    printer_model, printer = get_printer_config()
    print(printer_model, printer)
    qlr = BrotherQLRaster(printer_model)

    # The brother ql library has conversion functions, but they are not updated
    # to newer versions of pillow, so they will crash.
    # Therefore we resize the label ourselves to the correct width.
    dots_printable = label_type_specs[LABEL_TYPE]['dots_printable']
    if label.size[0] != dots_printable[0]:
        hsize = int((dots_printable[0] / label.size[0]) * label.size[1])
        label = label.resize((dots_printable[0], hsize), Image.LANCZOS)

    qlr = convert(qlr, [label], LABEL_TYPE)

    return send(instructions=qlr, printer_identifier=printer, backend_identifier=PRINTER_BACKEND, blocking=True)
