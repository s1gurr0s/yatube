import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, User

INDEX_URL = reverse('posts:index')
POST_CREATE_URL = reverse('posts:post_create')
USERNAME = 'Author'
PROFILE_URL = reverse('posts:profile', kwargs={'username': USERNAME})
SLUG = 'slug'
SLUG_2 = 'slug_2'
GROUP_URL = reverse('posts:group_list', kwargs={'slug': SLUG})
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.author = Client()
        cls.author.force_login(cls.user)
        cls.group = Group.objects.create(
            title='test_title',
            slug=SLUG,
            description='test_desc',
        )
        cls.group_2 = Group.objects.create(
            title='test_title_2',
            slug=SLUG_2,
            description='test_desc_2'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='test_text',
            group=cls.group
        )
        cls.POST_DETAIL_URL = reverse('posts:post_detail', args=[cls.post.pk])
        cls.POST_EDIT_URL = reverse('posts:post_edit', args=[cls.post.pk])
        cls.ADD_COMMENT_URL = reverse('posts:add_comment', args=[cls.post.id])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post_form(self):
        """Проверка формы создания поста."""
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'group': self.group.pk,
            'text': 'test_text',
            'image': uploaded
        }
        post_count = Post.objects.count()
        response = self.author.post(
            POST_CREATE_URL,
            data=form_data,
            follow=True
        )
        image_name = form_data['image'].name
        post = Post.objects.order_by('-pub_date').first()
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.image.name, f'posts/{image_name}')
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertRedirects(response, PROFILE_URL)

    def test_edit_post_form(self):
        """Проверка формы редактирования поста и его изменения
        в базе данных."""
        uploaded = SimpleUploadedFile(
            name='small2.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': 'test_text',
            'group': self.group_2.pk,
            'image': uploaded,
        }
        response = self.author.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True
        )
        image_name = form_data['image'].name
        post = Post.objects.order_by('-pub_date').first()
        self.assertRedirects(response, self.POST_DETAIL_URL)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.image.name, f'posts/{image_name}')
        self.assertEqual(Post.objects.count(), 1)

    def test_post_create_and_edit_pages_show_correct_context(self):
        """Шаблоны post_edit и post_create содержат корректную форму."""
        urls = [
            POST_CREATE_URL,
            self.POST_EDIT_URL
        ]
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        for url in urls:
            response = self.author.get(url)
            for value, expected in form_fields.items():
                with self.subTest(field=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_create_post_guest(self):
        """При отправке валидной формы не создаётся новая запись."""
        post_count: int = Post.objects.count()
        form_data = {
            'text': 'test_post_for_form',
            'group': self.group.pk,
        }
        self.assertEqual(Post.objects.count(), post_count)
        self.assertRedirects(
            self.client.post(
                reverse('posts:post_create'), data=form_data, follow=True),
            '/auth/login/?next=/create/'
        )

    def test_image_shows_correctly_context(self):
        """Изображение передается в словаре context."""
        urls = [
            INDEX_URL,
            PROFILE_URL,
            GROUP_URL
        ]
        for url in urls:
            response = self.author.get(url)
            object_list = response.context['page_obj'][0]
            self.assertEqual(object_list.image, self.post.image)

    def test_post_detail_shows_correctly_context(self):
        """Изображение передается в словаре context для post_detail."""
        response = self.author.get(self.POST_DETAIL_URL)
        self.assertEqual(self.post.image, response.context['post'].image)

    def test_comment_shows_correctly(self):
        """Комментарий отображается корректно."""
        form_data = {
            'text': 'test_text',
            'post': self.post.id,
            'author': self.user,
        }
        response = self.author.post(
            self.ADD_COMMENT_URL,
            data=form_data,
            follow=True
        )
        comment = response.context['comments'][0]
        self.assertEqual(len(response.context['comments']), 1)
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.author, self.user)
