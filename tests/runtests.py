#!/usr/bin/env python
import os
import sys

from argparse import ArgumentParser
from path import path

from django.conf import settings
from django.core.management import call_command

from site_conf import DICT_CONF

def run_tests():
    """
    Setup the environment to run the tests as stand alone
    uses sqlite3 in memory db
    """
    argument_parser = ArgumentParser(description="Run all tests for django-spreedly")
    #TODO add some configuration here

    settings.configure(**DICT_CONF)
    call_command("syncdb")
    call_command("test", 'spreedly')

if __name__ == "__main__":
    run_tests()
