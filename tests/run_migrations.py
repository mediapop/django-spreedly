#!/usr/bin/env python
import os
import sys

from argparse import ArgumentParser
from path import path

from django.conf import settings
from django.core.management import call_command

from site_conf import DICT_CONF

def conf():
    settings.configure(**DICT_CONF)

def syncdb():
    call_command("syncdb")

def migrate():
    call_command("schemamigration","spreedly",auto=True)


if __name__ == "__main__":
    conf()
    syncdb()
    migrate()
