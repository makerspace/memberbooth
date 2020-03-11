from enum import Enum, unique

class WrongEventData(TypeError):
    pass

@unique
class BaseEvent(Enum):
    def __init__(self, event, datatype=None):
        self.event = event
        self.datatype = datatype
        self.data = None

    def __call__(self, data):
        '''
        Add data to an event by calling the event with the data
        '''
        if self.datatype is None:
            raise WrongEventData(f"The event {self.name} does not take any data")
        elif not isinstance(data, self.datatype):
            raise WrongEventData(f"The data must be of type {self.datatype}")
        self.data = data
        return self

    def __repr__(self):
        return f'{self.__class__.__name__}.{self.name}'

    def __str__(self):
        if self.datatype:
            data_str = "with data" if self.data is not None else "without data"
            return f'{repr(self)}, {data_str}'
        else:
            return repr(self)


class Event(BaseEvent):
    MAKERADMIN_CLIENT_CONFIGURED = ('makeradmin_configured', None)
    TAG_READ = ('tag_read', str)
    MEMBER_INFORMATION_RECEIVED = ('member_information_received', None)
    LOG_OUT = ('log_out', None)
    PRINT_STORAGE_BOX_LABEL = ('print_storage_box_label', None)
    PRINT_TEMPORARY_STORAGE_LABEL = ('print_temporary_storage_label', None)
    LABEL_PRINTED = ('label_printed', None)
    CANCEL = ('cancel', None)
    PRINTING_FAILED = ('printing_failed', None)
    PRINTING_SUCCEEDED = ('printing_succeeded', None)
    SERIAL_PORT_DISCONNECTED = ('serial_port_disconnected', None)
    KEY_READER_CONNECTED = ('key_reader_connected', None)

class GuiEvent(BaseEvent):
    PRINT_TEMPORARY_STORAGE_LABEL = ('print_storage_label', str)
    PRINT_BOX_LABEL = ('print_box_label', None)
    PRINT_CHEMICAL_LABEL = ('print_chemical_label', None)
    LOG_OUT = ('log_out', None)
    TAG_READ = ('tag_read', str)
    DRAW_STORAGE_LABEL_GUI = ('draw_storage_label', None)
    CANCEL = ('cancel', None)
    TIMEOUT_TIMER_EXPIRED = ('timeout_timer_expired', None)

