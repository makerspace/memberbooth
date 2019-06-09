from config import LIST_ARDUINO_SERIAL_DEVICES_PATH
from src.util.logger import get_logger
import subprocess
import serial

logger = get_logger()

class NoReaderFound(Exception):
    pass

class KeyReader(object):
    @classmethod
    def get_devices(cls):
        raise NotImplemented("This is only and abstract function")

    @classmethod
    def get_reader(cls):
        key_readers = cls.get_devices()
        if len(key_readers) == 0:
            raise NoReaderFound()

        key_reader = key_readers[0]
        if len(key_readers) > 1:
            logger.warning(f"There are several key readers connected: {key_readers}. Choose {key_reader}")

class EM4100_KeyReader(KeyReader):
    def __init__(self, serial_device):
        self.serial_device = serial_device
        logger.info(f"Connecting to serial port {serial_device}")

        # Arduino is restarted when serial port is opened
        self.com = serial.Serial(port=serial_device, baudrate=115200, timeout=2)
        com = self.com
        com.readline() # Just wait until it starts up and starts printing something (hopefully less than 2 second timeout)
        com.timeout = 0
        self.check_echo()

    def __repr__(self):
        return f"<EM4100 Key Reader tty={self.serial_device}>"

    def check_echo(self):
        com = self.com
        previous_timeout = com.timeout
        com.timeout = 0.2
        com.reset_input_buffer()
        com.write(b"?\n")
        com.flush()
        response = com.readline().decode("utf-8")
        if not response.startswith("EM4100 Reader"):
            logger.error("Response: " + str(response))
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
            except Exception as e:
                logger.exception(e)

        return key_readers
