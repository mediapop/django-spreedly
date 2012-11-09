from django.conf.urls.defaults import *
from django.contrib.auth.views import login

urlpatterns = patterns('',
    url(r'^accounts/login/$',login, name='login'),
    url(r'^', include('spreedly.urls')),
    )
