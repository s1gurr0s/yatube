from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Author')
        cls.group = Group.objects.create(
            title='test_title',
            slug='test_slug',
            description='test_desc',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='test_text',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        field_verboses = {
            'title': 'Заголовок',
            'slug': 'Заголовок URL-адреса',
            'description': 'Описание группы',
        }
        for field, expected in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Group._meta.get_field(field).verbose_name,
                    expected
                )

    def test_models_have_correct_object_str(self):
        self.assertEqual(self.post.text[:15], str(self.post))
