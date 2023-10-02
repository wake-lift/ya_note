    # +++ Залогиненный пользователь может создать заметку, а анонимный — не может.

    # +++ Невозможно создать две заметки с одинаковым slug.

    # +++ Если при создании заметки не заполнен slug, то он формируется автоматически, с помощью функции pytils.translit.slugify.

    # +++ Пользователь может редактировать и удалять свои заметки, но не может редактировать или удалять чужие.
from http import HTTPStatus
from pytils.translit import slugify

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse


from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestLogic(TestCase):

    USER1_NOTE_TITLE = 'Заголовок 1'
    USER1_NOTE_TEXT = 'Текст 1'
    USER1_NOTE_SLUG = 'test_note_1'

    @classmethod
    def setUpTestData(cls):
        """Метод класса. Создает двух разных авторов и логинит авторов в клиенте. Создает заметку для одного из авторов. Формирует необходимые маршруты."""
        cls.user1 = User.objects.create(username='Юзер 1')
        cls.user1_client = Client()
        cls.user1_client.force_login(cls.user1)
        cls.user2 = User.objects.create(username='Юзер 2')
        cls.user2_client = Client()
        cls.user2_client.force_login(cls.user2)
        cls.note_user1 = Note.objects.create(title=cls.USER1_NOTE_TITLE, text=cls.USER1_NOTE_TEXT, slug=cls.USER1_NOTE_SLUG, author=cls.user1)
        cls.url_create = reverse('notes:add')
        cls.url_success = reverse('notes:success')
        cls.url_edit = reverse('notes:edit', args=(cls.note_user1.slug,))
        cls.url_delete = reverse('notes:delete', args=(cls.note_user1.slug,))
        cls.form_data = {'title': 'Заголовок', 'text': 'Текст', 'slug': 'test_note'}
    
    def test_anonymous_user_cant_create_note(self):
        self.client.post(self.url_create, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1, msg='Убедитесь, что анонимный пользователь не может создать заметку.')
    
    def test_user_can_create_note(self):
        response = self.user1_client.post(self.url_create, data=self.form_data)
        self.assertRedirects(response, self.url_success, msg_prefix='Убедитесь, что после создания заметки пользователь перенаправляется на страницу успешного выполнения операции.')
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 2, msg='Убедитесь, что залогиненный пользователь может создать заметку.')
        note = Note.objects.get(title=self.form_data['title'])
        self.assertEqual(note.title, self.form_data['title'], msg='Убедитесь, что заголовок заметки соответствует тому, что передается в форме.')
        self.assertEqual(note.text, self.form_data['text'], msg='Убедитесь, что текст заметки соответствует тому, что передается в форме.')
        self.assertEqual(note.slug, self.form_data['slug'], msg='Убедитесь, что слаг заметки соответствует тому, что передается в форме.')
        self.assertEqual(note.author, self.user1, msg='Убедитесь, что авторство заметки принадлежит ее создателю.')

    def test_author_can_delete_note(self):
        response = self.user1_client.delete(self.url_delete)
        self.assertRedirects(response, self.url_success, msg_prefix='Убедитесь, что после удаления заметки пользователь перенаправляется на страницу успешного выполнения операции.')
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0, msg='Убедитесь, что автор может удалять свои заметки.')

    def test_user_cant_delete_note_of_another_user(self):
        response = self.user2_client.delete(self.url_delete)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND, msg='Убедитесь, что при попытке удалить чужую заметку возникает ошибка 404.')
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1, msg='Убедитесь, что юзер не может удалять заметки другого юзера.')

    def test_author_can_edit_note(self):
        response = self.user1_client.post(self.url_edit, data=self.form_data)
        self.assertRedirects(response, self.url_success, msg_prefix='Убедитесь, что после редактирования заметки пользователь перенаправляется на страницу успешного выполнения операции.')
        self.note_user1.refresh_from_db()
        self.assertEqual(self.note_user1.title, self.form_data['title'], msg='Убедитесь, что при редактировавании заметки заголовок соответствует тому, что передается в форме.')
        self.assertEqual(self.note_user1.text, self.form_data['text'], msg='Убедитесь, что при редактировавании заметки текст соответствует тому, что передается в форме.')
        self.assertEqual(self.note_user1.slug, self.form_data['slug'], msg='Убедитесь, что при редактировавании заметки слаг соответствует тому, что передается в форме.')

    def test_user_cant_edit_note_of_another_user(self):
        response = self.user2_client.post(self.url_edit, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND, msg='Убедитесь, что при попытке редактировать чужую заметку возникает ошибка 404.')
        self.note_user1.refresh_from_db()
        self.assertEqual(self.note_user1.title, self.USER1_NOTE_TITLE, msg='Убедитесь, что при попытке редактировавания чужой заметки ее заголовок не меняется.')
        self.assertEqual(self.note_user1.text, self.USER1_NOTE_TEXT, msg='Убедитесь, что при попытке редактировавания чужой заметки ее текст не меняется.')
        self.assertEqual(self.note_user1.slug, self.USER1_NOTE_SLUG, msg='Убедитесь, что при попытке редактировавания чужой заметки ее слаг не меняется.')

    def test_not_unique_slug(self):
        self.form_data['slug'] = self.USER1_NOTE_SLUG
        response = self.user1_client.post(self.url_create, data=self.form_data)
        self.assertFormError(response, 'form', 'slug', errors=(self.form_data['slug'] + WARNING), msg_prefix='Убедитесь, что при попытке создания заметки с неуникальным слагом возвращается ошибка формы.')
        self.note_user1.refresh_from_db()
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1, msg='Убедитесь, что невозможно создать две заметки с одинаковым слагом.')

    def test_empty_slug(self):
        self.form_data.pop('slug')
        response = self.user1_client.post(reverse('notes:add'), data=self.form_data)
        self.assertRedirects(response, self.url_success, msg_prefix='Убедитесь, что после создания заметки без слага пользователь перенаправляется на страницу успешного выполнения операции.')
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 2, msg='Убедитесь, что можно создавать заметки с пустым слагом.')
        new_note = Note.objects.get(title=self.form_data['title'])
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug, msg='Проверьте правильность автоматического формирования слага, если он не был передан в форме.')
