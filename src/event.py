
class Event(object):

    def __init__(self, event, data=None):
        self.event = event
        self.data = data

    def __str__(self):
        return f'Event: {self.event}, data: {self.data}'

class Event(Event):
    TAG_READ = 'event_tag_read'
    MEMBER_INFORMATION_RECEIVED = 'event_member_information_received'
    LOG_OUT = 'event_log_out'
    PRINT_STORAGE_BOX_LABEL = 'event_print_storage_box_label'
    PRINT_TEMPORARY_STORAGE_LABEL = 'event_print_temporary_storage_label'
    LABEL_PRINTED = 'event_label_printed'
    CANCEL = 'event_cancel'
    PRINTING_FAILED = 'event_printing_failed'
    PRINTING_SUCCEEDED = 'event_printing_succeeded'

