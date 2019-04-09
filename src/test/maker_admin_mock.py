import datetime

class MakerAdminClient(object):
    def __init__(self, *args, **kwargs):
        pass

    def is_logged_in(self):
        return True

    def get_tag_info(self, tagid):
        return {"data": {
            "member": {
                "end_date": datetime.datetime.today().isoformat(),
                "member_number": 1234,
                "firstname": "Stockholm",
                "lastname": "Makerspace"
            },
        }}
