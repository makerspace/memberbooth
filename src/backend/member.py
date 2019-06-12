import dateutil.parser
import datetime

from logging import getLogger
logger = getLogger("memberbooth")

class NoMatchingTagId(KeyError):
    def __init__(self, tagid):
        super().__init__(f"No tag associated with tagid: {tagid}")

class NoMatchingMemberNumber(KeyError):
    def __init__(self, member_number):
        super().__init__(f"No member associated with member number: {member_number}")

class Member(object):
    def __init__(self, first_name, last_name, member_number, lab_end_date):
        self.first_name = first_name
        self.last_name = last_name
        self.member_number = member_number
        self.lab_end_date = lab_end_date

    def get_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f'{self.member_number}, {self.get_name()}, {self.lab_end_date}'

    @classmethod
    def from_response(cls, response_data):
        member_data = response_data["data"]["member"]
        lab_end_date = member_data["end_date"]
        if lab_end_date is not None:
            lab_end_date = dateutil.parser.parse(lab_end_date).date()
            lab_end_time = datetime.datetime.combine(lab_end_date, datetime.time(23, 59, 59))
        return cls(member_data["firstname"], member_data["lastname"], member_data["member_number"], lab_end_time)

    @classmethod
    def from_tagid(cls, client, tagid):
        data = client.get_tag_info(tagid)
        if data["data"] is None:
            raise NoMatchingTagId(tagid)

        member_data = data["data"]["member"]
        return cls.from_response(data)

    @classmethod
    def from_member_number(cls, client, member_number):
        data = client.get_member_number_info(member_number)
        if data["data"] is None:
            raise NoMatchingMemberNumber(member_number)
        
        return cls.from_response(data)

