Use
===

After the app is installed, you can start creating subscriptions!

The app is designed to work with the following flow:

* new user enters user information and chooses a plan
* inactive user object is created and the user is sent an email with a link to spreedly to pay for plan
* after successful payment, user is directed back to your site
* the app will check with spreedly for users status
* if the user has an active subscription, the user object will be set to active and the user will be given a login url

If you want to make your site subscription only you can set the SPREEDLY_USERS_ONLY to True.
This will redirect any anonymous user (or user with an inactive subscription) who visits a page not in the SPREEDLY_ALLOWED_PATHS list to your SPREEDLY_URL

Some Important Notes
--------------------

Spreedly is sent a redirect url that will check and see if the user has signed up and activate their account. **A user may not click on this link** and in that case their account won't be active, unless:

Spreedly will ping a url with subscriptions change, and django-spreedly is setup to listen for this.

in your spreedly setting is the following: 'Subscribers Changed Notification URL'

if you changed SPREEDLY_URL, you'll need to substitute that for subscriptions.

If you want to add a fallback, you can also add the following to your login view after a user is logged in (but before you check if they are active):

	from spreedly.functions import get_subscription
	
	if not user.is_active:
		get_subscription(user)

