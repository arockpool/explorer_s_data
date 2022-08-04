from django.conf.urls import url

from rmd import views

urlpatterns = [
    url(r'^get_miner_day_record', views.get_miner_day_record),

    url(r'^get_day_overview', views.get_day_overview),
]
