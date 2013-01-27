from path import path
from xml.etree import ElementTree as ET

rd = path(__file__).abspath().dirname()

class SpreedlySubscriptionXML(object):
    def __init__(self, subscriptions='fixtures/test_subscription.xml',
                       plans='fixtures/test_plans.xml'):
        with open(rd / subscriptions, 'r') as mock_subscription_fd:
            self._subscription_xml = ET.parse(mock_subscription_fd)
        with open(rd / plans, 'r') as mock_plan_fd:
            self._plan_xml = ET.parse(mock_plan_fd)
        root = self._subscription_xml.find('.')
        subscription_name = root.find('./subscription-plan-name')
        subscription_version = root.find('./subscription-plan-version')
        root.remove(subscription_name)
        root.remove(subscription_version)

    def _update_plan_xml(self, version_no, subscriber_root, plan):
        """factor out the update code for updating the plan name and no"""
        for version in plan.findall('./versions/version'):
            if int(version.find('version').text) == version_no:
                subscription_plan_version = ET.Element(
                        'subscription-plan-version')
                subscription_plan_version.extend(version.findall('.//'))
                subscription_plan_name = ET.Element(
                        'subscription-plan-name')
                subscription_plan_name.text = plan.find('name').text
                subscriber_root.append(subscription_plan_name)
                subscriber_root.append(subscription_plan_version)
                return
        raise KeyError('version_no: {0} not found'.format(version_no))
