import json
import datetime

from django.test import SimpleTestCase
from django.test.client import Client
from explorer_s_common.openapi.sign import get_api
from explorer_s_common import consts
from explorer_s_common.cache import Cache
import json
import hmac
import hashlib
import datetime
import uuid
from explorer_s_common.cache import Cache
from requests import request as do_request

class OpenapiTestCase(SimpleTestCase):

    def setUp(self):
        self.client = Client()

    def print(self, msg):
        print('')
        print('')
        print('==================== ' + msg + ' ====================')

    def test_openpi(self):
        host = "http://127.0.0.1:8001/"
        # host = "https://testxm-openapi.arockpool.com/"
        host = "https://openapi.arockpool.com/"
        # uri = "data/openapi/v1/miners"
        uri ="v1/data/miners"
        api = get_api("V1")(None, "rtjiopfsx5z41lku", "463fa60ae09c11ebaa4764bc58bc4fb5", host=host)
        http_status, result = api.send("GET", uri, {"page_index":2, "page_size":200})

        print(http_status)
        print(result)
        # appid = "rtjiopfsx5z41lku"
        # appsecret = "463fa60ae09c11ebaa4764bc58bc4fb5"
        # host = "http://127.0.0.1:8001/"
        # uri = "data/openapi/v1/miners"
        # data = {"page_index":1,"page_size":20}
        # headers = {
        #     'AppId': appid,
        #     'Authorization': None,
        #     'Timestamp': '2021-07-16T15:18:42+0800',
        #     'SignatureVersion': 'V1',
        #     'SignatureMethod': 'HMAC-SHA256',
        #     'SignatureNonce': 'b9b6fba6-85d1-4cf5-b50b-1f214f66c3c7',
        #     'Signature': '',
        # }
        # payload = json.dumps(data or {})
        # sign_str = 'body={0}&timestamp={1}&signatureNonce={2}'.format(payload, headers.get('Timestamp'),
        #                                                               headers.get('SignatureNonce'))
        # s = hmac.new(appsecret.encode(), sign_str.encode(), digestmod=hashlib.sha256)
        # signature = s.hexdigest()
        # headers['Signature'] = signature
        # response = do_request(method="GET", url=host + uri, json=data, headers=headers)
        # print(response.status_code),
        # print(response.json())
