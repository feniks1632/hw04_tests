from http import HTTPStatus

from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HamidMusic')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Описание',
        )
        Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        super().setUp()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_urls_exists_at_desired_locations_for_guest_client(self):
        urls = [
            '/',
            '/profile/HamidMusic/',
            '/posts/1/',
            '/group/test-slug/'
        ]
        for url in urls:
            response = self.guest_client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_exists_at_desired_locations_for_authorized_client(self):
        urls = [
            '/create/',
            '/posts/1/edit/',
        ]
        for url in urls:
            response = self.authorized_client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_redirect_anonymous_on_login(self):
        urls = [
            '/create/',
            '/posts/1/edit/',
        ]
        for url in urls:
            response = self.guest_client.get(url, follow=True)
            self.assertRedirects(response, '/auth/login/?next=' + url)

    def test_wrong_url_returns_404(self):
        response = self.client.get('something/really/weird/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            '/': 'posts/index.html',
            '/profile/HamidMusic/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/posts/1/edit/': 'posts/post_create.html',
            '/create/': 'posts/post_create.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/something/really/weird/': 'core/404.html'
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
