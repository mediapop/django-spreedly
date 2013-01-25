from django.conf.urls.defaults import *
from views import (PlanList, EmailSent, SpreedlyReturn,
        SubscriptionDetails, PlanDetails, EditSubscriber)

urlpatterns = patterns('spreedly.views',
    url(r'^email_sent/(?P<user_id>\d+)/$', EmailSent.as_view(), name='spreedly_email_sent'),
    url(r'^spreedly_listener/$', 'spreedly_listener', name='spreedly_listener'),
    url(r'^return/(?P<user_id>\d+)/(?P<plan_pk>\w+)/$',  SpreedlyReturn.as_view(), name='spreedly_return'),
    url(r'^subscription/(?P<user_id>)\d+/edit/$', EditSubscriber.as_view(), name='edit_subscription'),
    url(r'^subscription/(?P<user_id>)\d+/$', SubscriptionDetails.as_view(), name='subscription_details'),
    url(r'^subscription/$', SubscriptionDetails.as_view(), name='my_subscription'),
    url(r'^plans/(?P<plan_pk>\d+)/', PlanDetails.as_view(), name='plan_details'),
    url(r'^plans/$', PlanList.as_view(), name='plan_list'),
)
