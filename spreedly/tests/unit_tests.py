from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from pyspreedly.api import Client
from spreedly.models import HttpUnprocessableEntity
from spreedly.models import Plan, Fee, FeeGroup, Subscription
from datetime import datetime, timedelta
import requests
from django.utils.unittest import skip
from pyspreedly.objectify import objectify_spreedly
import pyspreedly.api
from . helpers import SpreedlySubscriptionXML
from mock import patch
from StringIO import StringIO


class TestCaseSetup(TestCase):
    fixtures = ['plans', 'fees', 'sites']
    def _setup_subscription_with_mock(self, status_code=200, plan=None, user=None):
        sxml = SpreedlySubscriptionXML()
        if not plan:
            plan = self.plan
        if not user:
            user = self.user
        xml = sxml.subscription_xml(plan.id, user.id)
        with patch('requests.get') as response_get_mock:
            with patch('requests.models.Response') as response_mock:
                response_mock.status_code = status_code
                response_mock.text = xml
                response_get_mock.return_value = response_mock
                self.subscription = Subscription.objects.get_or_create(
                        user=user,
                        plan=plan)

    def setUp(self):
        self.spreedly_client = Client(settings.SPREEDLY_AUTH_TOKEN, settings.SPREEDLY_SITE_NAME)
        self.patcher = patch.object(Plan.objects, 'sync_plans')
        self.mock_sync_plans = self.patcher.start()
        self.mock_sync_plans.return_value = None
        self.user = User.objects.create_user(username='test user',
                email='test@mediapopinc.com',
                password='testpassword')
        self.trial_plan = Plan.objects.get(id=12345)
        self.paid_plan = Plan.objects.get(id=67890)

    def tearDown(self):
        self.patcher.stop()


class TestSyncPlans(TestCase):
    fixtures = ['plans', 'fees', 'sites']
    def setUp(self):
        self.user = User.objects.create_user(username='test',
                email='test@mediapopinc.com',
                password='testpassword')
        self.spreedly_client = Client(settings.SPREEDLY_AUTH_TOKEN, settings.SPREEDLY_SITE_NAME)

    def tearDown(self):
        # Remove all subscribers
        self.spreedly_client.cleanup()

    def test_sync_plans(self):
        # Initial sync
        status_code = 200
        sxml = SpreedlySubscriptionXML()
        xml = sxml.all_plans()
        with patch('requests.get') as response_get_mock:
            with patch('requests.models.Response') as response_mock:
                response_mock.status_code = status_code
                response_mock.text = xml
                response_get_mock.return_value = response_mock
                spreedly_count = len(self.spreedly_client.get_plans())
                Plan.objects.sync_plans()
                qs = Plan.objects.all()
                self.assertEquals(qs.count(), spreedly_count)


class TestPlan(TestCaseSetup):
    def test_trial_eligibility(self):
        """Plan should have a check for eligibility"""
        self.assertTrue(self.trial_plan.trial_eligible(self.user))
        self.assertFalse(self.paid_plan.trial_eligible(self.user))

    def test_start_trial(self):
        """A user should be able to start a free trial on an eligibile plan"""
        sxml = SpreedlySubscriptionXML()
        with patch.object(pyspreedly.api.Client, 'get_info') as mock_get_info:
            with patch.object(pyspreedly.api.Client, 'create_subscriber') as mock_create_subscriber:
                with patch.object(pyspreedly.api.Client, 'subscribe') as mock_subscribe:
                    mock_get_info.side_effect = requests.HTTPError
                    mock_create_subscriber.return_value = objectify_spreedly(sxml.create_user(self.user.id))
                    mock_subscribe.return_value = objectify_spreedly(sxml.free_trial_response(12345, self.user.id))
                    self.assertTrue(self.trial_plan.start_trial(self.user))
        with patch.object(pyspreedly.api.Client, 'get_info') as mock_get_info:
            with patch.object(pyspreedly.api.Client, 'create_subscriber') as mock_create_subscriber:
                with patch.object(pyspreedly.api.Client, 'subscribe') as mock_subscribe:
                    mock_get_info.side_effect = requests.HTTPError
                    mock_create_subscriber.return_value = objectify_spreedly(sxml.create_user(self.user.id))
                    mock_subscribe.side_effect = requests.HTTPError
                    self.assertRaises(Plan.NotEligibile,self.paid_plan.start_trial,self.user)

    def test_trial_eligibility_on_trial(self):
        sxml = SpreedlySubscriptionXML()
        with patch.object(pyspreedly.api.Client, 'get_info') as mock_get_info:
            with patch.object(pyspreedly.api.Client, 'create_subscriber') as mock_create_subscriber:
                with patch.object(pyspreedly.api.Client, 'subscribe') as mock_subscribe:
                    mock_get_info.side_effect = requests.HTTPError
                    mock_create_subscriber.return_value = objectify_spreedly(sxml.create_user(self.user.id))
                    mock_subscribe.return_value = objectify_spreedly(sxml.free_trial_response(12345, self.user.id))
                    self.trial_plan.start_trial(self.user)
                    self.assertFalse(self.trial_plan.trial_eligible(self.user))

    def test_get_return_url(self):
        url = self.trial_plan.get_return_url(self.user)
        self.assertEquals(url, 'https://www.testsite.com/return/1/12345/')

class TestSubscriptions(TestCaseSetup):
    def setUp(self):
        super(TestSubscriptions, self).setUp(self)
        sxml = SpreedlySubscriptionXML()
        with patch.object(pyspreedly.api.Client, 'get_info') as mock_get_info:
            with patch.object(pyspreedly.api.Client, 'create_subscriber') as mock_create_subscriber:
                with patch.object(pyspreedly.api.Client, 'subscribe') as mock_subscribe:
                    mock_get_info.side_effect = requests.HTTPError
                    mock_create_subscriber.return_value = objectify_spreedly(sxml.create_user(self.user.id))
                    mock_subscribe.return_value = objectify_spreedly(sxml.free_trial_response(12345, self.user.id))
                    self.subscription = self.trial_plan.start_trial(self.user)

    def test_add_charge(self):
        """This should fail as it is a trial plan - so no fee should be added.
        Not sure how to add a test to check a real add fee as you need
        user interaction"""
        with patch('requests.get') as response_get_mock:
            with patch('requests.models.Response') as response_mock:
                response_mock.status_code = 422
                response_mock.text = ''
                response_get_mock.return_value = response_mock
                fee = Fee.objects.get(plan=self.trial_plan)
                self.assertRaises(HttpUnprocessableEntity,self.subscription.add_fee,
                        *(fee, 'a description',24,))


class TestFees(TestCaseSetup):
    def test_create_fee(self):
        self.plan = Plan.objects.get(id=67890)
        fee_group = FeeGroup.objects.create(name="Test feegroup 1")
        fee_group2 = FeeGroup.objects.create(name="test feegroup 2")
        fee = Fee.objects.create(
                plan=self.plan,
                name=u"test fee",
                group=fee_group,
                default_amount=0)
        fee2 = Fee.objects.create(
                plan=self.plan,
                name=u"test fee 2",
                group=fee_group,
                default_amount=10)
        self.assertRaises(ValueError, Fee.objects.create, kwargs={
                'plan':self.plan,
                'name':u"test fee 2",
                'group':fee_group,
                'default_amount':-10})
        fee.delete()
        fee2.delete()
        fee_group.delete()
        fee_group2.delete()


class Resp(object):
    def __init__(self, text='hi',status_code=201):
        self.text = text
        self.status_code = status_code


class TestAddFee(TestCaseSetup):
    def setUp(self):
        self.spreedly_client = Client(settings.SPREEDLY_AUTH_TOKEN, settings.SPREEDLY_SITE_NAME)
        self.plan = Plan.objects.get(pk=22215)
        self.user = User.objects.create(username='test')
        self.client_data = self.spreedly_client.create_subscriber(self.user.id,'test')
        self.fee_group = FeeGroup.objects.create(name="Test feegroup 1")
        self.fee_group2 = FeeGroup.objects.create(name="test feegroup 2")
        self.fee = Fee.objects.create(
                plan=self.plan,
                name=u"test fee",
                group=self.fee_group,
                default_amount=0)
        self.fee2 = Fee.objects.create(
                plan=self.plan,
                name=u"test fee 2",
                group=self.fee_group,
                default_amount=10)
        # Get them subscribed to a real Plan

    def tearDown(self):
        self.fee.delete()
        self.fee2.delete()
        self.fee_group.delete()
        self.fee_group2.delete()
        self.user.delete()
        self.spreedly_client.cleanup()

    def test_add_fee(self):
        self.skipTest("add fee needs to be mocked some how")
        user_data = {
            'name':'test_subscriber',
            'first_name'    : 'hi',
            'last_name'     : 'world',
            'feature_level' : 'test fees',
            'active_until'  : datetime.today() + timedelta(days=1),
            'token'         : 'hello world',
            'eligible_for_free_trial' : False,
            'active'        : True,
            'url'           : 'https://www.example.com/',
            }

        subscriber = Subscription.objects.get_or_create(self.user, self.plan,
                data=user_data)
        line_item = self.fee.add_fee(self.user, "test Stuff", 10)
        self.assertEquals(line_item.fee, self.fee)
        self.assertEquals(line_item.user, self.user)
        self.assertEquals(line_item.amount, 10)
        self.assertTrue(line_item.successfull)
