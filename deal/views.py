from explorer_s_common.decorator import common_ajax_response
from explorer_s_common.utils import format_return, format_power
from explorer_s_common.page import Page
from deal.interface import DealBase,Deal
from deal.serializer import DealSerializer,DealModeSerializer


@common_ajax_response
def get_deal_stat(request):
    '''
    增量同步订单
    '''
    data = DealBase().get_deal_stat_from_es()
    return format_return(0, data={
        'deal_size': data['deal_size']['value'],
        'deal_size_str': format_power(data['deal_size']['value']),
        'deal_count': data['deal_count']['value']
    })


@common_ajax_response
def sync_deal(request):
    '''
    增量同步订单
    '''
    return DealBase().sync_deal_new()


@common_ajax_response
def deal_list(request):
    key_words = request.POST.get('key_words')
    page_size = int(request.POST.get('page_size', 20))
    page_index = int(request.POST.get('page_index', 1))
    objs = DealBase().get_deal_list(key_words)
    data = Page(objs, page_size).page(page_index)
    serializer = DealSerializer(data['objects'], many=True, fields=("deal_id", "client", "provider", "piece_size",
                                                                    "is_verified", "height", "record_time"))
    return format_return(0, data={'objs': serializer.data,
                                  'total_page': data['total_page'], 'total_count': data['total_count']
    })


@common_ajax_response
def deal_info(request):
    deal_id = request.POST.get('deal_id')
    obj = Deal.objects.filter(deal_id=deal_id)
    return format_return(0, data=DealSerializer(obj, many=True).data)


@common_ajax_response
def deal_all_list(request):
    height = int(request.POST.get('height'))
    objs = DealBase().deal_all_list(height)
    serializer = DealModeSerializer(objs, many=True)
    return format_return(0, data=serializer.data)
