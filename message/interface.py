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
    str_2_power, format_fil_to_decimal, _d, datetime_to_height, height_to_datetime,get_aggregate_gas
from explorer_s_common.decorator import validate_params, cache_required
from explorer_s_common.third.filfox_sdk import FilfoxBase
from explorer_s_common.third.filscout_sdk import FilscoutBase
from explorer_s_common.third.filscan_sdk import FilscanBase
from explorer_s_common.third.bbhe_sdk import BbheBase, BbheEsBase

from explorer_s_data.consts import ERROR_DICT
from message.models import TipsetGasSum, TipsetGasStat, PoolTipsetGasStat, PledgeHistory, OvertimePledge
from miner.interface import MinerBase


class MessageBase(object):

    def __init__(self):
        self.launch_date = datetime.datetime(2020, 8, 25, 6, 0, 0)

    def get_transfer_list(self, miner_no, page_index=0, page_size=100):
        result = FilfoxBase().get_miner_transfers(miner_address=miner_no, page_index=page_index, page_size=page_size)
        if not result:
            return []

        data = []
        for per in result['transfers']:
            data.append({
                'height': per['height'],
                'record_time': datetime.datetime.fromtimestamp(per['timestamp']),
                'from': per['from'],
                'to': per['to'],
                'type': per['type'],
                'value': per['value'],
                'value_str': format_fil(per['value']) + ' FIL',
                "message": per.get("message")
            })
        return {"data": data, "totalCount": result.get("totalCount"), "types": result.get("types")}

    def get_gas_sum_by_day(self, start_date=None, end_date=None):

        now = datetime.datetime.now() - datetime.timedelta(minutes=10)
        if not start_date:
            start_date = (now - datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
            end_date = now.strftime('%Y-%m-%d %H:%M:%S')

        sql = '''
        SELECT 
        DATE_FORMAT(record_time,'%%Y-%%m-%%d') as d,
        SUM(`win_post_gas`), SUM(`win_post_gas_count`),
        SUM(`pre_gas`), SUM(`pre_gas_count`),
        SUM(`prove_gas`), SUM(`prove_gas_count`)
        FROM message_tipsetgassum 
        WHERE record_time >= %s AND record_time < %s
        GROUP BY d
        ORDER BY d
        '''
        records = raw_sql.exec_sql(sql, [start_date, end_date])

        data = {}
        for per in records:
            data[per[0]] = {
                'win_post_gas': per[1], 'win_post_gas_count': per[2],
                'pre_gas': per[3], 'pre_gas_count': per[4],
                'prove_gas': per[5], 'prove_gas_count': per[6]
            }
        return data

    def get_gas_stat_all(self, sector_type=None, is_pool=False):
        '''获取完整的gas统计信息'''

        now = datetime.datetime.now()
        objs = TipsetGasStat.objects.exclude(record_time__isnull=True)
        end_date = objs[0].record_time.strftime('%Y-%m-%d %H:%M:%S')
        start_date = (objs[0].record_time - datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')

        condition = ''
        if sector_type is not None:
            condition = ' AND sector_type = %s' % sector_type

        # 表名
        table_name = 'message_pooltipsetgasstat' if is_pool else 'message_tipsetgasstat'

        sql = '''
        SELECT method, SUM(count) AS count, SUM(gas_limit) AS gas_limit, SUM(gas_fee_cap) AS gas_fee_cap,
        SUM(gas_premium) AS gas_premium, SUM(gas_used) AS gas_used, SUM(base_fee_burn) AS base_fee_burn, 
        SUM(total_cost) AS total_cost, SUM(msg_value) AS msg_value
        FROM ''' + table_name + ''' 
        WHERE record_time >= %s AND record_time < %s
        ''' + condition + '''
        GROUP BY method
        '''
        reocrds = raw_sql.exec_sql(sql, [start_date, end_date])

        data = {'total': {}}
        sum_data = {
            'count': 0,
            'gas_limit': 0, 'avg_gas_limit': 0,
            'gas_fee_cap': 0, 'avg_gas_fee_cap': 0,
            'gas_premium': 0, 'avg_gas_premium': 0,
            'gas_used': 0, 'avg_gas_used': 0,
            'base_fee_burn': 0, 'avg_base_fee_burn': 0,
            'total_cost': 0, 'avg_cost': 0,
            'msg_value': 0
        }
        for per in reocrds:
            method = per[0]
            count = per[1]
            data[method] = {
                'count': count,
                'gas_limit': per[2], 'avg_gas_limit': per[2] / count,
                'gas_fee_cap': per[3], 'avg_gas_fee_cap': per[3] / count,
                'gas_premium': per[4], 'avg_gas_premium': per[4] / count,
                'gas_used': per[5], 'avg_gas_used': per[5] / count,
                'base_fee_burn': per[6], 'avg_base_fee_burn': per[6] / count,
                'total_cost': per[7], 'avg_cost': per[7] / count,
                'msg_value': per[8]
            }
            sum_data['count'] += count
            sum_data['gas_limit'] += per[2]
            sum_data['gas_fee_cap'] += per[3]
            sum_data['gas_premium'] += per[4]
            sum_data['gas_used'] += per[5]
            sum_data['base_fee_burn'] += per[6]
            sum_data['total_cost'] += per[7]
            sum_data['msg_value'] += per[8]

        sum_data['avg_gas_limit'] = sum_data['gas_limit'] / sum_data['count']
        sum_data['avg_gas_fee_cap'] = sum_data['gas_fee_cap'] / sum_data['count']
        sum_data['avg_gas_premium'] = sum_data['gas_premium'] / sum_data['count']
        sum_data['avg_gas_used'] = sum_data['gas_used'] / sum_data['count']
        sum_data['avg_base_fee_burn'] = sum_data['base_fee_burn'] / sum_data['count']
        sum_data['avg_cost'] = sum_data['total_cost'] / sum_data['count']

        data['total'] = sum_data
        return data

    def get_gas_sum_by_time(self, sector_type, start_date=None, end_date=None):
        now = datetime.datetime.now()
        if not start_date:
            start_date = (now - datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
            end_date = now.strftime('%Y-%m-%d %H:%M:%S')

        if sector_type == "0":
            sql = '''
            SELECT 
            SUM(`win_post_gas_32`), SUM(`win_post_gas_count_32`),
            SUM(`pre_gas_32`), SUM(`pre_gas_count_32`),
            SUM(`prove_gas_32`), SUM(`prove_gas_count_32`)
            FROM message_tipsetgassum 
            WHERE record_time >= %s AND record_time < %s
            '''
        else:
            sql = '''
                    SELECT 
                    SUM(`win_post_gas_64`), SUM(`win_post_gas_count_64`),
                    SUM(`pre_gas_64`), SUM(`pre_gas_count_64`),
                    SUM(`prove_gas_64`), SUM(`prove_gas_count_64`)
                    FROM message_tipsetgassum 
                    WHERE record_time >= %s AND record_time < %s
                        '''
        records = raw_sql.exec_sql(sql, [start_date, end_date])

        return records[0] if records else None

    def get_base_fee_trends(self, start_date=None, end_date=None, step=60):
        '''获取base_fee趋势'''
        now = datetime.datetime.now() - datetime.timedelta(minutes=10)
        if not start_date:
            start_date = (now - datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
            end_date = now.strftime('%Y-%m-%d %H:%M:%S')

        sql = '''
            SELECT height, record_time, base_fee, create_gas_32, keep_gas_32, create_gas_64, keep_gas_64
            FROM message_tipsetgassum 
            WHERE record_time >= %s AND record_time < %s
            AND height %% %s = 0
            AND base_fee > 0
            ORDER BY height
        '''

        return raw_sql.exec_sql(sql, [start_date, end_date, step])

    def get_memory_pool_message(self, page_size=20, page_index=1):
        '''获取内存池消息'''
        return BbheEsBase().get_memory_pool_message(page_size=page_size, page_index=page_index)

    def get_message_list(self, is_next=False, miner_no=None, msg_method=None, msg_ids=[],
                         start_time=None, end_time=None, all=False,
                         is_transfer=False, page_index=1, page_size=10):
        '''获取消息列表'''
        start_height, end_height = None, None
        if start_time:
            start_height = datetime_to_height(start_time)
        if end_time:
            end_height = datetime_to_height(end_time)
        return BbheEsBase().get_message_list(is_next=is_next, miner_no=miner_no,
                                               msg_method=msg_method, msg_ids=msg_ids,
                                               start_height=start_height, end_height=end_height,
                                               all=all, is_transfer=is_transfer,
                                               page_index=page_index, page_size=page_size)

    def get_scroll(self, scroll_id):
        """获取ES数据信息"""
        return BbheEsBase().scroll(scroll_id)

    # def get_transfer_list_self(self, timestamp=0, is_next=False, miner_no=None, msg_ids=[], page_index=1, page_size=10,
    #                            all=False):
    #     '''获取消息列表'''
    #     return BbheEsBase().get_transfer_message_list(timestamp=timestamp, is_next=is_next, miner_no=miner_no,
    #                                                     msg_ids=msg_ids, page_index=page_index, page_size=page_size)
    #
    # def get_transfer_message_count(self, miner_no=None, msg_ids=[]):
    #     '''获取消息列表'''
    #     return BbheEsBase().get_transfer_message_count(miner_no=miner_no, msg_ids=msg_ids)

    def get_message_count(self, miner_no=None, msg_ids=[], msg_method=None, is_transfer=False, start_time=None,
                          end_time=None, all=False):
        '''获取消息总数'''
        start_height, end_height = None, None
        if start_time:
            start_height = datetime_to_height(start_time)
        if end_time:
            end_height = datetime_to_height(end_time)
        return BbheEsBase().get_message_count(miner_no=miner_no, msg_ids=msg_ids, msg_method=msg_method,
                                                start_height=start_height, end_height=end_height,
                                                is_transfer=is_transfer, all=all)

    # def get_all_message_count(self, miner_no=None, ):
    #     '''获取地址发送和接收的消息总数'''
    #     return BbheEsBase().get_all_message_count(miner_no=miner_no)

    @cache_required(cache_key='get_message_method_types_%s', expire=2 * 60)
    def get_message_method_types(self, redis_k, miner_no=None, msg_ids=[], is_transfer=False,
                                 start_time=None, end_time=None, all=False):
        '''获取消息所有类型'''
        start_height, end_height = None, None
        if start_time:
            start_height = datetime_to_height(start_time)
        if end_time:
            end_height = datetime_to_height(end_time)
        message_method_types = BbheEsBase().get_message_method_types(miner_no=miner_no, msg_ids=msg_ids,
                                                                       start_height=start_height, end_height=end_height,
                                                                       is_transfer=is_transfer, all=all)
        return [x["key"] for x in message_method_types["msg_methods"]['buckets'] if x["key"]]

    def get_message_detail(self, msg_cid):
        '''获取单个消息'''
        return BbheEsBase().get_message_detail(msg_cid=msg_cid)

    def get_miner_gas_cost_stat(self, msg_method, start_height, end_height, miner_no=None):
        '''获取指定时间段矿工gas消耗'''
        data = BbheEsBase().get_miner_gas_cost_stat(
            msg_method=msg_method, start_height=start_height, end_height=end_height,
            miner_no=miner_no
        )['miner_group']['buckets']

        return dict([(x['key'], {'count': x['doc_count'], 'sum': _d(x['gas_sum']['value'])}) for x in data])

    # @cache_required(cache_key='data_gas_cost_stat_%s', expire=2 * 60)
    def get_gas_cost_stat(self, ck, sector_type='0', is_pool=False, must_update_cache=False):
        '''获取生产gas、维护gas'''
        data = self.get_gas_sum_by_time(sector_type=sector_type)
        if data:
            # 生产成本
            pre_gas = data[2] / data[3]
            prove_gas = data[4] / data[5]
            # 32 GiB
            if sector_type == '0':
                create_gas = (pre_gas + prove_gas) * _d(32) / _d(10 ** 18)
            else:
                create_gas = (pre_gas + prove_gas) * _d(16) / _d(10 ** 18)

            # 维护成本
            winpost_gas = data[0]
            total_power = \
                MinerBase().get_miners_by_sector_type(sector_type=sector_type,
                                                      is_pool=is_pool if is_pool else None).aggregate(
                    Sum('power'))['power__sum'] or 0
            keep_gas = winpost_gas / (total_power / _d(1024 ** 4)) / _d(10 ** 18)

            return {'create_gas': create_gas, 'keep_gas': keep_gas}
        return {'create_gas': 0, 'keep_gas': 0}

    def get_avg_base_fee(self, date):
        '''获取24小时平均base_fee'''
        start_date = date + ' 00:00:00'
        end_date = date + ' 23:59:59'

        return TipsetGasSum.objects.filter(record_time__range=(start_date, end_date)).aggregate(Avg('base_fee'))[
            'base_fee__avg'] or 0

    def sync_tipset_gas_warning(self):
        '''同步gas费预警'''
        from explorer_s_common.mq.mq_kafka import Producer, MQ_TOPIC_SYS_ERROR

        now_height = datetime_to_height(datetime.datetime.now())
        if (now_height - TipsetGasSum.objects.first().height) > 60:
            Producer().send(MQ_TOPIC_SYS_ERROR,
                            {'service': 'data', 'url': '同步gas费延迟预警', 'detail': 'TipsetGasSum 数据延迟超过60个高度'})

        if (now_height - TipsetGasStat.objects.first().height) > 60:
            Producer().send(MQ_TOPIC_SYS_ERROR,
                            {'service': 'data', 'url': '同步gas费延迟预警', 'detail': 'TipsetGasStat 数据延迟超过60个高度'})

        # if (now_height - PledgeHistory.objects.first().height) > 60:
        #     Producer().send(MQ_TOPIC_SYS_ERROR,
        #                     {'service': 'data', 'url': '同步质押数据预警', 'detail': 'PledgeHistory 数据延迟超过60个高度'})

    @cache_required(cache_key='get_gas_sum_by_per_%s', expire=2 * 60)
    def get_gas_sum_by_per(self, ck, start_date=None, end_date=None, sector_type="0"):
        """
        时候获取全网生产gas汇总
        """
        # 开始时间戳
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        start_height = int((start_date - self.launch_date).total_seconds() / 30)
        # 结束时间戳 PreCommitSector ProveCommitSector
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        end_height = int((end_date - self.launch_date).total_seconds() / 30)

        if sector_type == "0":
            data = BbheEsBase().get_gas_cost_stat_by_miner_no(None, [6, 7, 25, 26], start_height,
                                                                end_height, sector_size="32 GiB")
            create_avg_gas_32 = _d(0)
            for per in data.get('miner_group', {}).get('buckets', []):
                create_avg_gas_32 += _d(per['gas_sum']['value']) / per['doc_count']
            create_gas_32 = format_fil_to_decimal(create_avg_gas_32 * _d(32), 4)
            return create_gas_32
        else:
            data = BbheEsBase().get_gas_cost_stat_by_miner_no(None, [6, 7, 25, 26], start_height,
                                                                end_height, sector_size="64 GiB")
            create_avg_gas_64 = _d(0)
            for per in data.get('miner_group', {}).get('buckets', []):
                create_avg_gas_64 += _d(per['gas_sum']['value']) / per['doc_count']
            create_gas_64 = format_fil_to_decimal(create_avg_gas_64 * _d(16), 4)
            return create_gas_64

    def sync_tipset_gas(self, height, pool_miners_dict={}):
        '''同步汽油费相关'''
        result = BbheEsBase().get_height_message(height=height)
        messages = result.get('hits', [])
        if not messages:
            return
        self.sync_tipset_gas_sum(height=height, messages=messages)
        self.sync_tipset_gas_stat(height=height, messages=messages)
        self.sync_pool_tipset_gas_stat(height=height, messages=messages, pool_miners_dict=pool_miners_dict)
        # 现在改版了算法不对了 2021-08-01
        # self.sync_pledge_history(height=height, messages=messages)

    def sync_tipset_gas_sum(self, height, messages):
        '''同步单个区块gas汇总'''
        pre_gas_32 = _d(0)
        pre_gas_32_count = 0
        pre_gas_64 = _d(0)
        pre_gas_64_count = 0
        prove_gas_32 = _d(0)
        prove_gas_32_count = 0
        prove_gas_64 = _d(0)
        prove_gas_64_count = 0
        winpost_gas_32 = _d(0)
        winpost_gas_32_count = 0
        winpost_gas_64 = _d(0)
        winpost_gas_64_count = 0

        base_fee = 0
        record_time = self.launch_date + datetime.timedelta(seconds=30 * height)

        for per in messages:
            s = per['_source']
            miner_no = s['msg_to']
            # if not s.get('msg_method_name'):
            #     continue
            if not base_fee:
                base_fee = s.get('base_fee2', 0)

            # SubmitWindowedPoSt
            if s['msg_method'] == 5:
                # if s['msg_method_name'] == 'SubmitWindowedPoSt':
                if s['sector_size'] == '32 GiB':
                    winpost_gas_32 += _d(s['gascost_total_cost'])
                    winpost_gas_32_count += 1
                else:
                    winpost_gas_64 += _d(s['gascost_total_cost'])
                    winpost_gas_64_count += 1
            # PreCommitSector PreCommitSectorBatch
            if s['msg_method'] in [6, 25]:
                # if s['msg_method_name'] == 'PreCommitSector':
                sector_count = 1
                if s['msg_method'] == 25:  # 多扇区封装
                    try:
                        msg_params = json.loads(s.get("msg_params") or "[]")
                        sector_count = max(len(msg_params), sector_count)
                    except:
                        pass
                pre_aggregate_gas = _d(get_aggregate_gas(sector_count, int(s["base_fee2"]), height, s['msg_method']))
                if s['sector_size'] == '32 GiB':
                    pre_gas_32 += _d(s['gascost_total_cost']) + pre_aggregate_gas
                    pre_gas_32_count += sector_count
                else:
                    pre_gas_64 += _d(s['gascost_total_cost']) + pre_aggregate_gas
                    pre_gas_64_count += sector_count
            # ProveCommitSector ProveCommitAggregate
            if s['msg_method'] in [7, 26]:
                # if s['msg_method_name'] == 'ProveCommitSector':
                sector_count = 1
                if s['msg_method'] == 26:  # 多扇区封装
                    sector_count = max(s.get('sector_count', 0), sector_count)
                prove_aggregate_gas = _d(get_aggregate_gas(sector_count, int(s["base_fee2"]), height, s['msg_method']))
                if s['sector_size'] == '32 GiB':
                    prove_gas_32 += _d(s['gascost_total_cost']) + prove_aggregate_gas
                    prove_gas_32_count += sector_count
                else:
                    prove_gas_64 += _d(s['gascost_total_cost']) + prove_aggregate_gas
                    prove_gas_64_count += sector_count

        obj, created = TipsetGasSum.objects.get_or_create(height=height)
        obj.record_time = record_time

        obj.pre_gas_32 = pre_gas_32
        obj.pre_gas_count_32 = pre_gas_32_count
        obj.prove_gas_32 = prove_gas_32
        obj.prove_gas_count_32 = prove_gas_32_count
        obj.win_post_gas_32 = winpost_gas_32
        obj.win_post_gas_count_32 = winpost_gas_32_count
        obj.pre_gas_64 = pre_gas_64
        obj.pre_gas_count_64 = pre_gas_64_count
        obj.prove_gas_64 = prove_gas_64
        obj.prove_gas_count_64 = prove_gas_64_count
        obj.win_post_gas_64 = winpost_gas_64
        obj.win_post_gas_count_64 = winpost_gas_64_count

        obj.pre_gas = pre_gas_32 + pre_gas_64
        obj.pre_gas_count = pre_gas_32_count + pre_gas_64_count
        obj.prove_gas = prove_gas_32 + prove_gas_64
        obj.prove_gas_count = prove_gas_32_count + prove_gas_64_count
        obj.win_post_gas = winpost_gas_32 + winpost_gas_64
        obj.win_post_gas_count = winpost_gas_32_count + winpost_gas_64_count
        obj.base_fee = base_fee

        if pre_gas_32_count and prove_gas_32_count:
            obj.create_gas_32 = (pre_gas_32 / pre_gas_32_count + prove_gas_32 / prove_gas_32_count) * _d(32) / _d(
                10 ** 18)
        if pre_gas_64_count and prove_gas_64_count:
            obj.create_gas_64 = (pre_gas_64 / pre_gas_64_count + prove_gas_64 / prove_gas_64_count) * _d(16) / _d(
                10 ** 18)

        total_power_32 = MinerBase().get_miners_by_sector_type(sector_type=0, is_pool=False).aggregate(Sum('power'))[
            'power__sum'] or 0
        if total_power_32:
            obj.keep_gas_32 = winpost_gas_32 / (total_power_32 / _d(1024 ** 4)) / _d(10 ** 18)

        total_power_64 = MinerBase().get_miners_by_sector_type(sector_type=1, is_pool=False).aggregate(Sum('power'))[
            'power__sum'] or 0
        if total_power_64:
            obj.keep_gas_64 = winpost_gas_64 / (total_power_64 / _d(1024 ** 4)) / _d(10 ** 18)
        obj.save()

    def sync_tipset_gas_stat(self, height, messages=[]):
        '''24小时内每个tipset的各种gas费汇总'''

        # 删除7天以前的数据
        yesterday = datetime.datetime.now() - datetime.timedelta(days=7)
        TipsetGasStat.objects.filter(record_time__lt=yesterday).delete()

        stat_data = {}
        # 整理数据
        record_time = self.launch_date + datetime.timedelta(seconds=30 * height)
        for per in messages:
            s = per['_source']
            sector_type = 1 if s.get('sector_size', '32 GiB') == '64 GiB' else 0
            if not s.get('msg_method_name'):
                continue
            method = s['msg_method_name']

            # method = ''
            # if s['msg_method'] == 5:
            #     method = 'SubmitWindowedPoSt'
            # if s['msg_method'] == 6:
            #     method = 'PreCommitSector'
            # if s['msg_method'] == 7:
            #     method = 'ProveCommitSector'

            if not method:
                continue

            key = '%s_%s' % (method, sector_type)

            # 排除费用为0的记录
            total_cost = _d(s['gascost_total_cost'])
            if total_cost <= 0:
                continue

            if key not in stat_data:
                stat_data[key] = {
                    'method': method, 'sector_type': sector_type, 'count': 0, 'gas_limit': 0,
                    'gas_fee_cap': 0, 'gas_premium': 0, 'gas_used': 0, 'base_fee_burn': 0,
                    'total_cost': 0, 'msg_value': 0
                }

            stat_data[key]['count'] += 1
            stat_data[key]['gas_limit'] += _d(s['msg_gas_limit'])
            stat_data[key]['gas_fee_cap'] += _d(s['msg_gas_fee_cap'])
            stat_data[key]['gas_premium'] += _d(s['msg_gas_premium'])
            stat_data[key]['gas_used'] += _d(s['gascost_gas_used'])
            stat_data[key]['base_fee_burn'] += _d(s['gascost_base_fee_burn'])
            stat_data[key]['total_cost'] += total_cost
            stat_data[key]['msg_value'] += _d(s['msg_value'])

        # 新增数据
        for key in stat_data:
            per = stat_data[key]
            obj, created = TipsetGasStat.objects.get_or_create(height=height, method=per['method'],
                                                               sector_type=per['sector_type'])
            obj.record_time = record_time
            obj.count = per['count']
            obj.gas_limit = per['gas_limit']
            obj.gas_fee_cap = per['gas_fee_cap']
            obj.gas_premium = per['gas_premium']
            obj.gas_used = per['gas_used']
            obj.base_fee_burn = per['base_fee_burn']
            obj.total_cost = per['total_cost']
            obj.msg_value = per['msg_value']
            obj.save()

    def sync_pool_tipset_gas_stat(self, height, messages=[], pool_miners_dict={}):
        '''24小时内每个tipset的各种gas费汇总'''
        from miner.interface import MinerBase

        # 删除7天以前的数据
        yesterday = datetime.datetime.now() - datetime.timedelta(days=7)
        PoolTipsetGasStat.objects.filter(record_time__lt=yesterday).delete()

        stat_data = {}
        # 整理数据
        record_time = self.launch_date + datetime.timedelta(seconds=30 * height)
        for per in messages:
            s = per['_source']
            sector_type = 1 if s.get('sector_size', '32 GiB') == '64 GiB' else 0
            if not s.get('msg_method_name'):
                continue
            method = s['msg_method_name']

            # 是否是矿池矿工的消息
            if s.get('msg_to') not in pool_miners_dict:
                continue

            # method = ''
            # if s['msg_method'] == 5:
            #     method = 'SubmitWindowedPoSt'
            # if s['msg_method'] == 6:
            #     method = 'PreCommitSector'
            # if s['msg_method'] == 7:
            #     method = 'ProveCommitSector'

            if not method:
                continue

            key = '%s_%s' % (method, sector_type)

            # 排除费用为0的记录
            total_cost = _d(s['gascost_total_cost'])
            if total_cost <= 0:
                continue

            if key not in stat_data:
                stat_data[key] = {
                    'method': method, 'sector_type': sector_type, 'count': 0, 'gas_limit': 0,
                    'gas_fee_cap': 0, 'gas_premium': 0, 'gas_used': 0, 'base_fee_burn': 0,
                    'total_cost': 0, 'msg_value': 0
                }

            stat_data[key]['count'] += 1
            stat_data[key]['gas_limit'] += _d(s['msg_gas_limit'])
            stat_data[key]['gas_fee_cap'] += _d(s['msg_gas_fee_cap'])
            stat_data[key]['gas_premium'] += _d(s['msg_gas_premium'])
            stat_data[key]['gas_used'] += _d(s['gascost_gas_used'])
            stat_data[key]['base_fee_burn'] += _d(s['gascost_base_fee_burn'])
            stat_data[key]['total_cost'] += total_cost
            stat_data[key]['msg_value'] += _d(s['msg_value'])

        # 新增数据
        for key in stat_data:
            per = stat_data[key]
            obj, created = PoolTipsetGasStat.objects.get_or_create(height=height, method=per['method'],
                                                                   sector_type=per['sector_type'])
            obj.record_time = record_time
            obj.count = per['count']
            obj.gas_limit = per['gas_limit']
            obj.gas_fee_cap = per['gas_fee_cap']
            obj.gas_premium = per['gas_premium']
            obj.gas_used = per['gas_used']
            obj.base_fee_burn = per['base_fee_burn']
            obj.total_cost = per['total_cost']
            obj.msg_value = per['msg_value']
            obj.save()

    def get_block_by_message_id(self, message_id):
        return BbheEsBase().get_block_by_message_id(message_id=message_id)

    def sync_pledge_history(self, height, messages):
        """同步封装消息数据"""
        # 删除2天以前的数据
        yesterday = height - 2880 * 2
        PledgeHistory.objects.filter(height__lt=yesterday).delete()
        record_time = height_to_datetime(height)
        for per in messages:
            s = per['_source']
            miner_no = s['msg_to']
            # PreCommitSector
            msg_method_name = None
            msg_value = _d(s["msg_value"])
            if s['msg_method'] == 6:
                msg_method_name = s["msg_method_name"]
            # ProveCommitSector
            if s['msg_method'] == 7:
                msg_method_name = s["msg_method_name"]
            if msg_method_name and msg_value != _d(0):
                sector_number = json.loads(s["msg_params"]).get("SectorNumber")
                obj, created = PledgeHistory.objects.get_or_create(height=height, method=msg_method_name,
                                                                   sector_number=sector_number)
                obj.value = msg_value
                obj.record_time = record_time
                obj.miner_no = miner_no
                obj.msg_id = s["msg_cid"]["/"]
                obj.save()

    def sync_overtime_pledge(self):
        """检查2880+150周期Pre和Prove配对情况"""
        overtime_height = datetime_to_height(datetime.datetime.today()) - 3030
        sql = """
            SELECT
                a.miner_no,a.height,a.value,a.msg_id,a.sector_number
            FROM
                ( SELECT * FROM message_pledgehistory WHERE method = "PreCommitSector" AND height < %s ) AS a
                LEFT JOIN ( SELECT * FROM message_pledgehistory WHERE method = "ProveCommitSector" ) AS b 
                ON a.sector_number = b.sector_number 
                AND a.miner_no = b.miner_no 
            WHERE
                b.miner_no IS NULL
            """
        records = raw_sql.exec_sql(sql, [overtime_height])
        for record in records:
            obj, created = OvertimePledge.objects.get_or_create(msg_id=record[3])
            if created:
                obj.miner_no = record[0]
                obj.height = record[1] + 3030
                obj.record_time = height_to_datetime(record[1] + 3030)
                obj.value = record[2]
                obj.sector_number = record[4]
                obj.save()
