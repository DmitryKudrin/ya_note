from http import HTTPStatus

from django.urls import reverse
from django.test import TestCase
from django.contrib.auth import get_user_model

from pytest_django.asserts import assertRedirects
from pytils.translit import slugify


from notes.models import Note
from notes.forms import WARNING

User = get_user_model()

class TestRoutes(TestCase):
    NEW_TITLE = 'Новый заголовок'
    NEW_TEXT = 'Текст комментария'
    NEW_SLUG = 'new-slug'

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
        cls.form_data = {
                    'title': cls.NEW_TITLE,
                    'text': cls.NEW_TEXT,
                    'slug': cls.NEW_SLUG,
                    }
    def test_user_can_create_note(self):
        self.notes.delete()
        url = reverse('notes:add')
        # В POST-запросе отправляем данные, полученные из фикстуры form_data:
        self.client.force_login(self.author)
        response = self.client.post(url, data=self.form_data)
        # Проверяем, что был выполнен редирект на страницу успешного добавления заметки:
        assertRedirects(response, reverse('notes:success'))
        # Считаем общее количество заметок в БД, ожидаем 1 заметку.
        self.assertEqual(Note.objects.count(), 1)
        # Чтобы проверить значения полей заметки - 
        # получаем её из базы при помощи метода get():
        new_note = Note.objects.get()
        # Сверяем атрибуты объекта с ожидаемыми.
        self.assertEqual(new_note.title, self.form_data['title'])
        self.assertEqual(new_note.text, self.form_data['text'])
        self.assertEqual(new_note.slug, self.form_data['slug'])
        self.assertEqual(new_note.author, self.author)

    def test_anonymous_user_cant_create_note(self):
        self.notes.delete()
        url = reverse('notes:add')
        response = self.client.post(url, data=self.form_data)
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={url}'
        assertRedirects(response, expected_url)
        self.assertEqual(Note.objects.count(), 0)
        
    def test_not_unique_slug(self):
        url = reverse('notes:add')
        # Подменяем slug новой заметки на slug уже существующей записи:
        self.client.force_login(self.author)
        self.form_data['slug'] = self.notes.slug
        # Пытаемся создать новую заметку:
        response = self.client.post(url, data=self.form_data)
        # Проверяем, что в ответе содержится ошибка формы для поля slug:
        self.assertFormError(response, 'form', 'slug', errors=(self.notes.slug + WARNING))
        # Убеждаемся, что количество заметок в базе осталось равным 1:
        self.assertEqual(Note.objects.count(), 1)

    def test_empty_slug(self):
        self.notes.delete()
        url = reverse('notes:add')
        # Убираем поле slug из словаря:
        self.form_data.pop('slug')
        self.client.force_login(self.author)
        response = self.client.post(url, data=self.form_data)
        # Проверяем, что даже без slug заметка была создана:
        assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)
        # Получаем созданную заметку из базы:
        new_note = Note.objects.get()
        # Формируем ожидаемый slug:
        expected_slug = slugify(self.form_data['title'])
        # Проверяем, что slug заметки соответствует ожидаемому:
        self.assertEqual(new_note.slug, expected_slug)

    def test_author_can_edit_note(self):
        self.client.force_login(self.author)
        # Получаем адрес страницы редактирования заметки:
        url = reverse('notes:edit', args=(self.notes.slug,))
        # В POST-запросе на адрес редактирования заметки
        # отправляем form_data - новые значения для полей заметки:
        response = self.client.post(url, self.form_data)
        # Проверяем редирект:
        assertRedirects(response, reverse('notes:success'))
        # Обновляем объект заметки note: получаем обновлённые данные из БД:
        self.notes.refresh_from_db()
        # Проверяем, что атрибуты заметки соответствуют обновлённым:
        self.assertEqual(self.notes.title, self.form_data['title'])
        self.assertEqual(self.notes.text, self.form_data['text'])
        self.assertEqual(self.notes.slug, self.form_data['slug'])
    

    def test_other_user_cant_edit_note(self):

        url = reverse('notes:edit', args=(self.notes.slug,))
        self.client.force_login(self.not_author)
        response = self.client.post(url, self.form_data)
        # Проверяем, что страница не найдена:
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Получаем новый объект запросом из БД.
        note_from_db = Note.objects.get(id=self.notes.id)
        # Проверяем, что атрибуты объекта из БД равны атрибутам заметки до запроса.
        self.assertEqual(self.notes.title, note_from_db.title)
        self.assertEqual(self.notes.text, note_from_db.text)
        self.assertEqual(self.notes.slug, note_from_db.slug)
        

    def test_author_can_delete_note(self):
        self.client.force_login(self.author)
        url = reverse('notes:delete', args=(self.notes.slug,))
        response = self.client.post(url)
        assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 0)


    def test_other_user_cant_delete_note(self):
        self.client.force_login(self.not_author)
        url = reverse('notes:delete', args=(self.notes.slug,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)