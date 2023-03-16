from http import HTTPStatus

from django.test import TestCase, Client


class AboutUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super(). setUpClass()

    def setUp(self):
        self.guest_client = Client()

    def test_url_exists_at_desired_location(self):
        urls = ['/about/author/', '/about/tech/']
        for url in urls:
            response = self.guest_client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)
