from django.test import RequestFactory, TestCase
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.contrib.auth import logout, login
from django.core.exceptions import ObjectDoesNotExist

from .. import views
from .. import models
from .. import forms


class UserLoginViewTest(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username='dummy', password='123secret')

    def test_positive_login_view(self):
        response = self.client.post(path='/login/', data={'username': 'dummy', 'password': '123secret'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/book/list/')

    def test_negative_login_view(self):
        response = self.client.post(path='/login/', data={'username': 'any', 'password': 'any'})
        self.assertEqual(response.status_code, 200)


class UserLogoutViewTest(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username='dummy', password='123secret')

    def test_logout(self):
        self.assertTrue(self.user.is_authenticated)
        response = self.client.get(path='/logout/')
        self.assertRedirects(response, '/login/')
        self.assertEqual(response.status_code, 302)


class RegistrationTest(TestCase):
    def test_registration_valid_credentials(self):
        response = self.client.post(path='/register/', data={'username':'dummy_one', 'password1':'123secret',
                                                             'password2':'123secret'})
        logged = self.client.login(username='dummy_one', password='123secret')
        self.assertTrue(logged)
        authenticated = authenticate(username='dummy_one', password='123secret')
        self.assertTrue(get_user_model().objects.all().contains(authenticated))
        self.assertRedirects(response, '/login/')
        self.assertEqual(response.status_code, 302)

    def test_profile_creation_within_registration(self):
        response = self.client.post(path='/register/', data={'username':'dummy_one', 'password1':'123secret',
                                                             'password2':'123secret'})
        user = authenticate(username='dummy_one', password='123secret')
        self.assertIsNotNone(user.profile)
        self.assertEqual(str(user.profile), user.username[:10] + '_profile')

    def test_registration_invalid_credentials(self):
        response = self.client.post(path='/register/', data={'username': '', 'password1': '',
                                                             'password2': ''})
        self.assertFalse(response.context_data['form'].is_valid())
        self.assertEqual(response.status_code, 200)


class ProfileListViewTest(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username='dummy', password='123secret')

    def test_authenticated_view(self):
        logged = self.client.login(username='dummy', password='123secret')
        self.assertTrue(logged)
        response = self.client.get(path='/profile/list/')
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_view(self):
        self.client.logout()
        response = self.client.get(path='/profile/list/')
        self.assertRedirects(response, '/login/?next=/profile/list/', status_code=302)


class ProfileDetailViewTest(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username='dummy', password='123secret')
        models.Profile.objects.create(name=self.user.username, user=self.user)

    def test_authenticated_view(self):
        logged = self.client.login(username='dummy', password='123secret')
        self.assertTrue(logged)
        self.assertIsNotNone(self.user.profile)
        uuid = self.user.profile.id
        response = self.client.get(path='/profile/{}/'.format(uuid))
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_view(self):
        self.client.logout()
        uuid = self.user.profile.id
        response = self.client.get(path='/profile/{}/'.format(uuid))
        self.assertRedirects(response, '/login/?next=/profile/{}/'.format(uuid), status_code=302)


class ProfileUpdateViewTest(TestCase):
    def setUp(self) -> None:
        self.user1 = get_user_model().objects.create_user(username='dummy1', password='123secret')
        models.Profile.objects.create(name=self.user1.username, user=self.user1)

    def test_unauthenticated_view(self):
        self.client.logout()
        uuid = self.user1.profile.id
        response = self.client.get(path='/profile/{}/update/'.format(uuid))
        self.assertRedirects(response, '/login/?next=/profile/{}/update/'.format(uuid), status_code=302)

    def test_authenticated_view_access_not_profile_owner(self):
        user2 = get_user_model().objects.create_user(username='dummy2', password='123secret')
        models.Profile.objects.create(name=user2.username, user=user2)
        logged2 = self.client.login(username='dummy2', password='123secret')
        self.assertTrue(logged2)
        self.assertIsNotNone(user2.profile)
        uuid = self.user1.profile.id
        book1 = models.Book.objects.create(title='First Book')
        response = self.client.post(path='/profile/{}/update/'.format(uuid), data={'books': [book1.id]})
        self.assertEqual(response.status_code, 403)

    def test_authenticated_view_update_as_profile_owner(self):
        book1 = models.Book.objects.create(title='First Book')
        book2 = models.Book.objects.create(title='Second Book')
        logged1 = self.client.login(username='dummy1', password='123secret')
        self.assertTrue(logged1)
        self.assertIsNotNone(self.user1.profile)
        self.assertFalse(self.user1.profile.books.exists())
        uuid = self.user1.profile.id
        response = self.client.post(path='/profile/{}/update/'.format(uuid), data={'books': [book1.id, book2.id]})
        self.assertTrue(self.user1.profile.books.exists())
        self.assertTrue(self.user1.profile.books.contains(book1))
        self.assertTrue(self.user1.profile.books.contains(book2))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/profile/{}/'.format(uuid), status_code=302)

    def test_get_success_url(self):
        logged1 = self.client.login(username='dummy1', password='123secret')
        book1 = models.Book.objects.create(title='First Book')
        uuid = self.user1.profile.id
        response = self.client.post(path='/profile/{}/update/'.format(uuid), data={'books': [book1.id]})
        self.assertEqual(response.url, '/profile/{}/'.format(uuid))


class BookCreateViewTest(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username='dummy', password='123secret')
        models.Profile.objects.create(name=self.user.username, user=self.user)

    def test_creating_simple_book_authenticated(self):
        self.assertFalse(models.Book.objects.exists())
        logged = self.client.login(username='dummy', password='123secret')
        self.assertTrue(logged)
        response = self.client.post(path='/book/create/', data={'title': 'Hobbit'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/book/1/')
        self.assertTrue(models.Book.objects.exists())
        book = models.Book.objects.get(id=1)
        self.assertEqual(book.title, 'Hobbit')
        self.assertFalse(book.authors.exists())
        self.assertFalse(book.categories.exists())
        self.assertFalse(book.publisher)

    def test_creating_simple_book_unauthenticated(self):
        self.assertFalse(models.Book.objects.exists())
        self.client.logout()
        response = self.client.post(path='/book/create/', data={'title': 'Hobbit'})
        self.assertRedirects(response, '/login/?next=/book/create/', status_code=302)
        self.assertFalse(models.Book.objects.exists())

    def test_creating_complex_book_authenticated(self):
        self.assertFalse(models.Book.objects.exists())
        self.assertFalse(models.Author.objects.exists())
        self.assertFalse(models.Category.objects.exists())
        self.assertFalse(models.Publisher.objects.exists())
        logged = self.client.login(username='dummy', password='123secret')
        self.assertTrue(logged)
        response = self.client.post(path='/book/create/',
                                    data={'title': 'Hobbit', 'authors': 'J.R.R. Tolkien', 'categories': 'fantasy',
                                          'publisher': 'Pub Inc.', 'isbn10': '1234567890', 'isbn13': '1234567890123',
                                          'description': 'Great book!'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/book/1/')
        self.assertTrue(models.Book.objects.exists())
        book = models.Book.objects.get(id=1)
        self.assertEqual(book.title, 'Hobbit')
        self.assertTrue(models.Author.objects.get(name='J.R.R. Tolkien'))
        self.assertTrue(models.Category.objects.get(name='fantasy'))
        self.assertTrue(models.Publisher.objects.get(name='Pub Inc.'))

    def test_creating_complex_book_authenticated_with_existing_auth_cat_pub(self):
        author = models.Author.objects.create(name='J.R.R. Tolkien')
        category = models.Category.objects.create(name='fantasy')
        publisher = models.Publisher.objects.create(name='Pub Inc.')
        logged = self.client.login(username='dummy', password='123secret')
        self.assertTrue(models.Author.objects.get(name='J.R.R. Tolkien'))
        self.assertTrue(models.Category.objects.get(name='fantasy'))
        self.assertTrue(models.Publisher.objects.get(name='Pub Inc.'))
        self.assertTrue(logged)
        response = self.client.post(path='/book/create/',
                                    data={'title': 'Hobbit', 'authors': author.name, 'categories': category.name,
                                          'publisher': publisher.name,  'isbn10': '1234567890', 'isbn13': '1234567890123',
                                          'description': 'Great book!'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/book/1/')
        self.assertTrue(models.Book.objects.exists())
        book = models.Book.objects.get(id=1)
        self.assertTrue(book.authors.get(name='J.R.R. Tolkien'))
        self.assertTrue(book.categories.get(name='fantasy'))
        self.assertEqual(book.publisher.name, 'Pub Inc.')
        self.assertEqual(book.title, 'Hobbit')


class BookUpdateViewTest(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username='dummy', password='123secret')
        models.Profile.objects.create(name=self.user.username, user=self.user)
        self.publisher = models.Publisher.objects.create(name='Pub Inc.')
        self.authors = models.Author.objects.create(name='J.R.R. Tolkien')
        self.categories = models.Category.objects.create(name='fantasy')
        self.book = models.Book.objects.create(title='Hobbit')
        self.book.added_by = self.user.profile
        self.book.authors.set([self.authors])
        self.book.categories.set([self.categories])
        self.book.publisher = self.publisher
        self.book.save()

    def test_update_book_authenticated_user(self):
        logged = self.client.login(username='dummy', password='123secret')
        self.assertTrue(logged)
        authors = models.Author.objects.create(name='Frank Herbert')
        categories = models.Category.objects.create(name='sci-fi')
        publisher = models.Publisher.objects.create(name='Another Pub Inc.')
        response = self.client.post(path='/book/{}/update/'.format(self.book.id),
                                    data={'title': 'Dune', 'authors': authors.name,
                                          'categories': categories.name,
                                          'publisher': publisher.name})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/book/1/')
        book = models.Book.objects.get(id=1)
        self.assertEqual(book.title, 'Dune')
        self.assertTrue(book.authors.get(name='Frank Herbert'))
        self.assertTrue(book.categories.get(name='sci-fi'))
        self.assertEqual(book.publisher.name, 'Another Pub Inc.')

    def test_update_book_unauthenticated_user(self):
        self.client.logout()
        authors = models.Author.objects.create(name='Frank Herbert')
        categories = models.Category.objects.create(name='sci-fi')
        publisher = models.Publisher.objects.create(name='Another Pub Inc.')
        response = self.client.post(path='/book/{}/update/'.format(self.book.id),
                                    data={'title': 'Dune', 'authors': authors.id,
                                          'categories': categories.id,
                                          'publisher': publisher.id})
        self.assertRedirects(response, '/login/?next=/book/{}/update/'.format(self.book.id), status_code=302)
        book = models.Book.objects.get(id=1)
        self.assertEqual(book.title, 'Hobbit')
        self.assertTrue(book.authors.get(name='J.R.R. Tolkien'))
        self.assertTrue(book.categories.get(name='fantasy'))
        self.assertEqual(book.publisher.name, 'Pub Inc.')

    def test_get_success_url(self):
        logged = self.client.login(username='dummy', password='123secret')
        self.assertTrue(logged)
        authors = models.Author.objects.create(name='Frank Herbert')
        categories = models.Category.objects.create(name='sci-fi')
        publisher = models.Publisher.objects.create(name='Another Pub Inc.')
        response = self.client.post(path='/book/{}/update/'.format(self.book.id),
                                    data={'title': 'Dune', 'authors': authors.id,
                                          'categories': categories.id,
                                          'publisher': publisher.id})
        self.assertEqual(response.url, '/book/{}/'.format(self.book.id))


class BookDeleteViewTest(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username='dummy', password='123secret')
        models.Profile.objects.create(name=self.user.username, user=self.user)
        self.book = models.Book.objects.create(title='Hobbit', added_by=self.user.profile)

    def test_delete_existing_book_authenticated_user(self):
        self.assertTrue(models.Book.objects.exists())
        logged = self.client.login(username='dummy', password='123secret')
        self.assertTrue(logged)
        response = self.client.post(path='/book/{}/delete/'.format(self.book.id))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/book/list/')
        self.assertFalse(models.Book.objects.exists())

    def test_delete_existing_book_unauthenticated_user(self):
        self.assertTrue(models.Book.objects.get(id=1))
        self.client.logout()
        response = self.client.post(path='/book/{}/delete/'.format(self.book.id))
        self.assertRedirects(response, '/login/?next=/book/{}/delete/'.format(self.book.id))
        self.assertTrue(models.Book.objects.get(id=1))


class BookDetailViewTest(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username='dummy', password='123secret')
        models.Profile.objects.create(name=self.user.username, user=self.user)
        self.book = models.Book.objects.create(title='Hobbit', added_by=self.user.profile)

    def test_book_detail_view_valid_id(self):
        response = self.client.get(path='/book/{}/'.format(self.book.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object'].title, 'Hobbit')
        self.assertEqual(self.book, response.context['object'])
        self.assertIsInstance(response.context['object'], models.Book)

    def test_book_detail_view_invalid_id(self):
        response = self.client.get(path='/book/2/')
        self.assertEqual(response.status_code, 404)


class BookListViewTest(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username='dummy', password='123secret')
        models.Profile.objects.create(name=self.user.username, user=self.user)
        self.book1 = models.Book.objects.create(title='Hobbit', added_by=self.user.profile)
        self.book2 = models.Book.objects.create(title='Dune', added_by=self.user.profile)

    def test_book_list_view(self):
        response = self.client.get(path='/book/list/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.book1, response.context['object_list'])
        self.assertIn(self.book2, response.context['object_list'])

    def test_book_list_get_context_method(self):
        response = self.client.get(path='/book/list/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], forms.BookSearchForm)


class VoteCreateUpdateViewTest(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username='dummy', password='123secret')
        models.Profile.objects.create(name=self.user.username, user=self.user)
        self.book = models.Book.objects.create(title='Hobbit', added_by=self.user.profile)

    def test_adding_first_vote_authenticated_user(self):
        logged = self.client.login(username='dummy', password='123secret')
        self.assertTrue(logged)
        self.assertFalse(models.Vote.objects.all().exists())
        self.assertFalse(self.book.vote_set.all().exists())
        response = self.client.post(path='/book/{}/vote/'.format(self.book.id), data={'value': 5})
        self.assertRedirects(response, expected_url='/book/{}/'.format(self.book.id))
        self.assertTrue(models.Vote.objects.all().exists())
        self.assertTrue(self.book.vote_set.all().exists())
        self.assertEqual(self.book.vote_set.get(id=1).value, 5)
        self.assertEqual(self.book.vote_set.get(id=1).profile, self.user.profile)

    def test_adding_first_vote_authenticated_user_invalid_value(self):
        logged = self.client.login(username='dummy', password='123secret')
        self.assertTrue(logged)
        self.assertFalse(models.Vote.objects.all().exists())
        self.assertFalse(self.book.vote_set.all().exists())
        response = self.client.post(path='/book/{}/vote/'.format(self.book.id), data={'value': 12})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(models.Vote.objects.all().exists())
        self.assertTrue(self.book.vote_set.all().exists())
        self.assertIsNone(self.book.vote_set.get(id=1).value)

    def test_update_first_vote_authenticated_user(self):
        logged = self.client.login(username='dummy', password='123secret')
        self.assertTrue(logged)
        self.assertFalse(models.Vote.objects.all().exists())
        self.assertFalse(self.book.vote_set.all().exists())
        response = self.client.post(path='/book/{}/vote/'.format(self.book.id), data={'value': 9})
        self.assertRedirects(response, expected_url='/book/{}/'.format(self.book.id))
        self.assertTrue(models.Vote.objects.all().exists())
        self.assertTrue(self.book.vote_set.all().exists())
        self.assertEqual(self.book.vote_set.get(id=1).value, 9)
        self.assertEqual(self.book.vote_set.get(id=1).profile, self.user.profile)

    def test_adding_vote_unauthenticated_user(self):
        self.client.logout()
        self.assertFalse(models.Vote.objects.all().exists())
        self.assertFalse(self.book.vote_set.all().exists())
        response = self.client.post(path='/book/{}/vote/'.format(self.book.id), data={'value': 9})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/book/{}/vote/'.format(self.book.id))
        self.assertFalse(models.Vote.objects.all().exists())
        self.assertFalse(self.book.vote_set.all().exists())


class PublisherCreateViewTest(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username='dummy', password='123secret')
        models.Profile.objects.create(name=self.user.username, user=self.user)

    def test_publisher_creation_authenticated_user(self):
        logged = self.client.login(username='dummy', password='123secret')
        self.assertTrue(logged)
        self.assertFalse(models.Publisher.objects.all().exists())
        response = self.client.post(path='/publisher/create/', data={'name': 'Pub inc.'})
        self.assertTrue(models.Publisher.objects.all().exists())
        self.assertTrue(models.Publisher.objects.get(id=1))
        self.assertEqual(models.Publisher.objects.get(id=1).name, 'Pub inc.')

    def test_publisher_creation_unauthenticated_user(self):
        self.client.logout()
        self.assertFalse(models.Publisher.objects.all().exists())
        response = self.client.post(path='/publisher/create/', data={'name': 'Pub inc.'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/publisher/create/')
        self.assertFalse(models.Publisher.objects.all().exists())

    def test_get_success_url(self):
        logged = self.client.login(username='dummy', password='123secret')
        self.assertTrue(logged)
        response = self.client.post(path='/publisher/create/', data={'name': 'Pub inc.'})
        self.assertEqual(response.url, '/publisher/1/')


class PublisherUpdateViewTest(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username='dummy', password='123secret')
        models.Profile.objects.create(name=self.user.username, user=self.user)
        self.publisher = models.Publisher.objects.create(name='Pub Inc.')

    def test_publisher_update_authenticated_user(self):
        logged = self.client.login(username='dummy', password='123secret')
        self.assertTrue(logged)
        self.assertEqual(models.Publisher.objects.get(id=1).name, 'Pub Inc.')
        response = self.client.post(path='/publisher/{}/update/'.format(self.publisher.id),
                                    data={'name': 'Another Pub Inc.'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/publisher/1/')
        self.assertEqual(models.Publisher.objects.get(id=1).name, 'Another Pub Inc.')
        self.assertTrue(models.Publisher.objects.get(name='Another Pub Inc.'))

    def test_publisher_update_unauthenticated_user(self):
        self.client.logout()
        response = self.client.post(path='/publisher/{}/update/'.format(self.publisher.id),
                                    data={'name': 'Another Pub Inc.'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/publisher/{}/update/'.format(self.publisher.id))
        self.assertEqual(models.Publisher.objects.get(id=1).name, 'Pub Inc.')

    def test_get_success_url(self):
        logged = self.client.login(username='dummy', password='123secret')
        self.assertTrue(logged)
        response = self.client.post(path='/publisher/{}/update/'.format(self.publisher.id),
                                    data={'name': 'Another Pub Inc.'})
        self.assertEqual(response.url, '/publisher/1/')


class PublisherDeleteViewTest(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username='dummy', password='123secret')
        models.Profile.objects.create(name=self.user.username, user=self.user)
        self.publisher = models.Publisher.objects.create(name='Pub Inc.')

    def test_publisher_delete_authenticated_user(self):
        logged = self.client.login(username='dummy', password='123secret')
        self.assertTrue(logged)
        response = self.client.post(path='/publisher/{}/delete/'.format(self.publisher.id))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/publisher/list/')
        self.assertFalse(models.Publisher.objects.exists())

    def test_delete_publisher_unauthenticated_user(self):
        self.client.logout()
        response = self.client.post(path='/publisher/{}/delete/'.format(self.publisher.id))
        self.assertRedirects(response, '/login/?next=/publisher/{}/delete/'.format(self.publisher.id))
        self.assertTrue(models.Publisher.objects.exists())
        self.assertTrue(models.Publisher.objects.get(id=1))
        self.assertEqual(models.Publisher.objects.get(id=1).name, 'Pub Inc.')


class PublisherDetailViewTest(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username='dummy', password='123secret')
        models.Profile.objects.create(name=self.user.username, user=self.user)
        self.publisher = models.Publisher.objects.create(name='Pub Inc.')

    def test_publisher_detail_view_valid_id(self):
        response = self.client.get(path='/publisher/{}/'.format(self.publisher.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object'].name, 'Pub Inc.')
        self.assertEqual(self.publisher, response.context['object'])
        self.assertIsInstance(response.context['object'], models.Publisher)

    def test_publisher_detail_view_invalid_id(self):
        response = self.client.get(path='/publisher/2/')
        self.assertEqual(response.status_code, 404)


class PublisherListViewTest(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username='dummy', password='123secret')
        models.Profile.objects.create(name=self.user.username, user=self.user)
        self.pub1 = models.Publisher.objects.create(name='First Pub Inc.', added_by=self.user.profile)
        self.pub2 = models.Publisher.objects.create(name='Second Pub Inc.', added_by=self.user.profile)

    def test_publisher_list_view(self):
        response = self.client.get(path='/publisher/list/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.pub1, response.context['object_list'])
        self.assertIn(self.pub2, response.context['object_list'])

    def test_publisher_list_get_context_method(self):
        response = self.client.get(path='/publisher/list/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], forms.PublisherSearchForm)


class AuthorCreateViewTest(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username='dummy', password='123secret')
        models.Profile.objects.create(name=self.user.username, user=self.user)

    def test_author_creation_authenticated_user(self):
        logged = self.client.login(username='dummy', password='123secret')
        self.assertTrue(logged)
        self.assertFalse(models.Author.objects.all().exists())
        response = self.client.post(path='/author/create/', data={'name': 'J.R.R. Tolkien'})
        self.assertTrue(models.Author.objects.all().exists())
        self.assertTrue(models.Author.objects.get(id=1))
        self.assertEqual(models.Author.objects.get(id=1).name, 'J.R.R. Tolkien')

    def test_author_creation_unauthenticated_user(self):
        self.client.logout()
        self.assertFalse(models.Author.objects.all().exists())
        response = self.client.post(path='/author/create/', data={'name': 'J.R.R. Tolkien'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/author/create/')
        self.assertFalse(models.Author.objects.all().exists())

    def test_get_success_url(self):
        logged = self.client.login(username='dummy', password='123secret')
        self.assertTrue(logged)
        response = self.client.post(path='/author/create/', data={'name': 'J.R.R. Tolkien'})
        self.assertEqual(response.url, '/author/1/')


class AuthorUpdateViewTest(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username='dummy', password='123secret')
        models.Profile.objects.create(name=self.user.username, user=self.user)
        self.author = models.Author.objects.create(name='J.R.R. Tolkien')

    def test_author_update_authenticated_user(self):
        logged = self.client.login(username='dummy', password='123secret')
        self.assertTrue(logged)
        self.assertEqual(models.Author.objects.get(id=1).name, 'J.R.R. Tolkien')
        response = self.client.post(path='/author/{}/update/'.format(self.author.id),
                                    data={'name': 'Frank Herbert'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/author/1/')
        self.assertEqual(models.Author.objects.get(id=1).name, 'Frank Herbert')
        self.assertTrue(models.Author.objects.get(name='Frank Herbert'))

    def test_author_update_unauthenticated_user(self):
        self.client.logout()
        response = self.client.post(path='/author/{}/update/'.format(self.author.id),
                                    data={'name': 'Frank Herbert'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/author/{}/update/'.format(self.author.id))
        self.assertEqual(models.Author.objects.get(id=1).name, 'J.R.R. Tolkien')

    def test_get_success_url(self):
        logged = self.client.login(username='dummy', password='123secret')
        self.assertTrue(logged)
        response = self.client.post(path='/author/{}/update/'.format(self.author.id),
                                    data={'name': 'Frank Herbert'})
        self.assertEqual(response.url, '/author/1/')


class AuthorDeleteViewTest(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username='dummy', password='123secret')
        models.Profile.objects.create(name=self.user.username, user=self.user)
        self.author = models.Author.objects.create(name='J.R.R. Tolkien')

    def test_author_delete_authenticated_user(self):
        logged = self.client.login(username='dummy', password='123secret')
        self.assertTrue(logged)
        response = self.client.post(path='/author/{}/delete/'.format(self.author.id))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/author/list/')
        self.assertFalse(models.Author.objects.exists())

    def test_delete_publisher_unauthenticated_user(self):
        self.client.logout()
        response = self.client.post(path='/publisher/{}/delete/'.format(self.author.id))
        self.assertRedirects(response, '/login/?next=/publisher/{}/delete/'.format(self.author.id))
        self.assertTrue(models.Author.objects.exists())
        self.assertTrue(models.Author.objects.get(id=1))
        self.assertEqual(models.Author.objects.get(id=1).name, 'J.R.R. Tolkien')

    def test_delete_publisher_get_success_url(self):
        logged = self.client.login(username='dummy', password='123secret')
        self.assertTrue(logged)
        response = self.client.post(path='/author/{}/delete/'.format(self.author.id))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/author/list/')


class AuthorDetailViewTest(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username='dummy', password='123secret')
        models.Profile.objects.create(name=self.user.username, user=self.user)
        self.author = models.Author.objects.create(name='J.R.R. Tolkien')

    def test_author_detail_view_valid_id(self):
        response = self.client.get(path='/author/{}/'.format(self.author.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object'].name, 'J.R.R. Tolkien')
        self.assertEqual(self.author, response.context['object'])
        self.assertIsInstance(response.context['object'], models.Author)

    def test_author_detail_view_invalid_id(self):
        response = self.client.get(path='/author/2/')
        self.assertEqual(response.status_code, 404)


class AuthorListViewTest(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username='dummy', password='123secret')
        models.Profile.objects.create(name=self.user.username, user=self.user)
        self.author1 = models.Author.objects.create(name='J.R.R. Tolkien', added_by=self.user.profile)
        self.author2 = models.Author.objects.create(name='Frank Herbert.', added_by=self.user.profile)

    def test_author_list_view(self):
        response = self.client.get(path='/author/list/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.author1, response.context['object_list'])
        self.assertIn(self.author2, response.context['object_list'])

    def test_author_list_get_context_method(self):
        response = self.client.get(path='/author/list/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], forms.AuthorSearchForm)


class CategoryCreateViewTest(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username='dummy', password='123secret')
        models.Profile.objects.create(name=self.user.username, user=self.user)

    def test_category_creation_authenticated_user(self):
        logged = self.client.login(username='dummy', password='123secret')
        self.assertTrue(logged)
        self.assertFalse(models.Category.objects.all().exists())
        response = self.client.post(path='/category/create/', data={'name': 'fantasy'})
        self.assertTrue(models.Category.objects.all().exists())
        self.assertTrue(models.Category.objects.get(id=1))
        self.assertEqual(models.Category.objects.get(id=1).name, 'fantasy')

    def test_category_creation_unauthenticated_user(self):
        self.client.logout()
        self.assertFalse(models.Category.objects.all().exists())
        response = self.client.post(path='/category/create/', data={'name': 'fantasy'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/category/create/')
        self.assertFalse(models.Category.objects.all().exists())

    def test_get_success_url(self):
        logged = self.client.login(username='dummy', password='123secret')
        self.assertTrue(logged)
        response = self.client.post(path='/category/create/', data={'name': 'fantasy'})
        self.assertEqual(response.url, '/category/1/')


class CategoryUpdateViewTest(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username='dummy', password='123secret')
        models.Profile.objects.create(name=self.user.username, user=self.user)
        self.category = models.Category.objects.create(name='fantasy')

    def test_category_update_authenticated_user(self):
        logged = self.client.login(username='dummy', password='123secret')
        self.assertTrue(logged)
        self.assertEqual(models.Category.objects.get(id=1).name, 'fantasy')
        response = self.client.post(path='/category/{}/update/'.format(self.category.id),
                                    data={'name': 'comedy'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/category/1/')
        self.assertEqual(models.Category.objects.get(id=1).name, 'comedy')
        self.assertTrue(models.Category.objects.get(name='comedy'))

    def test_category_update_unauthenticated_user(self):
        self.client.logout()
        response = self.client.post(path='/category/{}/update/'.format(self.category.id),
                                    data={'name': 'comedy'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/category/{}/update/'.format(self.category.id))
        self.assertEqual(models.Category.objects.get(id=1).name, 'fantasy')

    def test_get_success_url(self):
        logged = self.client.login(username='dummy', password='123secret')
        self.assertTrue(logged)
        response = self.client.post(path='/category/{}/update/'.format(self.category.id),
                                    data={'name': 'comedy'})
        self.assertEqual(response.url, '/category/1/')


class CategoryDeleteViewTest(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username='dummy', password='123secret')
        models.Profile.objects.create(name=self.user.username, user=self.user)
        self.category = models.Category.objects.create(name='fantasy')

    def test_category_delete_authenticated_user(self):
        logged = self.client.login(username='dummy', password='123secret')
        self.assertTrue(logged)
        response = self.client.post(path='/category/{}/delete/'.format(self.category.id))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/category/list/')
        self.assertFalse(models.Category.objects.exists())

    def test_delete_publisher_unauthenticated_user(self):
        self.client.logout()
        response = self.client.post(path='/publisher/{}/delete/'.format(self.category.id))
        self.assertRedirects(response, '/login/?next=/publisher/{}/delete/'.format(self.category.id))
        self.assertTrue(models.Category.objects.exists())
        self.assertTrue(models.Category.objects.get(id=1))
        self.assertEqual(models.Category.objects.get(id=1).name, 'fantasy')

    def test_delete_publisher_get_success_url(self):
        logged = self.client.login(username='dummy', password='123secret')
        self.assertTrue(logged)
        response = self.client.post(path='/category/{}/delete/'.format(self.category.id))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/category/list/')


class CategoryDetailViewTest(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username='dummy', password='123secret')
        models.Profile.objects.create(name=self.user.username, user=self.user)
        self.category = models.Category.objects.create(name='fantasy')

    def test_category_detail_view_valid_id(self):
        response = self.client.get(path='/category/{}/'.format(self.category.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object'].name, 'fantasy')
        self.assertEqual(self.category, response.context['object'])
        self.assertIsInstance(response.context['object'], models.Category)

    def test_category_detail_view_invalid_id(self):
        response = self.client.get(path='/category/2/')
        self.assertEqual(response.status_code, 404)


class CategoryListViewTest(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username='dummy', password='123secret')
        models.Profile.objects.create(name=self.user.username, user=self.user)
        self.category1 = models.Category.objects.create(name='fantasy', added_by=self.user.profile)
        self.category2 = models.Category.objects.create(name='comedy', added_by=self.user.profile)

    def test_category_list_view(self):
        response = self.client.get(path='/category/list/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.category1, response.context['object_list'])
        self.assertIn(self.category2, response.context['object_list'])

    def test_category_list_get_context_method(self):
        response = self.client.get(path='/category/list/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], forms.CategorySearchForm)