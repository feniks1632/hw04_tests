from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

TEST_POST_AMMOUNT: int = 13
User = get_user_model()


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='HamidMusic')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        arr_post: list = []
        for i in range(TEST_POST_AMMOUNT):
            arr_post.append(
                Post(
                    text=f'Тестовый текст № {i}',
                    group=cls.group,
                    author=cls.user,
                )
            )
        Post.objects.bulk_create(arr_post)

    def setUp(self):
        super().setUp()
        self.guest_client = Client() 

    def test_paginator(self):
        pages = (
            reverse('posts:index'),
            reverse('posts:profile', kwargs={'username': 'HamidMusic'}),
            reverse('posts:group_list', kwargs={'slug': 'test_slug'})
        )
        for page in pages:
            response1 = self.guest_client.get(page)
            response2 = self.guest_client.get(page + '?page=2')
            self.assertEqual(
                len(response1.context.get('page_obj')),
                settings.OBJECTS_PER_PAGE,
            )
            self.assertEqual(
                len(response2.context.get('page_obj')),
                TEST_POST_AMMOUNT - settings.OBJECTS_PER_PAGE,
            )


class PostViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='HamidMusic')
        cls.second_user = User.objects.create(username='AnotherHamid')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.another_group = Group.objects.create(
            title='Ещё одна тестовая группа',
            slug='another_test_slug',
            description='Ещё одно тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Какой-то тестовый текст для теста',
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        super().setUp()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        pages_names_templates = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}):
                'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}):
                'posts/post_create.html',
            reverse('posts:post_create'): 'posts/post_create.html',
        }
        for reverse_name, template in pages_names_templates.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_asserts(self, post=None):
        if not post:
            post = self.post
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group, self.post.group)

    def test_index_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:index'))
        post = response.context.get('page_obj')[0]
        self.test_post_asserts(post)

    def test_group_list_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        post = response.context.get('page_obj')[0]
        group = response.context.get('group')
        self.test_post_asserts(post)
        self.assertEqual(group, self.group)

    def test_profile_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user})
        )
        post = response.context.get('page_obj')[0]
        count = response.context.get('count')
        author = response.context.get('author')
        self.test_post_asserts(post)
        self.assertEqual(count, len(response.context.get('page_obj')))
        self.assertEqual(author, self.user)

    def test_post_detail_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        post = response.context.get('post')
        count = response.context.get('count')
        self.assertEqual(post, self.post)
        self.assertEqual(count, 1)

    def test_post_create_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        post = response.context.get('post')
        self.assertEqual(post, self.post)
        self.assertTrue(response.context.get('is_edit'))

    def test_check_group_in_pages(self):
        form_fields = {
            reverse('posts:index'):
            Post.objects.get(group=self.post.group),
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ):
            Post.objects.get(group=self.post.group),
            reverse(
                'posts:profile', kwargs={'username': self.post.author}
            ): Post.objects.get(group=self.post.group),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context.get('page_obj')
                self.assertIn(expected, form_field)

    def test_no_test_in_another_group(self):
        form_fields = {
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ):
            Post.objects.exclude(group=self.post.group),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context.get('page_obj')
                self.assertNotIn(expected, form_field)
