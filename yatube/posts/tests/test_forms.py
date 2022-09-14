import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
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

    @classmethod
    def tearDownClass(cls):
        """Удаление тестовых медиа."""
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        """Создание клиента зарегистрированного пользователя и автора."""
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post_author = Client()
        self.post_author.force_login(self.author)

    def test_create_post(self):
        """Валидная форма создаёт запись в Post."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый пост',
            'group': self.group.id,
            'image': self.uploaded,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        latest_post = Post.objects.latest('id')
        self.assertEqual(latest_post.text, form_data['text'])
        self.assertEqual(latest_post.group.id, form_data['group'])
        self.assertEqual(latest_post.author, self.user)
        self.assertEqual(latest_post.image, 'posts/small.gif')

    def test_edit_post(self):
        """Валидная форма вносит изменения в существующую запись в Post."""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        self.post = Post.objects.create(
            text='Исходный текст',
            group=self.group,
            author=self.author
        )
        self.another_group = Group.objects.create(
            title='Котики',
            slug='cats',
            description='Сладкие котики',
        )
        form_data = {
            'text': 'Отредактированный текст',
            'group': self.another_group.id,
            'image': self.uploaded
        }
        self.post_author.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        edited_post = Post.objects.get(id=self.post.id)
        self.assertEqual(edited_post.text, form_data['text'])
        self.assertEqual(edited_post.group.id, form_data['group'])
        self.assertEqual(edited_post.author, self.author)

    def test_add_comment(self):
        """Валидная форма создает запись в Comment."""
        comments_count = Comment.objects.count()
        self.post = Post.objects.create(
            text='Какой-то пост',
            group=self.group,
            author=self.author
        )
        form_data = {
            'post': self.post,
            'text': 'ВАУ!',
            'author': self.user
        }
        self.authorized_client.post(
            reverse(
                'posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        latest_comment = Comment.objects.latest('id')
        self.assertEqual(latest_comment.text, form_data['text'])
        self.assertEqual(latest_comment.author, self.user)
        self.assertEqual(latest_comment.post, self.post)
