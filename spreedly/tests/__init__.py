import unittest
from unit_tests import TestSyncPlans, TestPlan, TestSubscriptions
def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestSyncPlans))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestPlan))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestSubscriptions))
    return suite
