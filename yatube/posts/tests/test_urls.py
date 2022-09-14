from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group
        )

    def setUp(self):
        """Создание клиента гостя, авторизованного пользователя
        и автора поста.
        """
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post_author = Client()
        self.post_author.force_login(self.author)

    def test_guest_have_access_to_public_pages_url(self):
        """Проверка статуса страниц для неавторизованного пользователя."""
        pages_url_status = {
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.author}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/': HTTPStatus.OK,
            '/create/': HTTPStatus.FOUND,
            f'/posts/{self.post.id}/edit/': HTTPStatus.FOUND,
            f'/posts/{self.post.id}/comment/': HTTPStatus.FOUND,
            '/follow/': HTTPStatus.FOUND,
            f'/profile/{self.user}/follow/': HTTPStatus.FOUND,
            f'/profile/{self.user}/unfollow/': HTTPStatus.FOUND
        }
        for url, expected in pages_url_status.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, expected)

    def test_guest_redirects_correct(self):
        """Проверка редиректов неавторизованного пользователя."""
        pages_url_redirect = {
            '/create/': reverse(
                'users:login') + '?next=/create/',
            f'/posts/{self.post.id}/edit/': reverse(
                'users:login') + f'?next=/posts/{self.post.id}/edit/',
            f'/posts/{self.post.id}/comment/': reverse(
                'users:login') + f'?next=/posts/{self.post.id}/comment/',
            '/follow/': reverse(
                'users:login') + '?next=/follow/',
            f'/profile/{self.user}/follow/': reverse(
                'users:login') + f'?next=/profile/{self.user}/follow/',
            f'/profile/{self.user}/unfollow/': reverse(
                'users:login') + f'?next=/profile/{self.user}/unfollow/'
        }
        for url, redirect_url in pages_url_redirect.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, redirect_url)

    def test_authorized_have_access_to_closed_pages_url(self):
        """"Проверка статуса страниц для авторизованного пользователя,
        автора поста.
        """
        pages_url_status = {
            '/create/': HTTPStatus.OK,
            f'/posts/{self.post.id}/edit/': HTTPStatus.OK,
            '/follow/': HTTPStatus.OK,
            f'/profile/{self.user}/follow/': HTTPStatus.FOUND,
            f'/profile/{self.user}/unfollow/': HTTPStatus.FOUND,
            f'/posts/{self.post.id}/comment/': HTTPStatus.FOUND,

        }
        for url, expected in pages_url_status.items():
            with self.subTest(url=url):
                response = self.post_author.get(url)
                self.assertEqual(response.status_code, expected)

    def test_edit_page_url_not_available_authorized_not_author(self):
        """Страница редактирования недоступна не-автору поста."""
        post_edit_page = f'/posts/{self.post.id}/edit/'
        response = self.authorized_client.get(post_edit_page)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_authorized_redirects_correct(self):
        """Проверка редиректов авторизованного пользователя,
        не-автора поста.
        """
        pages_url_redirect = {
            f'/posts/{self.post.id}/edit/': f'/posts/{self.post.id}/',
            f'/posts/{self.post.id}/comment/': f'/posts/{self.post.id}/',
            f'/profile/{self.user}/follow/': f'/profile/{self.user}/',
            f'/profile/{self.user}/unfollow/': f'/profile/{self.user}/'
        }
        for url, redirect_url in pages_url_redirect.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertRedirects(response, redirect_url)

    def test_urls_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.author}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html',
            '/unexisting_page/': 'core/404.html'
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.post_author.get(url)
                self.assertTemplateUsed(response, template)
