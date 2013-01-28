from path import path
from xml.etree import ElementTree as ET
import copy
from StringIO import StringIO

rd = path(__file__).abspath().dirname()

class SpreedlySubscriptionXML(object):
    """Generate singular xml responses for various spreedly api actions"""
    def __init__(self, subscriptions='fixtures/test_subscription.xml',
                       plans='fixtures/test_plans.xml',
                       create_user='fixtures/create_user.xml',
                       free_trial_response='fixtures/free_trial_response.xml',
                       trial_subscription_info='fixtures/free_trial_subscription_info.xml'):
        with open(rd / subscriptions, 'r') as mock_subscription_fd:
            self._subscription_xml = ET.parse(mock_subscription_fd)
        with open(rd / plans, 'r') as mock_plan_fd:
            self._plan_xml = ET.parse(mock_plan_fd)
        with open(rd / free_trial_response, 'r') as mock_free_trial_fd:
            self._free_trial_response = ET.parse(mock_free_trial_fd)
        with open(rd / create_user, 'r') as mock_create_user_fd:
            self._create_user = ET.parse(mock_create_user_fd)
        with open(rd / trial_subscription_info, 'r') as mock_trial_subscription_info_fd:
            self._trial_subscription_info = ET.parse(mock_trial_subscription_info_fd)
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

    def create_user(self, user_id=None):
        """ py:method: SpreedlySubscriptionXML.create_user(user_id=None)
        takes the create_user xml response and updates the user_id to the
        supplied ID.  No plan is associated and it is not an activated account
        if no `user_id` is supplied, then it will not be changed from that in
        the xml.

        :param user_id: id of the user the subscription will be using
        :return: XML for a subscription
        """
        create_user_xml = copy.deepcopy(self._create_user)
        create_user_root = create_user_xml.find('.')
        if user_id:
            self._update_user_id(create_user_root, user_id)
        xml_io = StringIO()
        create_user_xml.write(xml_io)
        xml_io.seek(0)
        return xml_io.read()

    def free_trial_response(self, plan_id, user_id=None):
        """ py:method: SpreedlySubscriptionXML.free_trial_response(plan_id, user_id=None)
        takes the free_trial_response xml response and updates the user_id and
        the plan_id to the supplied IDs.
        if no `user_id` is supplied, then it will not be changed from that in
        the xml.

        :param plan_id: id of the plan the subscription will be using
        :param user_id: id of the user the subscription will be using
        :return: XML for a subscription with `plan`
        """
        plan_xml = copy.deepcopy(self._plan_xml)
        response_xml= copy.deepcopy(self._free_trial_response)
        response_root = response_xml.find('.')
        plans = plan_xml.findall('./subscription-plan')
        for plan in plans:
            if plan.find('./id').text == str(plan_id):
                version_no = int(plan.find('version').text)
                self._update_plan_xml(
                        version_no,
                        response_root,
                        plan)
                if user_id:
                    self._update_user_id(response_root, user_id)
                xml_io = StringIO()
                response_xml.write(xml_io)
                xml_io.seek(0)
                return xml_io.read()
        # Well now, if you are here, that didn't work.
        raise KeyError('plan id: {0} not found'.format(plan_id))

    def trial_subscription_info(self, plan_id, user_id=None):
        """ py:method: SpreedlySubscriptionXML.trial_subscription_info(plan_id, user_id=None)
        takes the free_trial_response xml response and updates the user_id and
        the plan_id to the supplied IDs.
        if no `user_id` is supplied, then it will not be changed from that in
        the xml.

        :param plan_id: id of the plan the subscription will be using
        :param user_id: id of the user the subscription will be using
        :return: XML for a subscription with `plan`
        """
        plan_xml = copy.deepcopy(self._plan_xml)
        response_xml= copy.deepcopy(self._trial_subscription_info)
        response_root = response_xml.find('.')
        plans = plan_xml.findall('./subscription-plan')
        for plan in plans:
            if plan.find('./id').text == str(plan_id):
                version_no = int(plan.find('version').text)
                self._update_plan_xml(
                        version_no,
                        response_root,
                        plan)
                if user_id:
                    self._update_user_id(response_root, user_id)
                xml_io = StringIO()
                response_xml.write(xml_io)
                xml_io.seek(0)
                return xml_io.read()
        # Well now, if you are here, that didn't work.
        raise KeyError('plan id: {0} not found'.format(plan_id))

    def subscription_xml(self, plan_id, user_id=None):
        """ py:method: SpreedlySubscriptionXML.subscription_xml(plan_id, user_id=None)
        Takes a subscription xml and changes the plan to that with id
        `plan`.

        :param plan_id: id of the plan the subscription will be using
        :param user_id: id of the user the subscription will be using
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
