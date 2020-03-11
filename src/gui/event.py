from enum import Enum, unique, auto

class WrongEventData(TypeError):
    pass

@unique
class BaseEvent(Enum):
    def _generate_next_value_(name, start, count, last_values):
        '''
        Overrides the value returned by the auto() function
        '''
        return name

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
    MAKERADMIN_CLIENT_CONFIGURED = (auto(), None)
    TAG_READ = (auto(), str)
    MEMBER_INFORMATION_RECEIVED = (auto(), None)
    LOG_OUT = (auto(), None)
    PRINT_STORAGE_BOX_LABEL = (auto(), None)
    PRINT_TEMPORARY_STORAGE_LABEL = (auto(), None)
    LABEL_PRINTED = (auto(), None)
    CANCEL = (auto(), None)
    PRINTING_FAILED = (auto(), None)
    PRINTING_SUCCEEDED = (auto(), None)
    SERIAL_PORT_DISCONNECTED = (auto(), None)
    KEY_READER_CONNECTED = (auto(), None)

class GuiEvent(BaseEvent):
    PRINT_TEMPORARY_STORAGE_LABEL = (auto(), str)
    PRINT_BOX_LABEL = (auto(), None)
    PRINT_CHEMICAL_LABEL = (auto(), None)
    LOG_OUT = (auto(), None)
    TAG_READ = (auto(), str)
    DRAW_STORAGE_LABEL_GUI = (auto(), None)
    CANCEL = (auto(), None)
    TIMEOUT_TIMER_EXPIRED = (auto(), None)

