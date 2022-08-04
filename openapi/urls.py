from django.conf.urls import url

from openapi import views

urlpatterns = [
    url(r'^miners', views.get_miners),
]
