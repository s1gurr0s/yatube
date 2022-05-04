import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

INDEX_URL = reverse('posts:index')
USERNAME = 'Author'
USERNAME_2 = 'User_2'
USERNAME_3 = 'User_3'
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
SLUG = 'slug'
GROUP_URL = reverse('posts:group_list', args=[SLUG])
SLUG_2 = 'slug_2'
GROUP_URL_2 = reverse('posts:group_list', args=[SLUG_2])
PAGINATOR_PAGE_COUNT_RANGE = 3
FOLLOW_URL = reverse('posts:follow_index')
PROFILE_FOLLOW_URL = reverse('posts:profile_follow', args=[USERNAME_3])
PROFILE_UNFOLLOW_URL = reverse('posts:profile_unfollow', args=[USERNAME_3])
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username=USERNAME)
        cls.author = Client()
        cls.author.force_login(cls.user)
        cls.user_2 = User.objects.create(username=USERNAME_2)
        cls.another_user = Client()
        cls.another_user.force_login(cls.user_2)
        cls.user_3 = User.objects.create(username=USERNAME_3)
        cls.another_user_2 = Client()
        cls.another_user_2.force_login(cls.user_3)
        cls.group = Group.objects.create(
            title='test_title',
            slug=SLUG,
            description='test_desc',
        )
        cls.second_group = Group.objects.create(
            title='test_title_2',
            slug=SLUG_2,
            description='test_desc_2',
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='test_text',
            group=cls.group,
            image=cls.uploaded,
        )
        Follow.objects.create(
            user=cls.user_2,
            author=cls.user,
        )
        cls.POST_DETAIL_URL = reverse('posts:post_detail', args=[cls.post.id])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_post_in_url_show_correct_context(self):
        """Шаблоны сформированы с правильным контекстом."""
        urls = [
            [INDEX_URL, self.author],
            [GROUP_URL, self.author],
            [PROFILE_URL, self.author],
            [FOLLOW_URL, self.another_user],
            [self.POST_DETAIL_URL, self.author],
        ]
        for url, client in urls:
            with self.subTest(url=url):
                response = client.get(url)
                if 'page_obj' in response.context:
                    self.assertEqual(len(response.context['page_obj']), 1)
                    post = response.context['page_obj'][0]
                else:
                    post = response.context['post']
                self.assertEqual(self.post, post)
                self.assertEqual(self.post.text, post.text)
                self.assertEqual(self.post.author, post.author)
                self.assertEqual(self.post.group, post.group)
                self.assertEqual(self.post.image, post.image)

    def test_profile_page_show_correct_context(self):
        """Проверка отображения автора в контексте профиля."""
        self.assertEqual(
            self.user,
            self.author.get(PROFILE_URL).context['author']
        )

    def test_post_page_show_correct_context_new(self):
        """Проверка отображения группы в контексте групп-ленты."""
        response = self.author.get(GROUP_URL)
        group = response.context['group']
        self.assertEqual(self.group, group)
        self.assertEqual(self.group.description, group.description)
        self.assertEqual(self.group.title, group.title)
        self.assertEqual(self.group.slug, group.slug)

    def test_post_not_show_in_the_group_2_and_another_feed(self):
        """Пост не показывается в другой группе и
        в чужой ленте подписок.
        """
        urls = [
            GROUP_URL_2,
            FOLLOW_URL,
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertNotIn(
                    self.post,
                    self.author.get(url).context['page_obj']
                )

    def test_subscribe(self):
        """Авторизованный пользователь может
        подписаться на другого пользователя.
        """
        self.another_user.get(PROFILE_FOLLOW_URL)
        self.assertTrue(Follow.objects.filter(
            user=self.user_2, author=self.user_3).exists()
        )
        self.assertEqual(Follow.objects.filter(
            user=self.user_2, author=self.user_3
        ).count(), 1)

    def test_unsubscribe(self):
        """Авторизованный пользователь может
        отписаться от другого пользователя.
        """
        self.another_user.get(PROFILE_UNFOLLOW_URL)
        self.assertFalse(Follow.objects.filter(
            user=self.user_2, author=self.user_3).exists()
        )

    def test_cache(self):
        """Проверка кэширования главной страницы."""
        response = self.author.get(INDEX_URL).content
        Post.objects.all().delete()
        response_cache = self.author.get(INDEX_URL).content
        self.assertEqual(response, response_cache)
        cache.clear()
        response_clear = self.author.get(INDEX_URL).content
        self.assertNotEqual(response, response_clear)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username=USERNAME)
        cls.author = Client()
        cls.author.force_login(cls.user)
        cls.user_2 = User.objects.create(username=USERNAME_2)
        cls.another_user = Client()
        cls.another_user.force_login(cls.user_2)
        cls.group = Group.objects.create(
            title='test_title',
            slug=SLUG,
            description='test_desc',
        )
        cls.INDEX_URL_PAGE_2 = f'{INDEX_URL}?page=2'
        cls.GROUP_URL_PAGE_2 = f'{GROUP_URL}?page=2'
        cls.PROFILE_URL_PAGE_2 = f'{PROFILE_URL}?page=2'
        cls.FOLLOW_URL_PAGE_2 = f'{FOLLOW_URL}?page=2'
        Post.objects.bulk_create(
            Post(
                text=f'Тестовый пост №{str(count)}',
                author=cls.user,
                group=cls.group,
            )
            for count in range(
                settings.POSTS + PAGINATOR_PAGE_COUNT_RANGE
            )
        )
        Follow.objects.create(
            user=cls.user_2,
            author=cls.user,
        )

    def test_pagination_first_and_second_pages(self):
        """Проверка пагинации для первой и второй страниц."""
        page_test_value = Post.objects.all().count() - settings.POSTS
        data = (
            (self.author, INDEX_URL, settings.POSTS),
            (self.author, GROUP_URL, settings.POSTS),
            (self.author, PROFILE_URL, settings.POSTS),
            (self.another_user, FOLLOW_URL, settings.POSTS),
            (self.author, self.INDEX_URL_PAGE_2, page_test_value),
            (self.author, self.GROUP_URL_PAGE_2, page_test_value),
            (self.author, self.PROFILE_URL_PAGE_2, page_test_value),
            (self.another_user, self.FOLLOW_URL_PAGE_2, page_test_value),
        )
        for client, url, page_count in data:
            with self.subTest(
                client=client,
                url=url,
                page_count=page_count
            ):
                self.assertEqual(
                    len(client.get(url).context['page_obj']),
                    page_count
                )
