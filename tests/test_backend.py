import unittest
from src.backend import member, makeradmin
from src.test import makeradmin_mock

class TestMock(unittest.TestCase):
    def setUp(self):
        self.client = makeradmin_mock.MakerAdminClient()

    def test_parse_response(self):
        m = member.Member.from_tagid(self.client, 0)
