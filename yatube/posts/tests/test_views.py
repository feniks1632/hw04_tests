from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post, Group

TEST_OF_POST: int = 13
User = get_user_model()


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HamidMusic')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(title='Тестовая группа',
                                          slug='test_slug',
                                          description='Тестовое описание'
                                          )
        ar_post: list = []
        for i in range(TEST_OF_POST):
            ar_post.append(Post(text=f'Тестовый текст {i}',
                                group=self.group,
                                author=self.user))
        Post.objects.bulk_create(ar_post)

    def test_correct_page_context_guest_client(self):
        pages: tuple = (reverse('posts:index'),
                        reverse('posts:profile',
                                kwargs={'username': 'HamidMusic'}),
                        reverse('posts:group_list',
                                kwargs={'slug': 'test_slug'}))
        for page in pages:
            response1 = self.guest_client.get(page)
            response2 = self.guest_client.get(page + '?page=2')
            count_posts1 = len(response1.context['page_obj'])
            count_posts2 = len(response2.context['page_obj'])
            self.assertEqual(count_posts1,
                             settings.OBJECTS_PER_PAGE,
                             )
            self.assertEqual(count_posts2,
                             TEST_OF_POST - settings.OBJECTS_PER_PAGE,
                             )

    def test_correct_page_context_authorized_client(self):
        pages = [reverse('posts:index'),
                 reverse('posts:profile',
                         kwargs={'username': 'HamidMusic'}),
                 reverse('posts:group_list',
                         kwargs={'slug': self.group.slug})]
        for page in pages:
            response1 = self.authorized_client.get(page)
            response2 = self.authorized_client.get(page + '?page=2')
            count_posts1 = len(response1.context['page_obj'])
            count_posts2 = len(response2.context['page_obj'])
            self.assertEqual(count_posts1,
                             settings.OBJECTS_PER_PAGE,
                             )
            self.assertEqual(count_posts2,
                             TEST_OF_POST - settings.OBJECTS_PER_PAGE,
                             )


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HamidMusic')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(title='Тестовая группа',
                                          slug='test_slug',
                                          description='Тестовое описание'
                                          )
        self.post = Post.objects.create(
            text='Тестовый текст',
            author=self.user,
            group=self.group,
        )

    def test_pages_uses_correct_template(self):
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
            'posts/group_list.html',

            reverse('posts:profile', kwargs={'username': 'HamidMusic'}):
            'posts/profile.html',

            reverse('posts:post_detail', kwargs={'post_id': 1}):
            'posts/post_detail.html',

            reverse('posts:post_create'):
            'posts/post_create.html',

            reverse('posts:post_edit', kwargs={'post_id': 1}):
            'posts/post_create.html'
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
# Первый вариант - тест для каждой страницы

    def test_post_asserts(self, post: Post = None):
        if not post:
            post = self.post
        tests = [
            (post.text, 'Тестовый текст'),
            (post.author, self.user),
            (post.group, self.group),
        ]
        for value, expected in tests:
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_home_page_show_correct_context(self):
        response = self.guest_client.get(reverse('posts:index'))
        post = response.context['page_obj'][0]
        self.test_post_asserts(post=post)

    def test_post_group_page_show_correct_context(self):
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        post = response.context['page_obj'][0]
        self.test_post_asserts(post=post)

    def test_profile_page_show_correct_context(self):
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': self.user}))
        post = response.context['page_obj'][0]
        self.test_post_asserts(post=post)

    def test_post_create_show_correct_context(self):
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField
        }
        response = self.authorized_client.get(reverse('posts:post_create'))
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField
        }
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': 1}))
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

# Второй вариант - тест для всех однотипных страниц (DRY)
    def test_posts_pages_show_correct_context(self):
        urls = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user})
        ]
        for url in urls:
            response = self.guest_client.get(url)
            post = response.context['page_obj'][0]

            self.assertEqual(post.text, 'Тестовый текст')
            self.assertEqual(post.author, self.user)
            self.assertEqual(post.group, self.group)

    def test_post_create_edit_show_correct_context(self):
        urls = [
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': 1})
        ]
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField
        }
        for url in urls:
            response = self.authorized_client.get(url)
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context['form'].fields[value]
                    self.assertIsInstance(form_field, expected)
