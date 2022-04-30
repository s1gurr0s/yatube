from django.test import TestCase, Client
from django.urls import reverse
from http import HTTPStatus
from django.core.cache import cache

from ..models import Group, Post, User


INDEX_URL = reverse('posts:index')
POST_CREATE_URL = reverse('posts:post_create')
UNEXISTING_PAGE = '/unexisting_page/'
LOGIN_URL = reverse('users:login')
USERNAME = 'Author'
USERNAME_2 = 'User_2'
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
SLUG = 'slug'
GROUP_URL = reverse('posts:group_list', args=[SLUG])
FOLLOW_URL = reverse('posts:follow_index')
PROFILE_FOLLOW_URL = reverse('posts:profile_follow', args=[USERNAME])
PROFILE_UNFOLLOW_URL = reverse('posts:profile_unfollow', args=[USERNAME])


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest = Client()
        cls.user = User.objects.create(username=USERNAME)
        cls.author = Client()
        cls.author.force_login(cls.user)
        cls.user_2 = User.objects.create_user(username=USERNAME_2)
        cls.another_user = Client()
        cls.another_user.force_login(cls.user_2)
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
        )
        cls.group = Group.objects.create(
            title='Заголовок для тестовой группы',
            slug=SLUG,
            description='Тестовое описание',
        )
        cls.POST_DETAIL = reverse(
            'posts:post_detail', kwargs={'post_id': cls.post.id}
        )
        cls.POST_EDIT = reverse(
            'posts:post_edit', kwargs={'post_id': cls.post.id}
        )
        cls.POST_EDIT_REDIRECT_ANON = f'{LOGIN_URL}?next={cls.POST_EDIT}'
        cls.POST_CREATE_REDIRECT_ANON = f'{LOGIN_URL}?next={POST_CREATE_URL}'
        cls.ADD_COMMENT = reverse(
            'posts:add_comment',
            kwargs={'post_id': cls.post.id}
        )
        cls.ADD_COMMENT_REDIRECT_ANON = f'{LOGIN_URL}?next={cls.ADD_COMMENT}'

    def test_posts_urls_exist_at_desired_location_unexist_page_unexists(self):
        """Страницы приложения доступны пользователям,
        страница /unexisting_page/ не существует.
        """
        cache.clear()
        posts_urls_names_status_code = (
            (self.guest, INDEX_URL, HTTPStatus.OK),
            (self.author, POST_CREATE_URL, HTTPStatus.OK),
            (self.guest, GROUP_URL, HTTPStatus.OK),
            (self.guest, PROFILE_URL, HTTPStatus.OK),
            (self.guest, UNEXISTING_PAGE, HTTPStatus.NOT_FOUND),
            (self.author, self.POST_EDIT, HTTPStatus.OK),
            (self.author, FOLLOW_URL, HTTPStatus.OK),
        )
        for client, url, status_code in posts_urls_names_status_code:
            with self.subTest(
                client=client,
                url=url,
                status_code=status_code
            ):
                self.assertEqual(client.get(url).status_code, status_code)

    def test_posts_urls_redirections(self):
        """Страницы приложения перенаправляют пользователей
        в зависимости от ситуаций.
        """
        posts_urls_names_redirect_addresses = (
            (self.another_user, self.POST_EDIT, self.POST_DETAIL),
            (self.guest, POST_CREATE_URL, self.POST_CREATE_REDIRECT_ANON),
            (self.guest, self.POST_EDIT, self.POST_EDIT_REDIRECT_ANON),
            (self.guest, self.ADD_COMMENT, self.ADD_COMMENT_REDIRECT_ANON),
            (self.another_user, PROFILE_FOLLOW_URL, PROFILE_URL),
            (self.another_user, PROFILE_UNFOLLOW_URL, PROFILE_URL),
        )
        for client, url, redirect in posts_urls_names_redirect_addresses:
            with self.subTest(
                client=client,
                url=url,
                redirect=redirect
            ):
                self.assertRedirects(client.get(url, follow=True), redirect)

    def test_posts_urls_use_correct_templates(self):
        """URL-адреса используют соответствующие шаблоны."""
        cache.clear()
        posts_urls_names_templates = (
            (self.guest, INDEX_URL, 'posts/index.html'),
            (self.guest, GROUP_URL, 'posts/group_list.html'),
            (self.guest, PROFILE_URL, 'posts/profile.html'),
            (self.guest, self.POST_DETAIL, 'posts/post_detail.html'),
            (self.author, POST_CREATE_URL, 'posts/create_or_edit_post.html'),
            (self.author, self.POST_EDIT, 'posts/create_or_edit_post.html'),
            (self.author, FOLLOW_URL, 'posts/follow.html'),
        )
        for client, url, template in posts_urls_names_templates:
            with self.subTest(
                client=client,
                url=url,
                template=template
            ):
                self.assertTemplateUsed(client.get(url), template)
