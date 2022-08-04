from django.conf.urls import url

from tipset import views

urlpatterns = [
    url(r'^get_tipsets$', views.get_tipsets),
    url(r'^get_tipset_by_height$', views.get_tipset_by_height),
    url(r'^get_block_detail$', views.get_block_detail),
    url(r'^get_block_message$', views.get_block_message),
    url(r'^get_miner_blocks$', views.get_miner_blocks),
    url(r'^get_lucky$', views.get_lucky),
    url(r'^get_block_count$', views.get_block_count),  # 查询该日期区块是否同步回来了

    url(r'^sync_tipset$', views.sync_tipset),
    url(r'^sync_temp_tipset$', views.sync_temp_tipset),
]
