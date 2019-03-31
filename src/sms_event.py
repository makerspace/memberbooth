
class Event(object):

    def __init__(self, event, data=None):
        self.event = event
        self.data = data

    def __str__(self):
        return f'Event: {self.event}, data: {self.data}'

class SMSEvent(Event):

    SMS_EVENT_PREFIX = 'sms_event'

    TAG_READ = f'{SMS_EVENT_PREFIX}_tag_read'
    MEMBER_INFORMATION_RECEIVED = f'{SMS_EVENT_PREFIX}_member_information_received'
    LOG_OUT = f'{SMS_EVENT_PREFIX}_log_out'
    PRINT_STORAGE_BOX_LABEL = f'{SMS_EVENT_PREFIX}_print_storage_box_label'
    PRINT_TEMPORARY_STORAGE_LABEL = f'{SMS_EVENT_PREFIX}_print_temporary_storage_label'
    LABEL_PRINTED = f'{SMS_EVENT_PREFIX}_label_printed'

