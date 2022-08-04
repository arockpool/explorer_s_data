from explorer_s_common.decorator import common_ajax_response
from explorer_s_common.utils import format_return
from explorer_s_common.openapi.security import open_api
from openapi import interface


@common_ajax_response
@open_api("V1")
def get_miners(request):
    '''获取矿工信息'''
    page_size = int(request.GET.get('page_size', 20))
    page_index = int(request.GET.get('page_index', 1))

    data = interface.get_miners(page_index, page_size)

    return format_return(0, data=data)
