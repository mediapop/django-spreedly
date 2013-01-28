from django.conf import settings
from django.contrib.auth.models import User
from pyspreedly.api import Client
from django.test import TestCase
from django.test.client import Client as DjClient
from django.core.urlresolvers import reverse
from pyspreedly import api
from spreedly.functions import sync_plans
from spreedly.models import HttpUnprocessableEntity
from spreedly.models import Plan, Subscription
from django.utils.unittest import skip


class TestReturn(TestCase):
    def setUp(self):
        self.spreedly_client = api.Client(settings.SPREEDLY_AUTH_TOKEN, settings.SPREEDLY_SITE_NAME)
        self.spreedly_client.cleanup()
        self.client = DjClient()
        Plan.objects.sync_plans()
        self.plan = Plan.objects.all()[0]
        user = User.objects.create_user(username='root',password='secret')
        user.is_staff = True
        user.save()
        self.user = User.objects.create_user(username='tester',password='secret')
        self.user2 = User.objects.create_user(username='tester2',password='secret')

    def tearDown(self):
        self.spreedly_client.cleanup()

    def TestSpreedlyReturnWithNoSubscription(self):
        self.assertEquals(Subscription.objects.all().count(), 0)
        url = reverse("spreedly_return", kwargs={'user_id': self.user.id,
                                                 'plan_id': self.plan.id})
        response = self.client.get(url)
        self.assertEquals(response.status_code, 404,
                "Created return without spreedly having the subscription")
        self.spreedly_client.create_subscriber(
                customer_id=self.user.id,
                screen_name=self.user.username)
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200,
                "Failed to create return with spreedly having the" \
                " subscription")
        self.assertEquals(Subscription.objects.all().count(), 1)


class TestViewsExist(TestCase):
    def setUp(self):
        self.spreedly_client = api.Client(settings.SPREEDLY_AUTH_TOKEN, settings.SPREEDLY_SITE_NAME)
        self.spreedly_client.cleanup()
        self.client = DjClient()
        Plan.objects.sync_plans()
        user = User.objects.create_user(username='root',password='secret')
        user.is_staff = True
        user.save()
        user = User.objects.create_user(username='tester',password='secret')
        self.subscriber = Subscription.objects.get_or_create(user)
        user = User.objects.create_user(username='tester2',password='secret')

    def tearDown(self):
        self.spreedly_client.cleanup()

    def test_plan_list_view(self):
        """(the poorly named) List view should show the plans, and a form."""
        url = reverse('plan_list')
        response = self.client.get(url)
        self.assertTemplateUsed(response,'spreedly/plan_list.html')

    def test_list_view(self):
        """there should be a view which shows a list of plans - enabled and not"""
        self.skipTest("Add real tests for this")
        url = reverse('plan_list')  #Whu?
        response = self.client.get(url)
        self.assertTemplateUsed(response,'spreedly/plan_list.html')

    def test_buy_view(self):
        """there should be a view which sends you to spreedly for purchace"""
        self.skipTest("Add real tests for this")
        url = reverse('plan_list')  #Again??
        response = self.client.get(url)
        self.assertTemplateUsed(response,'spreedly/plan_list.html')

    def test_email_set(self):
        """Email sent view should also exist"""
        url = reverse('spreedly_email_sent', kwargs={'user_id': 1})
        response = self.client.get(url)
        self.assertTemplateUsed(response,'spreedly/email_sent.html')

    def test_spreedly_return(self):
        """The welcome back and thank you for your plastic page should also exist
        (I need more caffine)"""
        url = reverse('spreedly_return', kwargs={'user_id':1,'plan_pk':Plan.objects.all()[0].id})
        response = self.client.get(url)
        self.assertTemplateUsed(response,'spreedly/return.html')

    def test_my_subscription(self):
        """my subscription page should exisit, wrapper view."""
        url = reverse('my_subscription')
        response = self.client.get(url)
        self.assertRedirects(response,reverse('login')+'?next=' + url)
        self.client.login(username='tester',password='secret')
        response = self.client.get(url)
        self.assertTemplateUsed(response,'spreedly/subscription_details.html')

    def test_plan_view(self):
        """There should be a view to show you a plan's details"""
        url = reverse('plan_details',kwargs={'plan_pk':Plan.objects.all()[0].id})
        response = self.client.get(url)
        self.assertTemplateUsed(response,'spreedly/plan_details.html')


    def test_subscriber_view(self):
        """there should be a view to show a subscriber's info"""
        url = reverse('subscription_details',kwargs={'user_id':self.subscriber.user.id})
        response = self.client.get(url)
        self.assertRedirects(response,reverse('login')+'?next=' + url)
        self.client.login(username='root',password='secret')
        response = self.client.get(url)
        self.assertTemplateUsed(response,'spreedly/subscription_details.html')

    @skip("not ready")
    def test_edit_subscriber(self):
        """Subscribers are mutable, change them"""
        url = reverse('edit_subscription',kwargs={'user_id':self.subscriber.user.id})
        response = self.client.get(url)
        self.assertRedirects(response,reverse('login'))
        self.client.login(username='root',password='secret')
        response = self.client.get(url)
        self.assertTemplateUsed(response,'spreedly/return.html')
