
class BaseEvent(object):

    def __init__(self, event, data=None):
        self.event = event
        self.data = data

    def __str__(self):
        data_str = "with data" if self.data is not None else "without data"
        return f'Event: {self.event}, {data_str}'

class Event(BaseEvent):
    MAKERADMIN_CLIENT_CONFIGURED = 'event_makeradmin_configured'
    TAG_READ = 'event_tag_read'
    MEMBER_INFORMATION_RECEIVED = 'event_member_information_received'
    LOG_OUT = 'event_log_out'
    PRINT_STORAGE_BOX_LABEL = 'event_print_storage_box_label'
    PRINT_TEMPORARY_STORAGE_LABEL = 'event_print_temporary_storage_label'
    LABEL_PRINTED = 'event_label_printed'
    CANCEL = 'event_cancel'
    PRINTING_FAILED = 'event_printing_failed'
    PRINTING_SUCCEEDED = 'event_printing_succeeded'
    SERIAL_PORT_DISCONNECTED = 'event_serial_port_disconnected'
    KEY_READER_CONNECTED = 'event_key_reader_connected'

class GuiEvent(BaseEvent):

    PRINT_TEMPORARY_STORAGE_LABEL = f'gui_event_print_storage_label'
    PRINT_BOX_LABEL = f'gui_event_print_box_label'
    PRINT_CHEMICAL_LABEL = f'gui_event_print_chemical_label'
    LOG_OUT = f'gui_event_log_out'
    TAG_READ = f'gui_event_tag_read'
    DRAW_STORAGE_LABEL_GUI = f'gui_event_draw_storage_label'
    CANCEL = f'gui_event_cancel'
    TIMEOUT_TIMER_EXPIRED = f'gui_event_timeout_timer_expired'

