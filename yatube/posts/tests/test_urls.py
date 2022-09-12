from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Неавторизованный пользователь
        cls.guest_client = Client()
        # Авторизованный пользователь
        cls.user = User.objects.create_user(username='user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        # Автор поста
        cls.author = User.objects.create_user(username='author')
        cls.post_author = Client()
        cls.post_author.force_login(cls.author)
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

    # Тестирование общедоступных страниц
    def test_pages_url_exist_at_desired_location(self):
        """Страницы доступны всем пользователям."""
        pages_code = {
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.author}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND
        }
        for address, expected_value in pages_code.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, expected_value)

    # Тестирование страницы Новой записи для авторизованного пользователя
    def test_create_url_exists_at_desired_location(self):
        """Страница создания записи доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    # Тестирование комментирования записи для авторизованного пользователя
    def test_add_comment_exists_at_desired_location(self):
        """Комментирование записи доступно авторизованному пользователю."""
        add_comment_page = f'/posts/{self.post.id}/comment/'
        response = self.authorized_client.get(add_comment_page)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    # Тестирование подписки для авторизованного пользователя
    def test_follow_exists_at_desired_location(self):
        """Подписка доступна авторизованному пользователю."""
        follow_page = f'/profile/{self.user}/follow/'
        response = self.authorized_client.get(follow_page)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    # Тестирование отписки для авторизованного пользователя
    def test_unfollow_exists_at_desired_location(self):
        """Отписка доступна авторизованному пользователю."""
        unfollow_page = f'/profile/{self.user}/unfollow/'
        response = self.authorized_client.get(unfollow_page)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    # Тестирование страницы Редактирования поста для автора
    def test_post_edit_url_exists_at_desired_location(self):
        """Страница редактирования поста доступна автору."""
        post_edit_page = f'/posts/{self.post.id}/edit/'
        response = self.post_author.get(post_edit_page)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    # Проверка редиректа авторизованного пользователя при попытке захода
    # на страницу редактирования поста
    def test_post_edit_url_redirects_authorized_client_on_post_detail(self):
        """Страница редактирования поста перенаправит
        авторизованного пользователя на подробную информацию о посте,
        если тот не является его автором.
        """
        post_edit_page = f'/posts/{self.post.id}/edit/'
        post_detail_page = f'/posts/{self.post.id}/'
        response = self.authorized_client.get(post_edit_page, follow=True)
        self.assertRedirects(response, post_detail_page)

    # Проверка редиректа авторизованного пользователя
    # после отправки комментария на страницу информации о посте
    def test_add_comment_url_redirects_authorized_client_on_post_detail(self):
        """Успешная отправка комментария перенаправит
        авторизованного пользователя на подробную информацию о посте.
        """
        add_comment_page = f'/posts/{self.post.id}/comment/'
        post_detail_page = f'/posts/{self.post.id}/'
        response = self.authorized_client.get(add_comment_page, follow=True)
        self.assertRedirects(response, post_detail_page)

    # Проверка редиректа неавторизованного пользователя при попытке
    # создать новую запись
    def test_create_url_redirects_guest_client_on_login(self):
        """Страница создания поста перенаправит
        неавторизованного пользователя на страницу входа.
        """
        redirect_login_page = reverse('users:login') + '?next=/create/'
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, redirect_login_page)

    # Проверка редиректа неавторизованного пользователя при попытке
    # перехода на страницу редактирования поста
    def test_post_edit_url_redirects_guest_client_on_login(self):
        """Страница редактирования поста перенаправит
        неавторизованного пользователя на страницу входа.
        """
        post_edit_page = f'/posts/{self.post.id}/edit/'
        redirect_login_page = reverse(
            'users:login') + f'?next=/posts/{self.post.id}/edit/'
        response = self.guest_client.get(post_edit_page, follow=True)
        self.assertRedirects(response, redirect_login_page)

    # Проверка редиректа неавторизованного пользователя при попытке
    # перехода на страницу комментирования поста
    def test_add_comment_url_redirects_guest_client_on_login(self):
        """Страница комментирования поста перенаправит
        неавторизованного пользователя на страницу входа.
        """
        add_comment_page = f'/posts/{self.post.id}/comment/'
        redirect_login_page = reverse(
            'users:login') + f'?next=/posts/{self.post.id}/comment/'
        response = self.guest_client.get(add_comment_page, follow=True)
        self.assertRedirects(response, redirect_login_page)

    # Проверка редиректа неавторизованного пользователя при попытке
    # перехода на страницу c постами избранных авторов
    def test_index_follow_url_redirects_guest_client_on_login(self):
        """Страница с избранными авторами перенаправит
        неавторизованного пользователя на страницу входа.
        """
        redirect_login_page = reverse('users:login') + '?next=/follow/'
        response = self.guest_client.get('/follow/', follow=True)
        self.assertRedirects(response, redirect_login_page)

    # Проверка вызываемых шаблонов для каждого адреса
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
