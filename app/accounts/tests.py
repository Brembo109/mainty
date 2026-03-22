from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class LoginViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="tester",
            password="strong-pass-123",
        )

    def test_login_page_returns_ok(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)

    def test_login_works_with_valid_credentials(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "tester", "password": "strong-pass-123"},
        )
        self.assertEqual(response.status_code, 302)
