from django.test import TestCase
from django.urls import reverse

from posts.urls import app_name

USERNAME = 'Author'
SLUG = 'test_slug'
POST_ID = 1
ROUTES = [
    ['/', 'index', []],
    ['/create/', 'post_create', []],
    ['/follow/', 'follow_index', []],
    [f'/group/{SLUG}/', 'group_list', [SLUG]],
    [f'/profile/{USERNAME}/', 'profile', [USERNAME]],
    [f'/posts/{POST_ID}/', 'post_detail', [POST_ID]],
    [f'/posts/{POST_ID}/edit/', 'post_edit', [POST_ID]],
    [f'/posts/{POST_ID}/comment/', 'add_comment', [POST_ID]],
    [f'/profile/{USERNAME}/follow/', 'profile_follow', [USERNAME]],
    [f'/profile/{USERNAME}/unfollow/', 'profile_unfollow', [USERNAME]]
]


class RoutingTest(TestCase):
    def test_urls_use_correct_routes(self):
        """Расчеты маршрутов дают ожидаемые URL"""
        for direct_url, reversed_url, args in ROUTES:
            self.assertEqual(
                direct_url,
                reverse(f'{app_name}:{reversed_url}', args=args)
            )
