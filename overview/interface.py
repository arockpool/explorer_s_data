import time
import math
import json
import logging
import decimal
import requests
import datetime
from lxml import etree

from django.db import transaction
from django.db.models import Avg, Q, F, Sum, Count

from explorer_s_common import debug, consts, cache, raw_sql
from explorer_s_common.utils import format_return, Validator, format_power, format_price, format_fil, \
    str_2_power, format_fil_to_decimal, _d
from explorer_s_common.decorator import validate_params, cache_required
from explorer_s_common.third.filfox_sdk import FilfoxBase
from explorer_s_common.third.bbhe_sdk import BbheBase
from explorer_s_common.third.gateio_sdk import GateioBase
from explorer_s_common.third.fxh_sdk import FxhBase

from explorer_s_data.consts import ERROR_DICT
from overview.models import Overview, OverviewDay, OverviewPool
from miner.interface import MinerBase
from tipset.interface import TipsetBase
from message.models import TipsetGasSum
from message.interface import MessageBase


class OverviewBase(object):

    @cache_required(cache_key='data_overview', expire=30 * 60)
    def get_overview(self, must_update_cache=False):
        result = BbheBase().get_overview()
        if not result:
            return None

        price = 0
        price_change = 0
        gateio_result = GateioBase().get_ticker()
        if gateio_result:
            price = _d(gateio_result.get('last', '0'))
            price_change = _d(gateio_result.get('percentChange', '0'))

        if price == 0:
            fxh_result = FxhBase().get_ticker()
            if fxh_result:
                temp = [x for x in fxh_result if x['symbol'] == 'FIL'][0]
                price = _d(temp.get('price_usd', '0'))
                price_change = _d(temp.get('percent_change_24h', '0'))

        block_lucky = TipsetBase().get_lucky(block=True)
        avg_reward = self.get_avg_reward_24_hour()
        avg_pledge = _d(result['data']['pledge_per_sector']) / 10**18
        avg_tipset_blocks = _d(5) * block_lucky
        now = datetime.datetime.now()

        # 按分钟记录
        minute = math.floor(now.minute / 10) * 10
        record_time = now.replace(minute=minute, second=0, microsecond=0)
        obj, created = Overview.objects.get_or_create(record_time=record_time)
        obj.power = result['data']['power']
        obj.raw_power = result['data']['raw_power']
        obj.height = result['data']['height']
        obj.reward = result['data']['reward']
        obj.block_count = result['data']['block_count']
        obj.block_reward = result['data']['block_reward']
        obj.active_miner_count = result['data']['active_miner']
        obj.account_count = result['data']['total_account']
        obj.avg_pledge = avg_pledge
        obj.avg_reward = avg_reward
        obj.circulating_supply = result['data']['circulating_supply']
        obj.base_fee = result['data']['base_fee']
        obj.burnt_supply = result['data']['burnt_supply']
        obj.msg_count = result['data']['msg_count']
        obj.total_pledge = result['data']['total_pledge']
        obj.price = price
        obj.price_change = price_change
        obj.avg_tipset_blocks = avg_tipset_blocks
        obj.save()

        # 24小时算力增长
        power_inc_24_hour = self.get_power_inc_24_hour()
        # 24小时出块奖励
        block_reward_24_hour = TipsetBase().get_temp_tipset_sum_reward()
        # 平均区块间隔
        avg_block_time = TipsetBase().get_avg_block_time()

        # 按天记录
        record_date = now - datetime.timedelta(days=1)
        obj_day, created = OverviewDay.objects.get_or_create(date=record_date.date())
        if created:
            # 24小时平均base_fee
            avg_base_fee = MessageBase().get_avg_base_fee(date=record_date.strftime('%Y-%m-%d'))
            # 生产gas
            ck = '%s_%s' % ('0', False)
            gas_32 = MessageBase().get_gas_cost_stat(ck, sector_type='0', is_pool=False)
            ck = '%s_%s' % ('1', False)
            gas_64 = MessageBase().get_gas_cost_stat(ck, sector_type='1', is_pool=False)

            obj_day.power = result['data']['power']
            obj_day.raw_power = result['data']['raw_power']
            obj_day.height = result['data']['height']
            obj_day.reward = result['data']['reward']
            obj_day.block_count = result['data']['block_count']
            obj_day.block_reward = result['data']['block_reward']
            obj_day.active_miner_count = result['data']['active_miner']
            obj_day.account_count = result['data']['total_account']
            obj_day.avg_pledge = avg_pledge
            obj_day.avg_reward = avg_reward
            obj_day.circulating_supply = result['data']['circulating_supply']
            obj_day.base_fee = result['data']['base_fee']
            obj_day.burnt_supply = result['data']['burnt_supply']
            obj_day.msg_count = result['data']['msg_count']
            obj_day.total_pledge = result['data']['total_pledge']
            obj_day.price = price
            obj_day.price_change = price_change
            obj_day.avg_tipset_blocks = avg_tipset_blocks
            obj_day.increase_power = power_inc_24_hour
            obj_day.avg_base_fee = avg_base_fee
            obj_day.create_gas_32 = gas_32['create_gas'] * 10**18
            obj_day.create_gas_64 = gas_64['create_gas'] * 10**18
            obj_day.keep_gas_32 = gas_32['keep_gas'] * 10**18
            obj_day.keep_gas_64 = gas_64['keep_gas'] * 10**18
            obj_day.save()

        # 最新生产gas
        gas_obj = TipsetGasSum.objects.filter(create_gas_32__gt=0)[0]
        # 返回
        data = {
            'power': obj.power, 'raw_power': obj.raw_power, 'height': obj.height, 'reward': obj.reward,
            'block_count': obj.block_count, 'block_reward': obj.block_reward,
            'active_miner_count': obj.active_miner_count, 'account_count': obj.account_count,
            'avg_pledge': obj.avg_pledge, 'avg_reward': obj.avg_reward, 'price_change': obj.price_change,
            'circulating_supply': obj.circulating_supply, 'base_fee': obj.base_fee, 'burnt_supply': obj.burnt_supply,
            'msg_count': obj.msg_count, 'total_pledge': obj.total_pledge, 'price': obj.price,
            'avg_tipset_blocks': obj.avg_tipset_blocks, 'power_inc_24_hour': power_inc_24_hour,
            'block_reward_24_hour': block_reward_24_hour, 'avg_block_time': avg_block_time,
            'create_gas_32': gas_obj.create_gas_32, 'create_gas_64': gas_obj.create_gas_64
        }
        return data

    @cache_required(cache_key='data_pool_overview', expire=30 * 60)
    def get_pool_overview(self, must_update_cache=False):

        power = 0
        raw_power = 0
        total_sector = 0
        active_sector = 0
        faulty_sector = 0
        recovering_sector = 0
        balance = 0
        available_balance = 0
        pledge_balance = 0
        total_reward = 0
        total_block_count = 0
        total_win_count = 0
        total_increase_power = 0  # 算力offset
        total_increase_power_add = 0  # 算力增量
        avg_reward = 0
        lucky = 0

        now = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday = now - datetime.timedelta(days=1)

        pool_miners = MinerBase().get_miner_list(is_pool=True)
        pool_count = pool_miners.count()
        for miner in pool_miners:
            # 计算算力增量
            objs = MinerBase().get_miner_day_records(miner_no=miner.miner_no, date=yesterday.strftime('%Y-%m-%d'))
            if not objs:
                objs = MinerBase().get_miner_day_records(miner_no=miner.miner_no, date=(yesterday - datetime.timedelta(days=1)).strftime('%Y-%m-%d'))

            if objs:
                total_increase_power_add += objs[0].increase_power

            power += miner.power
            raw_power += miner.raw_power
            total_sector += miner.total_sector
            active_sector += miner.active_sector
            faulty_sector += miner.faulty_sector
            recovering_sector += miner.recovering_sector
            balance += miner.balance
            available_balance += miner.available_balance
            pledge_balance += miner.pledge_balance
            total_reward += miner.total_reward
            total_block_count += miner.total_block_count
            total_win_count += miner.total_win_count
            avg_reward += miner.miner_day_stat.avg_reward
            lucky += miner.miner_day_stat.lucky

        yesterday_obj = OverviewPool.objects.filter(record_time=yesterday)
        total_increase_power = power - yesterday_obj[0].power

        obj, created = OverviewPool.objects.get_or_create(record_time=now)
        obj.power = power
        obj.raw_power = raw_power
        obj.total_sector = total_sector
        obj.active_sector = active_sector
        obj.faulty_sector = faulty_sector
        obj.recovering_sector = recovering_sector
        obj.balance = balance
        obj.available_balance = available_balance
        obj.pledge_balance = pledge_balance
        obj.total_reward = total_reward
        obj.total_block_count = total_block_count
        obj.total_win_count = total_win_count
        obj.increase_power = total_increase_power
        obj.increase_power_add = total_increase_power_add
        obj.avg_reward = avg_reward / _d(pool_count) if pool_count else 0
        obj.lucky = lucky / _d(pool_count) if pool_count else 0
        obj.count = pool_count
        obj.save()

        # 返回
        data = {
            'power': obj.power,
            'raw_power': obj.raw_power,
            'total_sector': obj.total_sector,
            'active_sector': obj.active_sector,
            'faulty_sector': obj.faulty_sector,
            'recovering_sector': obj.recovering_sector,
            'balance': obj.balance,
            'available_balance': obj.available_balance,
            'pledge_balance': obj.pledge_balance,
            'total_reward': obj.total_reward,
            'total_block_count': obj.total_block_count,
            'total_win_count': obj.total_win_count,
            'increase_power': obj.increase_power,
            'increase_power_add': obj.increase_power_add,
            'avg_reward': obj.avg_reward,
            'lucky': obj.lucky,
            'count': obj.count
        }
        return data

    def get_avg_reward_24_hour(self):
        '''获取24小时平均奖励'''
        # 24小时总奖励
        temp_tipset_sum_reward = TipsetBase().get_temp_tipset_sum_reward() / 10 ** 18

        # 24小时之前算力
        now = datetime.datetime.now()
        yesterday = now - datetime.timedelta(days=1)

        avg_power = Overview.objects.filter(record_time__range=(yesterday, now), power__gt=0).aggregate(Avg('power'))['power__avg'] or 0
        avg_power = avg_power / 1024**4

        return _d(temp_tipset_sum_reward / avg_power) if avg_power else 0

    def get_power_inc_24_hour(self):
        '''24小时算力增量'''

        # 24小时之前算力
        now = datetime.datetime.now()
        yesterday = now - datetime.timedelta(days=1)

        now_obj = Overview.objects.filter(power__gt=0)[0]
        yesterday_obj = Overview.objects.filter(record_time__lte=yesterday, power__gt=0)[0]
        return now_obj.power - yesterday_obj.power

    def get_overview_day_records(self, start_date=None, end_date=None):
        '''查询全网历史数据'''
        objs = OverviewDay.objects.filter()
        if start_date:
            objs = objs.filter(date__range=(start_date, end_date))
        return objs

    def get_overview_one_day_records(self, date):
        '''查询全网历史数据'''
        objs = OverviewDay.objects.filter(date=date)
        return objs[0] if objs else None

    @cache_required(cache_key='data_usd_rate', expire=1800 * 1)
    def get_usd_rate(self, must_update_cache=False):
        '''
        获取美元汇率
        '''
        rate = 6.68
        try:
            res = requests.get('https://api.exchangerate-api.com/v4/latest/USD').json()
            rate = res.get('rates', {}).get('CNY', 6.68)
        except Exception as e:
            print(e)
        return float(rate)
