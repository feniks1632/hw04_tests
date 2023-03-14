from http import HTTPStatus

from django.test import TestCase, Client


class AboutUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super(). setUpClass()

    def setUp(self):
        self.guest_client = Client()

    def test_about_url_exists_at_desired_location(self):
        response = self.guest_client.get('/about/author/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_tech_url_exists_at_desired_location(self):
        response = self.guest_client.get('/about/tech/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
