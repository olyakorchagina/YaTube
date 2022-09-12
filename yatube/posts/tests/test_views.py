import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

COUNT_TEST_POSTS = 13
POSTS_ON_PAGE = 10


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        # Авторизированный пользователь
        cls.user = User.objects.create_user(username='user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        # Автор поста
        cls.author = User.objects.create_user(username='author')
        cls.post_author = Client()
        cls.post_author.force_login(cls.author)
        # Тестовая группа
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        # Ещё одна тестовая группа «Котики»
        cls.another_group = Group.objects.create(
            title='Котики',
            slug='cats',
            description='Любители котиков',
        )
        # Тестовый пост
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded
        )
        # Тестовый комментарий
        cls.comment_post = Comment.objects.create(
            author=cls.author,
            text='Тестовый комментарий',
            post=cls.post
        )

    @classmethod
    def tearDownClass(cls):
        """Удаление тестовых медиа."""
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def post_exists(self, page_context):
        """Метод для проверки существования поста на страницах
        и проверка его атрибутов.
        """
        page_obj = page_context.get('page_obj')
        first_object = page_context['page_obj'][0]
        self.assertIsNotNone(page_obj)
        self.assertEqual(first_object.author.username, self.author.username)
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.group, self.group)
        self.assertEqual(first_object.image, self.post.image)

    # Проверка вызываемых шаблонов для каждого адреса
    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            reverse(
                'posts:index'):
                    'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}):
                    'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': self.author.username}):
                    'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}):
                    'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}):
                    'posts/create_post.html',
            reverse(
                'posts:post_create'):
                    'posts/create_post.html',
            reverse(
                'posts:follow_index'):
                    'posts/follow.html',
            
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.post_author.get(url)
                self.assertTemplateUsed(response, template)

    # Проверка: содержимое ключа словаря context страницы index
    # не является None и в первом элементе списка содержит ожидаемые значения
    def test_index_first_element_contains_expected_values(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.post_author.get(reverse('posts:index'))
        page_context = response.context
        self.post_exists(page_context)

    # Проверка: содержимое ключей словаря context страницы group_list
    # не является None и в первом элементе списка содержат ожидаемые значения
    def test_group_list_first_element_contains_expected_values(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.post_author.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        page_context = response.context
        group = response.context.get('group')
        self.post_exists(page_context)
        self.assertIsNotNone(group)
        self.assertEqual(group, self.group)

    # Проверка: содержимое ключей словаря context страницы profile
    # не является None и в первом элементе списка содержат ожидаемые значения
    def test_profile_first_element_contains_expected_values(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.post_author.get(
            reverse('posts:profile', kwargs={'username': self.author.username})
        )
        page_context = response.context
        author = response.context.get('author')
        following = response.context.get('following')
        self.post_exists(page_context)
        self.assertIsNotNone(author)
        self.assertIsNotNone(following)
        self.assertIs(following, False)
        self.assertEqual(author, self.author)

    # Проверка: содержимое ключей словаря context страницы post_detail
    # не является None и содержит ожидаемые значения
    def test_post_detail_page_shows_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.post_author.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        post = response.context.get('post') 
        self.assertIsNotNone(post)
        self.assertEqual(
            response.context['post'].group, self.group
        )
        self.assertEqual(
            response.context['post'].text, self.post.text
        )
        self.assertEqual(
            response.context['post'].author.username, self.author.username
        )
        self.assertEqual(
            response.context['post'].image, 'posts/small.gif'
        )
        self.assertEqual(
            response.context['post'].comments.latest('id'), self.comment_post
        )

    # Проверка словаря context страницы create (в нём передаётся форма)
    def test_create_page_shows_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.post_author.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    # Проверка словаря context страницы post_edit
    # (в нём передаётся форма и is_edit)
    def test_post_edit_page_shows_correct_context(self):
        """Шаблон create_post при редактировании поста
        сформирован с правильным контекстом.
        """
        response = self.post_author.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        is_edit = response.context.get('is_edit')
        self.assertIsNotNone(is_edit)
        self.assertIs(is_edit, True)

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    # Проверка: пост не попал на страницу другой группы
    def test_another_group_page_has_not_new_post(self):
        response = self.post_author.get(
            reverse(
                'posts:group_list', kwargs={'slug': self.another_group.slug})
        )
        page_obj = response.context.get('page_obj')
        self.assertNotIn(self.post, page_obj.object_list)

    # Проверка: при удалении записи из базы, она остаётся в response.content 
    # главной страницы до принудительной очистки кэша
    def test_index_caches(self):
        """Тестирование кэша главной страницы."""
        self.new_post = Post.objects.create(
            author=self.author,
            text='Пост тестирования кэша'
        )
        response_1 = self.post_author.get(
            reverse('posts:index')
        )
        self.new_post.delete()
        response_2 = self.post_author.get(
            reverse('posts:index')
        )
        self.assertEqual(response_1.content, response_2.content)
        cache.clear()
        response_3 = self.post_author.get(
            reverse('posts:index')
        )
        self.assertNotEqual(response_2.content, response_3.content)

    # Проверка: новая запись пользователя появляется в ленте тех, 
    # кто на него подписан.
    def test_following_posts(self):
        """Тестирование появления поста автора в ленте подписчика."""
        self.new_user = User.objects.create(username='olya')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.new_user)
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.author.username}
            )
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        page_context = response.context
        self.post_exists(page_context)

    # Проверка: новая запись пользователя не появляется в ленте тех, 
    # кто на него не подписан.
    def test_unfollowing_posts(self):
        """Тестирование отсутствия поста автора у нового пользователя."""
        self.new_user = User.objects.create(username='katya')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.new_user)
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        page_obj = response.context.get('page_obj')
        self.assertNotIn(self.post, page_obj.object_list)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Автор поста
        cls.author = User.objects.create_user(username='author')
        cls.post_author = Client()
        cls.post_author.force_login(cls.author)
        # Тестовая группа
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        # Создание 13 постов
        for i in range(COUNT_TEST_POSTS):
            Post.objects.bulk_create([Post(
                author=cls.author,
                text=f'Тестовый пост № {i}',
                group=cls.group)
            ])

    def test_pages_contain_correct_records(self):
        '''Проверка количества постов на первой и второй страницах. '''
        paginator_pages = [
            reverse('posts:index'),
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ),
            reverse(
                'posts:profile', kwargs={'username': self.author.username}
            )
        ]
        for url in paginator_pages:
            with self.subTest(url=url):
                first_response = self.post_author.get(url)
                second_response = self.post_author.get((url) + '?page=2')
                self.assertEqual(len(
                    first_response.context['page_obj']),
                    POSTS_ON_PAGE
                )
                self.assertEqual(len(
                    second_response.context['page_obj']),
                    COUNT_TEST_POSTS - POSTS_ON_PAGE
                )
