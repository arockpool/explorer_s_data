from django.conf.urls import url
from overview import views

urlpatterns = [
    url(r'^get_overview$', views.get_overview),
    url(r'^get_overview_day_records$', views.get_overview_day_records),
    url(r'^get_history_day_records$', views.get_history_day_records),

    url(r'^get_pool_overview$', views.get_pool_overview),

    url(r'^get_usd_rate$', views.get_usd_rate),

]
