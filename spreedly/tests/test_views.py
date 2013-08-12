from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.core.exceptions import SuspiciousOperation
from django.core.urlresolvers import reverse
from pyspreedly import api
from spreedly.models import Plan, Subscription
from django.utils.unittest import skip
from mock import patch
from mocks import get_client_mock


ClientMock = get_client_mock(settings.SPREEDLY_SITE_NAME)


@patch('pyspreedly.api.Client', new_callable=ClientMock)
class ViewsSetup(TestCase):
    fixtures = ['plans.json', 'fees.json']

    def setUp(self):
        with patch('pyspreedly.api.Client',
                   new=ClientMock) as client_mock:
            self.spreedly_client = client_mock()
            self.user = User.objects.create_user(username='test user',
                                                 email='test@mediapopinc.com',
                                                 password='testpassword')
            self.trial_plan = Plan.objects.get(id=12345)
            self.paid_plan = Plan.objects.get(id=67890)
            self.subscription = Subscription.objects.create(
                user=self.user,
                plan=self.paid_plan)


@patch('pyspreedly.api.Client', new=ClientMock)
class TestViewsExist(ViewsSetup):
    def test_plan_list_view(self):
        """(the poorly named) List view should show the plans, and a form."""
        url = reverse('plan_list')
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'spreedly/plan_list.html')

    def test_list_view(self):
        """there should be a view which shows a list of plans - enabled and
        not"""
        self.skipTest("Add real tests for this")
        url = reverse('plan_list')  #Whu?
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'spreedly/plan_list.html')

    def test_buy_view(self):
        """there should be a view which sends you to spreedly for purchase"""
        self.skipTest("Add real tests for this")
        url = reverse('plan_list')  #Again??
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'spreedly/plan_list.html')

    def test_email_set(self):
        """Email sent view should also exist"""
        url = reverse('spreedly_email_sent', kwargs={'user_id': 1})
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'spreedly/email_sent.html')

    def test_spreedly_return(self):
        """The welcome back and thank you for your plastic page should also
        exist"""
        user = User.objects.create_user(username='test user2',
                                        email='test@mediapopinc.com',
                                        password='testpassword')
        url = reverse('spreedly_return',
                      kwargs={'user_id': user.id,
                              'plan_pk': Plan.objects.all()[0].id})
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'spreedly/return.html')

    def test_spreedly_return_already_subscribed(self):
        """The welcome back and thank you for your plastic page should also
        exist"""
        url = reverse('spreedly_return',
                      kwargs={'user_id': self.user.id,
                              'plan_pk': Plan.objects.all()[0].id})
        self.assertRaises(SuspiciousOperation, self.client.get, url)

    def test_my_subscription(self):
        """my subscription page should exisit, wrapper view."""
        url = reverse('my_subscription')
        response = self.client.get(url)
        self.assertRedirects(response, reverse('login') + '?next=' + url)
        self.assertTrue(
            self.client.login(username=self.user, password='testpassword')
        )
        url = reverse('my_subscription')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_plan_view(self):
        """There should be a view to show you a plan's details"""
        url = reverse('plan_details',
                      kwargs={'plan_pk': Plan.objects.all()[0].id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        #self.assertTemplateUsed(response, 'spreedly/plan_details.html')

    def test_subscriber_view(self):
        """there should be a view to show a subscriber's info"""
        url = reverse('subscription_details', kwargs={
            'user_id': self.subscription.user.id
        })

        response = self.client.get(url)
        self.assertRedirects(response, reverse('login') + '?next=' + url)

        self.assertTrue(self.client.login(username=self.subscription.user,
                                          password='testpassword'))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'spreedly/subscription_details.html')

    @skip("Not ready")
    def test_edit_subscriber(self):
        """Subscribers are mutable, change them"""
        url = reverse('edit_subscription',
                      kwargs={'user_id': self.subscriber.user.id})
        response = self.client.get(url)
        self.assertRedirects(response, reverse('login'))
        self.client.login(username='root', password='secret')
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'spreedly/return.html')
