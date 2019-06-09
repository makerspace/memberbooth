from config import LIST_ARDUINO_SERIAL_DEVICES_PATH
from src.util.logger import get_logger
import subprocess
import serial

logger = get_logger()

class KeyReader(object):
    @classmethod
    def get_devices(cls):
        raise NotImplemented("This is only and abstract function")

    @classmethod
    def get_reader(cls):
        key_readers = cls.get_devices()
        if len(key_readers) == 0:
            logger.error("There are no key readers connected")

        key_reader = key_readers[0]
        if len(key_readers) > 1:
            logger.warning(f"There are several key readers connected: {key_readers}. Choose {key_reader}")

class EM4100_KeyReader(KeyReader):
    def __init__(self, serial_device):
        self.serial_device = serial_device
        logger.info(f"Connecting to serial port {serial_device}")
        com = serial.Serial(port=serial_device, baudrate=115200, timeout=0.2)
        self.port_handle = com

        # Arduino is restarted when serial port is opened
        com.timeout = 2
        com.readline() # Just wait until it starts up (hopefully less than 2 second timeout)
        com.timeout = 0.2
        self.check_echo()

    def __repr__(self):
        return f"<EM4100 Key Reader tty={self.serial_device}>"

    def check_echo(self):
        self.port_handle.reset_input_buffer()
        self.port_handle.write(b"?\n")
        self.port_handle.flush()
        response = self.port_handle.readline().decode("utf-8")
        if not response.startswith("EM4100 Reader"):
            logger.error("Response: " + str(response))

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
