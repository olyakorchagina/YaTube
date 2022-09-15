import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Comment, Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

COUNT_TEST_POSTS = 13
POSTS_ON_PAGE = 10
POSTS_ON_SECOND_PAGE = 3


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
            group=cls.group,
            image=cls.uploaded
        )
        cls.comment_post = Comment.objects.create(
            author=cls.author,
            text='Тестовый комментарий',
            post=cls.post
        )
        cls.another_group = Group.objects.create(
            title='Котики',
            slug='cats',
            description='Любители котиков',
        )

    @classmethod
    def tearDownClass(cls):
        """Удаление тестовых медиа."""
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        """Создание клиента зарегистрированного пользователя и автора поста."""
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post_author = Client()
        self.post_author.force_login(self.author)

    def post_exists(self, page_context):
        """Метод для проверки существования поста на страницах
        и проверка его атрибутов.
        """
        page_obj = page_context.get('page_obj')
        self.assertIsNotNone(page_obj)
        first_object = page_obj[0]
        self.assertIn(first_object, page_obj)
        self.assertEqual(first_object.author.username, self.author.username)
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.group, self.group)
        self.assertEqual(first_object.image, self.post.image)

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

    def test_index_first_element_contains_expected_values(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.post_author.get(reverse('posts:index'))
        page_context = response.context
        self.post_exists(page_context)

    def test_group_list_first_element_contains_expected_values(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.post_author.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        page_context = response.context
        group = response.context.get('group')
        self.assertIsNotNone(group)
        self.post_exists(page_context)
        self.assertEqual(group, self.group)

    def test_profile_first_element_contains_expected_values(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.post_author.get(
            reverse('posts:profile', kwargs={'username': self.author.username})
        )
        page_context = response.context
        author = response.context.get('author')
        self.assertIsNotNone(author)
        following = response.context.get('following')
        self.assertIsNotNone(following)
        self.post_exists(page_context)
        self.assertFalse(following)
        self.assertEqual(author, self.author)

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

    def test_another_group_page_has_not_new_post(self):
        """Новый пост не попал на страницу другой группы."""
        response = self.post_author.get(
            reverse(
                'posts:group_list', kwargs={'slug': self.another_group.slug})
        )
        page_obj = response.context.get('page_obj')
        self.assertNotIn(self.post, page_obj.object_list)

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

    def test_follow(self):
        """Тестирование: подписка на автора создаёт запись в БД."""
        count_follow = Follow.objects.count()
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.author.username})
        )
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        latest_follow = Follow.objects.latest('id')
        self.assertEqual(latest_follow.author, self.author)
        self.assertEqual(latest_follow.user, self.user)

    def test_unfollow(self):
        """Тестирование: отписка от автора удаляет запись из БД."""
        count_follow = Follow.objects.count()
        self.follow = Follow.objects.create(
            user=self.user,
            author=self.author
        )
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.author.username})
        )
        self.assertEqual(Follow.objects.count(), count_follow)

    def test_following_posts(self):
        """Тестирование появления поста автора в ленте подписчика."""
        self.new_user = User.objects.create(username='olya')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.new_user)
        self.follow = Follow.objects.create(
            user=self.new_user,
            author=self.author
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        page_context = response.context
        self.post_exists(page_context)

    def test_unfollowing_posts(self):
        """Тестирование отсутствия поста автора в ленте
        у нового пользователя.
        """
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
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        for i in range(COUNT_TEST_POSTS):
            Post.objects.bulk_create([Post(
                author=cls.author,
                text=f'Тестовый пост № {i}',
                group=cls.group)
            ])

    def setUp(self):
        """Создание клиента автора постов."""
        self.post_author = Client()
        self.post_author.force_login(self.author)

    def test_pages_contain_correct_records(self):
        """Проверка количества постов на первой и второй страницах."""
        paginator_pages_url = [
            reverse('posts:index'),
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ),
            reverse(
                'posts:profile', kwargs={'username': self.author.username}
            )
        ]
        page_posts = [
            (1, 10),
            (2, 3)
        ]
        for url in paginator_pages_url:
            for num_page, num_of_posts in page_posts:
                with self.subTest(url=url):
                    response = self.post_author.get(f'{url}?page={num_page}')
                    self.assertEqual(len(
                        response.context['page_obj']), num_of_posts
                    )
