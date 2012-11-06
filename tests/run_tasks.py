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

def run_tests():
    """
    Setup the environment to run the tests as stand alone
    uses sqlite3 in memory db
    """
    argument_parser = ArgumentParser(description="Run all tests for django-spreedly")
    #TODO add some configuration here

    settings.configure(**DICT_CONF)
    call_command("test", 'spreedly')

def syncdb():
    call_command("syncdb")

def schema_migrate(auto=True, empty=False, update=False):
    call_command("schemamigration","spreedly",auto=auto,empty=empty,update=update)


if __name__ == "__main__":
    sys.path.append(path(__file__).abspath().dirname().dirname())
    parser = ArgumentParser(description="run tasks for django-spreedly")
    parser.add_argument('--test', action='store_true', default=False,
            help="Run the test for django-spreedly")
    parser.add_argument('--datamigration', action='store_true',
            help="run datamigration")
    schemamigration = parser.add_argument_group('migrate')
    schemamigration.add_argument('--schemamigration', action='store_true', 
            default=False, help="preform a schema migration")
    schema_migrate_opts = schemamigration.add_mutually_exclusive_group(required=False)
    schema_migrate_opts.add_argument('--auto',action='store_true')
    schema_migrate_opts.add_argument('--empty',action='store_true')
    schema_migrate_opts.add_argument('--update',action='store_true')
    args = parser.parse_args()
    if args.test:
        run_tests()
    if args.schemamigration:
        conf()
        syncdb()
        schema_migrate(auto=args.auto,empty=args.empty,update=args.update)
