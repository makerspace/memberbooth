from dataclasses import dataclass


class BaseEvent(object):
    def __init__(self, event, data=None):
        self.event = event
        self.data = data

    def __str__(self):
        data_str = "with data" if self.data is not None else "without data"
        return f'Event: {self.event}, {data_str}'


class Event(BaseEvent):
    MAKERADMIN_CLIENT_CONFIGURED = 'event_makeradmin_configured'
    MEMBER_INFORMATION_RECEIVED = 'event_member_information_received'
    LOG_OUT = 'event_log_out'
    PRINT_STORAGE_BOX_LABEL = 'event_print_storage_box_label'
    PRINT_TEMPORARY_STORAGE_LABEL = 'event_print_temporary_storage_label'
    PRINT_DRYING_LABEL = 'event_print_drying_label'
    LABEL_PRINTED = 'event_label_printed'
    CANCEL = 'event_cancel'
    PRINTING_FAILED = 'event_printing_failed'
    PRINTING_SUCCEEDED = 'event_printing_succeeded'
    LOGIN = 'event_login'


class GuiEvent(BaseEvent):
    PRINT_TEMPORARY_STORAGE_LABEL = 'gui_event_print_storage_label'
    PRINT_BOX_LABEL = 'gui_event_print_box_label'
    PRINT_FIRE_BOX_LABEL = 'gui_event_print_fire_box_label'
    PRINT_3D_PRINTER_LABEL = 'gui_event_print_3d_printer_label'
    PRINT_NAME_TAG = 'gui_event_print_name_tag'
    PRINT_MEETUP_NAME_TAG = 'gui_event_print_meetup_name_tag'
    DRAW_DRYING_LABEL_GUI = 'gui_event_draw_drying_label_gui'
    PRINT_DRYING_LABEL = 'gui_event_print_drying_label'
    LOG_OUT = 'gui_event_log_out'
    DRAW_STORAGE_LABEL_GUI = 'gui_event_draw_storage_label'
    CANCEL = 'gui_event_cancel'
    TIMEOUT_TIMER_EXPIRED = 'gui_event_timeout_timer_expired'
    LOGIN = 'gui_event_login'


@dataclass
class MemberLoginData:
    member_number: str
    pin_code: str
