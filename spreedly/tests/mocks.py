from pyspreedly.api import Client
from mock import MagicMock
import requests
from urlparse import urljoin

from helpers import SpreedlySubscriptionXML
from pyspreedly.objectify import objectify_spreedly

def get_client_mock(site_name, API_VERSION='v4'):
    base_host = 'https://spreedly.com'
    base_path = '/api/{api_version}/{site_name}/'.format(
                api_version=API_VERSION, site_name=site_name)

    def CM(bh, bp):
        class ClientMagic(MagicMock):
            base_host = bh
            base_path = bp
            base_url = urljoin(base_host, base_path)
        return ClientMagic

    ClientMagic = CM(base_host, base_path)
    cm = set_client_mock_returns(ClientMagic())
    cm.return_value = cm
    return cm


def set_client_mock_returns(client_mock):
    spreedly_xml = SpreedlySubscriptionXML()
    subscriber = objectify_spreedly(spreedly_xml.create_user())
    plans = objectify_spreedly(spreedly_xml.all_plans())

    def get_signup_url(subscriber_id, plan_id, screen_name, token=None):
        subscriber_id = str(subscriber_id)
        plan_id = str(plan_id)
        if token:
            url = '/'.join(('subscribers',subscriber_id,token,
                            'subscribe', plan_id))
        else:
            url = '/'.join(('subscribers',subscriber_id,'subscribe',
                            plan_id,screen_name))
        url = urljoin(client_mock.base_url, url)
        return url

    def allow_free_trial(subscriber_id):
        subscriber['eligible_for_free_trial'] = True
        return subscriber

    def set_info(subscriber_id, **kw):
        if 'new_customer_id' in kw:
            c_id = kw.pop('new_customer_id')
            if c_id in self._subscriptions:
                raise requests.HTTPError(
                        "status code: 403, text: you fail it")
            subscriber['customer_id'] = c_id
        for key in kw:
            subscriber[key] = kw[key]
        return subscriber

    client_mock.get_plans.return_value = plans
    client_mock.delete_subscriber.return_value = '200'
    client_mock.create_subscriber.return_value = subscriber
    client_mock.get_signup_url.side_effect = get_signup_url
    client_mock.get_info.return_value = subscriber

    client_mock.allow_free_trial.side_effect = allow_free_trial
    client_mock.set_info.side_effect = set_info

    return client_mock
