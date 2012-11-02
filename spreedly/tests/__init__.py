import unittest
from unit_tests import TestSubscription
def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestSubscription))
    return suite
