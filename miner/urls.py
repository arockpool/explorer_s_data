from django.conf.urls import url

from miner import views

urlpatterns = [
    url(r'^get_miner_list$', views.get_miner_list),
    url(r'^get_miner_list_by_miners$', views.get_miner_list_by_miners),
    url(r'^get_miner_list_by_power_inc$', views.get_miner_list_by_power_inc),
    url(r'^get_miner_list_by_power_inc_24$', views.get_miner_list_by_power_inc_24),  # 根据24小时封装量
    url(r'^get_miner_list_by_block$', views.get_miner_list_by_block),
    url(r'^get_miner_list_by_avg_reward$', views.get_miner_list_by_avg_reward),
    url(r'^get_miner_list_by_avg_reward_for_month_avg$', views.get_miner_list_by_avg_reward_for_month_avg),
    url(r'^get_miner_list_by_avg_reward_24$', views.get_miner_list_by_avg_reward_24),
    url(r'^get_miner_by_no$', views.get_miner_by_no),
    url(r'^get_miner_day_records$', views.get_miner_day_records),
    url(r'^get_miner_increment$', views.get_miner_increment),  # 获得矿工所有数据的增量
    url(r'^get_miner_mining_stats_by_no$', views.get_miner_mining_stats_by_no),  # 获取每个矿工产出统计7/30
    url(r'^get_miner_line_chart_by_no$', views.get_miner_line_chart_by_no),  # 矿工的算力变化和出块统计24/30/180
    url(r'^get_148888_active_miners$', views.get_148888_active_miners),
    # 节点健康报告
    url(r'^get_miner_health_report_24h_by_no', views.get_miner_health_report_24h_by_no),
    url(r'^get_miner_health_report_day_by_no', views.get_miner_health_report_day_by_no),
    url(r'^get_miner_health_report_gas_stat_by_no', views.get_miner_health_report_gas_stat_by_no),
    url(r'^get_messages_stat_by_miner_no', views.get_messages_stat_by_miner_no),
    url(r'^get_wallet_address_estimated_service_day', views.get_wallet_address_estimated_service_day),

    url(r'^get_company_miner_mapping$', views.get_company_miner_mapping),
    url(r'^get_miner_to_company_mapping$', views.get_miner_to_company_mapping),
    url(r'^get_pool_miner_detail$', views.get_pool_miner_detail),
    url(r'^get_pool_activate_miner_detail$', views.get_pool_activate_miner_detai),  # 取活跃矿工数据
    url(r'^get_pool_attention_miner_detail$', views.get_pool_attention_miner_detail),  # 获取关注的矿工信息数据(矿池优先使用)
    url(r'^get_miner_type$', views.get_miner_type),  # 取矿工类型(存储矿工,普通矿工)
    url(r'^get_init_value$', views.get_init_value),  # 获得初始数据

    url(r'^sync_active_miners$', views.sync_active_miners),
    # url(r'^sync_pool_miners$', views.sync_pool_miners),
    url(r'^sync_miner_total_stat$', views.sync_miner_total_stat),
    # url(r'^sync_miner_day_stat$', views.sync_miner_day_stat),
    # url(r'^sync_miner_temp_stat$', views.sync_miner_temp_stat),
    url(r'^sync_miner_history$', views.sync_miner_history),
    url(r'^sync_miner_day_gas$', views.sync_miner_day_gas),
    url(r'^sync_miner_day_overtime_pledge_fee$', views.sync_miner_day_overtime_pledge_fee),  # 同步每日浪费质押gas
    url(r'^sync_miner_lotus$', views.sync_miner_lotus),  # 同步链上的数据

]
