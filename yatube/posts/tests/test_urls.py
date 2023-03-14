from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HamidMusic')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        Post.objects.create(
            text='Тестовый текст',
            author=self.user,
        )

    def test_home_url_exists_at_desired_location(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_profile_url_exists_at_desired_location(self):
        response = self.guest_client.get('/profile/HamidMusic/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_detail_url_exists_at_desired_location(self):
        response = self.guest_client.get('/posts/1/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_url_exists_at_desired_location(self):
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_exists_at_desired_location_authorized(self):
        response = self.authorized_client.get('/posts/1/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_url_redirect_anonymous_on_admin_login(self):
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/')

    def test_post_edit_url_redirect_anonymous_on_admin_login(self):
        response = self.guest_client.get('/posts/1/edit/', follow=True)
        self.assertRedirects(
            response, ('/auth/login/?next=/posts/1/edit/'))

    def test_wrong_url_returns_404(self):
        response = self.client.get('something/really/weird/')
        self.assertEqual(response.status_code, 404)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            'posts/index.html': '/',
            'posts/profile.html': '/profile/HamidMusic/',
            'posts/post_detail.html': '/posts/1/',
            'posts/post_create.html': '/posts/1/edit/',
        }
        for template, url in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)


class GroupURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Описание',
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HamidMusic')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_group_posts_url_exists_at_desired_location(self):
        response = self.guest_client.get('/group/test-slug/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            'posts/group_list.html': '/group/test-slug/'
        }
        for template, url in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
