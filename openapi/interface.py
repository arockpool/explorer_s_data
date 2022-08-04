from django.db.models import Sum, Count, Avg, F, IntegerField
from deal.models import Deal
from miner.interface import MinerBase
from explorer_s_common.page import Page
from explorer_s_common.decorator import validate_params, cache_required
from explorer_s_common import inner_server


@cache_required(cache_key='_get_total_miners', expire=60 * 60)
def _get_total_miners():
    total_deal = Deal.objects.aggregate(storage_deals=Count("deal_id"), data_stored=Sum("piece_size"))
    total_deal_verified = Deal.objects.filter(is_verified=True).aggregate(verified_storageDeals=Count("deal_id"),
                                                                          verified_dataStored=Sum("piece_size"))
    client_count = Deal.objects.values('client').distinct().count()
    provider_count = Deal.objects.values('provider').distinct().count()
    result = {
        "storage_deals": total_deal.get("storage_deals") or 0,
        "data_stored": total_deal.get("data_stored") or 0,
        "verified_storageDeals": total_deal_verified.get("verified_storageDeals") or 0,
        "verified_dataStored": total_deal_verified.get("verified_dataStored") or 0,
        "client": client_count,
        "provider": provider_count,
    }
    return result


def get_miners(page_index,page_size):
    """
    给予官方的向相关数据
    """

    result = _get_total_miners()

    # 每个miner
    objects = MinerBase().get_miner_list()
    data = Page(objects, page_size).page(page_index)
    miner_no_list = [tmp.miner_no for tmp in data["objects"]]

    miner_dict = {}
    # 订单总数 订单总存储数据
    miner_deals = Deal.objects.filter(provider__in=miner_no_list).values("provider")\
        .annotate(storage_deals=Count("deal_id"), data_stored=Sum("piece_size"),
                  storage_price=Avg(F("storage_price_per_epoch")*(F("end_epoch")-F("start_epoch")),
                                    output_field=IntegerField())).order_by()
    for miner_deal in miner_deals:
        miner_dict.setdefault(miner_deal["provider"], {})
        miner_dict[miner_deal["provider"]]["storage_deals"] = miner_deal["storage_deals"] or 0
        miner_dict[miner_deal["provider"]]["data_stored"] = miner_deal["data_stored"] or 0
        miner_dict[miner_deal["provider"]]["average_deal_cost"] = miner_deal["storage_price"] or 0
    # 验证过的订单数 验证过订单总存储数据
    miner_deals_verified = Deal.objects.filter(is_verified=True, provider__in=miner_no_list).values("provider")\
        .annotate(verified_storageDeals=Count("deal_id"), verified_dataStored=Sum("piece_size")).order_by()
    for miner_deal_verified in miner_deals_verified:
        miner_dict.setdefault(miner_deal_verified["provider"], {})
        miner_dict[miner_deal_verified["provider"]]["verified_storageDeals"] = miner_deal_verified["verified_storageDeals"] or 0
        miner_dict[miner_deal_verified["provider"]]["verified_dataStored"] = miner_deal_verified["verified_dataStored"] or 0
    # 标签
    apply_tag_dic = {}
    apply_tag_result = inner_server.get_miner_apply_tag(dict(miner_no_list=miner_no_list))
    if apply_tag_result.get("code") == 0:
        for apply_tag in apply_tag_result.get("data", []):
            apply_tag_dic[apply_tag["miner_no"]] = {"tag":apply_tag["en_tag"], "verified": apply_tag["signed"]}
    miners = []
    for miner in data["objects"]:
        tmp = dict(address=miner.miner_no, adjusted_power=miner.power, raw_power=miner.raw_power,
                   max_pieceSize=miner.max_pieceSize, min_pieceSize=miner.min_pieceSize, price=miner.price,
                   verified_price=miner.verified_price,)
        tmp.update(apply_tag_dic.get(miner.miner_no, {}))
        tmp.update({"storage_deals": 0, "data_stored": 0, "verified_storageDeals": 0, "verified_dataStored": 0,
                    "average_deal_cost":0 })
        tmp.update(miner_dict.get(miner.miner_no, {}))
        miners.append(tmp)
    data.pop("objects", None)
    result.update(data)
    result["miners"] = miners
    return result
