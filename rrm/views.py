import json
import time
import decimal
import datetime
import requests
from collections import Iterable

from django.http import HttpResponse

from explorer_s_common.decorator import common_ajax_response, add_request_log
from explorer_s_common.utils import format_return, format_price, format_power, str_2_power, format_fil, _d
from explorer_s_common.third.bbhe_sdk import BbheBase

from miner.interface import MinerBase
from overview.interface import OverviewBase
from rmd.interface import RMDBase


@common_ajax_response
@add_request_log(["rmd3c8a2b3451214", "tx705ba7560dfa4d", "pl0fbebc29bd5646"])
def get_miner_day_record(request):
    miner_nos = json.loads(request.POST.get('miner_nos', '[]'))
    date = request.POST.get('date')
    # 没有传默认取昨天
    if not date:
        date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

    data = []
    for miner_no in miner_nos[:20]:

        # objs = MinerBase().get_miner_day_records(miner_no=miner_no, date=date)
        # if not objs:
        #     continue
        # obj = objs[0]
        # create_gas = obj.pre_gas + obj.prove_gas
        # inc_pledge = get_inc_pledge(miner_no=miner_no, date=date)
        # data.append({
        #     'miner_no': miner_no,
        #     'available_balance': format_price(obj.available_balance, 0), 'available_balance_str': format_fil(obj.available_balance, 4) + ' FIL',
        #     'initial_pledge_balance': format_price(obj.initial_pledge_balance, 0), 'initial_pledge_balance_str': format_fil(obj.initial_pledge_balance, 4) + ' FIL',
        #     'locked_pledge_balance': format_price(obj.locked_pledge_balance, 0), 'locked_pledge_balance_str': format_fil(obj.locked_pledge_balance, 4) + ' FIL',
        #     'day_reward': format_price(obj.block_reward, 0), 'day_reward_str': format_fil(obj.block_reward, 4) + ' FIL',
        #     'create_gas': format_price(create_gas, 0), 'create_gas_str': format_fil(create_gas, 4) + ' FIL',
        #     'keep_gas': format_price(obj.win_post_gas, 0), 'keep_gas_str': format_fil(obj.win_post_gas, 4) + ' FIL',
        #     'inc_power': format_price(obj.increase_power, 0), 'inc_power_str': format_power(obj.increase_power),
        #     'power': format_price(obj.power, 0), 'power_str': format_power(obj.power),
        #     'inc_pledge': format_price(inc_pledge, 0), 'inc_pledge_str': format_fil(inc_pledge, 4) + ' FIL'
        # })
        result = BbheBase().get_miner_stat(miner_no=miner_no, date=date)
        if not result or not result.get('data') or result.get('code') == 1001:
            continue
        r = result['data']

        # 走BBHE接口
        available_balance = _d(r['availableBalance']) * 10 ** 18
        initial_pledge_balance = _d(r['initialPledge']) * 10 ** 18
        locked_pledge_balance = _d(r['lockedFunds']) * 10 ** 18
        day_reward = _d(r['dayRewardIncr']) * 10 ** 18
        create_gas = (_d(r['dayPreGasFee']) + _d(r['dayProveGasFee'])) * 10 ** 18
        keep_gas = _d(r['dayPostMaintainGasFee']) * 10 ** 18
        inc_power = _d(r['dayPackingNum']) * 1024 ** 4
        power = _d(r['actualPower'])
        inc_pledge = _d(r['pledgeFee']) * 10 ** 18
        temp = {
            'miner_no': miner_no,
            'available_balance': format_price(available_balance, 0),
            'available_balance_str': format_fil(available_balance, 4) + ' FIL',
            'initial_pledge_balance': format_price(initial_pledge_balance, 0),
            'initial_pledge_balance_str': format_fil(initial_pledge_balance, 4) + ' FIL',
            'locked_pledge_balance': format_price(locked_pledge_balance, 0),
            'locked_pledge_balance_str': format_fil(locked_pledge_balance, 4) + ' FIL',
            'day_reward': format_price(day_reward, 0), 'day_reward_str': format_fil(day_reward, 4) + ' FIL',
            'create_gas': format_price(create_gas, 0), 'create_gas_str': format_fil(create_gas, 4) + ' FIL',
            'keep_gas': format_price(keep_gas, 0), 'keep_gas_str': format_fil(keep_gas, 4) + ' FIL',
            'inc_power': format_price(inc_power, 0), 'inc_power_str': format_power(inc_power),
            'power': format_price(power, 0), 'power_str': format_power(power),
            'inc_pledge': format_price(inc_pledge, 0), 'inc_pledge_str': format_fil(inc_pledge, 4) + ' FIL',
            'extend_power': format_price(0, 0), 'extend_power_str': format_power(0),
            'extend_gas': format_price(0, 0), 'extend_gas_str': format_fil(0, 4) + ' FIL',
            'extend_pledge': format_price(0, 0), 'extend_pledge_str': format_fil(0, 4) + ' FIL',
        }

        # 添加 balance 字段
        objs = MinerBase().get_miner_day_records(miner_no=miner_no, date=date)
        if objs:
            obj = objs[0]
            temp.update({
                'worker_balance': format_price(obj.worker_balance, 0), 'worker_balance_str': format_fil(obj.worker_balance, 4) + ' FIL',
                'poster_balance': format_price(obj.poster_balance, 0), 'poster_balance_str': format_fil(obj.poster_balance, 4) + ' FIL',
                'owner_balance': format_price(obj.owner_balance, 0), 'owner_balance_str': format_fil(obj.owner_balance, 4) + ' FIL',
            })

        data.append(temp)
    return format_return(0, data=data)


@common_ajax_response
@add_request_log(["rmd3c8a2b3451214"])
def get_day_overview(request):
    '''获取每天的预览信息'''
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    date = request.POST.get('date', yesterday.strftime('%Y-%m-%d'))

    overview = {
        'tipset_height': 0, 'total_power': 0, 'total_power_str': 0, 'unit_price': 0,
        'pool_total_power': 0, 'pool_total_power_str': 0,
    }

    # 获取全网信息
    net_data = OverviewBase().get_overview()
    overview.update({
        'tipset_height': net_data.get('height'),
        'total_power': format_price(net_data.get('power'), 0),
        'total_power_str': format_power(net_data.get('power')),
        'unit_price': format_price(net_data.get('price')),
    })

    # 获取矿池信息
    pool_data = OverviewBase().get_pool_overview()
    overview.update({
        'pool_total_power': format_price(pool_data.get('power'), 0),
        'pool_total_power_str': format_power(pool_data.get('power')),
        'pool_total_block': pool_data.get('total_block_count'),
        'pool_total_win_count': pool_data.get('total_win_count'),
        'pool_increase_power': format_price(pool_data.get('increase_power_add'), 0),
        'pool_increase_power_str': format_power(pool_data.get('increase_power_add'))
    })

    # 获取矿池挖矿效率
    url = 'https://rmdine-api2.renrenmine.com/open/stat/solomine/data'
    try:
        pool_efficiency = requests.get(url, timeout=5).json()['data']
    except Exception as e:
        pool_efficiency = '0.0698'
    overview.update({'pool_efficiency': format_price(pool_efficiency, 4)})

    # 获取昨日信息，没有则取前天
    day_overview = RMDBase().get_net_stat_day(date)
    if not day_overview:
        return format_return(99904, data={})

    overview.update(day_overview)

    return format_return(0, data=overview)
