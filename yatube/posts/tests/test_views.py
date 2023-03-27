import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Follow, Group, Post


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
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
            reverse('posts:profile', kwargs={'username': self.user}),
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
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


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
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
        cls.small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif', content=cls.small_gif, content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

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
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def assert_post(self, post):
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group, self.post.group)

    def test_index_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:index'))
        post = response.context.get('page_obj')[0]
        self.assert_post(post)

    def test_group_list_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        post = response.context.get('page_obj')[0]
        group = response.context.get('group')
        self.assert_post(post)
        self.assertEqual(group, self.group)

    def test_profile_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user})
        )
        post = response.context.get('page_obj')[0]
        count = response.context.get('count')
        author = response.context.get('author')
        self.assert_post(post)
        self.assertEqual(count, len(response.context.get('page_obj')))
        self.assertEqual(author, self.user)

    def test_post_detail_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        post = response.context.get('post')
        count = response.context.get('count')
        self.assert_post(post)
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

    def test_no_post_in_another_group(self):
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

    def test_image_in_pages(self):
        templates = (
            reverse('posts:index'),
            reverse('posts:profile', kwargs={'username': self.post.author}),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
        )
        for url in templates:
            with self.subTest(url):
                response = self.guest_client.get(url)
                post = response.context.get('page_obj')[0]
                self.assertEqual(post.image, self.post.image)

    def test_image_in_post_detail_page(self):
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        post = response.context.get('post')
        self.assertEqual(post.image, self.post.image)

    def test_comment_correct_context(self):
        comments_count = Comment.objects.count()
        form_data = {'text': 'Тестовый комментарий'}
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(text=form_data.get('text')).exists()
        )

    def test_check_cache(self):
        response = self.guest_client.get(reverse('posts:index'))
        response_1 = response.content
        Post.objects.get(pk=1).delete()
        response2 = self.guest_client.get(reverse('posts:index'))
        response_2 = response2.content
        self.assertEqual(response_1, response_2)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='HamidMusic')
        cls.author_1 = User.objects.create(username='HamidCompositor')
        cls.author_2 = User.objects.create(username='HamidScenario')
        cls.group_1 = Group.objects.create(
            title='Тестовая группа композиторов',
            slug='test_slug',
            description='Сюда композиторы пишут свои статьи'
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа сценаристов',
            slug='test_slug_2',
            description='Сюда сценаристы пишут свои статьи'
        )
        cls.post_1 = Post.objects.create(
            text='Тестовый пост автора HamidCompositor',
            author=cls.author_1,
            group=cls.group_1
        )
        cls.post_2 = Post.objects.create(
            text='Тестовый пост автора HamidScenario',
            author=cls.author_2,
            group=cls.group_2
        )

    def setUp(self):
        super().setUp()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_user_follow_unfollow_author(self):
        response = self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.author_1})
        )
        self.assertTrue(
            Follow.objects.filter(user=self.user, author=self.author_1)
        )
        self.assertRedirects(response, reverse('posts:follow_index'))

        response = self.authorized_client.get(
            reverse(
                'posts:profile_unfollow', kwargs={'username': self.author_1}
            )
        )
        self.assertFalse(
            Follow.objects.filter(user=self.user, author=self.author_1)
        )
        self.assertRedirects(response, reverse('posts:follow_index'))

    def test_follower_show_correct_posts(self):
        # Проверка подписки на автора поста
        Follow.objects.get_or_create(user=self.user, author=self.author_1)
        response = self.authorized_client.get(reverse('posts:follow_index'))

        self.assertIn(self.post_1, response.context.get('page_obj'))

        self.authorized_client.force_login(self.author_2)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotIn(self.post_1, response.context.get('page_obj'))
