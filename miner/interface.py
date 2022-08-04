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

from explorer_s_common.third.bbhe_mng_sdk import BbheMngBase
from explorer_s_common import debug, consts, cache, raw_sql
from explorer_s_common.utils import format_return, Validator, format_power, format_price, format_fil, \
    str_2_power, format_fil_to_decimal, _d, get_aggregate_gas
from explorer_s_common.decorator import validate_params, cache_required
from explorer_s_common.third.filfox_sdk import FilfoxBase
from explorer_s_common.third.bbhe_sdk import BbheBase, BbheEsBase
from explorer_s_common.third.fam_sdk import FamBase
import pandas as pd
from tipset.interface import TipsetBase
from deal.interface import DealBase
from message.models import OvertimePledge
from miner.models import Miner, MinerDayStat, MinerDay, MinerSyncLog, Company, CompanyMiner, \
    MinerHotHistory
from explorer_s_common.third.bbhe_louts_sdk import BbheLoutsBase


class MinerBase(object):

    def __init__(self):
        self.launch_date = datetime.datetime(2020, 8, 25, 6, 0, 0)

    def get_miner_by_no(self, miner_no):
        objs = Miner.objects.filter(miner_no=miner_no)
        return objs[0] if objs else None

    def get_miner_list(self, is_pool=None, sector_type=None, miner_no_list=[]):
        objs = Miner.objects.filter(~Q(join_time=None))
        if is_pool is not None:
            objs = objs.filter(is_pool=is_pool)
        if sector_type is not None:
            if sector_type == '0':
                objs = objs.filter(sector_size=34359738368)
            if sector_type == '1':
                objs = objs.filter(sector_size=68719476736)
        if miner_no_list:
            objs = objs.filter(miner_no__in=miner_no_list)
        return objs

    def get_miner_ranking(self, miner_no):
        '''获取矿工排名'''
        ranking = 999
        miner = self.get_miner_by_no(miner_no=miner_no)
        if not miner:
            return ranking

        ranking = Miner.objects.filter(power__gt=miner.power).count() + 1
        return ranking

    def get_miner_day_records(self, miner_no=None, date=None, start_date=None, end_date=None, order=None,
                              big_miner=None):
        '''获取指定日期的矿工记录'''
        objs = MinerDay.objects.filter()
        if miner_no:
            if len(miner_no.split(",")) > 1:
                objs = objs.filter(miner_no__in=miner_no.split(","))
            else:
                objs = objs.filter(miner_no=miner_no)
        if date:
            objs = objs.filter(date=date)
        if start_date and end_date is None:
            objs = objs.filter(date__lt=start_date)
        if start_date and end_date:
            objs = objs.filter(date__range=(start_date, end_date))
        if order:
            objs = objs.order_by(order)
        if big_miner:
            # 查询加入时间大于30天的矿工
            miner_no_list = list(Miner.objects.filter(join_time__lte=start_date).values_list("miner_no", flat=True))
            objs = objs.filter(power__gte=str_2_power("1 PiB"), miner_no__in=miner_no_list)
        return objs

    def get_miner_24h_ranking_list(self, order=None, big_miner=None, sector_type=None, miner_no_list=[]):
        '''获取24小时的矿工排名记录'''
        objs = MinerDayStat.objects.filter()
        if order:
            objs = objs.order_by(order)

        # 查询加入时间大于30天并且算力大于1PiB的矿工
        if big_miner:
            join_time = datetime.datetime.now() - datetime.timedelta(days=30)
            objs = objs.filter(miner__power__gte=str_2_power("1 PiB"), miner__join_time__lte=join_time)
        if sector_type is not None:
            if sector_type == '0':
                objs = objs.filter(miner__sector_size=34359738368)
            if sector_type == '1':
                objs = objs.filter(miner__sector_size=68719476736)
        if miner_no_list:
            objs = objs.filter(miner__miner_no__in=miner_no_list)
        return objs

    def get_miner_24h_total_block_reward(self):
        """获取指定日期的出块总数"""
        total_block_reward = MinerDayStat.objects.filter().aggregate(block_reward=Sum("block_reward"))[
                                 'block_reward'] or 0
        return total_block_reward

    def get_miner_day_ranking_list(self, start_date, end_date, sector_type=None, miner_no_list=[],
                                   filter_type="increase_power"):
        """获取指定日期的矿工排行榜数据"""
        objs = MinerDay.objects.filter(date__range=(start_date, end_date))
        if sector_type is not None:
            if sector_type == '0':
                objs = objs.filter(sector_size=34359738368)
            if sector_type == '1':
                objs = objs.filter(sector_size=68719476736)
        if miner_no_list:
            objs = objs.filter(miner_no__in=miner_no_list)
        else:
            miner_no_list = [miner.miner_no for miner in Miner.objects.filter().only("miner_no").all()]
            objs = objs.filter(miner_no__in=miner_no_list)
        objs = objs.values_list("miner_no")
        if filter_type == "increase_power":
            objs = objs.annotate(avg_increase_power=Avg("increase_power"),
                                 increase_power_offset=Sum("increase_power_offset")).order_by("-avg_increase_power")
        if filter_type == "avg_reward":
            objs = objs.filter(avg_reward__lt=1).annotate(avg_avg_reward=Avg("avg_reward")).order_by("-avg_avg_reward")
        if filter_type == "block":
            objs = objs.annotate(win_count=Sum("win_count"), lucky=Avg("lucky"),
                                 block_reward=Sum("block_reward")).order_by("-win_count")
        return objs

    @cache_required("get_miner_day_ranking_list_cache_%s", expire=60 * 60)
    def get_miner_day_ranking_list_cache(self, ck, start_date, end_date, sector_type=None, miner_no_list=[],
                                         filter_type="increase_power"):

        return self.get_miner_day_ranking_list(start_date, end_date, sector_type=sector_type, miner_no_list=miner_no_list,
                                               filter_type=filter_type)

    @cache_required("get_miner_day_total_block_reward_%s", expire=60 * 24)
    def get_miner_day_total_block_reward(self, cl, start_date, end_date):
        """获取指定日期的出块总数"""
        total_block_reward = MinerDay.objects.filter(date__range=(start_date, end_date)).aggregate(block_reward=Sum("block_reward"))[
                                 'block_reward'] or 0
        return total_block_reward

    @cache_required("miner_day_records_for_month_avg_value_%s", expire=60 * 60 * 24)
    def get_miner_day_records_for_month_avg_value(self, date, order, data_queryset):
        """
        获得平均值的评分
        """
        data_field = order
        # 转为data frame 重构结构
        base_df = pd.DataFrame(list(data_queryset.values()))
        avg_df = base_df[["date", 'miner_no', data_field]]
        pivot_df = avg_df.pivot(index="miner_no", columns="date", values=data_field)
        mean_series = pivot_df.mean(skipna=True, axis=1)
        mean_dict = {"miner_no": mean_series.index, "mean_avg": mean_series.values}
        mean_df = pd.DataFrame(mean_dict)
        # 获得今日的算力,扇区质押,用于拼接到月平均算力
        today = pd.DataFrame(base_df)["date"].max()
        today_df = base_df[base_df['date'] == today]
        result_df = pd.merge(mean_df, today_df, how='inner', on='miner_no')
        # 排序
        result_df = result_df.sort_values(by=['mean_avg'], axis=0, ascending=False)
        return result_df.to_dict(orient="records")

    def get_companys(self, company_code):
        '''获取所有矿商'''
        if company_code:
            return Company.objects.filter(code=company_code)
        else:
            return Company.objects.filter()

    def get_miners_by_sector_type(self, sector_type=None, is_pool=None):
        '''根据扇区大小获取矿工列表'''
        objs = Miner.objects.filter()
        if sector_type is not None:
            sector_size = 34359738368 if str(sector_type) == '0' else 68719476736
            objs = objs.filter(sector_size=sector_size)
        if is_pool is not None:
            objs = objs.filter(is_pool=is_pool)
        return objs

    @cache_required(cache_key='data_miner_to_company', expire=24 * 60 * 60)
    def get_miner_to_company_mapping(self, must_update_cache=False):
        '''获取矿工对应的矿商'''
        data = {}
        for per in CompanyMiner.objects.filter():
            data[per.miner_no] = {'code': per.company.code, 'name': per.company.name}
        return data

    def get_148888_active_miners(self):
        '''获取148888高度的矿工信息'''
        data = BbheEsBase().get_148888_active_miners()['hits']
        return dict([(x['_source']['miner_id'], x['_source']) for x in data])

    def add_miner_hot_history(self, data):
        '''添加矿工48小时热表数据'''
        now = datetime.datetime.now()
        minute = math.floor(now.minute / 30) * 30
        record_time = datetime.datetime(now.year, now.month, now.day, now.hour, minute, 0)
        obj, created = MinerHotHistory.objects.get_or_create(miner_no=data['miner_no'], record_time=record_time)
        if created:
            obj.raw_power = data['raw_power']
            obj.power = data['power']
            obj.total_sector = data['total_sector']
            obj.active_sector = data['active_sector']
            obj.faulty_sector = data['faulty_sector']
            obj.recovering_sector = data['recovering_sector']
            obj.sector_size = data['sector_size']
            obj.save()

    def clear_miner_hot_history(self, days=2):
        '''定期清除热表历史记录'''
        delete_time = datetime.datetime.now() - datetime.timedelta(days=days)
        MinerHotHistory.objects.filter(record_time__lte=delete_time).delete()

    def get_24h_power_increase(self, miner_no):
        '''获取24小时封装量、算力增量'''
        now_record = MinerHotHistory.objects.filter(miner_no=miner_no)
        if not now_record:
            return 0, 0
        now_record = now_record[0]

        last_time = now_record.record_time - datetime.timedelta(days=1)
        last_record = MinerHotHistory.objects.filter(miner_no=miner_no, record_time__lte=last_time)
        if not last_record:
            return now_record.total_sector * now_record.sector_size, now_record.power
        last_record = last_record[0]
        # 计算封装量、算力增量
        increase_power = (now_record.total_sector - last_record.total_sector) * now_record.sector_size
        increase_power_offset = now_record.power - last_record.power
        return increase_power, increase_power_offset

    def update_miner_data(self, data, pool_miners=[]):
        miner, created = Miner.objects.get_or_create(miner_no=data['miner_no'])
        miner.miner_address = data['miner_address']
        miner.raw_power = data['raw_power']
        miner.power = data['power']
        miner.sector_size = data['sector_size']
        miner.total_sector = data['total_sector']
        miner.active_sector = data['active_sector']
        miner.faulty_sector = data['faulty_sector']
        miner.recovering_sector = data['recovering_sector']
        # miner.join_time = data['create_time']
        miner.balance = data['balance']
        miner.available_balance = data['available_balance']
        miner.pledge_balance = data['pledge_balance']
        miner.initial_pledge_balance = data['initial_pledge']
        miner.locked_pledge_balance = data['locked_funds']
        # miner.total_reward = 0
        # miner.total_block_count = 0
        # miner.total_win_count = 0
        miner.ip = data['ip']
        miner.peer_id = data['peer_id']
        miner.account_type = data['account_type']
        miner.worker = data['worker']
        miner.worker_balance = data.get('worker_blance_value') or 0
        miner.worker_address = data.get('worker_address')
        miner.owner = data['owner']
        miner.owner_balance = data.get('onwer_blance_value') or 0
        miner.owner_address = data.get('owner_address')
        miner.poster = data.get('poster_id')
        miner.poster_balance = data.get('post_blance_value') or 0
        miner.poster_address = data.get('post_address')
        if data['miner_no'] in pool_miners:
            miner.is_pool = True
        else:
            miner.is_pool = False
        miner.save()

        stat, created = MinerDayStat.objects.get_or_create(miner=miner)
        stat.lucky = data['lucky']
        stat.save()

    def get_miner_type(self, miner_no):
        # 数据可能存在的字段
        field_list_common = ["owner", "owner_address", "worker", "worker_address", "poster", "poster_address"]
        field_list_store = ["miner_no", "miner_address"]
        objs = Miner.objects.filter(
            Q(owner=miner_no) | Q(owner_address=miner_no) | Q(worker=miner_no) | Q(worker_address=miner_no) |
            Q(poster=miner_no) | Q(poster_address=miner_no) | Q(miner_no=miner_no) | Q(miner_address=miner_no))
        if not objs:
            data = objs[0].__dict__
            data = dict([val, key] for key, val in data.items() if isinstance(val, str))
            key = data.get(miner_no)
            if key in field_list_common:
                return "common"
            else:
                return "store"
        else:
            field_list_common = ["owner_id", "owner_address", "worker_id", "worker_address", "poster_id",
                                 "poster_address"]
            field_list_store = ["miner_id", "miner_address"]

            # 数据库中没有找到的话,需要去es中查找
            result = BbheEsBase().get_miner_info_by_address(miner_no)
            if result.get("hits"):
                data = result.get("hits")[0].get("_source")
                data = dict([val, key] for key, val in data.items() if isinstance(val, str))
                key = data.get(miner_no)
                if key in field_list_common:
                    return "common"
                else:
                    return "store"
            else:
                data = -1
            return data

    def sync_active_miners(self):
        '''
        同步有效矿工
        '''

        pool_miners = FamBase().get_pool_miners()['data']
        # pool_miners=[]
        page_index = 0
        page_size = 100
        result = BbheBase().get_active_miners(page_index=page_index, page_size=page_size)
        if not result:
            return format_return(0)

        while result.get('data', []):
            for per in result.get('data', []):
                self.update_miner_data(data=per, pool_miners=pool_miners)
                self.add_miner_hot_history(data=per)

            page_index += 1
            result = BbheBase().get_active_miners(page_index=page_index, page_size=page_size)

        # 删掉老数据
        date = datetime.datetime.now().strftime('%Y-%m-%d') + ' 00:00:00'
        for miner in Miner.objects.filter(update_time__lte=date):
            MinerDayStat.objects.filter(miner=miner).delete()
            miner.delete()

        # 同步矿工创建时间
        for miner in Miner.objects.filter(join_time__isnull=True):
            result = FilfoxBase().get_miner_overview(miner.miner_no)
            if result.get('createTimestamp'):
                miner.join_time = datetime.datetime.fromtimestamp(result['createTimestamp'])
            miner.save()
            time.sleep(1)

        # 定期清除热表历史记录
        self.clear_miner_hot_history()
        return format_return(0)

    def sync_pool_miners(self):
        '''同步矿池矿工'''
        result = FamBase().get_pool_miners()
        for per in result.get('data', []):
            Miner.objects.filter(miner_no=per).update(is_pool=True)
        return format_return(0)

    # def sync_miner(self, miner_no):
    #     '''
    #     同步矿工数据
    #     '''
    #     result = BbheBase().get_miner_detail(miner_no=miner_no)
    #     if not result:
    #         return format_return(0)

    #     self.update_miner_data(data=result['data'])

    #     return format_return(0)

    def sync_miner_temp_stat(self, miner_no=None):
        '''同步累计统计信息'''
        success = 0
        data = TipsetBase().get_temp_tipset_stat(miner_no=miner_no)
        dict_block_info = dict([(x[0], x) for x in data])

        for miner in Miner.objects.filter():
            temp = dict_block_info.get(miner.miner_no)
            stat, created = MinerDayStat.objects.get_or_create(miner=miner)
            stat.block_reward = temp[1] if temp else 0
            stat.win_count = temp[2] if temp else 0
            stat.block_count = temp[3] if temp else 0
            # 计算平均收益
            avg_reward = stat.block_reward / (miner.power / _d(math.pow(1024, 4))) if miner.power else 0
            stat.avg_reward = avg_reward / _d(math.pow(10, 18))
            # 计算24小时算力增速、增量
            increase_power, increase_power_offset = self.get_24h_power_increase(miner_no=miner.miner_no)
            stat.increase_power = increase_power
            stat.increase_power_offset = increase_power_offset
            stat.save()
            success += 1

        return format_return(0, data={'success': success})

    def sync_miner_lotus(self):
        '''链上价格和piece_size'''
        for miner in Miner.objects.filter():
            result_louts = BbheLoutsBase().bill_to_miner_no(miner.miner_no)
            if result_louts.get("code") == 0:
                miner.max_pieceSize = result_louts.get("data").get("max_piece_size", "0")
                miner.min_pieceSize = result_louts.get("data").get("min_piece_size", "0")
                miner.price = result_louts.get("data").get("price", "0")
                miner.verified_price = result_louts.get("data").get("verified_price", "0")
                miner.save()
        return format_return(0, )

    def sync_miner_day_stat(self, date=None, miner_no=None):
        '''同步指定日期统计信息'''
        start_date = datetime.datetime.strptime(date, '%Y-%m-%d')
        start_date_str = start_date.strftime('%Y-%m-%d') + ' 00:00:00'
        end_date = start_date + datetime.timedelta(days=1)
        end_date_str = end_date.strftime('%Y-%m-%d') + ' 00:00:00'

        success = 0
        data = TipsetBase().get_date_tipset_stat(start_date=start_date_str, end_date=end_date_str, miner_no=miner_no)
        for per in data:
            miner = self.get_miner_by_no(miner_no=per[0])
            if not miner:
                continue
            stat, created = MinerDayStat.objects.get_or_create(miner=miner)
            stat.block_reward = per[1]
            stat.win_count = per[2]
            stat.block_count = per[3]
            # 计算平均收益
            avg_reward = stat.block_reward / (miner.power / _d(math.pow(1024, 4)))
            stat.avg_reward = avg_reward / _d(math.pow(10, 18))
            stat.save()
            success += 1
        return format_return(0, data={'success': success})

    def sync_miner_total_stat(self, miner_no=None):
        '''同步累计统计信息'''
        success = 0
        data = TipsetBase().get_date_tipset_stat(miner_no=miner_no)
        # 优化数据过多很卡 已经快30多秒执行统计
        for per in data:
            miner = self.get_miner_by_no(miner_no=per[0])
            if not miner:
                continue
            miner.total_reward = per[1]
            miner.total_win_count = per[2]
            miner.total_block_count = per[3]
            miner.save()
            success += 1
        return format_return(0, data={'success': success})

    def sync_miner_history(self, date):
        '''记录历史快照，获取当日活跃矿工，与昨日对比计算增量'''
        page_index = 0
        page_size = 100
        result = BbheBase().get_active_miners(page_index=page_index, page_size=page_size)
        if not result:
            return format_return(0)

        while result.get('data', []):
            for per in result.get('data', []):
                self.add_miner_history(miner_no=per['miner_no'], date=date)
            page_index += 1
            result = BbheBase().get_active_miners(page_index=page_index, page_size=page_size)

        return format_return(0)

    def add_miner_history(self, miner_no, date=None):
        '''添加矿工历史数据'''
        record_date = datetime.datetime.strptime(date, '%Y-%m-%d')
        miner = self.get_miner_by_no(miner_no=miner_no)
        if not miner:
            return

        # 获取上一次的记录，用于计算增量
        last_record = MinerDay.objects.filter(miner_no=miner_no, date__lt=record_date.date())
        if last_record:
            last_record = last_record[0]

        # 新增扇区
        new_sector = miner.total_sector
        if last_record:
            new_sector = miner.total_sector - last_record.total_sector
        # 新增算力
        increase_power = new_sector * miner.sector_size
        # 新增算力增量
        increase_power_offset = 0
        if last_record:
            increase_power_offset = miner.power - last_record.power

        obj, created = MinerDay.objects.get_or_create(date=record_date.date(), miner_no=miner_no)
        obj.raw_power = miner.raw_power
        obj.power = miner.power
        obj.sector_size = miner.sector_size
        obj.total_sector = miner.total_sector
        obj.active_sector = miner.active_sector
        obj.faulty_sector = miner.faulty_sector
        obj.recovering_sector = miner.recovering_sector
        obj.new_sector = new_sector
        obj.balance = miner.balance
        obj.available_balance = miner.available_balance
        obj.pledge_balance = miner.pledge_balance
        obj.initial_pledge_balance = miner.initial_pledge_balance
        obj.locked_pledge_balance = miner.locked_pledge_balance
        obj.total_reward = miner.total_reward
        obj.total_block_count = miner.total_block_count
        obj.total_win_count = miner.total_win_count
        obj.increase_power = increase_power
        obj.increase_power_offset = increase_power_offset
        obj.worker = miner.worker
        obj.worker_balance = miner.worker_balance
        obj.worker_address = miner.worker_address
        obj.owner = miner.owner
        obj.owner_balance = miner.owner_balance
        obj.owner_address = miner.owner_address
        obj.poster = miner.poster
        obj.poster_balance = miner.poster_balance
        obj.poster_address = miner.poster_address

        start_date = datetime.datetime.strptime(date, '%Y-%m-%d')
        start_date_str = start_date.strftime('%Y-%m-%d') + ' 00:00:00'
        end_date = start_date + datetime.timedelta(days=1)
        end_date_str = end_date.strftime('%Y-%m-%d') + ' 00:00:00'
        data = TipsetBase().get_date_tipset_stat(start_date=start_date_str, end_date=end_date_str, miner_no=miner_no)
        for per in data:
            obj.block_reward = per[1]
            obj.win_count = per[2]
            obj.block_count = per[3]
            obj.save()

        day_stat = MinerDayStat.objects.filter(miner=miner)
        if day_stat:
            day_stat = day_stat[0]
            obj.avg_reward = day_stat.avg_reward
            obj.lucky = day_stat.lucky
        obj.save()

    def get_init_value(self, miner_no, fields, end_time):
        objs = MinerDay.objects.filter(date__lt=end_time, miner_no=miner_no)
        field_list = fields.split(",")
        result_dict = {}
        for field in field_list:
            if field == "create_gas":  # 生产gas
                pre_gas = objs.aggregate(sum=Sum('pre_gas'))['sum'] if objs.aggregate(sum=Sum('pre_gas'))['sum'] else 0
                prove_gas = objs.aggregate(sum=Sum('prove_gas'))['sum'] if objs.aggregate(sum=Sum('prove_gas'))[
                    'sum'] else 0
                result = pre_gas + prove_gas
            elif field == "initial_pledge_balance":
                if not objs:
                    result = 0
                else:
                    result = objs.order_by("date").last().initial_pledge_balance
            else:
                result = objs.aggregate(sum=Sum(field))['sum'] if objs.aggregate(sum=Sum(field))['sum'] else 0
            result_dict[field] = result
        return result_dict

    def sync_miner_day_gas_2(self, date):
        '''同步每日汽油费 使用es聚合'''
        _time_start = time.time()
        # 开始时间戳
        start_date = datetime.datetime.strptime(date, '%Y-%m-%d')
        start_height = int((start_date - self.launch_date).total_seconds() / 30)
        # 结束时间戳 SubmitWindowedPoSt PreCommitSector ProveCommitSector
        end_height = start_height + 2880

        # 统计 SubmitWindowedPoSt
        # result = BbheEsBase().get_miner_gas_cost_stat_2(
        #     msg_method_name=['SubmitWindowedPoSt'], start_height=start_height, end_height=end_height
        # )
        result = BbheEsBase().get_miner_gas_cost_stat(
            msg_method=['5'], start_height=start_height, end_height=end_height
        )
        for per in result.get('miner_group', {}).get('buckets', []):
            miner_no = per['key']
            gas = per['gas_sum']['value']
            count = per['doc_count']

            obj, created = MinerDay.objects.get_or_create(date=date, miner_no=miner_no)
            obj.win_post_gas = gas
            obj.win_post_gas_count = count
            obj.save()

        # 统计 PreCommitSector
        # result = BbheEsBase().get_miner_gas_cost_stat_2(
        #     msg_method_name=['PreCommitSector'], start_height=start_height, end_height=end_height
        # )
        result = BbheEsBase().get_miner_gas_cost_stat(
            msg_method=['6'], start_height=start_height, end_height=end_height
        )
        for per in result.get('miner_group', {}).get('buckets', []):
            miner_no = per['key']
            gas = per['gas_sum']['value']
            count = per['doc_count']

            obj, created = MinerDay.objects.get_or_create(date=date, miner_no=miner_no)
            obj.pre_gas = gas
            obj.pre_gas_count = count
            obj.save()

        # 统计 ProveCommitSector
        # result = BbheEsBase().get_miner_gas_cost_stat_2(
        #     msg_method_name=['ProveCommitSector'], start_height=start_height, end_height=end_height
        # )
        result = BbheEsBase().get_miner_gas_cost_stat(
            msg_method=['7'], start_height=start_height, end_height=end_height
        )
        for per in result.get('miner_group', {}).get('buckets', []):
            miner_no = per['key']
            gas = per['gas_sum']['value']
            count = per['doc_count']

            obj, created = MinerDay.objects.get_or_create(date=date, miner_no=miner_no)
            obj.prove_gas = gas
            obj.prove_gas_count = count
            obj.save()

        logging.warning('同步汽油费总耗时: %s s' % (time.time() - _time_start))
        return format_return(0)

    def sync_miner_day_gas(self, date, reset=True):
        '''同步每日汽油费'''
        _time_start = time.time()
        save_per_count = 200
        search_step = 5
        sync_obj, created = MinerSyncLog.objects.get_or_create(date=date)

        # 开始时间戳
        start_date = datetime.datetime.strptime(date, '%Y-%m-%d')
        start_index = int((start_date - self.launch_date).total_seconds() / 30)
        temp_index = max(start_index, sync_obj.gas_sync_height)

        # 结束时间戳
        end_date = start_date + datetime.timedelta(days=1)
        end_index = int((end_date - self.launch_date).total_seconds() / 30)

        # end_index = start_index + 110
        # 如果需要重置
        if reset:
            # 重置进度表
            sync_obj.gas_sync_height = start_index
            sync_obj.save()
            temp_index = start_index
            # 重置每日矿工表
            MinerDay.objects.filter(date=date).update(pre_gas=0, prove_gas=0, win_post_gas=0, pre_gas_count=0,
                                                      prove_gas_count=0, win_post_gas_count=0)

        def _add_v(d, k, t, v, ps, s_c=1):
            if k not in d:
                d[k] = {
                    'pre_gas': 0, 'prove_gas': 0, 'win_post_gas': 0, 'pledge_gas': 0,
                    'pre_gas_count': 0, 'prove_gas_count': 0, 'win_post_gas_count': 0
                }
            d[k][t] += v
            d[k]["pledge_gas"] += ps
            d[k][t + '_count'] += s_c

        miner_gas_dict = {}
        while temp_index < end_index:
            result = BbheEsBase().get_height_messages(
                heights=[x for x in range(temp_index, temp_index + search_step)])
            messages = result.get('hits', [])
            for per in messages:
                s = per['_source']
                miner_no = s['msg_to']

                # SubmitWindowedPoSt
                if s['msg_method'] == 5:
                    # if s.get('msg_method_name') == 'SubmitWindowedPoSt':
                    _add_v(miner_gas_dict, miner_no, 'win_post_gas', _d(s['gascost_total_cost']), _d(s['msg_value']))
                # PreCommitSector PreCommitSectorBatch
                if s['msg_method'] in [6, 25]:
                    # if s.get('msg_method_name') == 'PreCommitSector':
                    pre_agg_gas = _d(0)
                    sector_count = 1
                    if s['msg_method'] == 25:  # 多扇区封装
                        try:
                            msg_params = json.loads(s.get("msg_params") or "{}")
                            sector_count = max(len(msg_params.get("Sectors", [])), sector_count)
                        except:
                            pass
                        if s.get('msgrct_exit_code', 0) == 0:
                            pre_agg_gas = _d(get_aggregate_gas(sector_count, int(s["base_fee2"]),
                                                               s["height"], s['msg_method']))
                    _add_v(miner_gas_dict, miner_no, 'pre_gas', _d(s['gascost_total_cost']) + pre_agg_gas,
                           _d(s['msg_value']), sector_count)
                # ProveCommitSector ProveCommitAggregate
                if s['msg_method'] in [7, 26]:
                    # if s.get('msg_method_name') == 'ProveCommitSector':
                    prove_agg_gas = _d(0)
                    sector_count = 1
                    if s['msg_method'] == 26:  # 多扇区封装
                        sector_count = max(s.get('sector_count', 0), sector_count)
                        if s.get('msgrct_exit_code', 0) == 0:
                            prove_agg_gas = _d(get_aggregate_gas(sector_count, int(s["base_fee2"]),
                                                                 s["height"], s['msg_method']))
                    _add_v(miner_gas_dict, miner_no, 'prove_gas', _d(s['gascost_total_cost']) + prove_agg_gas,
                           _d(s['msg_value']), sector_count)

            temp_index += search_step
            # 每隔save_per_count次保存一次
            if temp_index % save_per_count == 0:
                self.save_miner_gas(data=miner_gas_dict, date=date, height=temp_index)
                miner_gas_dict = {}
        # 收尾
        if miner_gas_dict:
            self.save_miner_gas(data=miner_gas_dict, date=date, height=temp_index)

        logging.warning('同步汽油费总耗时: %s s' % (time.time() - _time_start))
        return format_return(0)

    def sync_miner_day_overtime_pledge_fee(self, date):
        result = BbheMngBase().get_ribao_cost(date)
        for miner_info in result.get("data"):
            miner_no = miner_info.get('miner_id')
            overtime_pledge_fee = float(miner_info.get('overtime_pledge_fee')) * (10 ** 18)
            miner_objs = self.get_miner_day_records(miner_no=miner_no, date=date)
            if miner_objs:
                miner_obj = miner_objs[0]
                miner_obj.overtime_pledge_fee = overtime_pledge_fee
                miner_obj.save()
        return format_return(0)

    def save_miner_gas(self, data, date, height):
        '''保存汽油费'''
        # with transaction.atomic():
        for miner_no in data:
            obj, created = MinerDay.objects.get_or_create(date=date, miner_no=miner_no)
            obj.pre_gas += data[miner_no]['pre_gas']
            obj.pre_gas_count += data[miner_no]['pre_gas_count']
            obj.prove_gas += data[miner_no]['prove_gas']
            obj.prove_gas_count += data[miner_no]['prove_gas_count']
            obj.win_post_gas += data[miner_no]['win_post_gas']
            obj.win_post_gas_count += data[miner_no]['win_post_gas_count']
            obj.pledge_gas += data[miner_no]['pledge_gas']
            obj.save()

        sync_obj, created = MinerSyncLog.objects.get_or_create(date=date)
        sync_obj.gas_sync_height = height
        sync_obj.save()
        logging.warning('保存汽油费-->%s %s %s' % (len(data.keys()), date, height))

    def get_pool_miner_detail(self, miner_no):
        result_miner = BbheEsBase().get_pool_miner_detail(miner_no)
        result_balance = BbheEsBase().get_pool_miner_wallet_detail(miner_no)
        data_miner = result_miner.get("hits")[0].get("_source")
        data_balance = result_balance.get("hits")[0].get("_source")
        data_miner.update(data_balance)
        return data_miner

    def get_pool_activate_miner_detail(self, miner_no):
        result = BbheEsBase().get_pool_miner_detail(miner_no)
        if result.get("hits"):
            data = result.get("hits")[0].get("_source")
            miner_wallet_search = BbheEsBase().get_pool_miner_wallet_detail(miner_no)
            data.update(miner_wallet_search.get("hits")[0].get("_source"))
        else:
            data = result.get("hits")
        return data

    def get_pool_attention_miner_detail(self, miner_no):
        result = BbheEsBase().get_pool_attention_miner_detail(miner_no)
        if result.get("hits"):
            data = result.get("hits")[0].get("_source")
            miner_wallet_search = BbheEsBase().get_pool_miner_wallet_detail(miner_no)
            if not miner_wallet_search.get("hits"):
                pass
            else:
                data.update(miner_wallet_search.get("hits")[0].get("_source"))
        else:
            data = result.get("hits")
        return data

    def get_miner_increment(self, miner_no, date, key=None):
        """
        获取该日的增量
        """
        before_day = str((datetime.datetime.strptime(date, "%Y-%m-%d") - datetime.timedelta(days=1)).date())
        forget_day_data = MinerDay.objects.filter(miner_no=miner_no, date=date).first()
        before_day_data = MinerDay.objects.filter(miner_no=miner_no, date=before_day).first()
        if not forget_day_data or not before_day_data:
            return format_return(15000, msg="数据缺失")
        else:
            pass
        if key:
            fields_data = [key]
        else:
            fields_data = forget_day_data._meta.fields

        result_dict = dict()
        for field_obj in fields_data:
            field = field_obj.name
            if isinstance(eval("forget_day_data.{}".format(field)), int) or isinstance(
                    eval("forget_day_data.{}".format(field)), decimal.Decimal):
                result_dict[field] = eval("forget_day_data.{}".format(field)) - eval("before_day_data.{}".format(field))
        return format_return(0, data=result_dict)

    def get_miner_mining_stats_by_no(self, miner_no, stats_type):
        """
        矿工详情展示产出统计
        """
        now_date = datetime.datetime.today()

        def _fomoat_data(days):
            increase_power = _d(0)
            increase_power_offset = _d(0)
            block_reward = _d(0)
            block_count = 0
            win_count = 0
            lucky = _d(0)
            objs = MinerDay.objects.filter(date__gte=days, miner_no=miner_no)
            if not objs:
                return format_return(0)
            power = objs[0].power
            count = 0
            for obj in objs:
                count += 1
                increase_power += obj.increase_power
                increase_power_offset += obj.increase_power_offset
                block_reward += obj.block_reward
                block_count += obj.block_count
                win_count += obj.win_count
                lucky += obj.lucky
            # 计算平均收益
            avg_reward = 0
            if power:
                avg_reward = block_reward / (power / _d(math.pow(1024, 4)))
            if count:
                lucky = lucky / count
            result_dict = dict(increase_power_24=increase_power, increase_power_offset_24=increase_power_offset,
                               block_reward=block_reward, block_count=block_count, win_count=win_count,
                               avg_reward=format_fil(avg_reward), lucky=format_price(lucky, 4))
            return format_return(0, data=result_dict)

        if stats_type == "7d":
            ds_7 = now_date - datetime.timedelta(days=7)
            return _fomoat_data(ds_7)
        if stats_type == "30d":
            ds_30 = now_date - datetime.timedelta(days=30)
            return _fomoat_data(ds_30)
        return format_return(0)

    def get_miner_line_chart_by_no(self, miner_no, stats_type):
        """
        矿工的算力变化和出块统计
        """
        now_date = datetime.datetime.today()
        if stats_type == "30d":
            ds_30 = now_date - datetime.timedelta(days=30)
            ds_30_list = [ds_30 + datetime.timedelta(days=1 * x) for x in range(0, 30)]
            objs = MinerDay.objects.filter(date__gte=ds_30, miner_no=miner_no)
            ds_30_dict = {}
            for obj in objs:
                ds_30_dict[obj.date.strftime('%Y-%m-%d')] = {
                    "power": obj.power,
                    "increase_power_offset": obj.increase_power_offset,
                    "block_reward": obj.block_reward,
                    "block_count": obj.block_count,
                    "date": obj.date.strftime('%Y-%m-%d')
                }
            ds_30_result = []
            for day1 in ds_30_list:
                ds_30_result.append(ds_30_dict.get(day1.strftime('%Y-%m-%d'), {
                    "power": 0,
                    "increase_power_offset": 0,
                    "block_reward": 0,
                    "block_count": 0,
                    "date": day1.strftime('%Y-%m-%d')
                }))
            return ds_30_result

        if stats_type == "180d":
            ds_180 = now_date - datetime.timedelta(days=180)
            ds_180_list = [now_date - datetime.timedelta(days=6 * x + 1) for x in range(0, 30)]
            objs = MinerDay.objects.filter(date__gte=ds_180, miner_no=miner_no)
            ds_180_dict = {}
            for obj in objs:
                ds_180_dict[obj.date.strftime('%Y-%m-%d')] = {
                    "power": obj.power,
                    "increase_power_offset": obj.increase_power_offset,
                    "block_reward": obj.block_reward,
                    "block_count": obj.block_count,
                    "date": obj.date.strftime('%Y-%m-%d')
                }
            ds_180_list.reverse()
            ds_180_result = []
            for i, day6 in enumerate(ds_180_list):
                power = ds_180_dict.get(day6.strftime('%Y-%m-%d'), {}).get('power', 0)
                increase_power_offset = _d(0)
                block_reward = _d(0)
                block_count = 0
                for day1 in [day6 - datetime.timedelta(days=x) for x in range(0, 6)]:
                    day_ = day1.strftime('%Y-%m-%d')
                    increase_power_offset += ds_180_dict.get(day_, {}).get('increase_power_offset', _d(0))
                    block_reward += ds_180_dict.get(day_, {}).get('block_reward', _d(0))
                    block_count += ds_180_dict.get(day_, {}).get('block_count', 0)
                ds_180_result.append({
                    "power": power,
                    "increase_power_offset": increase_power_offset,
                    "block_reward": block_reward,
                    "block_count": block_count,
                    "date": day6.strftime('%Y-%m-%d')
                })
            return ds_180_result

        if stats_type == "24h":
            hs_24 = datetime.datetime.now() - datetime.timedelta(days=1)
            hs_24_list = [(hs_24 + datetime.timedelta(hours=1 * x)).replace(minute=0, second=0, microsecond=0) for x in
                          range(0, 24)]

            condition = "WHERE miner_no = '%s' AND record_time >= '%s'" % (miner_no,
                                                                           hs_24_list[0].strftime('%Y-%m-%d %H'))
            sql = """
                SELECT sum(reward), DATE_FORMAT(record_time ,'%Y-%m-%d %H'),count(*)
                FROM tipset_temptipsetblock
                """ + condition + """
                GROUP BY  DATE_FORMAT(record_time ,'%Y-%m-%d %H')
            """
            objs = raw_sql.exec_sql(sql)
            hs_24_dict = {}
            for obj in objs:
                hs_24_dict[obj[1]] = {
                    "block_reward": obj[0],
                    "block_count": obj[2],
                    "date": obj[1] + ":00:00"
                }
            hs_24_result = []
            for hs1 in hs_24_list:
                hs_24_result.append(hs_24_dict.get(hs1.strftime('%Y-%m-%d %H'), {
                    "block_reward": 0,
                    "block_count": 0,
                    "date": hs1.strftime('%Y-%m-%d %H:%M:%S')
                }))
            return hs_24_result

    def get_miner_day_stat_info(self, miner_no):
        miner = Miner.objects.filter(miner_no=miner_no).first()
        if miner:
            return miner, MinerDayStat.objects.filter(miner=miner).first()
        return None, None

    def get_overtime_pledge(self, miner_no, start_date=None, end_date=None):
        """获取指定实际内过期质押"""
        now = datetime.datetime.now()
        if not start_date:
            start_date = (now - datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
            end_date = now.strftime('%Y-%m-%d %H:%M:%S')
        return OvertimePledge.objects.filter(miner_no=miner_no, record_time__range=(start_date, end_date)).aggregate(
            Avg('value'))['value__avg'] or 0

    def get_gas_cost_by_miner_no(self, miner_no):
        '''根据矿工ID获取指定时间段矿工gas消耗'''
        # 单个矿工的生产gas 和全网计算不同
        # pre+prove+过期质押/算力增加量
        end_height = int((datetime.datetime.now() - self.launch_date).total_seconds() / 30)
        # SubmitWindowedPoSt PreCommitSector ProveCommitSector
        start_height = end_height - 2880
        data = BbheEsBase().get_gas_cost_stat_by_miner_no(miner_no, [5, 6, 25, 26, 7], start_height,
                                                            end_height)
        create_total_gas = _d(0)
        winpost_gas = _d(0)
        pledge_gas = _d(0)
        for per in data.get('miner_group', {}).get('buckets', []):
            if per['key'] in [7, 6, 25, 26]:
                create_total_gas += _d(per['gas_sum']['value'])
                pledge_gas += _d(per['pledge_sum']['value'])
            if per['key'] == 5:
                winpost_gas = _d(per['gas_sum']['value'])
        overtime_pledge = self.get_overtime_pledge(miner_no)
        create_gas = overtime_pledge + create_total_gas
        return create_gas, winpost_gas, pledge_gas, create_gas + winpost_gas + pledge_gas

    def get_gas_cost_stat_by_miner_no(self, miner_no, stat_type="24h"):
        '''根据矿工ID获取指定时间段矿工gas消耗统计分析'''
        # SubmitWindowedPoSt PreCommitSector ProveCommitSector
        height = 2880
        if stat_type == "7d":
            height *= 7
        if stat_type == "30d":
            height *= 30
        end_height = int((datetime.datetime.now() - self.launch_date).total_seconds() / 30)
        start_height = end_height - height
        data = BbheEsBase().get_gas_cost_stat_by_miner_no(miner_no, [], start_height,
                                                            end_height, is_stat=True)

        result = {x['key']: x['gas_sum']['value'] for x in data["miner_group"]["buckets"] if
                  x['key'] in [5, 6, 7, 25, 26]}
        total_gas = data["gas_sum_total"]["value"]
        win_gas = result.get(5, 0)
        pre_gas = result.get(6, 0)
        prove_gas = result.get(7, 0)
        pre_gas_batch = result.get(25, 0)
        prove_gas_aggregate = result.get(26, 0)
        return dict(total_gas=format_fil_to_decimal(total_gas, 4),
                    SubmitWindowedPoSt=format_fil_to_decimal(win_gas, 4),
                    PreCommitSector=format_fil_to_decimal(pre_gas, 4),
                    ProveCommitSector=format_fil_to_decimal(prove_gas, 4),
                    PreCommitSectorBatch=format_fil_to_decimal(pre_gas_batch, 4),
                    ProveCommitAggregate=format_fil_to_decimal(prove_gas_aggregate, 4),
                    other_gas=format_fil_to_decimal(total_gas - win_gas - pre_gas - prove_gas, 4))

    @cache_required(cache_key='get_messages_stat_by_miner_no_%s', expire=2 * 60)
    def get_messages_stat_by_miner_no(self, ck, miner_no, stat_type="24h"):
        '''根据矿工ID获取指定时间段矿工gas消耗统计分析'''
        # SubmitWindowedPoSt PreCommitSector ProveCommitSector
        height = 2880
        if stat_type == "7d":
            height *= 7
        if stat_type == "30d":
            height *= 30
        end_height = int((datetime.datetime.now() - self.launch_date).total_seconds() / 30)
        start_height = end_height - height
        msg_methods = [5, 6, 7, 25, 26]
        data = BbheEsBase().get_messages_stat_by_miner_no(miner_no, msg_methods, start_height, end_height)

        result = {'SubmitWindowedPoSt': {"count": 0, "ok_count": 0, "error_count": 0},
                  'PreCommitSector': {"count": 0, "ok_count": 0, "error_count": 0},
                  'ProveCommitSector': {"count": 0, "ok_count": 0, "error_count": 0},
                  'PreCommitSectorBatch': {"count": 0, "ok_count": 0, "error_count": 0},
                  'ProveCommitAggregate': {"count": 0, "ok_count": 0, "error_count": 0},
                  'others': {"count": 0, "ok_count": 0, "error_count": 0},
                  }
        for methods in data["miner_group"]["buckets"]:
            method_name = methods['key']
            result[method_name]['count'] = methods["doc_count"]
            for per in methods["msg_status"]["buckets"]:
                if per['key'] == 0:
                    result[method_name]["ok_count"] = per["doc_count"]
                else:
                    result[method_name]["error_count"] = per["doc_count"]
            result[method_name]["ok_rate"] = round(result[method_name]["ok_count"] / result[method_name]['count'], 4)
        # 其他类型
        data_others = BbheEsBase().get_messages_stat_others_by_miner_no(miner_no, msg_methods, start_height, end_height)
        for per in data_others["msg_status"]["buckets"]:
            if per['key'] == 0:
                result["others"]["ok_count"] = per["doc_count"]
            else:
                result["others"]["error_count"] = per["doc_count"]
            result["others"]['count'] += per["doc_count"]

        result["others"]["ok_rate"] = round(result["others"]["ok_count"] / result["others"]['count'], 4) if result["others"]['count'] else 0

        return result

    def calc_create_gas(self, pre_gas, pre_gas_count, prove_gas, prove_gas_count, sector_size):
        """
        计算生产gas费
        """
        return (pre_gas / max(pre_gas_count, 1) + prove_gas / max(prove_gas_count, 1)) * (
            _d(32) if sector_size == 34359738368 else _d(16))
