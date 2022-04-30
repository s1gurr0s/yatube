from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

ABOUT_AUTHOR_URL = reverse('about:author')
ABOUT_TECH_URL = reverse('about:tech')


class StaticPagesURLTests(TestCase):
    def setUp(self):
        # Создаем неавторизованый клиент
        self.guest_client = Client()

    def tests_about_urls_exist_and_correct_templates(self):
        """Проверка шаблонов и доступности адресов."""
        data = (
            (ABOUT_AUTHOR_URL, 'about/author.html'),
            (ABOUT_TECH_URL, 'about/tech.html')
        )
        for url, template in data:
            with self.subTest(
                url=url,
                template=template
            ):
                self.assertEqual(
                    self.guest_client.get(url).status_code,
                    HTTPStatus.OK
                )
                self.assertTemplateUsed(
                    self.guest_client.get(url),
                    template
                )
