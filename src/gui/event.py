from dataclasses import dataclass

class BaseEvent(object):
    def __init__(self, event: str, data: object | None = None):
        self.event: str = event
        self.data: object | None = data

    def __str__(self):
        data_str = "with data" if self.data is not None else "without data"
        return f'Event: {self.event}, {data_str}'


class Event(BaseEvent):
    MAKERADMIN_CLIENT_CONFIGURED = 'event_makeradmin_configured'
    MEMBER_INFORMATION_RECEIVED = 'event_member_information_received'
    LOG_OUT = 'event_log_out'
    PRINT_STORAGE_BOX_LABEL = 'event_print_storage_box_label'
    PRINT_TEMPORARY_STORAGE_LABEL = 'event_print_temporary_storage_label'
    PRINT_ROTATING_STORAGE_LABEL = 'event_print_rotating_storage_label'
    PRINT_DRYING_LABEL = 'event_print_drying_label'
    LABEL_PRINTED = 'event_label_printed'
    CANCEL = 'event_cancel'
    PRINTING_FAILED = 'event_printing_failed'
    PRINTING_SUCCEEDED = 'event_printing_succeeded'
    LOGIN = 'event_login'


class GuiEvent(BaseEvent):
    DRAW_DRYING_LABEL_GUI = 'gui_event_draw_drying_label_gui'
    LOG_OUT = 'gui_event_log_out'
    DRAW_STORAGE_LABEL_GUI = 'gui_event_draw_storage_label'
    DRAW_ROTATING_LABEL_GUI = 'gui_event_draw_rotating_label'
    CANCEL = 'gui_event_cancel'
    TIMEOUT_TIMER_EXPIRED = 'gui_event_timeout_timer_expired'
    LOGIN = 'gui_event_login'
    PRINT_LABEL = 'gui_event_print_label'
    ENTERED_DESCRIPTION = "gui_event_entered_description"

@dataclass
class MemberLoginData:
    member_number: str
    pin_code: str
