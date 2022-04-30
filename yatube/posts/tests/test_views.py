from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from django.conf import settings

from ..models import Follow, Group, Post, User


INDEX_URL = reverse('posts:index')
USERNAME = 'Author'
USERNAME_2 = 'User_2'
PROFILE_URL = reverse('posts:profile', kwargs={'username': USERNAME})
SLUG = 'slug'
GROUP_URL = reverse('posts:group_list', kwargs={'slug': SLUG})
SLUG_2 = 'slug_2'
GROUP_URL_2 = reverse('posts:group_list', kwargs={'slug': SLUG_2})
PAGINATOR_PAGE_COUNT_RANGE = 3
FOLLOW_URL = reverse('posts:follow_index')
PROFILE_FOLLOW_URL = reverse('posts:profile_follow', args=[USERNAME])
PROFILE_UNFOLLOW_URL = reverse('posts:profile_unfollow', args=[USERNAME])


class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username=USERNAME)
        cls.author = Client()
        cls.author.force_login(cls.user)
        cls.user_2 = User.objects.create_user(username=USERNAME_2)
        cls.another_user = Client()
        cls.another_user.force_login(cls.user_2)
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
        cls.post = Post.objects.create(
            author=cls.user,
            text='test_text',
            group=cls.group,
        )
        cls.POST_DETAIL_URL = reverse('posts:post_detail', args=[cls.post.id])

    def assert_post(self, context_test):
        self.assertEqual(self.post, context_test)
        self.assertEqual(self.post.text, context_test.text)
        self.assertEqual(self.post.author, context_test.author)
        self.assertEqual(self.post.group, context_test.group)

    def test_post_in_url_show_correct_context(self):
        """Шаблоны сформированы с правильным контекстом."""
        urls = [
            INDEX_URL,
            GROUP_URL,
            PROFILE_URL
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assert_post(
                    self.author.get(url).context['page_obj'][0]
                )

    def test_profile_page_show_correct_context(self):
        """Проверка отображения автора в контексте профиля."""
        self.assertEqual(
            self.user,
            self.author.get(PROFILE_URL).context['author']
        )

    def test_post_page_show_correct_context(self):
        """Проверка отображения страницы post_detail."""
        self.assert_post(
            self.author.get(self.POST_DETAIL_URL).context['post']
        )

    def test_post_page_show_correct_context_new(self):
        """Проверка отображения группы в контексте групп-ленты."""
        response = self.author.get(GROUP_URL)
        group_test = response.context['group']
        self.assertEqual(self.group, group_test)
        self.assertEqual(self.group.description, group_test.description)
        self.assertEqual(self.group.title, group_test.title)
        self.assertEqual(self.group.slug, group_test.slug)

    def test_group_post_page_show_post_not_in_the_group_2(self):
        """Пост не показывается в другой группе."""
        self.assertNotIn(
            self.post,
            self.author.get(GROUP_URL_2).context['page_obj']
        )

    def test_subscribe(self):
        """Авторизованный пользователь может
        подписаться на другого пользователя.
        """
        self.another_user.get(PROFILE_FOLLOW_URL)
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_unsubscribe(self):
        """Авторизованный пользователь может
        отписаться от другого пользователя.
        """
        self.another_user.get(PROFILE_UNFOLLOW_URL)
        self.assertEqual(Follow.objects.all().count(), 0)


class PaginatorViewsTest(TestCase):
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

    def test_pagination_first_page(self):
        """Проверка пагинации для первой страницы."""
        data = [
            [INDEX_URL, settings.POSTS],
            [GROUP_URL, settings.POSTS],
            [PROFILE_URL, settings.POSTS],
        ]
        for url, page_count in data:
            with self.subTest(url=url):
                self.assertEqual(
                    len(self.author.get(url).context['page_obj']),
                    page_count
                )

    def test_pagination_second_page(self):
        """Проверка пагинации для второй страницы."""
        page_test_value = Post.objects.all().count() - settings.POSTS
        data = [
            [INDEX_URL, page_test_value],
            [GROUP_URL, page_test_value],
            [PROFILE_URL, page_test_value]
        ]
        for url, page_count in data:
            with self.subTest(url=url):
                self.assertEqual(
                    len(self.author.get(url, {'page': 2}).context['page_obj']),
                    page_count
                )


class FollowTests(TestCase):
    def setUp(self):
        self.user = Client()
        self.author = Client()
        self.follower = User.objects.create_user(username=USERNAME)
        self.following = User.objects.create_user(username=USERNAME_2)
        self.post = Post.objects.create(
            author=self.following,
            text='test_text'
        )
        self.user.force_login(self.follower)
        self.author.force_login(self.following)

    def test_subscription_feed(self):
        """Запись появляется в ленте подписчиков
        и не появляется у остальных.
        """
        Follow.objects.create(
            user=self.follower,
            author=self.following
        )
        self.assertEqual(
            self.user.get(FOLLOW_URL).context["page_obj"][0].text,
            self.post.text
        )
        self.assertNotContains(self.author.get(FOLLOW_URL), self.post.text)


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.author = Client()
        cls.author.force_login(cls.user)
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
        )

    def test_cache(self):
        """Проверка кэширования главной страницы."""
        response = self.author.get(INDEX_URL).content
        self.post.delete()
        response_cache = self.author.get(INDEX_URL).content
        self.assertEqual(response, response_cache)
        cache.clear()
        response_clear = self.author.get(INDEX_URL).content
        self.assertNotEqual(response, response_clear)
