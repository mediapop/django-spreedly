import unittest
from unit_tests import TestSyncPlans, TestPlan, TestSubscriptions
from test_views import TestViewsExist
def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestSyncPlans))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestPlan))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestSubscriptions))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestViewsExist))
    return suite
