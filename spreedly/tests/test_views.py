from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client as DjClient
from django.core.urlresolvers import reverse
from pyspreedly import api
from spreedly.models import Plan, Subscription
from django.utils.unittest import skip
from . helpers import SpreedlySubscriptionXML
from mock import patch


class ViewsSetup(TestCase):
    fixtures = ['plans', 'fees']
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
        self.spreedly_client = api.Client(settings.SPREEDLY_AUTH_TOKEN, settings.SPREEDLY_SITE_NAME)
        self.spreedly_client.cleanup()
        self.client = DjClient()
        self.patcher = patch.object(Plan.objects, 'sync_plans')
        self.mock_sync_plans = self.patcher.start()
        self.mock_sync_plans.return_value = None
        self.user = User.objects.create_user(username='test user',
                email='test@mediapopinc.com',
                password='testpassword')
        import ipdb; ipdb.set_trace()  # BREAKPOINT
        self.trial_plan = Plan.objects.get(id=12345)
        self.paid_plan = Plan.objects.get(id=67890)
        self._setup_subscription_with_mock(plan=self.paid_plan)

    def tearDwon(self):
        self.patcher.stop()

class TestViewsExist(ViewsSetup):
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

    @skip("Not ready")
    def test_edit_subscriber(self):
        """Subscribers are mutable, change them"""
        url = reverse('edit_subscription',kwargs={'user_id':self.subscriber.user.id})
        response = self.client.get(url)
        self.assertRedirects(response,reverse('login'))
        self.client.login(username='root',password='secret')
        response = self.client.get(url)
        self.assertTemplateUsed(response,'spreedly/return.html')
