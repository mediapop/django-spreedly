from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.core.exceptions import SuspiciousOperation
from django.utils.decorators import classonlymethod
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.models import User
from django.template import RequestContext
from django.core.cache import cache
from django.conf import settings
from django import forms
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import (ListView, TemplateView, View, FormView,
        DetailView, UpdateView)
from django.views.generic.edit import FormMixin
from django.core.urlresolvers import reverse

from pyspreedly.api import Client
from spreedly.functions import sync_plans, get_subscription, start_free_trial
from spreedly.models import Plan, Subscription, Gift
import spreedly.settings as spreedly_settings
from spreedly.forms import SubscribeForm, GiftRegisterForm, AdminGiftForm, SubscribeUpdateForm
from spreedly import signals

class SubscribeMixin(FormMixin):
    """
    inherits from FormMixin, handles, get_success_url, form valid, invalid and
    post.  Needs to be integerated into get context data and get_success_url
    """
    form_class = SubscribeForm

    def get_success_url(self):
        return reverse('spreedly_email_sent', args=[self.request.user_id])

    def form_valid(self, form):
        form.save()
        super(PlanList, self).form_valid(form)

    def form_invalid(self, form):
        self.render_to_response(self.get_context_data(
            object_list=self.object_list, form=form))

    def post(self):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class PlanList(ListView, SubscribeMixin):
    """
    inherits from :py:class:`ListView` and :py:class:`FormMixin`, hybrid list and
    subscription entry view.
    default template name is `spreedly_plan_list.html`,
    object_list name is `plans`
    cache's plans for 24 hours
    """
    template_name = "spreedly/plan_list.html"
    model = Plan
    context_object_name = 'plans'

    def get_context_data(self, object_list, **kwargs):
        """
            Adds form and object list plus whatever else is passed as a kwarg
            to the context.
            :param object_list: list of :py:class:`Plan`s (actually queryset)
            """
        context = ListView.get_context_data(self, object_list=object_list)
        context.update(SubscribeMixin.get_context_data(self, **kwargs))
        if self.request.user.is_authenticated():
            context['current_user_subscription'] = getattr(self.request.user, 'subscription', None)
        else:
            context['current_user_subscription'] = None
        return context

    def get_queryset(self):
        """
            Gets and caches the plan list for 1 day
        """
        cache_key = 'spreedly_plans_list'
        plans = cache.get(cache_key)
        if not plans:
            Plan.objects.sync_plans()
            plans = Plan.objects.enabled()
            cache.set(cache_key, plans, 60*60*24)
        return plans

    def get(self, *args, **kwargs):
        """
            Gets the form and object list and returns a rendered template
        """
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        self.object_list = self.get_queryset()
        allow_empty = self.get_allow_empty()
        if not allow_empty and len(self.object_list) == 0:
            raise Http404(_(u"Empty list and '%(class_name)s.allow_empty' is False.")
                          % {'class_name': self.__class__.__name__})
        context = self.get_context_data(object_list=self.object_list, form=form, **kwargs)
        return self.render_to_response(context)


class EmailSent(TemplateView):
    """
        A thankyou page for after registration saying an email has been sent
    """
    template_name = 'spreedly/email_sent.html'

    def get_context_data(self, *args, **kwargs):
        self.context_data = super(EmailSent, self).get_context_data(*args, **kwargs)
        self.context_data['user'] = get_object_or_404(User, pk=self.kwargs['user_id'])
        return self.context_data

def email_sent(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise Http404

    return render_to_response(
        spreedly_settings.SPREEDLY_EMAIL_SENT_TEMPLATE, {
            'request': request,
            'user': user
        }
    )


class SpreedlyReturn(TemplateView):
    template_name = 'spreedly/return.html'

    def get_context_data(self, *args, **kwargs):
        # removed gift, request and login url
        self.context_data = super(SpreedlyReturn,self).get_context_data(*args, **kwargs)
        user = get_object_or_404(User, pk=self.kwargs['user_id'])
        plan = get_object_or_404(Plan, pk=self.kwargs['plan_pk'])
        if self.request.GET.has_key('trial'):
            if plan.trial_eligible(user):
                subscription = plan.start_trial(user)
            else:
                raise SuspiciousOperation("Trial asked for - but you are not eligibile for a free trial")
        else:
            subscription = Subscription.objects.get_or_create(user, plan)
        self.context_data['subscription'] = subscription
        return self.context_data


@csrf_exempt
def spreedly_listener(request):
    if request.method == 'POST':
        # Try to extract customers' IDs
        if request.POST.has_key('subscriber_ids'):
            subscriber_ids = request.POST['subscriber_ids'].split(',')
            if len(subscriber_ids):
                client = Client(settings.SPREEDLY_AUTH_TOKEN, settings.SPREEDLY_SITE_NAME)
                for id in subscriber_ids:
                    # Now let's query Spreedly API for the actual changes
                    data = client.get_info(int(id))
                    try:
                        user = User.objects.get(pk=id)


                        subscription, created = Subscription.objects.get_or_create(user=user)

                        for k, v in data.items():
                            if hasattr(subscription, k):
                                setattr(subscription, k, v)
                        subscription.save()

                        signals.subscription_update.send(sender=subscription, user=User.objects.get(id=id))
                    except User.DoesNotExist:
                        # TODO not sure what exactly to do here. Delete the subscripton on spreedly?
                        pass
                #handle gifts
                for gift in Gift.objects.filter(to_user__pk__in=subscriber_ids):
                    gift.send_activation_email()
    return HttpResponse() #200 OK


class SubscriptionDetails(DetailView):
    """
    view to see subscription details.  takes subscription id as an optional
    parameter.  if it is not there return the user's subscription if available,
    if not 404.  if user.is_staff() - then you can see any Subscription details.
    """
    model = Subscription
    context_object_name = 'subscription'
    template_name = 'spreedly/subscription_details.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(SubscriptionDetails, self).dispatch(*args, **kwargs)

    def get_object(self, queryset=None):
        """
        if you are admin - any subscription can be shown, else, only that
        which is associated with you
        """
        try:
            obj = super(SubscriptionDetails, self).get_object(queryset)
        except AttributeError:
            # Called w/o id, so return my subscription or 404
            try:
                return self.request.user.subscription
            except Subscription.DoesNotExist:
                return Http404(_(u"You have no subscriptions!"))
        if obj.user != self.request.user and not self.request.user.is_staff():
            raise SuspiciousOperation(_(u"That isn't yours"))
        return obj


class PlanDetails(DetailView, SubscribeMixin):
    model = Plan
    pk_url_kwarg = 'plan_pk'
    slug_url_kwarg = 'plan_pk'
    context_object_name = 'plan'
    template_name = 'spreedly/plan_details.html'

    def get_context_data(self, **kwargs):
        context = DetailView.get_context_data(self, **kwargs)
        if self.request.user.is_authenticated():
            context['current_user_subscription'] = getattr(self.request.user, 'subscription', None)
        else:
            context['current_user_subscription'] = None
        return context

    def get(self, *args, **kwargs):
        self.object = self.get_object()
        kwargs['object'] = self.object
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        form.fields['subscription'].widget = forms.HiddenInput()
        form.fields['subscription'].initial = self.object
        kwargs['form'] = form
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class EditSubscriber(UpdateView):
    model = Subscription
    form = SubscribeUpdateForm

    def dispatch(self, *args, **kwargs):
        raise NotImplementedError
