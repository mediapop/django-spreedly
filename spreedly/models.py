from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from django.http import Http404
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from pyspreedly import api
from urlparse import urljoin
import spreedly.settings as spreedly_settings
from django.conf import settings
import warnings

try:
    from django.utils.timezone import datetime
except ImportError:
    from datetime import datetime
from datetime import timedelta


class HttpUnprocessableEntity(Exception):
    pass


class PlanManager(models.Manager):
    def enabled(self):
        return self.model.objects.filter(enabled=True)

    def sync_plans(self):
        """
        Gets a full list of plans from spreedly, and updates the local db
        to match it
        """
        client = api.Client(settings.SPREEDLY_AUTH_TOKEN, settings.SPREEDLY_SITE_NAME)

        for plan in client.get_plans():
            plan = plan['subscription_plan']
            p, created = Plan.objects.get_or_create(pk=plan['id'])

            changed = False
            for k, v in plan.items():
                if hasattr(p, k) and not getattr(p, k) == v:
                    setattr(p, k, v)
                    changed = True
            if changed:
                p.save()


# Figure out what spreedly calls these in XML to get the lookup correct.
PLAN_TYPES = (
                ('regular', _('Regular')),
                ('metered', _('Metered')),
                ('free_trial', _('Trial'),)
                )


class Plan(models.Model):
    '''
    Subscription plan
    '''
    id = models.IntegerField(db_index=True, primary_key=True,
            verbose_name="Spreedly ID",
            help_text="Spreedly plan ID")
    name = models.CharField(max_length=64, null=True)
    description = models.TextField(null=True,blank=True)
    terms = models.CharField(max_length=100, blank=True)

    plan_type = models.CharField(max_length=10, choices=PLAN_TYPES,blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, default='0',
        help_text=u'USD', null=True)

    enabled = models.BooleanField(default=False)
    force_recurring = models.BooleanField(default=False)
    needs_to_be_renewed = models.BooleanField(default=False)

    duration_quantity = models.IntegerField(blank=True, default=0)
    duration_units = models.CharField(max_length=10, blank=True)

    feature_level = models.CharField(max_length=100, blank=True)

    return_url = models.URLField(blank=True)

    created_at = models.DateTimeField(editable=False, null=True)
    date_changed = models.DateTimeField(editable=False, null=True)

    version = models.IntegerField(blank=True, default=1)

    spreedly_site_id = models.IntegerField(db_index=True, null=True)

    objects = PlanManager()

    class NotEligibile(Exception):
        pass


    class Meta:
        ordering = ['name']

    def __init__(self, *args, **kwargs):
        self._client = api.Client(settings.SPREEDLY_AUTH_TOKEN, settings.SPREEDLY_SITE_NAME)
        super(Plan, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return self.name

    def trial_eligible(self, user):
        """Is a customer/user eligibile for a trial?"""
        try:
            subscription = user.subscription
            if subscription.plan == self and subscription.eligible_for_free_trial:
                return True
            else:
                return False
        except Subscription.DoesNotExist:
            return self.is_free_trial_plan

    def start_trial(self, user):
        """Check if a user is eligibile for a trial on this plan, and if so,
        start a plan
        :param user: user object to check
        :returns: py:class:`Subscription`
        :raises: py:class:`Plan.NotEligibile` if the user is not eligibile
        """
        if self.trial_eligible(user):
            response = self._client.subscribe(user.id, self.id)
            return Subscription.objects.get_or_create(user, self, response)
        else:
            raise self.NotEligibile()

    @property
    def plan_type_display(self):
        warnings.warn("Deprecated due to switiching to choices",DeprecationWarning)
        return self.plan_type.replace('_',' ').title()


    @property
    def is_gift_plan(self):
        return self.plan_type == "gift"

    @property
    def is_free_trial_plan(self):
        return self.plan_type == "free_trial"

    def get_return_url(self, user):
        site = Site.objects.get(pk=settings.SITE_ID)
        base_url = 'https://{site.domain}/'.format(site=site)
        url = urljoin(base_url, reverse('spreedly_return', args=[user.id, self.id]))
        return url

    def subscription_url(self,user):
        try:
            token = user.subscription.token
        except (AttributeError, Subscription.DoesotExist):
            token = None
        return self._client.get_signup_url(subscriber_id=user.id,plan_id=self.id,
            screen_name=user.username, token=token)


class SubscriptionManager(models.Manager):
    def get_or_create(self, user, plan=None, data=None):
        """ .. py:method:: get_or_create(user, plan, data)
        get or create a subscription based on a user, plan and data passed
        :param user: py:class:`auth.User`
        :param plan: py:class:`Plan`
        :param data: python dict containing the data as returned from spreedly
        :returns: py:class:`Subscription`
        """
        try:
            subscription = self.get(user=user,plan=plan)
        except Subscription.DoesNotExist:
            subscription = Subscription()
            if not data:  # new client, no plan.
                data = subscription._client.create_subscriber(user.id, user.username)
            for k in data:
                try:
                    if data[k] is not None:
                        if subscription.get(k) != data[k]:
                            setattr(subscription,k,data[k])
                except AttributeError:
                    pass
        subscription.user = user
        subscription.plan = plan
        subscription.active = getattr(subscription, 'active', bool(plan))
        subscription.save()
        return subscription


class Subscription(models.Model):
    name = models.CharField(max_length=100, blank=True)

    user = models.OneToOneField('auth.User', primary_key=True)
    first_name = models.CharField(blank=True, max_length=100)
    last_name = models.CharField(blank=True, max_length=100)
    feature_level = models.CharField(max_length=100, blank=True)
    active_until = models.DateTimeField(blank=True, null=True)
    token = models.CharField(max_length=100, blank=True)

    eligible_for_free_trial = models.BooleanField(default=False)
    lifetime = models.BooleanField(default=False)
    recurring = models.BooleanField(default=False)
    active = models.BooleanField(default=False)

    plan = models.ForeignKey(Plan, null=True, default=None)

    url = models.URLField(editable=False)

    card_expires_before_next_auto_renew = models.BooleanField(default=False)

    objects = SubscriptionManager()

    def __init__(self, *args, **kwargs):
        self._client = api.Client(settings.SPREEDLY_AUTH_TOKEN, settings.SPREEDLY_SITE_NAME)
        super(Subscription,self).__init__(*args, **kwargs)

    def __unicode__(self):
        return u'Subscription for %s' % self.user

    def save(self, *args, **kwargs):
        if self.active and not self.user.is_active:
            self.user.is_active = True
            self.user.save()
        self.url = urljoin(self._client.base_url,'subscriber_accounts/{token}'.format(token=self.token))
        super(Subscription, self).save(*args, **kwargs)

    @property
    def ending_this_month(self):
        """Will this plan end within the next 30 days"""
        return datetime.today() <= self.active_until <= datetime.today() + timedelta(days=30)

    @property
    def subscription_active(self):
        '''gets the status based on current active status and active_until'''
        if self.active and (self.active_until > datetime.today() or self.active_until == None):
            return True
        return False

    def subscription_url(self, user):
        raise NotImplementedError()

    def allow_free_trial(self):
        """ .. py:method:: allow_free_trial()
        Allow a free Trial
        :returns: :py:class:`Subscription`
        :raises: :py:class:`Exception` (of some kind) if bad juju
        """
        response  = self._client.allow_free_trial(self.user.id)
        for k in response:
            try:
                if response[k] is not None:
                    if getattr(self,k) != response[k]:
                        setattr(self,k,response[k])
            except AttributeError:
                pass
        self.save()
        return self

    def create_complimentary_subscription(self, time, unit, feature_level):
        """ .. py:method:create_complimentary_subscription(time, unit, feature_level)
        :raises: :py:cls: `NotImplementedError` cause it isn't implemented
        """
        raise NotImplementedError()

    def add_fee(self, name, description, group, amount):
        """ .. py:method:: add_fee(name, description, group, ammount)
        Add a fee to the subscription
        :param name: the name of the fee (eg - Excess Bandwidth Charge)
        :param description: a description of the charge
        :param group: a group to add this charge too
        :param amount: the amount the charge is for
        :returns: None
        :raises: Http404 if incorrect subscriber, HttpUnprocessableEntity for
            any other 422 error
        """
        response = self._client.add_fee(self.user.id,name,description,group,
                amount)
        if response == 404:
            raise Http404()
        elif response == 422:
            raise HttpUnprocessableEntity()


class Gift(models.Model):
    uuid = models.CharField(max_length=32, unique=True, db_index=True)

    from_user = models.ForeignKey(User, related_name='gifts_sent')
    to_user = models.ForeignKey(User, related_name='gifts_received')

    plan_name = models.CharField(max_length=100)
    message = models.TextField(blank=True)

    created_at = models.DateField(auto_now_add=True)
    sent_at = models.DateField(blank=True, null=True)

    def get_activation_url(self):
        return 'http://%s%s' % (spreedly_settings.SPREEDLY_SITE_URL, reverse('gift_sign_up', args=[self.uuid]))

    def send_activation_email(self):
        if not self.sent_at: #don't spam user with invitations
            send_mail(
                spreedly_settings.SPREEDLY_GIFT_EMAIL_SUBJECT,
                render_to_string(spreedly_settings.SPREEDLY_GIFT_EMAIL, {
                    'message': self.message,
                    'plan_name': self.plan_name,
                    'giver': '%s (%s)' % (self.from_user, self.from_user.email),
                    'site': spreedly_settings.SPREEDLY_SITE_URL,
                    'register_url': self.get_activation_url()
                }),
                settings.DEFAULT_FROM_EMAIL,
                [self.to_user.email,]
            )
            self.sent_at = datetime.today()
            self.save()
