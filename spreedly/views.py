from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render_to_response
from django.contrib.auth.models import User
from django.template import RequestContext
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, TemplateView, View, FormView
from django.views.generic.edit import FormMixin
from django.core.urlresolvers import reverse

from pyspreedly.api import Client
from spreedly.functions import sync_plans, get_subscription, start_free_trial
from spreedly.models import Plan, Subscription, Gift
import spreedly.settings as spreedly_settings
from spreedly.forms import SubscribeForm, GiftRegisterForm, AdminGiftForm
from spreedly import signals

class PlanList(ListView, FormMixin):
    """.. py:class:: PlanList
    inherits from :py:cls:`ListView` and :py:cls:`FormMixin`, hybrid list and
    subscription entry view.
    default template name is `spreedly_plan_list.html`,
    object_list name is `plans`
    cache's plans for 24 hours
    """
    template_name = "spreedly_plan_list.html"
    model = Plan
    context_object_name = 'plans'
    form_class = SubscribeForm

    def get_context_data(self, object_list, **kwargs):
        context = ListView.get_context_data(self, object_list)
        context.update(FormMixin.get_context_data(self, **kwargs))
        if self.request.user.is_authenticated():
            context['current_user_subscription'] = getattr(self.request.user, 'subscription', None)
        else:
            context['current_user_subscription'] = None

    def get_queryset(self):
        cache_key = 'spreedly_plans_list'
        plans = cache.get(cache_key)
        if not plans:
            Plan.objects.sync_plans()
            plans = Plan.objects.enabled()
            cache.set(cache_key, plans, 60*60*24)
        return plans

    def get_success_url(self):
        return reverse('spreedly_email_sent', args=[self.request.user_id])

    def get(self):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        self.object_list = self.get_queryset()
        allow_empty = self.get_allow_empty()
        if not allow_empty and len(self.object_list) == 0:
            raise Http404(_(u"Empty list and '%(class_name)s.allow_empty' is False.")
                          % {'class_name': self.__class__.__name__})
        context = self.get_context_data(object_list=self.object_list)
        context['form'] = form
        return self.render_to_response(context)

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


def plan_list(request, extra_context=None, **kwargs):
    sub = None
    if request.user.is_authenticated():
        try:
            sub = Subscription.objects.get(user=request.user)
        except Subscription.DoesNotExist:
            pass
    
    # cache the subscription list from spreedly for a day
    cache_key = 'spreedly_plans_list'
    plans = cache.get(cache_key)
    if not plans:
        sync_plans()
        plans = list(Plan.objects.enabled())
        cache.set(cache_key, plans, 60*60*24)
    
    # deal with the form
    form = SubscribeForm(request.POST or None)
    if form.is_valid():
        redirect_url = form.save()
        return HttpResponseRedirect(redirect_url)
    
    our_context={
        'current_user_subscription': sub,
        'site': settings.SPREEDLY_SITE_NAME,
        'login': settings.LOGIN_URL,
        'plans': plans,
        'request': request,
        'form': form
    }
    if extra_context:
        our_context.update(extra_context)
    context = RequestContext(request)
    for key, value in our_context.items():
        context[key] = callable(value) and value() or value
    return render_to_response(
        spreedly_settings.SPREEDLY_LIST_TEMPLATE,
        kwargs,
        context_instance=context
    )


class AdminGift(FormView):
    form = AdminGiftForm
    template_name = 'spreedly_admin_gift.html'

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(AdminGift, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        user = form.save(request)

        subscriber = Subscription.objects.get_or_create(user,
                form.cleaned_data['plan'])  # No data -> get from client
        subscriber.create_complimentary_subscription(form.cleaned_data['time'],
                form.cleaned_data['units'], form.cleaned_data['feature_level'])
        user.gifts_received.latest('id').send_activation_email()
        return super(AdminGift, self).form_valid(form)


@staff_member_required
def admin_gift(request):
    if request.method == 'POST':
        form = AdminGiftForm(request.POST)
        if form.is_valid():
            user = form.save(request)
            
            client = Client(settings.SPREEDLY_AUTH_TOKEN, settings.SPREEDLY_SITE_NAME)
            client.create_subscriber(user.pk, user.email)
            client.create_complimentary_subscription(user.pk, form.cleaned_data['time'], form.cleaned_data['units'], form.cleaned_data['feature_level'])
            user.gifts_received.latest('id').send_activation_email()
            get_subscription(user)
    else:
        form = AdminGiftForm()
    
    
    return render_to_response(
        spreedly_settings.SPREEDLY_ADMIN_GIFT_TEMPLATE,
        {'form': form},
        context_instance=RequestContext(request),
    )


def gift_sign_up(request, gift_id, extra_context=None, **kwargs):
    try:
        gift = Gift.objects.get(uuid=gift_id)
    except Gift.DoesNotExist:
        raise Http404('Requested gift is not valid')
    
    if request.method == 'POST':
        form = GiftRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            signals.gift_accepted.send(sender=user)
            
            return HttpResponseRedirect('/')
    else:
        form = GiftRegisterForm(initial={
            'gift_key': gift_id
        })

    our_context = {
        'request': request,
        'form': form,
    }

    if extra_context:
        our_context.update(extra_context)
    context = RequestContext(request)
    for key, value in our_context.items():
        context[key] = callable(value) and value() or value
    return render_to_response(
        spreedly_settings.SPREEDLY_GIFT_REGISTER_TEMPLATE,
        kwargs,
        context_instance=context
    )


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

def spreedly_return(request, user_id, plan_pk=None, extra_context=None, **kwargs):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise Http404
    
    if plan_pk:
        plan = Plan.objects.get(pk=plan_pk)
        
        if plan.plan_type == 'gift':
            Gift.objects.get(to_user=user_id).send_activation_email()
        
        if request.GET.has_key('trial'):
            start_free_trial(plan, user)
        
    subscription = get_subscription(user)
    
    our_context = {
        'subscription': subscription,
        'request': request,
        'login_url': settings.LOGIN_URL
    }
    if extra_context:
        our_context.update(extra_context)
    context = RequestContext(request)
    for key, value in our_context.items():
        context[key] = callable(value) and value() or value
    return render_to_response(
        spreedly_settings.SPREEDLY_RETURN_TEMPLATE,
        kwargs,
        context_instance=context
    )

@login_required
def my_subscription(request):
    return spreedly_return(request, request.user.id)


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
