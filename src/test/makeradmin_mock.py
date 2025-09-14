from typing import Any


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
            'effective_labaccess_end': '2023-06-30',
            'labaccess_active': True,
            'labaccess_end': '2023-06-30',
            'membership_active': True,
            'membership_end': '2025-12-31',
            'special_labaccess_active': False,
            'special_labaccess_end': None
        }
    },
    'status': 'ok'
}


class MakerAdminClient(object):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    @property
    def configured(self):
        return True

    def is_logged_in(self) -> bool:
        return True

    def get_tag_info(self, tagid: int) -> dict[str, Any]:
        return response

    def get_member_with_pin(self, member_number: int, pin_code: str) -> dict[str, Any]:
        return response

    def get_member_number_info(self, member_number: int) -> dict[str, Any]:
        return response
    
    def login(self) -> bool:
        return True
