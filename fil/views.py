import json
import time
import decimal
import datetime
import requests
from collections import Iterable

from django.http import HttpResponse

from explorer_s_common.decorator import common_ajax_response, add_request_log
from explorer_s_common.utils import format_return, format_price, format_power, str_2_power, format_fil, _d
from explorer_s_common.page import Page
from explorer_s_common import inner_server, cache

from explorer_s_data import consts
from miner.interface import MinerBase


@common_ajax_response
def get_miner_day_info(request):
    '''获取矿工信息'''
    miner_nos = json.loads(request.POST.get('miner_nos', '[]'))
    date = request.POST.get('date')
    if date:
        yesterday = datetime.datetime.strptime(date, '%Y-%m-%d')
    else:
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    yesterday_str = yesterday.strftime('%Y-%m-%d')
    third_day = yesterday - datetime.timedelta(days=1)
    third_day_str = third_day.strftime('%Y-%m-%d')

    data = []
    for miner_no in miner_nos:
        # 查询昨天数据
        objs = MinerBase().get_miner_day_records(date=yesterday_str, miner_no=miner_no)
        if not objs:
            continue
        yesterday_obj = objs[0]
        yesterday_data = {
            'miner_no': miner_no, 'block_reward': format_price(yesterday_obj.block_reward, 0),
            'initial_pledge_balance': format_price(yesterday_obj.initial_pledge_balance, 0),
            'overtime_pledge_fee': format_price(yesterday_obj.overtime_pledge_fee, 0),
            'pre_gas': format_price(yesterday_obj.pre_gas, 0),
            'prove_gas': format_price(yesterday_obj.prove_gas, 0)
        }

        # 查询前天数据
        third_day_objs = MinerBase().get_miner_day_records(date=third_day_str, miner_no=miner_no)
        if not third_day_objs:
            yesterday_data['initial_pledge_balance_offset'] = yesterday_data['initial_pledge_balance']
            continue
        third_day_obj = third_day_objs[0]
        initial_pledge_balance_offset = yesterday_obj.initial_pledge_balance - third_day_obj.initial_pledge_balance

        yesterday_data['initial_pledge_balance_offset'] = format_price(initial_pledge_balance_offset, 0)

        data.append(yesterday_data)

    return format_return(0, data=data)
