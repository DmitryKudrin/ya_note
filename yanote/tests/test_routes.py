from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from notes.models import Note

User = get_user_model()

class TestRoutes(TestCase):


    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.not_author = User.objects.create(username='Не автор')
        
        cls.notes = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=cls.author,
        )

        
    def test_pages_availability(self):
        urls = (
            ('notes:home'),
            ('users:login'),
            ('users:logout'),
            ('users:signup'),
        )
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK) 


    def test_pages_availability_for_auth_user(self):
        urls = (
            ('notes:list'),
            ('notes:add'),
            ('notes:success'),
        )
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                self.client.force_login(self.not_author)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK) 
    

    def test_pages_availability_for_different_users(self):
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.not_author, HTTPStatus.NOT_FOUND),
        )
        urls = (
            ('notes:detail', (self.notes.slug,)),
            ('notes:edit', (self.notes.slug,)),
            ('notes:delete', (self.notes.slug,)),
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for name, args in urls:
                with self.subTest(name=name):
                    url = reverse(name, args=args)
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirects(self):
        urls = (
            ('notes:detail', (self.notes.slug,)),
            ('notes:edit', (self.notes.slug,)),
            ('notes:delete', (self.notes.slug,)),
            ('notes:list', None),
            ('notes:add', None),
            ('notes:success', None),
        )
        login_url = reverse('users:login')
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
