import datetime
from explorer_s_common.utils import format_return, format_price, format_power, str_2_power, format_fil, _d
from explorer_s_common.third.bbhe_sdk import BbheBase
from explorer_s_common.decorator import cache_required


class RMDBase(object):

    @cache_required(cache_key='get_net_stat_day_%s', expire=3600 * 6)
    def get_net_stat_day(self, date):
        """
        根据用户id获取profile
        """
        # 获取昨日信息，没有则取前天
        data={}
        yesterday_info = BbheBase().get_net_stat(date=date)
        if yesterday_info['code'] != 200 or (not yesterday_info['data']) or (
                yesterday_info['data'].get('poolUnitTReward', 0) <= 0) or (
                yesterday_info['data'].get('unitTReward', 0) <= 0):
            date = (datetime.datetime.now() - datetime.timedelta(days=2)).strftime('%Y-%m-%d')
            yesterday_info = BbheBase().get_net_stat(date=date)

        if yesterday_info['code'] != 200 or (not yesterday_info['data']):
            return format_return(99904, data={})

        avg_pledge = _d(yesterday_info['data'].get('unitTPackingPledgeFee', '8.2410'))
        create_gas_32 = max(_d(yesterday_info['data'].get('unitTPackingGasFee32', '0.0001')), _d(0.0001))
        create_gas_64 = max(_d(yesterday_info['data'].get('unitTPackingGasFee64', '0.0001')), _d(0.0001))
        keep_gas_32 = max(_d(yesterday_info['data'].get('unitTMaintainGasFee32', '0.0001')), _d(0.0001))
        keep_gas_64 = max(_d(yesterday_info['data'].get('unitTMaintainGasFee64', '0.0001')), _d(0.0001))
        pool_unit_t_reward = yesterday_info['data'].get('poolUnitTReward', '0')
        unit_t_reward = yesterday_info['data'].get('unitTReward', '0')

        data.update({
            'avg_pledge': format_price(avg_pledge, 4),
            'create_cost_gas_per_t': format_price(create_gas_32, 4),
            'create_cost_gas_per_t_64': format_price(create_gas_64, 4),
            'keep_cost_gas_per_t': format_price(keep_gas_32, 4),
            'keep_cost_gas_per_t_64': format_price(keep_gas_64, 4),
            'pool_unit_t_reward': format_price(pool_unit_t_reward, 4),
            'unit_t_reward': format_price(unit_t_reward, 4),
        })
        return data
