from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from pyspreedly.api import Client
from django.core.urlresolvers import reverse
from spreedly.functions import sync_plans
from spreedly.models import HttpUnprocessableEntity
from spreedly.models import Plan, Fee, FeeGroup, LineItem, Subscription
from datetime import datetime, timedelta
import requests
from mock import patch
import ipdb


class TestSyncPlans(TestCase):
    def setUp(self):
        user = User.objects.create(username='test')
        self.sclient = Client(settings.SPREEDLY_AUTH_TOKEN, settings.SPREEDLY_SITE_NAME)

    def tearDown(self):
        # Remove all subscribers
        self.sclient.cleanup()

    def test_sync_plans(self):
        # Initial sync
        spreedly_count = len(self.sclient.get_plans())
        Plan.objects.sync_plans()
        qs = Plan.objects.all()
        self.assertEquals(qs.count(), spreedly_count)


class TestPlan(TestCase):
    fixtures = ['sites',]
    @classmethod
    def setUpClass(self):
        self.sclient = Client(settings.SPREEDLY_AUTH_TOKEN, settings.SPREEDLY_SITE_NAME)
        Plan.objects.sync_plans()
        self.plan = Plan.objects.get(pk=21327)  # make sure this is trial-enabled
        self.plan2 = Plan.objects.get(pk=22215)  # and that this one is not

    def setUp(self):
        self.user = User.objects.create(username='test')
        self.client_data = self.sclient.create_subscriber(self.user.id,'test')

    def tearDown(self):
        self.user.delete()
        self.sclient.cleanup()

    def test_trial_eligibility(self):
        """Plan should have a check for eligibility"""
        self.assertTrue(self.plan.trial_eligible(self.user))
        self.assertFalse(self.plan2.trial_eligible(self.user))

    def test_start_trial(self):
        """A user should be able to start a free trial on an eligibile plan"""
        self.assertTrue(self.plan.start_trial(self.user))
        self.assertRaises(Plan.NotEligibile,self.plan2.start_trial,self.user)

    def test_trial_eligibility_on_trial(self):
        self.plan.start_trial(self.user)
        self.assertFalse(self.plan.trial_eligible(self.user))

    def test_get_return_url(self):
        url = self.plan.get_return_url(self.user)
        self.assertEquals(url, 'https://www.testsite.com/return/1/21327/')

class TestSubscriptions(TestCase):
    fixtures = ['sites',]
    @classmethod
    def setUpClass(self):
        Plan.objects.sync_plans()

    def setUp(self):
        self.sclient = Client(settings.SPREEDLY_AUTH_TOKEN, settings.SPREEDLY_SITE_NAME)
        self.plan = Plan.objects.get(pk=21327)
        self.user = User.objects.create(username='test')
        self.client_data = self.sclient.create_subscriber(self.user.id,'test')
        self.subscription = self.plan.start_trial(self.user)

    def tearDown(self):
        self.user.delete()
        self.sclient.cleanup()

    def test_add_charge(self):
        """This should fail as it is a trial plan - so no fee should be added.
        Not sure how to add a test to check a real add fee as you need
        user interaction"""
        fee_group = FeeGroup.objects.create(name="Test feegroup 1")
        fee = Fee.objects.create(
                plan=self.plan,
                name=u"test fee",
                group=fee_group,
                default_amount=1)
        self.assertRaises(HttpUnprocessableEntity,self.subscription.add_fee,
                *(fee, 'a description',24,))


class TestFees(TestCase):
    fixtures = ['sites',]
    @classmethod
    def setUpClass(self):
        Plan.objects.sync_plans()

    def setUp(self):
        self.sclient = Client(settings.SPREEDLY_AUTH_TOKEN, settings.SPREEDLY_SITE_NAME)
        self.plan = Plan.objects.get(pk=21431)
        self.user = User.objects.create(username='test')
        self.client_data = self.sclient.create_subscriber(self.user.id,'test')
        # Get them subscribed to a real Plan

    def tearDown(self):
        self.user.delete()
        self.sclient.cleanup()

    def test_create_fee(self):
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


class TestAddFee(TestCase):
    fixtures = ['sites',]

    @classmethod
    def setUpClass(self):
        Plan.objects.sync_plans()

    def setUp(self):
        self.sclient = Client(settings.SPREEDLY_AUTH_TOKEN, settings.SPREEDLY_SITE_NAME)
        self.plan = Plan.objects.get(pk=22215)
        self.user = User.objects.create(username='test')
        self.client_data = self.sclient.create_subscriber(self.user.id,'test')
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
        self.sclient.cleanup()

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
