import datetime

class MakerAdminClient(object):
    def __init__(self, *args, **kwargs):
        pass

    def is_logged_in(self):
        return True

    def get_tag_info(self, tagid):
        return {
            "data": {
                "member": {
                    "end_date": "2019-04-19",
                    "member_number": 9999,
                    "firstname": "Firstname",
                    "lastname": "Lastname"
                },
            },
            "status": "success"
        }
