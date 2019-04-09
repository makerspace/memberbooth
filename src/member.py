import dateutil.parser

class Member(object):
    def __init__(self, first_name, last_name, member_number, lab_end_date):
        self.first_name = first_name
        self.last_name = last_name
        self.member_number = member_number
        self.lab_end_date = lab_end_date
    
    def get_name(self):
        return f"{self.first_name} {self.last_name}"

    @classmethod
    def from_tagid(cls, client, tagid):
        data = client.get_tag_info(tagid)
        if data["data"] is None:
            raise Exception(f"No key/member associated with tagid {tagid}")

        member_data = data["data"]["member"]
        lab_end_date = member_data["end_date"]
        if lab_end_date is not None:
            lab_end_date = dateutil.parser.parse(lab_end_date)
        return cls(member_data["firstname"], member_data["lastname"], member_data["member_number"], lab_end_date)


