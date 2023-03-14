from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.conf import settings
from django import forms

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
        Post.objects.create(
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

        def test_home_page_show_correct_context(self):
            response = self.guest_client.get(reverse('posts:index'))
            form_fields = {
                'text': forms.fields.CharField,
                'group': forms.fields.CharField,
            }

            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context['form'].fields[value]
                    self.assertIsInstance(form_field, expected)

        def test_post_list_page_list_is_1(self):
            response = self.authorized_client.get(reverse('post:post_list'))
            self.assertEqual(response.context['object_list'].count(), 1)

        def test_posts_list_page_show_correct_context(self):
            response = self.authorized_client.get(reverse('posts:posts_list'))
            first_object = response.context['page_obj'][0]
            post_text = first_object.text
            post_pub_date = first_object.pub_date
            post_author = first_object.author.get_full_name
            post_group = first_object.group
            self.assertEqual(post_text, 'Текстовый текст')
            self.assertEqual(post_pub_date, '1.01.1991')
            self.assertEqual(post_author, 'HamidMusic')
            self.assertEqual(post_group, 'Тестовая группа')

        def test_post_detail_pages_show_correct_context(self):
            response = self.authorized_client.get(
                reverse('posts:post_detail', kwargs={'id': 'post_id'})
            )
            self.assertEqual(response.context['post'].title, 'Тестовый текст')
            self.assertEqual(response.context['count'].text,
                             'Колличество постов')

        def test_initial_value(self):
            response = self.guest_client.get(reverse('posts:index'))
            title_inital = response.context['form'].fields['title'].initial
            self.assertEqual(title_inital, 'Значение по-умолчанию')
