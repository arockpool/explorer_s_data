import json
import datetime
import math
from collections import Iterable
from explorer_s_common.decorator import common_ajax_response
from explorer_s_common.utils import format_return, format_price, format_power, format_fil_to_decimal, format_fil, \
    format_power_to_TiB, _d
from explorer_s_common.page import Page
from miner.interface import MinerBase
from tipset.interface import TipsetBase
from overview.interface import OverviewBase


def format_miner(objs):
    if objs is None:
        return None

    def _format_obj(obj):
        stat = obj.miner_day_stat
        date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        objs = MinerBase().get_miner_day_records(miner_no=obj.miner_no, date=date)
        increase_power = 0
        increase_power_offset = 0
        is_32 = True if obj.sector_size == 34359738368 else False  # 是否是32扇区
        total_gas = 0
        create_gas = 0
        pledge_gas = 0
        overview_day_create_gas = 0  # 全网昨日生成值
        overview_day = OverviewBase().get_overview_one_day_records(date)
        if overview_day:
            overview_day_create_gas = overview_day.create_gas_32 if is_32 else overview_day.create_gas_64
        if objs:
            increase_power = objs[0].increase_power
            increase_power_offset = objs[0].increase_power_offset
            pledge_gas = objs[0].pledge_gas
            create_total_gas = objs[0].pre_gas + objs[0].prove_gas + objs[0].overtime_pledge_fee
            total_gas = create_total_gas + objs[0].win_post_gas
            create_gas = (create_total_gas / (increase_power / _d(math.pow(1024, 4)))) if increase_power else 0
        gas_offset = format_fil_to_decimal(create_gas, 4) - format_fil_to_decimal(overview_day_create_gas, 4)
        return {
            'miner_no': obj.miner_no, 'miner_address': obj.miner_address,
            'raw_power': obj.raw_power, 'power': obj.power,
            'sector_size': obj.sector_size, 'total_sector': obj.total_sector,
            'active_sector': obj.active_sector, 'faulty_sector': obj.faulty_sector,
            'recovering_sector': obj.recovering_sector,
            'join_time': obj.join_time.strftime('%Y-%m-%d %H:%M:%S'),
            'balance': obj.balance, 'available_balance': obj.available_balance,
            'pledge_balance': obj.pledge_balance, 'initial_pledge_balance': obj.initial_pledge_balance,
            'locked_pledge_balance': obj.locked_pledge_balance, 'total_reward': obj.total_reward,
            'total_block_count': obj.total_block_count, 'total_win_count': obj.total_win_count,
            'ip': obj.ip, 'peer_id': obj.peer_id, 'worker': obj.worker,
            'owner': obj.owner, 'ranking': MinerBase().get_miner_ranking(miner_no=obj.miner_no),
            'is_pool': obj.is_pool, 'avg_reward': stat.avg_reward, 'lucky': stat.lucky,
            'block_reward': stat.block_reward, 'block_count': stat.block_count, 'win_count': stat.win_count,
            'increase_power_24': stat.increase_power, 'increase_power_offset_24': stat.increase_power_offset,
            'worker_balance': obj.worker_balance, 'worker_address': obj.worker_address,
            'owner_balance': obj.owner_balance, 'owner_address': obj.owner_address,
            'poster': obj.poster, 'poster_balance': obj.poster_balance, 'poster_address': obj.poster_address,
            # gas 消耗
            'day_increase_power': format_power_to_TiB(increase_power),
            'day_increase_power_offset': format_power_to_TiB(increase_power_offset),
            'day_total_gas': format_fil(total_gas), 'day_pledge_gas': pledge_gas,
            'day_create_gas': format_fil(create_gas),
            'day_overview_create_gas': format_fil(overview_day_create_gas), 'day_gas_offset': gas_offset,
        }

    return [_format_obj(obj) for obj in objs] if isinstance(objs, Iterable) else _format_obj(objs)


def format_miner_day(objs):
    if objs is None:
        return None

    def _format_obj(obj):
        return {
            'miner_no': obj.miner_no,
            'raw_power': obj.raw_power, 'power': obj.power,
            'sector_size': obj.sector_size, 'total_sector': obj.total_sector,
            'active_sector': obj.active_sector, 'faulty_sector': obj.faulty_sector,
            'recovering_sector': obj.recovering_sector, 'new_sector': obj.new_sector,
            'balance': obj.balance, 'available_balance': obj.available_balance,
            'pledge_balance': obj.pledge_balance, 'initial_pledge_balance': obj.initial_pledge_balance,
            'locked_pledge_balance': obj.locked_pledge_balance, 'total_reward': obj.total_reward,
            'total_block_count': obj.total_block_count, 'total_win_count': obj.total_win_count,
            'increase_power': obj.increase_power, 'increase_power_offset': obj.increase_power_offset,
            'pre_gas': obj.pre_gas, 'prove_gas': obj.prove_gas, 'win_post_gas': obj.win_post_gas,
            'pre_gas_count': obj.pre_gas_count, 'prove_gas_count': obj.prove_gas_count,
            'avg_reward': obj.avg_reward, 'lucky': obj.lucky, 'date': obj.date.strftime('%Y-%m-%d'),
            'block_reward': obj.block_reward, 'block_count': obj.block_count, 'win_count': obj.win_count,
            'worker': obj.worker, 'worker_balance': obj.worker_balance, 'worker_address': obj.worker_address,
            'owner': obj.owner, 'owner_balance': obj.owner_balance, 'owner_address': obj.owner_address,
            'poster': obj.poster, 'poster_balance': obj.poster_balance, 'poster_address': obj.poster_address,
            'overtime_pledge_fee': obj.overtime_pledge_fee, 'pledge_gas': obj.pledge_gas
        }

    return [_format_obj(obj) for obj in objs] if isinstance(objs, Iterable) else _format_obj(objs)


@common_ajax_response
def get_miner_list(request):
    '''获取矿工列表'''
    is_pool = request.POST.get('is_pool')
    page_index = int(request.POST.get('page_index', 1))
    page_size = min(int(request.POST.get('page_size', 10)), 1000)
    sector_type = request.POST.get('sector_type')
    miner_no_list = json.loads(request.POST.get('miner_no_list', '[]'))
    objs = MinerBase().get_miner_list(is_pool=is_pool, sector_type=sector_type, miner_no_list=miner_no_list)
    data = Page(objs, page_size).page(page_index)

    return format_return(0, data={
        'objs': format_miner(data['objects']), 'total_page': data['total_page'], 'total_count': data['total_count']
    })


@common_ajax_response
def get_miner_list_by_miners(request):
    '''获取矿工列表'''
    page_index = int(request.POST.get('page_index', 1))
    page_size = min(int(request.POST.get('page_size', 10)), 1000)
    miner_no_list = json.loads(request.POST.get('miner_no_list', '[]'))
    objs = MinerBase().get_miner_list(miner_no_list=miner_no_list)
    data = Page(objs, page_size).page(page_index)
    data['objects'] = [{"miner_no": obj.miner_no, "power": obj.power,
                        "sector_size": obj.sector_size} for obj in data['objects']]
    return format_return(0, data=data)


@common_ajax_response
def get_miner_list_by_power_inc(request):
    '''根据算力增速排序'''
    page_index = int(request.POST.get('page_index', 1))
    page_size = min(int(request.POST.get('page_size', 10)), 100)
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    sector_type = request.POST.get('sector_type')
    miner_no_list = json.loads(request.POST.get('miner_no_list', '[]'))
    if miner_no_list:
        objs = MinerBase().get_miner_day_ranking_list(start_date, end_date, sector_type=sector_type, miner_no_list= miner_no_list)
    else:
        clkey = "{0}_{1}_{2}".format(start_date, end_date, "increase_power")
        objs = MinerBase().get_miner_day_ranking_list_cache(clkey, start_date, end_date, filter_type="increase_power")
    data = Page(objs, page_size).page(page_index)
    miner_list = MinerBase().get_miner_list(miner_no_list=[miner_day[0] for miner_day in data['objects']]).all()
    miner_no_dict = {}
    for miner in miner_list:
        tmp = {"power": miner.power, "sector_size": miner.sector_size}
        miner_no_dict[miner.miner_no] = tmp
    miner_data = []
    for miner_day in data['objects']:
        tmp = dict(miner_no=miner_day[0], increase_power_24=miner_day[1], increase_power_offset_24=miner_day[2])
        tmp.update(miner_no_dict.get(miner_day[0]))
        miner_data.append(tmp)
    data["objs"] = miner_data
    data.pop('objects', True)
    return format_return(0, data=data)


@common_ajax_response
def get_miner_list_by_power_inc_24(request):
    '''根据24小时封装量排序'''
    page_index = int(request.POST.get('page_index', 1))
    page_size = min(int(request.POST.get('page_size', 10)), 100)
    sector_type = request.POST.get('sector_type')
    miner_no_list = json.loads(request.POST.get('miner_no_list', '[]'))

    objs = MinerBase().get_miner_24h_ranking_list(order='-increase_power', sector_type=sector_type,
                                                  miner_no_list=miner_no_list)
    data = Page(objs, page_size).page(page_index)

    temp = [x.miner for x in data['objects']]
    return format_return(0, data={
        'objs': format_miner(temp), 'total_page': data['total_page'], 'total_count': data['total_count']
    })


@common_ajax_response
def get_miner_list_by_avg_reward(request):
    '''根据挖矿效率排序'''
    page_index = int(request.POST.get('page_index', 1))
    page_size = min(int(request.POST.get('page_size', 10)), 100)
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    sector_type = request.POST.get('sector_type')
    miner_no_list = json.loads(request.POST.get('miner_no_list', '[]'))
    if miner_no_list:
        objs = MinerBase().get_miner_day_ranking_list(start_date, end_date, sector_type=sector_type,
                                                      miner_no_list=miner_no_list, filter_type="avg_reward")
    else:
        clkey = "{0}_{1}_{2}".format(start_date, end_date, "avg_reward")
        objs = MinerBase().get_miner_day_ranking_list_cache(clkey, start_date, end_date, filter_type="avg_reward")

    data = Page(objs, page_size).page(page_index)
    miner_list = MinerBase().get_miner_list(miner_no_list=[miner_day[0] for miner_day in data['objects']]).all()
    miner_no_dict = {}
    for miner in miner_list:
        tmp = {"power": miner.power, "sector_size": miner.sector_size}
        miner_no_dict[miner.miner_no] = tmp
    miner_data = []
    for miner_day in data['objects']:
        tmp = dict(miner_no=miner_day[0], avg_reward=miner_day[1])
        tmp.update(miner_no_dict.get(miner_day[0], {}))
        miner_data.append(tmp)
    data["objs"] = miner_data
    data.pop('objects', True)
    return format_return(0, data=data)


@common_ajax_response
def get_miner_list_by_avg_reward_for_month_avg(request):
    '''根据挖矿效率排序(一个月平均)'''
    page_index = int(request.POST.get('page_index', 1))
    page_size = min(int(request.POST.get('page_size', 10)), 100)
    big_miner = request.POST.get("big_miner")

    date = request.POST.get('date')
    if not date:
        date = (datetime.datetime.now() - datetime.timedelta(days=1))
    else:
        date = datetime.datetime.strptime(date, '%Y-%m-%d')
    start_time = date - datetime.timedelta(days=30)
    end_time = date
    objs = MinerBase().get_miner_day_records(big_miner=big_miner, start_date=start_time, end_date=end_time)
    result_data = MinerBase().get_miner_day_records_for_month_avg_value(str(date.date()), order='avg_reward',
                                                                        data_queryset=objs)
    data = Page(result_data, page_size).page(page_index)
    result_list = []
    for value in data['objects']:
        temp_dict = {"miner_no": value.get("miner_no"), "avg_reward": value.get("mean_avg"),  # 这个其实是月平均挖矿效率
                     "power": int(value.get("power")), "sector_size": int(value.get("sector_size")),
                     "raw_power": int(value.get("raw_power"))}
        result_list.append(temp_dict)

    return format_return(0, data={
        'objs': result_list, 'total_page': data['total_page'], 'total_count': data['total_count']
    })


@common_ajax_response
def get_miner_list_by_avg_reward_24(request):
    '''根据24小时挖矿效率排序'''
    page_index = int(request.POST.get('page_index', 1))
    page_size = min(int(request.POST.get('page_size', 10)), 100)
    big_miner = json.loads(request.POST.get("big_miner", "0"))
    sector_type = request.POST.get('sector_type')
    miner_no_list = json.loads(request.POST.get('miner_no_list', '[]'))

    objs = MinerBase().get_miner_24h_ranking_list(order='-avg_reward', big_miner=big_miner,
                                                  sector_type=sector_type, miner_no_list=miner_no_list)
    objs= objs.filter(avg_reward__lt=1)
    data = Page(objs, page_size).page(page_index)

    temp = [x.miner for x in data['objects']]
    return format_return(0, data={
        'objs': format_miner(temp), 'total_page': data['total_page'], 'total_count': data['total_count']
    })


@common_ajax_response
def get_miner_list_by_block(request):
    '''根据出块排序'''
    page_index = int(request.POST.get('page_index', 1))
    page_size = min(int(request.POST.get('page_size', 10)), 100)
    stats_type = request.POST.get('stats_type', 1)
    if stats_type == "24h":
        objs = MinerBase().get_miner_24h_ranking_list(order='-block_count')
        total_block_reward = MinerBase().get_miner_24h_total_block_reward()
    else:
        end_date = datetime.date.today() - datetime.timedelta(days=1)
        start_date = end_date - datetime.timedelta(days=int(stats_type[0:stats_type.find("d")]))
        clkey = "{0}_{1}_{2}".format(start_date, end_date,"block")
        objs = MinerBase().get_miner_day_ranking_list_cache( clkey,start_date, end_date, filter_type="block")
        clkey = "{0}_{1}".format(start_date, end_date)
        total_block_reward = MinerBase().get_miner_day_total_block_reward(clkey,start_date, end_date)
    data = Page(objs, page_size).page(page_index)
    miner_no_list = [miner_day[0] if type(miner_day) == tuple else miner_day.miner.miner_no for miner_day in data['objects']]
    miner_list = MinerBase().get_miner_list(miner_no_list=miner_no_list).all()
    miner_no_dict = {}
    for miner in miner_list:
        tmp = {"power": miner.power, "sector_size": miner.sector_size}
        miner_no_dict[miner.miner_no] = tmp
    miner_data = []
    for miner_day in data['objects']:
        if type(miner_day) == tuple:
            tmp = dict(miner_no=miner_day[0], win_count=miner_day[1], lucky=miner_day[2], block_reward=miner_day[3])
            tmp.update(miner_no_dict.get(miner_day[0]))
        else:
            tmp = dict(miner_no=miner_day.miner.miner_no, win_count=miner_day.win_count, lucky=miner_day.lucky,
                       block_reward=miner_day.block_reward)
            tmp.update(miner_no_dict.get(miner_day.miner.miner_no))
        miner_data.append(tmp)
    data["objs"] = miner_data
    data.pop('objects', True)
    data["total_block_reward"] = total_block_reward
    return format_return(0, data=data)


@common_ajax_response
def get_miner_day_records(request):
    '''按天获取矿工历史数据'''
    page_index = int(request.POST.get('page_index', 1))
    page_size = min(int(request.POST.get('page_size', 10)), 10000)
    miner_no = request.POST.get('miner_no')
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    date = None
    if not start_date:
        date = request.POST.get('date')
        if not date:
            date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

    objs = MinerBase().get_miner_day_records(date=date, start_date=start_date, end_date=end_date, miner_no=miner_no)
    data = Page(objs, page_size).page(page_index)

    return format_return(0, data={
        'objs': format_miner_day(data['objects']), 'total_page': data['total_page'], 'total_count': data['total_count']
    })


@common_ajax_response
def get_148888_active_miners(request):
    '''获取148888高度的矿工信息'''
    data = MinerBase().get_148888_active_miners()
    return format_return(0, data=data)


@common_ajax_response
def get_miner_by_no(request):
    '''根据矿工no获取信息'''
    miner_no = request.POST.get('miner_no')
    miner = MinerBase().get_miner_by_no(miner_no=miner_no)
    return format_return(0, data=format_miner(miner))


@common_ajax_response
def get_miner_mining_stats_by_no(request):
    """获取每个矿工产出统计"""
    miner_no = request.POST.get('miner_no')
    stats_type = request.POST.get('stats_type')
    return MinerBase().get_miner_mining_stats_by_no(miner_no, stats_type)


@common_ajax_response
def get_miner_line_chart_by_no(request):
    '''矿工的算力变化和出块统计24/30/180'''
    miner_no = request.POST.get('miner_no')
    stats_type = request.POST.get('stats_type')
    return format_return(0, data=MinerBase().get_miner_line_chart_by_no(miner_no, stats_type))


@common_ajax_response
def get_company_miner_mapping(request):
    '''获取矿商与矿工对应关系'''
    mc_code = request.POST.get("mc_code")
    data = {}
    for per in MinerBase().get_companys(mc_code):
        data[per.code] = {
            'name': per.name, 'join_time': per.join_time.strftime('%Y-%m-%d') if per.join_time else '',
            'code': per.code,
            'miners': [x.miner_no for x in per.miners.all()]
        }
    return format_return(0, data=data)


@common_ajax_response
def get_miner_to_company_mapping(request):
    '''获取矿工对应的矿商'''
    must_update_cache = json.loads(request.POST.get('must_update_cache', '0'))
    data = MinerBase().get_miner_to_company_mapping(must_update_cache=must_update_cache)
    return format_return(0, data=data)


@common_ajax_response
def get_pool_miner_detail(request):
    '''查询矿池miner详情(最新的一条)'''
    miner_no = request.POST.get("miner_no")
    data = MinerBase().get_pool_miner_detail(miner_no)
    return format_return(0, data=data)


@common_ajax_response
def get_pool_activate_miner_detai(request):
    '''查询矿池miner详情(最新的一条)'''
    miner_no = request.POST.get("miner_no")
    data = MinerBase().get_pool_activate_miner_detail(miner_no)
    return format_return(0, data=data)


@common_ajax_response
def get_pool_attention_miner_detail(request):
    '''查询矿池miner详情(最新的一条)'''
    miner_no = request.POST.get("miner_no")
    data = MinerBase().get_pool_attention_miner_detail(miner_no)
    return format_return(0, data=data)


@common_ajax_response
def get_miner_type(request):
    miner_no = request.POST.get("miner_no")
    data = MinerBase().get_miner_type(miner_no)
    return format_return(0, data=data)


@common_ajax_response
def get_init_value(request):
    miner_no = request.POST.get("miner_no")
    end_time = request.POST.get("end_time")
    filed = request.POST.get("filed")
    data = MinerBase().get_init_value(miner_no, filed, end_time)
    return format_return(0, data=data)


@common_ajax_response
def get_miner_increment(request):
    date = request.POST.get("date")
    key = request.POST.get("key")
    miner_no = request.POST.get("miner_no")
    if not date:
        date = str(datetime.date.today() - datetime.timedelta(days=1))
    result = MinerBase().get_miner_increment(miner_no, date, key)
    return result


# ========================================================== 同步数据任务


# @common_ajax_response
# def sync_miner_day_stat(request):
#     '''
#     同步矿工状态
#     '''
#     date = request.POST.get('date')
#     return MinerBase().sync_miner_day_stat(date=date)


@common_ajax_response
def sync_miner_total_stat(request):
    '''
    同步矿工状态
    '''
    return MinerBase().sync_miner_total_stat()


# @common_ajax_response
# def sync_miner_temp_stat(request):
#     '''
#     同步矿工最近24小时状态
#     '''
#     return MinerBase().sync_miner_temp_stat()


@common_ajax_response
def sync_active_miners(request):
    MinerBase().sync_active_miners()
    MinerBase().sync_miner_temp_stat()
    return format_return(0)


# @common_ajax_response
# def sync_pool_miners(request):
#     return MinerBase().sync_pool_miners()


@common_ajax_response
def sync_miner_history(request):
    date = request.POST.get('date')
    return MinerBase().sync_miner_history(date=date)


@common_ajax_response
def sync_miner_day_gas(request):
    date = request.POST.get('date')
    return MinerBase().sync_miner_day_gas(date=date)


@common_ajax_response
def sync_miner_day_overtime_pledge_fee(request):
    date = request.POST.get('date')
    if not date:
        date = str((datetime.datetime.now() - datetime.timedelta(days=1)).date())
    return MinerBase().sync_miner_day_overtime_pledge_fee(date=date)


@common_ajax_response
def sync_miner_lotus(request):
    MinerBase().sync_miner_lotus()
    return format_return(0)


@common_ajax_response
def get_miner_health_report_24h_by_no(request):
    """
    获取节点健康报告24小时数据
    """
    miner_no = request.POST.get('miner_no')
    result = {}
    miner, miner_day_stat = MinerBase().get_miner_day_stat_info(miner_no)
    if miner_day_stat:
        result["power"] = miner.power
        result["sector_size"] = format_power(miner.sector_size, "GiB")
        result["avg_reward"] = miner_day_stat.avg_reward
        result["block_count"] = miner_day_stat.block_count
        result["block_reward"] = miner_day_stat.block_reward
        result["create_gas"], result["keep_gas"], result["pledge_gas"], result["total_gas"]\
            = MinerBase().get_gas_cost_by_miner_no(miner_no)
        result["lucky"] = miner_day_stat.lucky
        overview_block_count = TipsetBase().get_temp_tipset_block_count()
        # 爆快率 = 出块数/全网总出块数
        result["block_rate"] = format_price(miner_day_stat.block_count / overview_block_count, 4)
        result["worker_balance"] = miner.worker_balance
        result["poster_balance"] = miner.poster_balance
        result["owner_address"] = miner.owner_address
        result["worker_address"] = miner.worker_address
        result["poster_address"] = miner.poster_address
        result["total_sector"] = miner.total_sector
        result["active_sector"] = miner.active_sector
        result["faulty_sector"] = miner.faulty_sector
        result["recovering_sector"] = miner.recovering_sector
    return format_return(0, data=result)


@common_ajax_response
def get_miner_health_report_day_by_no(request):
    """
    获取节点健康报告7天数组
    """
    result = []
    miner_no = request.POST.get('miner_no')
    stat_type = request.POST.get('stat_type', '7d')
    if stat_type == "7d":
        end_date = datetime.datetime.today()
        start_date = end_date - datetime.timedelta(days=7)
    objs = MinerBase().get_miner_day_records(start_date=start_date, end_date=end_date, miner_no=miner_no).all()

    for obj in objs:
        result.append(dict(
            date=obj.date.strftime("%Y-%m-%d"),
            avg_reward=obj.avg_reward,
            lucky=obj.lucky,
            total_pledge=format_fil_to_decimal(obj.pre_gas + obj.prove_gas + obj.win_post_gas, 4),
            is_32=True if obj.sector_size == 34359738368 else False,
            create_gas=MinerBase().calc_create_gas(obj.pre_gas, obj.pre_gas_count, obj.prove_gas,
                                                   obj.prove_gas_count, obj.sector_size),
            keep_gas=(obj.win_post_gas / (obj.power / _d(1024 ** 4))) if obj.power else 0,
            worker_balance=obj.worker_balance,
            poster_balance=obj.poster_balance
        ))
    return format_return(0, data=result)


@common_ajax_response
def get_miner_health_report_gas_stat_by_no(request):
    miner_no = request.POST.get('miner_no')
    stat_type = request.POST.get('stat_type', '24h')
    result = MinerBase().get_gas_cost_stat_by_miner_no(miner_no, stat_type)
    return format_return(0, data=result)


@common_ajax_response
def get_messages_stat_by_miner_no(request):
    miner_no = request.POST.get('miner_no')
    stat_type = request.POST.get('stat_type', '24h')
    ck = '%s_%s' % (miner_no, stat_type)
    result = MinerBase().get_messages_stat_by_miner_no(ck, miner_no, stat_type)
    return format_return(0, data=result)


@common_ajax_response
def get_wallet_address_estimated_service_day(request):
    """
    钱包预计使用天数
    """
    # worker预计天数 = worker余额 / (节点近2日平均封装量 * (节点七天平均单T质押量 + 节点七天平均单T封装gas费))
    # post预计天数=post余额/(最近7天的矿池平均单T维护gas费*节点有效算力）
    miner_no = request.POST.get('miner_no')
    miner = MinerBase().get_miner_by_no(miner_no)
    end_date = datetime.datetime.today()
    start_date = end_date - datetime.timedelta(days=7)
    miner_objs = MinerBase().get_miner_day_records(start_date=start_date, end_date=end_date, miner_no=miner_no).all()
    increase_power_list = []  # 7天封装量
    create_gas_list = []  # 7天节点单体gas费
    win_gas_list = []  # 7天封装量
    for miner_obj in miner_objs:
        increase_power_list.append(miner_obj.increase_power)
        create_gas_list.append(MinerBase().calc_create_gas(miner_obj.pre_gas, miner_obj.pre_gas_count,
                                                           miner_obj.prove_gas, miner_obj.prove_gas_count,
                                                           miner_obj.sector_size))
        win_gas_list.append((miner_obj.win_post_gas / miner_obj.power) if miner_obj.power else 0)
    increase_power_avg = sum(increase_power_list)/len(increase_power_list) / _d(math.pow(1024, 4))  # 节点近2日平均封装量;单位是T
    create_gas_avg = sum(create_gas_list)/len(create_gas_list)  # 节点七天平均单T质押量
    win_gas_avg = sum(win_gas_list)/len(win_gas_list)  # 单位是Bytes

    overview_objs = OverviewBase().get_overview_day_records(start_date=start_date, end_date=end_date).all()
    pledge_list = []  # 7天单T质押量
    for overview_obj in overview_objs:
        pledge_list.append(overview_obj.avg_pledge*_d(32))
    pledge_avg = sum(pledge_list)/len(pledge_list) * _d(math.pow(10, 18))  # 节点七天平均单T质押量
    worker_estimated_service_day = -1
    if increase_power_avg and miner.worker_balance:
        worker_estimated_service_day = miner.worker_balance // (increase_power_avg * (create_gas_avg+pledge_avg))
    poster_estimated_day = miner.poster_balance // (win_gas_avg * miner.power)
    return format_return(0, data=dict(worker_estimated_day=worker_estimated_service_day,
                                      poster_estimated_day=poster_estimated_day))

