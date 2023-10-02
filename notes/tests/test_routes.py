    # +++ Главная страница доступна анонимному пользователю.

    # +++ Аутентифицированному пользователю доступна страница со списком заметок notes/,  страница успешного добавления заметки done/, страница добавления новой заметки add/.

    # +++ Страницы отдельной заметки, удаления и редактирования заметки доступны только автору заметки. Если на эти страницы попытается зайти другой пользователь — вернётся ошибка 404.
    
    # +++ При попытке перейти на страницу списка заметок, страницу успешного добавления записи, страницу добавления заметки, отдельной заметки,
    # +++ редактирования или удаления заметки анонимный пользователь перенаправляется на страницу логина.

    # +++ Страницы регистрации пользователей, входа в учётную запись и выхода из неё доступны всем пользователям.

from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        """Метод класса. Создает заметку, пользователя - автора заметки
        и пользователя, не являющегося автором заметки."""
        cls.author = User.objects.create(username='Автор заметки')
        cls.non_author = User.objects.create(username='Не автор заметки')
        cls.note = Note.objects.create(title='Заголовок', text='Текст', slug='test_note', author=cls.author)
    
    def test_notes_pages_availability(self):
        urls = (
            ('notes:home', 'Убедитесь, что что любому пользователю доступна главная страница.',),
            ('users:signup', 'Убедитесь, что что любому пользователю доступна страница регистрации пользователей.',),
            ('users:login', 'Убедитесь, что что любому пользователю доступна страница входа в учётную запись.',),
            ('users:logout', 'Убедитесь, что что любому пользователю доступна страница выхода из учётной записи.',),
            ('notes:list', 'Убедитесь, что что аутентифицированному пользователю доступна страница со списком заметок.',),
            ('notes:success', 'Убедитесь, что что аутентифицированному пользователю доступна страница успешного добавления заметки.',),
            ('notes:add', 'Убедитесь, что что аутентифицированному пользователю доступна страница добавления новой заметки.',),
        )
        for name, msg in urls:
            with self.subTest(name=name):
                url = reverse(name)
                if name in ('notes:list', 'notes:success', 'notes:add'):
                    self.client.force_login(self.non_author)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK, msg=msg)

    def test_availability_for_note_detail_edit_delete(self):
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.non_author, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for name, msg in (
                ('notes:detail', 'Убедитесь, что страница отдельной заметки доступна только автору, иначе возвращается ошибка 404.',),
                ('notes:delete', 'Убедитесь, что страница удаления заметки доступна только автору, иначе возвращается ошибка 404.'),
                ('notes:edit', 'Убедитесь, что страница редактировавния заметки доступна только автору, иначе возвращается ошибка 404.'),
            ):
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status, msg=msg)

    def test_redirect_for_anonymous_client(self):
        login_url = reverse('users:login')
        urls = (
            ('notes:list', None, 'Убедитесь, что при попытке перейти на страницу списка заметок анонимный пользователь перенаправляется на страницу логина.',),
            ('notes:success', None, 'Убедитесь, что при попытке перейти на страницу успешного добавления записи анонимный пользователь перенаправляется на страницу логина.',),
            ('notes:add', None, 'Убедитесь, что при попытке перейти на страницу добавления заметки анонимный пользователь перенаправляется на страницу логина.',),
            ('notes:detail', (self.note.slug,), 'Убедитесь, что при попытке перейти на страницу отдельной заметки анонимный пользователь перенаправляется на страницу логина.',),
            ('notes:delete', (self.note.slug,), 'Убедитесь, что при попытке перейти на страницу удаления заметки анонимный пользователь перенаправляется на страницу логина.',),
            ('notes:edit', (self.note.slug,), 'Убедитесь, что при попытке перейти на страницу редактирования заметки анонимный пользователь перенаправляется на страницу логина.',),
        )
        for name, args, msg in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url, msg_prefix=msg)
