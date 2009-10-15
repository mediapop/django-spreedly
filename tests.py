# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase

from pyspreedly.api import Client
from subscription.models import Plan

SPREEDLY_AUTH_TOKEN = getattr(settings, 'SPREEDLY_AUTH_TOKEN', '')
SPREEDLY_SITE_NAME = getattr(settings, 'SPREEDLY_SITE_NAME', '')

class TestSubscription(TestCase):
    def setUp(self):
        user = User.objects.create(username='test')
        self.sclient = Client(SPREEDLY_AUTH_TOKEN, SPREEDLY_SITE_NAME)

    def tearDown(self):
        # Remove all subscribers
        self.sclient.cleanup()

    def test_sync_plans(self):
        # Initial sync
        Plan.objects.sync()
        qs = Plan.objects.all()
        self.assertEquals(qs.count(), 4)

        # Lets simulate a situation when some plan was changed.
        # We change it locally to cheat the system.
        p = qs[0]
        p.name = 'New Plan'
        p.save()
        Plan.objects.sync()
        qs = Plan.objects.all()
        self.assertEquals(qs.count(), 4)
        p = qs[0]
        self.assertEquals(p.name, 'Plan') # It should be 'Subscription' again

    def test_changes(self):
        response = self.client.post('/subscription/changes/', {'subscriber_ids': '1,2'})
        print response