from django.conf.urls import url

from message import views

urlpatterns = [
    url(r'^get_transfer_list$', views.get_transfer_list),
    url(r'^get_gas_sum_by_day$', views.get_gas_sum_by_day),
    url(r'^get_gas_sum_by_per$', views.get_gas_sum_by_per),
    url(r'^get_gas_stat_all$', views.get_gas_stat_all),
    url(r'^get_gas_cost_stat$', views.get_gas_cost_stat),
    url(r'^get_base_fee_trends$', views.get_base_fee_trends),
    url(r'^get_miner_gas_cost_stat$', views.get_miner_gas_cost_stat),

    url(r'^get_memory_pool_message$', views.get_memory_pool_message),
    url(r'^get_message_list$', views.get_message_list),
    url(r'^get_message_detail$', views.get_message_detail),

    url(r'^sync_tipset_gas$', views.sync_tipset_gas),
    url(r'^sync_overtime_pledge$', views.sync_overtime_pledge),
]
