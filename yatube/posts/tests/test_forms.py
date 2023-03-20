from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post, Group

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='HamidMusic')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )

    def setUp(self):
        super().setUp()

    def test_create_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'author': self.user,
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                author=form_data['author'],
                group=form_data['group']
            ).exists()
        )

    def test_edit_post(self):
        self.post = Post.objects.create(
            text='Тестовый текст',
            author=self.user,
            group=self.group
        )
        old_text = self.post
        self.group2 = Group.objects.create(
            title='Тестовая группа2',
            slug='test-group',
            description='Описание'
        )
        form_data = {
            'text': 'Текст записанный в форму',
            'group': self.group2.id
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': old_text.id}
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(Post.objects.filter(
            group=self.group2.id,
            author=self.user,
            pub_date=self.post.pub_date
        ).exists()
        )
        self.assertNotEqual(old_text.text, form_data['text'])
        self.assertNotEqual(
            old_text.group,
            form_data['group'],
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': old_text.id})
        )

        
