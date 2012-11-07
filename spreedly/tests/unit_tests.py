from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from pyspreedly.api import Client
from django.core.urlresolvers import reverse
from spreedly.functions import sync_plans
from spreedly.models import Plan


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
        self.user = User.objects.create(username='test')
        self.client_data = self.sclient.create_subscriber(self.user.id,'test')
        Plan.objects.sync_plans()
        self.plan = Plan.objects.get(pk=21431)  # make sure this is trial-enabled
        self.plan2 = Plan.objects.get(pk=21430)  # and that this one is not

    @classmethod
    def tearDownClass(self):
        self.user.delete()
        self.sclient.cleanup()

    def test_trial_elegibility(self):
        """Plan should have a check for elegibility"""
        self.assertTrue(self.plan.trial_elegible(self.user))
        self.assertFalse(self.plan2.trial_elegible(self.user))

    def test_start_trial(self):
        """A user should be able to start a free trial on an elegibile plan"""
        self.assertTrue(self.plan.start_trial(self.user))
        self.assertFalse(self.plan2.start_trial(self.user))

    def test_get_return_url(self):
        url = self.plan.get_return_url(self.user)
        self.assertEquals(url, 'https://www.testsite.com/return/1/21431/')

class TestSubscriptions(TestCase):
    fixtures = ['sites',]
    @classmethod
    def setUpClass(self):
        self.user = User.objects.create(username='test')
        Plan.objects.sync_plans()


    def setUp(self):
        self.sclient = Client(settings.SPREEDLY_AUTH_TOKEN, settings.SPREEDLY_SITE_NAME)
        self.plan = Plan.objects.get(pk=21430)  # and that this one is not
        self.subscription = self.plan.start_trial(self.user)

    def tearDown(self):
        self.sclient.cleanup()

    def test_add_charge(self):
        new_charge = self.subscription.add_fee('test fee', 'a description',
                'test bill group', 24)
