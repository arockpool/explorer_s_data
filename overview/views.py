import json
import time
import decimal
import datetime
from collections import Iterable

from django.http import HttpResponse

from explorer_s_common.decorator import common_ajax_response
from explorer_s_common.utils import format_return, format_price, format_power, str_2_power, format_fil
from explorer_s_common.page import Page
from explorer_s_common import inner_server, cache

from explorer_s_data import consts
from overview.interface import OverviewBase


@common_ajax_response
def get_overview(request):
    '''
    获取统计信息
    '''
    must_update_cache = json.loads(request.POST.get('must_update_cache', '0'))
    data = OverviewBase().get_overview(must_update_cache=must_update_cache)
    return format_return(0, data=data)


@common_ajax_response
def get_overview_day_records(request):
    end_date_str = request.POST.get('end_date', datetime.datetime.now().strftime('%Y-%m-%d'))
    end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d')
    start_date_str = request.POST.get('start_date')
    if not start_date_str:
        start_date = end_date - datetime.timedelta(days=14)
        start_date_str = start_date.strftime('%Y-%m-%d')

    data = []
    for per in OverviewBase().get_overview_day_records(start_date=start_date_str, end_date=end_date_str):
        data.append({
            'date': per.date.strftime('%Y-%m-%d'), 'power': per.power, 'raw_power': per.raw_power,
            'reward': per.reward, 'block_count': per.block_count, 'block_reward': per.block_reward,
            'active_miner_count': per.active_miner_count, 'account_count': per.account_count,
            'avg_pledge': per.avg_pledge, 'avg_reward': per.avg_reward,
            'circulating_supply': per.circulating_supply, 'base_fee': per.base_fee,
            'burnt_supply': per.burnt_supply, 'msg_count': per.msg_count, 'total_pledge': per.total_pledge,
            'price': per.price, 'avg_tipset_blocks': per.avg_tipset_blocks, 'increase_power': per.increase_power,
            "create_gas_64_overview": per.create_gas_64, "create_gas_32_overview": per.create_gas_32,
            "keep_gas_32_overview": per.keep_gas_32, "keep_gas_64_overview": per.keep_gas_64,
        })

    return format_return(0, data=data)


@common_ajax_response
def get_history_day_records(request):
    """查询历史某一天的全网概览"""
    date = request.POST.get('date')
    if not date:
        date = str(datetime.datetime.now().date())

    per = OverviewBase().get_overview_one_day_records(date=date)
    if per:
        result = {
            'date': per.date.strftime('%Y-%m-%d'), 'power': per.power, 'raw_power': per.raw_power,
            'reward': per.reward, 'block_count': per.block_count, 'block_reward': per.block_reward,
            'active_miner_count': per.active_miner_count, 'account_count': per.account_count,
            'avg_pledge': per.avg_pledge, 'avg_reward': per.avg_reward,
            'circulating_supply': per.circulating_supply, 'base_fee': per.base_fee,
            'burnt_supply': per.burnt_supply, 'msg_count': per.msg_count, 'total_pledge': per.total_pledge,
            'price': per.price, 'avg_tipset_blocks': per.avg_tipset_blocks, 'increase_power': per.increase_power,
            "create_gas_32": per.create_gas_32, "create_gas_64": per.create_gas_64,
            "keep_gas_32": per.keep_gas_32, "keep_gas_64": per.keep_gas_64
        }
    else:
        result = {}

    return format_return(0, data=result)


@common_ajax_response
def get_pool_overview(request):
    '''
    获取统计信息
    '''
    must_update_cache = json.loads(request.POST.get('must_update_cache', '0'))
    data = OverviewBase().get_pool_overview(must_update_cache=must_update_cache)
    return format_return(0, data=data)


@common_ajax_response
def get_usd_rate(request):
    rate = OverviewBase().get_usd_rate()
    return format_return(0, data=rate)
