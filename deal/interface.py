import time
import json
import datetime
from django.db.models import Q,  Sum, Count

from explorer_s_common import  raw_sql
from explorer_s_common.utils import format_return, height_to_datetime
from explorer_s_common.third.bbhe_sdk import BbheEsBase

from deal.models import Deal


class DealBase(object):

    def __init__(self):
        self.launch_date = datetime.datetime(2020, 8, 25, 6, 0, 0)

    def get_deal_stat(self):
        return Deal.objects.filter().aggregate(Sum('piece_size'), Count('piece_size'))

    def get_deal_stat_from_es(self):
        '''直接从es统计'''
        return BbheEsBase().get_deal_stat()

    def sync_deal(self):
        '''增量更新订单'''
        now = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday = now - datetime.timedelta(days=1)
        start_height = int((yesterday - self.launch_date).total_seconds() / 30)
        end_height = int((now - self.launch_date).total_seconds() / 30)

        update_deals = BbheEsBase().get_update_deal(height=start_height).get('hits')
        increase_deals = BbheEsBase().get_increase_deal(height=end_height).get('hits')
        # 删除昨天之前就放弃的订单
        Deal.objects.filter(slash_epoch__lt=start_height, slash_epoch__gt=-1, start_epoch__lt=start_height).delete()
        # 删除昨天之前就应该开始但是没开始的订单
        Deal.objects.filter(start_epoch__lt=start_height, sector_start_epoch=-1).delete()

        count = 0
        for per in update_deals + increase_deals:
            s = per['_source']
            obj, created = Deal.objects.update_or_create(
                deal_id=s['DealID'], defaults=dict(
                    piece_cid=s['PieceCID']['/'], piece_size=s['PieceSize'],
                    is_verified=s['VerifiedDeal'], client=s['Client'], provider=s['Provider'],
                    start_epoch=s['StartEpoch'], end_epoch=s['EndEpoch'],
                    storage_price_per_epoch=s['StoragePricePerEpoch'],
                    provider_collateral=s['ProviderCollateral'], client_collateral=s['ClientCollateral'],
                    sector_start_epoch=s['SectorStartEpoch'], last_updated_epoch=s['LastUpdatedEpoch'],
                    slash_epoch=s['SlashEpoch']
                )
            )
            if created:
                count += 1

        return format_return(0, data=count)

    def sync_all_deal(self):
        '''全量更新订单'''
        # 同步开始时间
        _time_start = time.time()

        start_time = datetime.datetime.now().replace(hour=3, minute=0, second=0, microsecond=0)
        start_timestamp = int(start_time.timestamp())
        end_time = datetime.datetime.now().replace(hour=5, minute=0, second=0, microsecond=0)
        end_timestamp = int(end_time.timestamp())

        # 清空订单表
        # Deal.objects.all().delete()
        sql = '''DELETE FROM deal_deal'''
        raw_sql.exec_sql(sql, [])

        result = BbheEsBase().get_deal_by_sync_timestamp(timestamp=start_timestamp)
        while True:
            if start_timestamp > end_timestamp and not result.get('hits'):
                break

            objs = []
            for per in result.get('hits'):
                s = per['_source']
                objs.append(Deal(
                    deal_id=s['DealID'], piece_cid=s['PieceCID']['/'], piece_size=s['PieceSize'],
                    is_verified=s['VerifiedDeal'], client=s['Client'], provider=s['Provider'],
                    start_epoch=s['StartEpoch'], end_epoch=s['EndEpoch'],
                    storage_price_per_epoch=s['StoragePricePerEpoch'],
                    provider_collateral=s['ProviderCollateral'], client_collateral=s['ClientCollateral'],
                    sector_start_epoch=s['SectorStartEpoch'], last_updated_epoch=s['LastUpdatedEpoch'],
                    slash_epoch=s['SlashEpoch']
                ))
            if objs:
                Deal.objects.bulk_create(objs)

            start_timestamp += 60
            result = BbheEsBase().get_deal_by_sync_timestamp(timestamp=start_timestamp)
        print('总耗时:', time.time() - _time_start, 's')
        return format_return(0)

    def get_deal_list(self, key_words):
        """
        安装关键字搜索订单列表
        """
        if key_words:
            return Deal.objects.filter(Q(client__contains=key_words) | Q(provider__contains=key_words) | Q(deal_id__contains=key_words)).order_by(
                "-deal_id")
        return Deal.objects.filter().order_by("-deal_id")

    def sync_deal_new(self):
        """直接通过消息表解析并且更新订单"""
        start_height = 0
        deal = Deal.objects.filter().order_by("-height").first()
        if deal:
            start_height = deal.height
        deal_hits = BbheEsBase().get_messages_deal_list(start_height=start_height).get('hits', [])

        count = 0
        for per in deal_hits:
            s = per['_source']
            try:
                msg_return = json.loads(s.get("msg_return") or "{}")
                deals = json.loads(s.get("msg_params") or "{}").get("Deals", [])
            except:
                continue
            for i, deal_id in enumerate(msg_return.get("IDs", [])):
                deal_info = deals[i]["Proposal"]
                obj, created = Deal.objects.update_or_create(
                    deal_id=deal_id, defaults=dict(
                        piece_cid=deal_info['PieceCID']['/'], piece_size=deal_info['PieceSize'],
                        is_verified=deal_info['VerifiedDeal'], client=deal_info['Client'],
                        provider=deal_info['Provider'],
                        start_epoch=deal_info['StartEpoch'], end_epoch=deal_info['EndEpoch'],
                        storage_price_per_epoch=deal_info['StoragePricePerEpoch'],
                        provider_collateral=deal_info['ProviderCollateral'],
                        client_collateral=deal_info['ClientCollateral'],
                        height=s["height"], record_time=height_to_datetime(s["height"]), msg_cid=s["msg_cid"]
                    )
                )
                if created:
                    count += 1

        return format_return(0, data=count)

    def deal_all_list(self, height):
        """
        安装关键字搜索订单列表
        """
        return Deal.objects.filter(height=height, msg_cid__isnull=False).all()