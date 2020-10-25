response = {
    'data': {
        'firstname': 'Firstname',
        'keys': [
            {'key_id': 1, 'rfid_tag': '123456789'}
        ],
        'lastname': 'Lastname',
        'member_id': 1,
        'member_number': 9999,
        'membership_data': {
            'effective_labaccess_active': True,
            'effective_labaccess_end': '2020-04-30',
            'labaccess_active': False,
            'labaccess_end': '2020-02-19',
            'membership_active': True,
            'membership_end': '2020-08-31',
            'special_labaccess_active': False,
            'special_labaccess_end': None
        }
    },
    'status': 'ok'
}


class MakerAdminClient(object):
    def __init__(self, *args, **kwargs):
        pass

    @property
    def configured(self):
        return True

    def is_logged_in(self):
        return True

    def get_tag_info(self, tagid):
        return response

    def get_member_number_info(self, member_number):
        return response
