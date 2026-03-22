from django.test import TestCase
from django.urls import reverse


class CoreViewsTests(TestCase):
    def test_homepage_returns_ok(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("core:dashboard"))
        self.assertEqual(response.status_code, 302)
