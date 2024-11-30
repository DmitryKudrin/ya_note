from django.urls import reverse
from django.test import TestCase
from django.contrib.auth import get_user_model

from notes.models import Note
from notes.forms import NoteForm

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

    def test_notes_list_for_different_users(self):
        users_statuses = (
            (self.author),
            (self.not_author),
        )
        for user in users_statuses:
            self.client.force_login(user)
            with self.subTest(user=user):
                url = reverse('notes:list')
                response = self.client.get(url)
                object_list = response.context['object_list']
                if user == self.author:
                    self.assertIn(self.notes, object_list)
                else:
                    self.assertNotIn(self.notes, object_list)

    def test_pages_contains_form(self):
        urls = (
            ('notes:edit', (self.notes.slug,)),
            ('notes:add', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                self.client.force_login(self.author)
                response = self.client.get(url)
                self.assertIn('form', response.context)
                # Проверяем, что объект формы относится к нужному классу.
                self.assertIsInstance(response.context['form'], NoteForm)