import json

from django.test import TestCase
from django.test.client import Client

from explorer_s_common.utils import format_return, format_price, format_power


class minerTestCase(TestCase):

    def setUp(self):
        self.user_id = '1'
        self.client = Client(HTTP_USERID=self.user_id)

    def test_get_overview(self):
        result = self.client.post(
            '/activity/api/dashboard/get_overview', {}
        ).json()
        print(result)
