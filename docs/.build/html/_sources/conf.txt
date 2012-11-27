Configuration
=============

Dependencies
------------

::
    pyspreedly>=2.0

Settings
--------

1) In your settings file, add spreedly to `INSTALLED_APPS`::

    INSTALLED_APPS = (
        ...
        'spreedly',
        ...
        )

2) Add your auth token and site name as well::

    SPREEDLY_AUTH_TOKEN = 'super-secret-token'
    SPREEDLY_SITE_NAME = 'site-name'

3) The following are in the process of being reviewed for being removal.  They can also be added, they are optiona::

	# this string will be used as the url for returning users from spreedly.
	# this defaults to '/thanks/'
	SPREEDLY_RETURN_URL = '/welcome/'

	# the base subscription url (where users will be redirected when their subscriptions expire)
	# this defaults to '/subscriptions/' if you don't add a value to your settings.
	SPREEDLY_URL ='/register/'

	# if you want to restrict access to your entire site based to only users with an active subscription
	# this defaults to False
	SPREEDLY_USERS_ONLY = True
	
	# URL paths that a user without a subscription can vist without being redirected to the subscription list:
	# these can be single pages ('/some/page/') of full directories ('/directory')
	SPREEDLY_ALLOWED_PATHS = ['/login', '/logout']

	# This template will be used when checking to make sure the user is using a valid email
	# this default to 'confirm_email.txt' Be sure to include {{ spreedly_url }} in your template
	SPREEDLY_CONFIRM_EMAIL = 'path/to/your/template.txt'

	# This subject will be used for confirmation emails
	# this defaults to "'complete your subscription to %s' % Site.object.get(id=settings.SITE_ID).name"
	SPREEDLY_CONFIRM_EMAIL_SUBJECT = 'This is a new subject'

	# Where a user is directed after signing up.
	# this defaults to 'email_sent.html'
	SPREEDLY_EMAIL_SENT_TEMPLATE = 'path/to/your/template.html'

	# this is the email that will be sent to the user recieving the gift subscription
	# this default to 'gift_email.txt' Be sure to include {{ spreedly_url }} in your template
	SPREEDLY_GIFT_EMAIL = 'path/to/your/template.txt'

	# the subject for the gift confirm email
	# this defaults to 'gift subscription to %s' % Site.objects.get(id=settings.SITE_ID).name
	SPREEDLY_GIFT_EMAIL_SUBJECT = 'This is a new subject'

	# the base url for your site to be used when returning users from spreedly.
	# this default to Site.objects.get(id=settings.SITE_ID) from the django Site app.
	SPREEDLY_SITE_URL = 'something.com'

4) Add the middleware to your `settings.py` MIDDLEWARE_CLASSES.  This will be turned into a decorator in a later version::

	'spreedly.middleware.SpreedlyMiddleware'

5) Add the following to urlpatterns in `urls.py`::

	import spreedly.settings as spreedly_settings
	(r'^spreedly', include('spreedly.urls')),


Syncdb
------

spreedly uses :py:module:`South` to manage database migrations.  So after
running `syncdb`, you must run `manage.py migrate spreedly`.
