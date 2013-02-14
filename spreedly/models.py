import warnings
import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db import models
from django.http import Http404
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.db import IntegrityError

from pyspreedly import api
import spreedly.settings as spreedly_settings

from requests import HTTPError
from urlparse import urljoin

logger = logging.getLogger(__name__)

try:
    from django.utils.timezone import datetime
except ImportError:
    from datetime import datetime
from datetime import timedelta


class HttpUnprocessableEntity(HTTPError):
    pass


class PlanManager(models.Manager):
    """
        Manager that handles syncing plans and finding enabled plans
    """
    def enabled(self):
        """
            :returns: Returns all enabled :py:class:`Plans`
        """
        return self.model.objects.filter(enabled=True)

    def get_by_natural_key(self, name):
        return self.get(name=name)

    def sync_plans(self):
        """
        Gets a full list of plans from spreedly, and updates the local db
        to match it
        """
        client = api.Client(settings.SPREEDLY_AUTH_TOKEN,
                settings.SPREEDLY_SITE_NAME)

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
    description = models.TextField(null=True, blank=True)
    terms = models.CharField(max_length=100, blank=True)

    plan_type = models.CharField(max_length=10,
            choices=PLAN_TYPES,
            blank=True)
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

    def natural_key(self):
        return (self.name, )

    def get_absolute_url(self):
        return reverse('plan_details', kwargs={'plan_pk': self.id})

    class Meta:
        ordering = ['name']

    def __init__(self, *args, **kwargs):
        self._client = api.Client(settings.SPREEDLY_AUTH_TOKEN,
                settings.SPREEDLY_SITE_NAME)
        super(Plan, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return self.name

    def trial_eligible(self, user):
        """
            Is a customer/user eligibile for a trial?
            :param user: :py:class:`auth.User`

        """
        try:
            subscription = user.subscription
            return (subscription.plan == self and
                    subscription.eligible_for_free_trial)
        except:
            return self.is_free_trial_plan

    def start_trial(self, user):
        """
            Check if a user is eligibile for a trial on this plan, and if so,
            start a plan.

            :param user: user object to check
            :returns: py:class:`Subscription`
            :raises: py:exc:`Plan.NotEligibile` if the user is not eligibile

        """
        if self.trial_eligible(user):
# user needs to exist on spreedly side before it can be signed up for trial
            try:
                self._client.get_info(user.id)
            except HTTPError:
                self._client.create_subscriber(customer_id=user.id,
                                               screen_name=user.username)

            response = self._client.subscribe(subscriber_id=user.id,
                                              plan_id=self.id)
            return Subscription.objects.get_or_create(user, self, response)
        else:
            raise self.NotEligibile()

    @property
    def plan_type_display(self):
        warnings.warn("Deprecated due to switiching to choices",
                DeprecationWarning)
        return self.plan_type.replace('_', ' ').title()

    @property
    def is_gift_plan(self):
        return self.plan_type == "gift"

    @property
    def is_free_trial_plan(self):
        return self.plan_type == "free_trial"

    def get_return_url(self, user, namespace=None):
        site = Site.objects.get(pk=settings.SITE_ID)
        base_url = 'https://{site.domain}/'.format(site=site)
        reverse_urlname = "{0}:spreedly_return".format(namespace) if \
                          namespace else 'spreedly_return'
        url = urljoin(base_url, reverse(reverse_urlname, kwargs={
            'user_id': user.id, 'plan_pk': self.id}))
        return url

    def subscription_url(self, user, namespace=None):
        try:
            token = user.subscription.token
        except (AttributeError, Subscription.DoesNotExist):
            token = None
        subscription_url = self._client.get_signup_url(
                subscriber_id=user.id,
                plan_id=self.id,
                screen_name=user.username,
                token=token)
        return_url = self.get_return_url(user, namespace)
        return "{subscription_url}?return_url={return_url}".format(
                subscription_url=subscription_url,
                return_url=return_url)


class FeeGroup(models.Model):
    name = models.CharField(max_length=100, primary_key=True)

    def __unicode__(self):
        return unicode(self.name)


class Fee(models.Model):
    """ .. py:class::Fee
    A Fee for a given Plan.

    :attr plan: ForeignKey(Plan)
    :attr name: CharField(max_length=100)
    :attr group: ForeignKey(FeeGroup)
    :attr default_amount: DecimalField(default=0)
    """
    plan = models.ForeignKey(Plan)
    name = models.CharField(max_length=100)
    group = models.ForeignKey(FeeGroup)
    default_amount = models.DecimalField(max_digits=6,
            decimal_places=2,
            default='0',
        help_text=u'USD')

    def __unicode__(self):
        return u"{self.plan.name}: {self.name}".format(self=self)

    def add_fee(self, user, description, amount=None):
        """ .. py:method::add_fee(user, description[, amount])

        add a fee to the given user, with description and amount.  if amount
        is not passed, then it will use `default_amount` if it is greater than
        0.

        if 404 or 422 are returned, the default action is not to save the
        line item to the db, this can be overriden with the setting
        SPREEDLY_SAVE_ON_FAIL, but it is not recomended as who knows what will
        happen.

        :param user: the user to bill for the fee.  they must be subscribed to `self.plan`
        :param description: The description of the fee to appear on the invoice
        :param amount: The amount to bill or `None`
        :raises: :py:exc:`ValueError` if the user is not subscribed to the plan or is subscribed to a different plan.
        :raises: :py:exc:`Http404` if spreedly can't find the plan, user, etc.
        :raises: :py:exc:`HttpUnprocessableEntity` if spreedly raised 422 for some reason.
        """
        if not amount:
            amount = self.default_amount
        if amount <= 0:
            raise ValueError("Amount must be greater than 0")
        try:
            if user.subscription.plan != self.plan:
                raise ValueError("This fee is not for the user's plan")
        except Subscription.DoesNotExist:
                raise ValueError("This user is not signed up to a plan")
        line_item = LineItem(
                fee=self,
                user=user,
                amount=amount,
                description=description)
        response = self.plan._client.add_fee(user.id, self.name,
                description, self.group.name, amount)
        response_code = response.status_code
        msg_template = 'fee failed to process due to {reason}: {fee}, ' \
                       '{user}, {description}, {amount}.  response: ' \
                       '{response}'
        if response_code == 404:
            logger.error(msg_template.format(reason="not found",
                             fee=self, user=user, description=description,
                             amount=amount, response=response))
            raise Http404()
        elif response_code == 422:
            logger.error(msg_template.format(reason="unprocesable",
                             fee=self, user=user, description=description,
                             amount=amount, response=response))
            raise HttpUnprocessableEntity()
        try:
            if response_code == 201:
                line_item.successfull = True
                line_item.save()
            elif spreedly_settings.SPREEDLY_SAVE_ON_FAIL:
                # This is probably a terrible idea
                line_item.successfull = False
                return line_item.save()
        except Exception as e:
            logger.critical(
                    'line_item failed to save: {fee}, {user}'
                    ', {description}, {amount}. response: {response} '
                    'line_item: {line_item}, error: {e}'.format(
                            fee=self, user=user, description=description,
                            amount=amount, response=response,
                            line_item=line_item, e=e))
            e.response = response
            raise e


class LineItem(models.Model):
    """This is an instance of a fee"""
    fee = models.ForeignKey(Fee)
    user = models.ForeignKey('auth.User')
    amount = models.DecimalField(max_digits=6, decimal_places=2, default='0',
        help_text=u'USD')
    issued_at = models.DateTimeField(auto_now_add=True)
    started = models.BooleanField(default=False)
    successfull = models.BooleanField(default=False)
    description = models.TextField()
    reference = models.CharField(max_length=100, null=True)
    error_code = models.TextField(null=True)


class SubscriptionManager(models.Manager):
    def create_local(self, user, plan=None):
        """
            Get a subscriber from spreedly and create the local model for it
            :param user: py:class:`auth.User`
            :param plan: py:class:`Plan`
            :returns: py:class:`Subscription`

        """
        try:
            subscription = self.get_query_set().get(user=user, plan=plan)
            raise IntegrityError("Subscriber already exists")
        except Subscription.DoesNotExist:
            subscription = Subscription()
            try:
                data = subscription._client.get_info(user.id)
            except HTTPError:
                logger.exception("Coudln't get subscriber from spreedly")
                raise
            for k in data:
                try:
                    if data[k] is not None:
                        if getattr(subscription, k, None) != data[k]:
                            setattr(subscription, k, data[k])
                except AttributeError:
                    pass
        subscription.user = user
        subscription.plan = plan
        subscription.active = getattr(subscription, 'active', bool(plan))
        subscription.save()
        return subscription

    def get_or_create(self, user, plan=None, data=None):
        """
            get or create a subscription based on a user, plan and data passed
            :param user: py:class:`auth.User`
            :param plan: py:class:`Plan`
            :param data: python dict containing the data as returned from spreedly
            :returns: py:class:`Subscription`

        """
        try:
            subscription = self.get_query_set().get(user=user, plan=plan)
        except Subscription.DoesNotExist:
            subscription = Subscription()
            if not data:  # new client, no plan.
                try:
                    data = subscription._client.get_info(user.id)
                except HTTPError:
                    data = subscription._client.create_subscriber(user.id,
                            user.username)
            for k in data:
                try:
                    if data[k] is not None:
                        if getattr(subscription, k, None) != data[k]:
                            setattr(subscription, k, data[k])
                except AttributeError:
                    pass
        subscription.user = user
        subscription.plan = plan
        subscription.active = getattr(subscription, 'active', bool(plan))
        subscription.save()
        return subscription


class Subscription(models.Model):
    """
    Class that manages the details for a specific :py:class:`auth.User`'s
    subscription to a plan.  Since a user can only have one subscription,
    this is sometimes treated as a user profile class.

    """
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

    plan = models.ForeignKey(Plan,
            null=True,
            default=None,
            on_delete=models.PROTECT)

    url = models.URLField(editable=False)

    card_expires_before_next_auto_renew = models.BooleanField(default=False)

    store_credit = models.DecimalField(max_digits=6,
            decimal_places=2,
            default='0',
            help_text=u'USD')

    objects = SubscriptionManager()

    def __init__(self, *args, **kwargs):
        self._client = api.Client(settings.SPREEDLY_AUTH_TOKEN,
                settings.SPREEDLY_SITE_NAME)
        super(Subscription, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return u'Subscription for %s' % self.user

    def save(self, *args, **kwargs):
        if self.active and not self.user.is_active:
            self.user.is_active = True
            self.user.save()
        self.url = urljoin(self._client.base_url,
                'subscriber_accounts/{token}'.format(token=self.token))
        return super(Subscription, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return self.url

    @property
    def ending_this_month(self):
        """
        Will this plan end within the next 30 days
        """
        return (datetime.today() <= self.active_until <=
                datetime.today() + timedelta(days=30))

    @property
    def subscription_active(self):
        '''
        gets the status based on current active status and active_until
        '''
        return self.active and (self.active_until > datetime.today()
                or self.active_until is None)

    def allow_free_trial(self):
        """
        Allow a free Trial

        :returns: :py:class:`Subscription`
        :raises: :py:class:`Exception` (of some kind) if bad juju
        """
        response = self._client.allow_free_trial(self.user.id)
        for k in response:
            try:
                if response[k] is not None:
                    if getattr(self, k) != response[k]:
                        setattr(self, k, response[k])
            except AttributeError:
                pass
        self.save()
        return self

    def update_subscription(self, data=None):
        """update a subscription with supplied data"""
        #TODO calculate surchargs/credits caused by changes.
        if data is None:
            data = self._client.get_info(self.user.id)
        plan = Plan.objects.get(pk=data['subscription_plan_version']['subscription_plan_id'])
        for k in data:
            try:
                if data[k] is not None:
                    if getattr(self, k) != data[k]:
                        setattr(self, k, data[k])
            except AttributeError:
                pass
        self.plan = plan
        self.save()

    def create_complimentary_subscription(self, time, unit, feature_level):
        """
        :raises: :py:exc:`NotImplementedError` cause it isn't implemented
        """
        raise NotImplementedError()

    def add_fee(self, fee, units, description):
        """
        Add a fee to the subscription

        :param fee: :py:class:`Fee` to add to the linked user
        :param units: the number of units the charge is for (100kb, 4 nights, etc.)
        :param description: a description of the charge
        :returns: None
        :raises: Http404 if incorrect subscriber, HttpUnprocessableEntity for any other 422 error

        """
        amount = fee.default_amount * units
        fee.add_fee(self.user, description, amount)
