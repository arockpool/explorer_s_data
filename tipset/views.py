import json
import time
import math
import decimal
import datetime
from collections import Iterable

from django.http import HttpResponse

from explorer_s_common.decorator import common_ajax_response
from explorer_s_common.utils import format_return, format_price, format_power, str_2_power, format_fil
from explorer_s_common.page import Page
from explorer_s_common import inner_server, cache
from explorer_s_common.third.filscout_sdk import FilscoutBase
from explorer_s_common.third.filfox_sdk import FilfoxBase

from explorer_s_data import consts
from tipset.interface import TipsetBase
from message.interface import MessageBase


def format_block(objs):
    if objs is None:
        return None

    def _format_obj(obj):
        return {
            'height': obj.height,
            'record_time': obj.record_time.strftime('%Y-%m-%d %H:%M:%S'),
            'block_hash': obj.block_hash, 'miner_no': obj.miner_no,
            'msg_count': obj.msg_count, 'win_count': obj.win_count,
            'reward': obj.reward, 'reward_str': format_fil(obj.reward) + ' FIL'
        }

    return [_format_obj(obj) for obj in objs] if isinstance(objs, Iterable) else _format_obj(objs)


def format_tipset(objs):
    if objs is None:
        return None

    def _format_obj(obj):
        blocks = []
        for per in obj.blocks.all():
            blocks.append(format_block(per))
        return {
            'height': obj.height, 'total_win_count': obj.total_win_count,
            'total_block_count': obj.total_block_count, 'total_reward': obj.total_reward,
            'total_reward_str': format_fil(obj.total_reward) + ' FIL',
            'blocks': blocks,
            'record_time': obj.record_time.strftime('%Y-%m-%d %H:%M:%S')
        }

    return [_format_obj(obj) for obj in objs] if isinstance(objs, Iterable) else _format_obj(objs)


@common_ajax_response
def get_tipsets(request):
    height = request.POST.get('height')
    page_index = int(request.POST.get('page_index', 1))
    page_size = min(int(request.POST.get('page_size', 10)), 50)

    objs = TipsetBase().get_tipsets(height=height)
    data = Page(objs, page_size).page(page_index)

    return format_return(0, data={
        'objs': format_tipset(data['objects']), 'total_page': data['total_page'], 'total_count': data['total_count']
    })


@common_ajax_response
def get_tipset_by_height(request):
    height = request.POST.get('height')

    tipset = TipsetBase().get_tipset_by_height(height=height)
    return format_return(0, data=format_tipset(tipset))


@common_ajax_response
def get_block_detail(request):
    block_id = request.POST.get('block_id')
    data = TipsetBase().get_block_detail(block_id=block_id)
    return format_return(0, data=data)


@common_ajax_response
def get_block_message(request):
    page_index = int(request.POST.get('page_index', '1'))
    page_size = min(int(request.POST.get('page_size', '10')), 50)
    block_id = request.POST.get('block_id')
    msg_method = request.POST.get('msg_method')
    data = TipsetBase().get_block_message(block_id=block_id)
    # total_count = data['total']['value']
    # total_page = math.ceil(total_count / page_size)

    # 获取消息id列表
    msg_ids = [x['_source']['message'] for x in data['hits']]

    records = []
    data = MessageBase().get_message_list(msg_ids=msg_ids, msg_method=msg_method, page_index=page_index,
                                          page_size=page_size)
    for per in data['hits']:
        records.append({
            'msg_id': per['_source']['msg_cid'],
            'msg_from': per['_source']['msg_from'],
            'msg_to': per['_source']['msg_to'],
            'msg_method': per['_source'].get('msg_method_name', ''),
            'msg_value': per['_source']['msg_value'],
            'msg_status': per['_source']['msgrct_exit_code']
        })
    total_count = MessageBase().get_message_count(msg_ids=msg_ids, msg_method=msg_method)
    total_page = math.ceil(total_count / page_size)
    redis_k = '%s' % (block_id,)
    msg_methods = MessageBase().get_message_method_types(redis_k, msg_ids=msg_ids)
    return format_return(0, data={
        'objs': records,
        'total_page': total_page, 'total_count': total_count, 'msg_methods': msg_methods
    })


@common_ajax_response
def get_miner_blocks(request):
    miner_no = request.POST.get('miner_no')
    page_index = int(request.POST.get('page_index', 1))
    page_size = min(int(request.POST.get('page_size', 10)), 2800)
    start_time = request.POST.get('start_time')
    end_time = request.POST.get('end_time')
    objs = TipsetBase().get_miner_blocks(miner_no=miner_no, start_time=start_time, end_time=end_time)
    data = Page(objs, page_size).page(page_index)

    return format_return(0, data={
        'objs': format_block(data['objects']), 'total_page': data['total_page'], 'total_count': data['total_count']
    })


@common_ajax_response
def get_lucky(request):
    '''
    获取全网幸运值
    '''
    date = request.POST.get('date')
    lucky = TipsetBase().get_lucky(date=date)
    return format_return(0, data=format_price(lucky, 4))


@common_ajax_response
def get_block_count(request):
    date = request.POST.get('date')
    count = TipsetBase().get_block_count(date=date)
    return format_return(0, data={"count": count})


@common_ajax_response
def sync_tipset(request):
    date = request.POST.get('date')
    return TipsetBase().sync_tipset(date=date)


@common_ajax_response
def sync_temp_tipset(request):
    TipsetBase().sync_temp_tipset()
    TipsetBase().sync_tipset_warning()
    return format_return(0)
