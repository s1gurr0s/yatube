from django.test import TestCase
from django.urls import reverse

USERNAME = 'Author'
SLUG = 'test_slug'
POST_ID = 1
ROUTES = [
    ['/', 'index', []],
    ['/create/', 'post_create', []],
    [f'/group/{SLUG}/', 'group_list', [SLUG]],
    [f'/profile/{USERNAME}/', 'profile', [USERNAME]],
    [f'/posts/{POST_ID}/', 'post_detail', [POST_ID]],
    [f'/posts/{POST_ID}/edit/', 'post_edit', [POST_ID]],
]


class RoutingTest(TestCase):
    def test_urls_use_correct_routes(self):
        """Расчеты маршрутов дают ожидаемые URL"""
        for direct_url, reversed_url, args in ROUTES:
            routes = reverse(f'posts:{reversed_url}', args=args)
            self.assertEqual(direct_url, routes)
