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
    str_2_power, format_fil_to_decimal, _d, format_coin_to_str, datetime_to_height
from explorer_s_common.decorator import validate_params, cache_required
from explorer_s_common.third.filfox_sdk import FilfoxBase
from explorer_s_common.third.bbhe_sdk import BbheBase, BbheEsBase

from explorer_s_data.consts import ERROR_DICT
from tipset.models import Tipset, TipsetBlock, TempTipsetBlock


class TipsetBase(object):

    def __init__(self):
        self.launch_date = datetime.datetime(2020, 8, 25, 6, 0, 0)

    def add_tipset(self, height, blocks=[]):
        record_time = self.launch_date + datetime.timedelta(seconds=30 * height)

        with transaction.atomic():
            tipset, created = Tipset.objects.get_or_create(height=height, record_time=record_time)

            total_win_count = 0
            total_block_count = 0
            total_reward = 0
            for per in blocks:
                # 排除空块
                if per['minerReward'] == '0':
                    continue
                block, c = TipsetBlock.objects.get_or_create(
                    block_hash=per['block_hash'], record_time=tipset.record_time
                )
                block.tipset = tipset
                block.miner_no = per['miner_no']
                block.msg_count = per['msg_count']
                block.win_count = per['win_count']
                block.reward = _d(per['reward'])
                block.penalty = _d(per['penalty']) if len(per['penalty']) <= 40 else _d(0)
                block.height = height
                block.save()

                total_win_count += per['win_count']
                total_block_count += 1
                total_reward += block.reward

            tipset.total_win_count = total_win_count
            tipset.total_block_count = total_block_count
            tipset.total_reward = total_reward
            tipset.save()
            return 1 if created else 0

    def sync_tipset(self, date):
        # 同步开始时间
        _time_start = time.time()
        # 每页大小
        page_size = 100

        now = datetime.datetime.now()

        # 开始时间戳
        start_date = datetime.datetime.strptime(date, '%Y-%m-%d')
        start_index = int((start_date - self.launch_date).total_seconds() / 30)

        # 结束时间戳
        end_date = datetime.datetime.strptime(date, '%Y-%m-%d') + datetime.timedelta(days=1)
        end_index = int((end_date - self.launch_date).total_seconds() / 30)

        logging.warning('%s %s' % (start_index, end_index))

        result = BbheBase().get_blocks(page_size=page_size, height=start_index + page_size)
        if not result.get('data', []):
            return format_return(0)

        success_count = 0
        while result.get('data', []) and start_index < end_index:
            i = 0
            temp_index = start_index
            for tipset in result['data']:
                height = tipset['height']
                while height != (temp_index + page_size - i):
                    self.add_tipset(height=temp_index + page_size - i, blocks=[])
                    start_index += 1
                    i += 1
                success_count += self.add_tipset(height=height, blocks=tipset['blocks'])
                start_index += 1
                i += 1

            result = BbheBase().get_blocks(page_size=page_size, height=start_index + page_size)

        logging.warning('同步总耗时: %s s' % (time.time() - _time_start))
        return format_return(0, data={'success_count': success_count})

    def sync_temp_tipset(self):
        '''
        从BBHE同步临时区块
        '''

        # 查询上次最后更新地址
        last_height = None
        last_record = TempTipsetBlock.objects.filter().order_by('-height')
        if last_record:
            last_height = last_record[0].height + 60

        result = BbheBase().get_blocks(page_size=60, height=last_height)
        if not result:
            return format_return(0)

        for tipset in result.get('data', []):
            height = tipset['height']
            record_time = self.launch_date + datetime.timedelta(seconds=30 * height)

            for per in tipset.get('blocks', []):
                # 排除空块
                if per['minerReward'] == '0':
                    continue
                block, c = TempTipsetBlock.objects.get_or_create(
                    block_hash=per['block_hash'], record_time=record_time
                )
                block.miner_no = per['miner_no']
                block.msg_count = per['msg_count']
                block.win_count = per['win_count']
                block.reward = per['reward']
                block.height = height
                block.save()

            # 往总表同步
            self.add_tipset(height=height, blocks=tipset.get('blocks', []))

        # 清除3天以前的数据
        yesterday = datetime.datetime.now() - datetime.timedelta(days=3)
        TempTipsetBlock.objects.filter(record_time__lt=yesterday).delete()

        return format_return(0)

    def get_tipsets(self, height=None):
        objs = Tipset.objects.all()
        if height is not None:
            objs = objs.filter(height__lte=height)
        return objs

    def get_tipset_by_height(self, height):
        objs = Tipset.objects.filter(height=height)
        return objs[0] if objs else None

    def get_miner_blocks(self, miner_no, start_time=None, end_time=None):
        query = TipsetBlock.objects.filter(miner_no=miner_no)
        if start_time:
            start_height = int((datetime.datetime.strptime(start_time + ' 00:00:00', "%Y-%m-%d %H:%M:%S") - self.launch_date).total_seconds() / 30)
            query = query.filter(height__gte=start_height)
        if end_time:
            end_height = int((datetime.datetime.strptime(end_time+' 23:59:59', "%Y-%m-%d %H:%M:%S") - self.launch_date).total_seconds() / 30)
            query = query.filter(height__lte=end_height)

        return query

    def get_miner_block_by_block_id(self, block_id):
        objs = TipsetBlock.objects.filter(block_hash=block_id)
        return objs[0] if objs else None

    def get_temp_block_date_range(self):
        '''获取临时区块24小时区间'''
        end_date = Tipset.objects.filter()[0].record_time
        start_date = Tipset.objects.filter()[2880].record_time
        return start_date, end_date

    def get_lucky(self, date=None, block=False):
        '''获取幸运值'''
        if date:
            start_date = date.strftime('%Y-%m-%d') + ' 00:00:00'
            end_date = (date + datetime.timedelta(days=1)).strftime('%Y-%m-%d') + ' 00:00:00'

            sql = """
                SELECT height, SUM(win_count), count(height)
                FROM tipset_tipsetblock
                WHERE %s <= record_time AND record_time < %s
                GROUP BY height
            """
            records = raw_sql.exec_sql(sql, [start_date, end_date])
        else:
            start_date, end_date = self.get_temp_block_date_range()
            sql = """
                SELECT height, SUM(win_count), count(height)
                FROM tipset_temptipsetblock
                WHERE %s <= record_time AND record_time < %s
                GROUP BY height
            """
            records = raw_sql.exec_sql(sql, [start_date, end_date])
        if not records:
            return _d(1)

        sum_win_count = 0
        sum_block_count = 0
        for per in records:
            sum_win_count += per[1]
            sum_block_count += per[2]

        if block:
            luck_v = _d(sum_block_count / (len(records) * 5))
        else:
            luck_v = _d(sum_win_count / (len(records) * 5))
        return min(1, luck_v)

    def get_temp_tipset_stat(self, miner_no=None):
        '''
        获取临时区块统计信息
        '''
        start_date, end_date = self.get_temp_block_date_range()
        conditions = (" AND miner_no = '%s' " % miner_no) if miner_no else ''
        sql = """
            SELECT miner_no, SUM(reward), SUM(win_count), COUNT(miner_no) 
            FROM tipset_temptipsetblock 
            WHERE %s <= record_time AND record_time < %s
        """ + conditions + """
            GROUP BY miner_no
        """

        return raw_sql.exec_sql(sql, [start_date, end_date])

    def get_date_tipset_stat(self, start_date=None, end_date=None, miner_no=None):
        '''获取指定日期的区块统计信息'''
        conditions = ''
        if start_date and miner_no:
            conditions = (" WHERE '%s' <= record_time AND record_time < '%s' AND miner_no = '%s' " % (
                start_date, end_date, miner_no))
        else:
            if start_date:
                conditions = (" WHERE '%s' <= record_time AND record_time < '%s' " % (start_date, end_date))
            if miner_no:
                conditions = (" WHERE miner_no = '%s' " % (miner_no))

        sql = """
            SELECT miner_no, SUM(reward), SUM(win_count), COUNT(miner_no) 
            FROM tipset_tipsetblock 
        """ + conditions + """
            GROUP BY miner_no
        """

        return raw_sql.exec_sql(sql)

    def get_temp_tipset_sum_reward(self):
        '''获取24小时临时奖励总和'''
        start_date, end_date = self.get_temp_block_date_range()
        return TempTipsetBlock.objects.filter(record_time__range=(start_date, end_date)).aggregate(Sum('reward'))[
                   'reward__sum'] or 0

    def get_temp_tipset_block_count(self):
        '''获取24小时临时奖出块数量'''
        start_date, end_date = self.get_temp_block_date_range()
        return TempTipsetBlock.objects.filter(record_time__range=(start_date, end_date)).count()

    def get_date_tipset_sum_reward(self, start_date=None, end_date=None):
        '''获取指定日期奖励总和'''
        objs = TipsetBlock.objects.filter()
        if start_date:
            objs = objs.filter(record_time__range=(start_date, end_date))
        return objs.aggregate(Sum('reward'))['reward__sum'] or 0

    def get_avg_block_time(self):
        '''获取24小时平均区间间隔'''
        start_date, end_date = self.get_temp_block_date_range()
        sql = """
            SELECT height FROM tipset_temptipsetblock 
            WHERE %s <= record_time AND record_time < %s 
            GROUP BY height;
        """
        records = raw_sql.exec_sql(sql, [start_date, end_date])
        return 30 * 2880 / len(records)

    def get_block_detail(self, block_id):
        info = BbheEsBase().get_block_detail(block_id=block_id)['hits']
        if not info:
            return {}

        info = info[0]['_source']
        info_2 = TipsetBlock.objects.get(block_hash=block_id)
        parent_blocks = [x.block_hash for x in TipsetBlock.objects.filter(height=info_2.height - 1)]

        return {
            'block_id': block_id,
            'height': info['height'],
            'miner_no': info['miner'],
            'create_time': datetime.datetime.fromtimestamp(info['timestamp']),
            'msg_count': info_2.msg_count,
            'reward': info_2.reward,
            'reward_str': format_coin_to_str(info_2.reward) + 'FIL',
            'win_count': info['win_count'],
            'parent_weight': info['parentWeight'],
            'parent_base_fee': info['parent_base_fee'],
            'parent_base_fee_str': format_coin_to_str(info['parent_base_fee']) + 'FIL',
            'penalty': info_2.penalty,
            'parent_blocks': parent_blocks
        }

    def get_block_message(self, block_id):
        return BbheEsBase().get_block_message(block_id=block_id)

    def sync_tipset_warning(self):
        '''同步block预警'''
        from explorer_s_common.mq.mq_kafka import Producer, MQ_TOPIC_SYS_ERROR

        now_height = datetime_to_height(datetime.datetime.now())
        if (now_height - TempTipsetBlock.objects.first().height) > 60:
            Producer().send(MQ_TOPIC_SYS_ERROR,
                            {'service': 'data', 'url': '同步block延迟预警', 'detail': 'TempTipsetBlock 数据延迟超过60个高度'})

    def get_block_count(self, date):
        # 日期转区块高度
        height = datetime_to_height(d=date)
        count = Tipset.objects.filter(height__gte=height).count()
        return count
