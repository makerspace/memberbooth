from config import LIST_ARDUINO_SERIAL_DEVICES_PATH
from src.util.logger import get_logger
from .parser import ArgparseEnum
import subprocess
import serial
import re

logger = get_logger()

class InputMethods(ArgparseEnum):
    EM4100 = "EM4100"
    APTUS  = "Aptus-reader"
    KEYBOARD = "Keyboard"

class NoReaderFound(OSError):
    pass

class KeyReaderInitError(IOError):
    pass

class KeyReaderNeedsRebootError(IOError):
    pass

def abstract(fun):
    def abstract_wrapper(*args, **kwargs):
        raise NotImplementedError("This is only an abstract function")
    return abstract_wrapper

class KeyReader(object):
    @classmethod
    @abstract
    def get_devices(cls):
        pass

    @abstract
    def tag_was_read(self):
        return False

    def is_open(self):
        return True

    def close(self):
        pass

    @classmethod
    def get_reader(cls):
        key_readers = cls.get_devices()
        if len(key_readers) == 0:
            raise NoReaderFound()

        key_reader = key_readers[0]
        if len(key_readers) > 1:
            logger.warning(f"There are several key readers connected: {key_readers}. Chose {key_reader}")
        for kr in key_readers[1:]:
            kr.close()

        return key_reader

class EM4100(KeyReader):
    def __init__(self, serial_device):
        self.serial_device = serial_device
        logger.info(f"Connecting to serial port {serial_device}")

        # Arduino is restarted when serial port is opened
        try:
            self.com = serial.Serial(port=serial_device, baudrate=115200, timeout=2)
        except serial.serialutil.SerialException as e:
            raise KeyReaderNeedsRebootError("Serial port to key reader seems to have hanged. Perhaps unplug it and plug it in again. Reported error: " + str(e))
        com = self.com
        com.readline() # Just wait until it starts up and starts printing something (hopefully less than 2 second timeout)
        com.timeout = 0
        self.check_echo()
        self.last_tag_id = None

    def __repr__(self):
        return f"<EM4100 Key Reader tty={self.serial_device}>"

    def flush(self):
        self.com.reset_input_buffer()

    def is_open(self):
        try:
            test_com = serial.Serial(port=self.com.name, baudrate=self.com.baudrate, timeout=0)
            test_com.close()
            return self.com.isOpen()
        except (serial.SerialException, termios.error):
            return False

    def close(self):
        self.com.close()

    def tag_was_read(self):
        try:
            if self.com.in_waiting == 0:
                return False
        except OSError:
            raise KeyReaderNeedsRebootError("The key reader has been disconnected")
        lines = self.com.read(self.com.in_waiting).decode("utf-8").split("\r\n")
        complete_readouts = []
        for line in lines:
            match = re.match(r"^DECODED: MANCHESTER=(0x[a-fA-F0-9]{10})$", line)
            if match is not None:
                complete_readouts.append(match.group(1))
        if len(complete_readouts) == 0:
            return False
        self.last_tag_id = complete_readouts[-1]
        return True

    def get_aptus_tag_id(self):
        aptus_tag_number = int(self.last_tag_id, 16) % int(1e9)
        aptus_tag_id = f"{aptus_tag_number:09}"
        return aptus_tag_id

    def check_echo(self):
        com = self.com
        previous_timeout = com.timeout
        com.timeout = 0.2
        com.reset_input_buffer()
        com.write(b"?\n")
        com.flush()
        response = com.readline().decode("utf-8")
        if len(response) == 0:
            raise KeyReaderInitError("Got no identification reponse from reader")
        if not response.startswith("EM4100 Reader"):
            raise KeyReaderInitError("Wrong response from reader: " + str(response))
        else:
            logger.info(f"Key reader {self} responds")
        com.timeout = previous_timeout

    @classmethod
    def get_devices(cls):
        output = subprocess.check_output(LIST_ARDUINO_SERIAL_DEVICES_PATH).decode("utf-8")
        devices = [dev for dev in output.split("\n") if len(dev) > 0]
        key_readers = []
        for dev in devices:
            try:
                key_readers.append(cls(dev))
            except KeyReaderInitError as e:
                logger.info(f"Could not initialize {dev} as {cls}. {e}")

        return key_readers

class Aptus(KeyReader):
    @classmethod
    def get_devices(cls):
        return []

class Keyboard(KeyReader):
    @classmethod
    def get_devices(cls):
        return [Keyboard()]
