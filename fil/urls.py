from django.conf.urls import url

from fil import views

urlpatterns = [
    url(r'^get_miner_day_info', views.get_miner_day_info),
]
