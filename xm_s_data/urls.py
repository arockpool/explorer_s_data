from django.conf.urls import url, include
urlpatterns = [
    url(r'^data/api/message/', include('message.urls')),

    url(r'^data/api/miner/', include('miner.urls')),

    url(r'^data/api/overview/', include('overview.urls')),

    url(r'^data/api/tipset/', include('tipset.urls')),

    url(r'^data/api/rmd/', include('rmd.urls')),

    url(r'^data/api/deal/', include('deal.urls')),

    url(r'^data/api/fil/', include('fil.urls')),

    url(r'^data/openapi/v1/', include('openapi.urls')),
]
