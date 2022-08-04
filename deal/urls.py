from django.conf.urls import url

from deal import views

urlpatterns = [
    url(r'^get_deal_stat$', views.get_deal_stat),

    url(r'^sync_deal$', views.sync_deal),
    url(r'^deal_list', views.deal_list),
    url(r'^deal_info', views.deal_info),
    url(r'^deal_all_list', views.deal_all_list)
]
