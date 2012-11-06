import unittest
from unit_tests import TestSubscription, TestPlan
def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestSubscription))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestPlan))
    return suite
