from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from pyspreedly.api import Client
from django.core.urlresolvers import reverse
from spreedly.functions import sync_plans
from spreedly.models import Plan


class TestSubscription(TestCase):
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
    @classmethod
    def setUpClass(self):
        self.user = User.objects.create(username='test')
        Plan.objects.sync_plans()


    def setUp(self):
        self.sclient = Client(settings.SPREEDLY_AUTH_TOKEN, settings.SPREEDLY_SITE_NAME)
        self.plan = Plan.objects.get(pk=1)  # make sure this is trial-enabled
        self.plan2 = Plan.objects.get(pk=2)  # and that this one is not



    def tearDown(self):
        self.sclient.cleanup()

    def test_trial_elegibility(self):
        """Plan should have a check for elegibility"""
        self.assertTrue(self.plan.trial_elegible(self.user))
        self.assertFalse(self.plan2.trial_elegible(self.user))

    def test_start_trial(self):
        """A user should be able to start a free trial on an elegibile plan"""
        self.assertTrue(self.plan.start_trial(self.user))
        self.assertFalse(self.plan2.start_trial(self.user))

    def test_return_url(self):
        url = self.sclient.base_url + reverse('spreedly_return', args=(
                self.user.id, self.plan.id)) + '?trial=true'
        self.assertEquals(self.plan.return_url(self.user), url)
        url =  + reverse('spreedly_return', args=(
                self.user.id, self.plan2.id))
        self.assertEquals(self.plan2.return_url(self.user), url)
