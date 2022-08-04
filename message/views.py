import json
import time
import math
import decimal
import datetime
from collections import Iterable

from django.http import HttpResponse
from django.db.models import Avg, Q, F, Sum, Count

from explorer_s_common.decorator import common_ajax_response
from explorer_s_common.utils import format_return, format_price, format_power, str_2_power, format_fil, _d,get_aggregate_gas
from explorer_s_common.page import Page
from message.interface import MessageBase
from miner.interface import MinerBase
from tipset.interface import TipsetBase


@common_ajax_response
def get_transfer_list(request):
    '''
    获取转账信息
    '''
    is_next = json.loads(request.POST.get('is_next', '0'))
    timestamp = int(request.POST.get('timestamp', 0))
    msg_method = request.POST.get('msg_method')
    miner_no = request.POST.get('miner_no')
    page_size = int(request.POST.get('page_size', 20))
    page_index = int(request.POST.get('page_index', 1))
    start_time = request.POST.get('start_time')
    end_time = request.POST.get('end_time')
    if start_time:
        start_time += ' 00:00:00'
    if end_time:
        end_time += ' 23:59:59'
    data = MessageBase().get_message_list(miner_no=miner_no, start_time=start_time, end_time=end_time,
                                          all=True, is_transfer=True, page_size=page_size,
                                          page_index=page_index, msg_method=msg_method)
    if not data:
        return format_return(0)
    total_count = MessageBase().get_message_count(miner_no=miner_no, all=True,start_time=start_time, end_time=end_time,
                                                  is_transfer=True, msg_method=msg_method)
    total_page = math.ceil(total_count / page_size)
    redis_k = '%s_%s_%s_%s' % (miner_no, "is_transfer", start_time, end_time)
    msg_methods = MessageBase().get_message_method_types(redis_k, miner_no=miner_no, start_time=start_time,
                                                         end_time=end_time, is_transfer=True, all=True)
    records = []
    for per in [x['_source'] for x in data['hits']]:
        per['block_time'] = MessageBase().launch_date + datetime.timedelta(seconds=30 * per['height'])
        per['block_time'] = per['block_time'].strftime('%Y-%m-%d %H:%M:%S')
        records.append(per)

    return format_return(0, data={
        'objs': records,
        'total_page': total_page, 'total_count': total_count, 'msg_methods': msg_methods
    })


@common_ajax_response
def get_gas_sum_by_day(request):
    '''获取gas统计信息'''
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    data = MessageBase().get_gas_sum_by_day(start_date=start_date, end_date=end_date)
    return format_return(0, data=data)


@common_ajax_response
def get_gas_sum_by_per(request):
    '''根据时间获取生产gas'''
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    sector_type = request.POST.get('sector_type', '0')
    ck = '%s_%s_%s' % (start_date, end_date, sector_type)
    data = MessageBase().get_gas_sum_by_per(ck, start_date=start_date, end_date=end_date, sector_type=sector_type)
    return format_return(0, data=data)


@common_ajax_response
def get_gas_stat_all(request):
    '''获取完整的gas统计信息'''
    sector_type = request.POST.get('sector_type')
    is_pool = json.loads(request.POST.get('is_pool', '0'))
    data = MessageBase().get_gas_stat_all(sector_type=sector_type, is_pool=is_pool)
    return format_return(0, data=data)


@common_ajax_response
def get_gas_cost_stat(request):
    '''获取gas消耗统计'''
    sector_type = request.POST.get('sector_type', '0')
    is_pool = json.loads(request.POST.get('is_pool', '0'))
    must_update_cache = json.loads(request.POST.get('must_update_cache', '0'))
    ck = '%s_%s' % (sector_type, is_pool)
    data = MessageBase().get_gas_cost_stat(ck, sector_type=sector_type, is_pool=is_pool,
                                           must_update_cache=must_update_cache)
    return format_return(0, data=data)


@common_ajax_response
def get_base_fee_trends(request):
    search_type = request.POST.get('search_type', 'day')
    search_type_dict = {"day": 1, "week": 7, "month": 30, "season": 90}
    now = datetime.datetime.now()
    start_date = (now - datetime.timedelta(days=search_type_dict[search_type])).strftime('%Y-%m-%d %H:%M:%S')
    end_date = now.strftime('%Y-%m-%d %H:%M:%S')
    step = 2880 * search_type_dict[search_type] / 48
    data = []
    for per in MessageBase().get_base_fee_trends(start_date=start_date, end_date=end_date, step=step):
        data.append({
            'height': per[0],
            'record_time': per[1].strftime('%Y-%m-%d %H:%M:%S'), 'base_fee': per[2],
            'create_gas_32': per[3], 'keep_gas_32': per[4],
            'create_gas_64': per[5], 'keep_gas_64': per[6]
        })
    return format_return(0, data=data)


@common_ajax_response
def get_miner_gas_cost_stat(request):
    msg_method = json.loads(request.POST.get('msg_method', '[]'))
    start_height = request.POST.get('start_height')
    end_height = request.POST.get('end_height')
    miner_no = request.POST.get('miner_no')
    data = MessageBase().get_miner_gas_cost_stat(
        msg_method=msg_method, start_height=start_height, end_height=end_height, miner_no=miner_no
    )
    return format_return(0, data=data)


@common_ajax_response
def get_memory_pool_message(request):
    '''获取内存池消息'''
    page_index = int(request.POST.get('page_index', '1'))
    page_size = min(int(request.POST.get('page_size', '10')), 50)

    data = MessageBase().get_memory_pool_message(page_size=page_size, page_index=page_index)
    if not data:
        result = Page(data, page_size).page(page_index)
        return format_return(0, data={
            "objs": result['objects'],
            'total_page': result['total_page'],
            'total_count': result['total_count']
        })

    total_count = data['total']['value']
    total_page = math.ceil(total_count / page_size)
    return format_return(0, data={
        'objs': [x['_source'] for x in data['hits']],
        'total_page': total_page, 'total_count': total_count
    })


@common_ajax_response
def get_message_list(request):
    '''获取消息列表'''
    miner_no = request.POST.get('miner_no')
    msg_method = request.POST.get('msg_method')
    all = request.POST.get("all", False)
    page_size = int(request.POST.get('page_size', 20))
    page_index = int(request.POST.get('page_index', 1))
    current_start_index = int(request.POST.get('current_start_index', 0))
    display_page = request.POST.get('display_page', 1)
    scroll_id = request.POST.get('scroll_id', "")
    is_next = json.loads(request.POST.get('is_next', '0'))
    if scroll_id:
        data = MessageBase().get_scroll(scroll_id)
        if not data:
            return format_return(15000, msg="数据缺失,请刷新")
    else:
        data = MessageBase().get_message_list(is_next=is_next, miner_no=miner_no,
                                              msg_method=msg_method, all=all, page_size=page_size * display_page,
                                              page_index=page_index)

    total_count = MessageBase().get_message_count(miner_no=miner_no, msg_method=msg_method, all=all)
    total_page = math.ceil(total_count / page_size)
    redis_k = '%s_%s' % (miner_no, all)
    msg_methods = MessageBase().get_message_method_types(redis_k, miner_no=miner_no, all=all)
    records = []
    for x in data and data['hits']:
        per = x['_source']
        per["_id"] = x["_id"]
        per['block_time'] = MessageBase().launch_date + datetime.timedelta(seconds=30 * per['height'])
        per['block_time'] = per['block_time'].strftime('%Y-%m-%d %H:%M:%S')
        records.append(per)
    if display_page > 1:
        result = {}
        current_start_index += 1
        for x in range(display_page):
            if current_start_index + x <= total_page:
                result[current_start_index + x] = records[x * page_size:(x + 1) * page_size]
    else:
        result = records

    return format_return(0, data={
        'objs': result,
        '_scroll_id': data.get("_scroll_id"),
        'total_page': total_page, 'total_count': total_count, 'msg_methods': msg_methods
    })


@common_ajax_response
def get_message_detail(request):
    '''获取消息列表'''
    msg_cid = request.POST.get('msg_cid')

    data = MessageBase().get_message_detail(msg_cid=msg_cid)['hits']
    if data:
        data = data[0]['_source']
        data['block_time'] = MessageBase().launch_date + datetime.timedelta(seconds=30 * data['height'])
        data['block_time'] = data['block_time'].strftime('%Y-%m-%d %H:%M:%S')
        # 销毁费
        data["fee_burn"] = _d(data.get('gascost_base_fee_burn', 0)) + _d(data.get('gascost_over_estimation_burn', 0))
        # batch_gas_charge
        data['batch_gas_charge'] = get_aggregate_gas(data.get("sector_count", 0), int(data["base_fee"] or data["base_fee2"]),
                                                     data['height'], data["msg_method"])
        # 打包矿工
        block_data = MessageBase().get_block_by_message_id(msg_cid)
        block_ids = [x['_source']['block'] for x in block_data['hits']]
        if block_ids:
            info = TipsetBase().get_miner_block_by_block_id(block_ids[0])
            if info:
                data["tip_miner_no"] = info.miner_no
    return format_return(0, data=data)


@common_ajax_response
def sync_tipset_gas(request):
    '''
    同步单个区块gas汇总
    '''
    launch_date = datetime.datetime(2020, 8, 25, 6, 0, 0)
    end_index = request.POST.get('end_index')
    if not end_index:
        end_index = int((datetime.datetime.now() - launch_date).total_seconds() / 30)
    end_index = int(end_index)

    start_index = request.POST.get('start_index')
    if not start_index:
        start_index = end_index - 121
    start_index = int(start_index)

    pool_miners_dict = dict([(x.miner_no, True) for x in MinerBase().get_miner_list(is_pool=True)])
    # 补汽油费为0的数据
    from message.models import TipsetGasSum
    for per in TipsetGasSum.objects.filter(pre_gas=0, prove_gas=0, win_post_gas=0)[:50]:
        MessageBase().sync_tipset_gas(height=per.height, pool_miners_dict=pool_miners_dict)
    # 同步新的数据
    for i in range(start_index, end_index):
        MessageBase().sync_tipset_gas(height=i, pool_miners_dict=pool_miners_dict)
    # 消息延迟预警
    MessageBase().sync_tipset_gas_warning()
    return format_return(0)


@common_ajax_response
def sync_overtime_pledge(request):
    '''
    同步过期质押
    '''
    MessageBase().sync_overtime_pledge()
    return format_return(0)
