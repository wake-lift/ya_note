    # +++ отдельная заметка передаётся на страницу со списком заметок в списке object_list в словаре context;

    # +++ в список заметок одного пользователя не попадают заметки другого пользователя;

    # +++ на страницы создания и редактирования заметки передаются формы.

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestContent(TestCase):
    NOTES_LIST_URL = reverse('notes:list')

    @classmethod
    def setUpTestData(cls):
        """Метод класса. Создает заметку, пользователя - автора заметки
        и пользователя, не являющегося автором заметки."""
        cls.author = User.objects.create(username='Автор заметки')
        cls.non_author = User.objects.create(username='Не автор заметки')
        cls.note = Note.objects.create(title='Заголовок', text='Текст', slug='test_note', author=cls.author)

    def test_note_goes_on_list_page(self):
        self.client.force_login(self.author)
        response = self.client.get(self.NOTES_LIST_URL)
        object_list = response.context['object_list']
        self.assertEqual(len(object_list), 1, msg='Убедитесь, что отдельная заметка передаётся на страницу со списком заметок.')
    
    def test_notes_belong_to_author(self):
        self.client.force_login(self.non_author)
        response = self.client.get(self.NOTES_LIST_URL)
        object_list = response.context['object_list']
        self.assertNotIn(self.note, object_list, msg='Убедитесь, что в список заметок одного пользователя не попадают заметки другого пользователя.')
    
    def test_create_page_has_form(self):
        self.client.force_login(self.author)
        response_note_create = self.client.get(reverse('notes:add'))
        self.assertIn('form', response_note_create.context, msg='Убедитесь, что на страницу создания заметки передается форма.')

    def test_delete_page_has_form(self):
        self.client.force_login(self.author)
        response_note_edit = self.client.get(reverse('notes:edit', args=(self.note.slug,)))
        self.assertIn('form', response_note_edit.context, msg='Убедитесь, что на страницу редактирования заметки передается форма.')

