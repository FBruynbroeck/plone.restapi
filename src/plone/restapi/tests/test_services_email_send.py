# -*- coding: utf-8 -*-
from Products.MailHost.interfaces import IMailHost

from plone.app.testing import setRoles
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_ID
from plone.restapi.testing import PLONE_RESTAPI_DX_FUNCTIONAL_TESTING
from plone.restapi.testing import RelativeSession
from zope.component import getUtility
from plone.registry.interfaces import IRegistry

import transaction
import unittest

try:
    from Products.CMFPlone.factory import _IMREALLYPLONE5  # noqa
except ImportError:
    PLONE5 = False
else:
    PLONE5 = True


@unittest.skipIf(not PLONE5, 'email send not implemented for Plone < 5.') # noqa
class EmailSendEndpoint(unittest.TestCase):

    layer = PLONE_RESTAPI_DX_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer['app']
        self.portal = self.layer['portal']
        self.portal_url = self.portal.absolute_url()
        setRoles(self.portal, TEST_USER_ID, ['Manager', ])

        self.mailhost = getUtility(IMailHost)

        registry = getUtility(IRegistry)
        registry['plone.email_from_address'] = 'info@plone.org'
        registry['plone.email_from_name'] = u'Plone test site'

        self.api_session = RelativeSession(self.portal_url)
        self.api_session.headers.update({'Accept': 'application/json'})
        self.api_session.auth = (SITE_OWNER_NAME, SITE_OWNER_PASSWORD)
        self.anon_api_session = RelativeSession(self.portal_url)
        self.anon_api_session.headers.update({'Accept': 'application/json'})

        transaction.commit()

    def test_email_send(self):
        response = self.api_session.post(
            '/@email-send',
            json={
                'to': 'jane@doe.com',
                'from': 'john@doe.com',
                'message': 'Just want to say hi.'
            })
        transaction.commit()

        self.assertEquals(response.status_code, 204)
        self.assertTrue('Subject: =?utf-8?q?A_portal_user_via_Plone_site?=' in
                        self.mailhost.messages[0])
        self.assertTrue('From: info@plone.org' in
                        self.mailhost.messages[0])
        self.assertTrue('Reply-To: john@doe.com' in
                        self.mailhost.messages[0])
        self.assertTrue('Just want to say hi.' in
                        self.mailhost.messages[0])

    def test_email_send_all_parameters(self):
        response = self.api_session.post(
            '/@email-send',
            json={
                'to': 'jane@doe.com',
                'from': 'john@doe.com',
                'message': 'Just want to say hi.',
                'name': 'John Doe',
                'subject': 'This is the subject.'
            })
        transaction.commit()

        self.assertEquals(response.status_code, 204)
        self.assertTrue('=?utf-8?q?This_is_the_subject' in
                        self.mailhost.messages[0])
        self.assertTrue('From: info@plone.org' in
                        self.mailhost.messages[0])
        self.assertTrue('John Doe' in
                        self.mailhost.messages[0])
        self.assertTrue('Reply-To: john@doe.com' in
                        self.mailhost.messages[0])
        self.assertTrue('Just want to say hi.' in
                        self.mailhost.messages[0])

    def test_email_send_anonymous(self):
        response = self.anon_api_session.post(
            '/@email-send',
            json={
                'to': 'jane@doe.com',
                'from': 'john@doe.com',
                'message': 'Just want to say hi.',
                'name': 'John Doe',
                'subject': 'This is the subject.'
            })

        self.assertEquals(response.status_code, 401)
