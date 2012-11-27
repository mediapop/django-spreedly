Configuration
=============

Dependencies
------------

::
    pyspreedly>=2.0

Settings
--------

In your settings file, add spreedly to `INSTALLED_APPS`::

    INSTALLED_APPS = (
        ...
        'spreedly',
        ...
        )

Add your auth token and site name as well::

    SPREEDLY_AUTH_TOKEN = 'super-secret-token'
    SPREEDLY_SITE_NAME = 'site-name'


Syncdb
------

spreedly uses :py:module:`South` to manage database migrations.  So after
running `syncdb`, you must run `manage.py migrate spreedly`.
