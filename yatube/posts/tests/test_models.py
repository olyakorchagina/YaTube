from django.test import TestCase
from posts.models import Group, Post, User

TEXT_LIMIT = 15


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост для теста',
        )

    def test_models_method_str_works_correctly(self):
        """Проверка: у моделей Group и Post корректно работает __str__."""
        group = PostModelTest.group
        post = PostModelTest.post
        object_name = group.title
        length_text = post.text[:TEXT_LIMIT]
        models_expected_values = {
            object_name: str(group),
            length_text: str(post)
        }
        for value, expected in models_expected_values.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)
