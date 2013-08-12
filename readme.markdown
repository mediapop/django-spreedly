[![Build Status](https://travis-ci.org/mediapop/django-spreedly.png)](https://travis-ci.org/mediapop/django-spreedly.png)

Info
====

This app can be used to add support for the [spreedly](https://spreedly.com/) subscription service to your django app.

**Note** this app is still in development, if you find issues or bugs, please submit them here:

Please report all issues to our git hub [issue tracker](https://github.com/mediapop/django-spreedly/issues)

The app currently covers:

* syncing subscriptions with your spreedly account.
* listing available subscriptions on your site.
* letting a user choose and signup for a subscription from your site.
* letting spreedly checkin and relay currently user subscription info.
* disabling part of your site for non-subscribed users (optional)
* redirecting users to the subscription page when their subscription expires.

Requirements
============

This code is currently only tested on django trunk, but should work without issue on 1.1

* python 2.5 
* [pyspreedly](http://github.com/mediapop/python-spreedly) >=2.0 
* LOGIN_URL variable in your settings file

Documentation
=============

Documentation is on [readthedocs.org](https://django-spreedly.readthedocs.org/en/latest/)
