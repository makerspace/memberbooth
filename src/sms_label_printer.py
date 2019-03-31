#!/usr/bin/env python3.7

from brother_ql.backends.helpers import send
from brother_ql.conversion import convert
from brother_ql.raster import BrotherQLRaster
from logging import getLogger

PRINTER_MODEL = 'QL-810W'
PRINTER_BACKEND = 'pyusb'
PRINTER_URL = 'usb://0x04f9:0x209c'
LABEL_TYPE = '62'

logger = getLogger('memberbooth') 

def print_label(label):

    qlr = BrotherQLRaster(PRINTER_MODEL)
    qlr = convert(qlr, [label], LABEL_TYPE)

    status = send(instructions=qlr, printer_identifier=PRINTER_URL, backend_identifier=PRINTER_BACKEND, blocking=True)

    if status['did_print']:
        return True
    else:
        logger.error(f'Printer error, status = {status}')
        return False 
