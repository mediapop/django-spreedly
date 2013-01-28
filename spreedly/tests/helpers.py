from path import path
from xml.etree import ElementTree as ET
import copy
from StringIO import StringIO

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

    def _update_user_id(self, subscriber_root, user_id):
        """Update the user_id to the supplied"""
        subscriber_root.find('./customer-id').text = str(user_id)

    def all_plans(self):
        xml_io = StringIO()
        self.root.write(xml_io)
        xml_io.seek(0)
        xml = xml_io.read()
        return xml

    def subscription_xml(self, plan_id, user_id=None):
        """ py:method: SpreedlySubscriptionXML.subscription_xml(plan_id)
        Takes a subscription xml and changes the plan to that with id
        `plan`.

        :param subscription: XML as returned by Spreedly
        :param plan_id: id of the plan the subscription will be using
        :return: XML for a subscription with `plan`
        """
        plan_xml = copy.deepcopy(self._plan_xml)
        subscription_xml = copy.deepcopy(self._subscription_xml)
        subscriber_root = subscription_xml.find('.')

        plans = plan_xml.findall('./subscription-plan')
        for plan in plans:
            if plan.find('./id').text == str(plan_id):
                version_no = int(plan.find('version').text)
                self._update_plan_xml(
                        version_no,
                        subscriber_root,
                        plan)
                if user_id:
                    self._update_user_id(subscriber_root, user_id)
                xml_io = StringIO()
                subscription_xml.write(xml_io)
                xml_io.seek(0)
                return xml_io.read()
        # Well now, if you are here, that didn't work.
        raise KeyError('plan id: {0} not found'.format(plan_id))
