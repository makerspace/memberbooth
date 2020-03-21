import dateutil.parser
import datetime
from dataclasses import dataclass

from logging import getLogger
logger = getLogger("memberbooth")

class NoMatchingTagId(KeyError):
    def __init__(self, tagid):
        super().__init__(f"No tag associated with tagid: {tagid}")

class NoMatchingMemberNumber(KeyError):
    def __init__(self, member_number):
        super().__init__(f"No member associated with member number: {member_number}")

@dataclass(frozen=True)
class EndDate:
    is_active: bool
    end_date:  datetime.datetime

    def __str__(self):
        return "✓" if self.is_active else "✕"

@dataclass(frozen=True)
class Member(object):
    first_name:          str
    last_name:           str
    member_number:       int
    membership:          EndDate
    labaccess:           EndDate
    special_labaccess:   EndDate
    effective_labaccess: EndDate

    def get_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f'{self.member_number}, {self.get_name()}, {self.lab_end_date}'

    @classmethod
    def from_response(cls, response_data):
        if (response_data or response_data["data"]) is None:
            return None

        def datify(makeradmin_date):
            if makeradmin_date is None:
                return None
            return datetime.datetime.combine(dateutil.parser.parse(makeradmin_date).date(), datetime.time(23, 59, 59))

        data = response_data["data"]
        membership_data = data["membership_data"]

        return cls(
            data["firstname"], data["lastname"],
            data["member_number"],
            membership = EndDate(membership_data["membership_active"], datify(membership_data["membership_end"])),
            labaccess = EndDate(membership_data["labaccess_active"], datify(membership_data["labaccess_end"])),
            special_labaccess = EndDate(membership_data["special_labaccess_active"], datify(membership_data["special_labaccess_end"])),
            effective_labaccess = EndDate(membership_data["effective_labaccess_active"], datify(membership_data["effective_labaccess_end"])),
        )

    @classmethod
    def from_tagid(cls, client, tagid):
        member = cls.from_response(client.get_tag_info(tagid))
        if member is None:
            raise NoMatchingTagId(tagid)

        return member

    @classmethod
    def from_member_number(cls, client, member_number):
        member = cls.from_response(client.get_member_number_info(member_number))
        if member is None:
            raise NoMatchingMemberNumber(member_number)

        return member

