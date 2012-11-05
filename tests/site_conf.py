from path import path
from  secret_conf import SPREEDLY_AUTH_TOKEN, SPREEDLY_SITE_NAME

DICT_CONF ={
        "DATABASES"         : {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME' : ':memory:',
                }
            },
        "ROOT_URLCONF"      : "tests.urls",
        "TEMPLATE_LOADERS"  : (
                        "django.template.loaders.filesystem.Loader",
                        "django.template.loaders.app_directories.Loader",
                        "django.template.loaders.eggs.Loader",
            ),
        "TEMPLATE_DIRS"     : (
            path(__file__).dirname() / 'templates',
            ),
        "INSTALLED_APPS"    : (
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.sites',
            'south',
            'pyspreedly',
            'spreedly',
            ),
        "SPREEDLY_AUTH_TOKEN" : SPREEDLY_AUTH_TOKEN,
        "SPREEDLY_SITE_NAME"  : SPREEDLY_SITE_NAME,
        "SITE_ID" : 1,
        }
