import unittest
from src.backend import member, makeradmin
from src.test import makeradmin_mock
from unittest.mock import patch
import copy

# Make a deep copy of an object and then restore it afterwards
def patch_deep_copy(target, template):
    return patch(target, new_callable=copy.deepcopy, x=template)

class TestMock(unittest.TestCase):
    def setUp(self):
        self.client = makeradmin_mock.MakerAdminClient()

    def test_parse_response(self):
        m = member.Member.from_member_number(self.client, 1000)

    def test_reports_backend_response_errors(self):
        with self.assertRaises(member.BackendParseError), patch_deep_copy("src.test.makeradmin_mock.response", makeradmin_mock.response) as response:
            response["data"]["membership_data"] = dict()
            m = member.Member.from_member_number(self.client, 1000)

        with self.assertRaises(member.BackendParseError), patch_deep_copy("src.test.makeradmin_mock.response", makeradmin_mock.response) as response:
            response["data"]["membership_data"]["membership_end"] = "Not a date"
            m = member.Member.from_member_number(self.client, 1000)

    def test_member_not_found(self):
        with self.assertRaises(member.NoMatchingMemberNumber), patch_deep_copy("src.test.makeradmin_mock.response", makeradmin_mock.response) as response:
            response["data"] = None
            m = member.Member.from_member_number(self.client, 1000)
