from django.test import RequestFactory, TestCase
from django.contrib.auth.models import User, AnonymousUser
from django.core.exceptions import ObjectDoesNotExist
from ..models import Book, Author, Category, Publisher, Profile, Vote


class BookCRUDTest(TestCase):
    def test_simple_book_creation(self):
        book = Book.objects.create(title='Hobbit')
        self.assertIsNotNone(book)
        self.assertIsInstance(book, Book)
        self.assertEqual(book.title, 'Hobbit')
        self.assertFalse(book.authors.exists())
        self.assertFalse(book.categories.exists())
        self.assertIsNone(book.publisher)

    def test_simple_book_update(self):
        book = Book.objects.create(title='Hobbit')
        book.title = "Lord Of The Rings"
        book.save()
        self.assertEqual(book.title, 'Lord Of The Rings')

    def test_simple_book_retrieving(self):
        book_created = Book.objects.create(title='Hobbit')
        book_retrieved = Book.objects.get(title='Hobbit')
        self.assertEqual(book_retrieved.id, book_created.id)

    def test_simple_book_deleting(self):
        book = Book.objects.create(title='Hobbit')
        id_of_book = book.id
        book.delete()
        self.assertFalse(Book.objects.filter(title='Hobbit').exists())
        self.assertFalse(Book.objects.filter(id=id_of_book).exists())

    def test_full_book_creation(self):
        author = Author.objects.create(name='J.R.R. Tolkien')
        category = Category.objects.create(name='fantasy')
        publisher = Publisher.objects.create(name='BookPub inc.')
        book = Book.objects.create(title='Hobbit', year=2000, isbn='1234567890123', description='Great book!')
        self.assertIsNotNone(book)
        self.assertIsInstance(book, Book)
        self.assertEqual(book.title, 'Hobbit')
        self.assertEqual(book.year, 2000)
        self.assertIsNotNone(book.description)

        book.authors.set([author])
        book.categories.set([category])
        book.publisher = publisher
        book.save()
        self.assertIsNotNone(book.publisher)
        self.assertEqual(book.publisher.name, 'BookPub inc.')
        self.assertTrue(book.authors.exists())
        self.assertTrue(book.authors.filter(name='J.R.R. Tolkien').exists())
        self.assertTrue(book.categories.exists())
        self.assertTrue(book.categories.filter(name='fantasy').exists())

    def test_full_book_update(self):
        author = Author.objects.create(name='J.R.R. Tolkien')
        category = Category.objects.create(name='fantasy')
        publisher = Publisher.objects.create(name='BookPub inc.')
        book = Book.objects.create(title='Hobbit', year=2000, isbn='1234567890123', description='Great book!')
        book.authors.set([author])
        book.categories.set([category])
        book.publisher = publisher
        book.save()

        book.title = 'Quo Vadis'
        book.authors.set([Author.objects.create(name='Henryk Sienkiewicz')])
        book.categories.set([Category.objects.create(name='historical')])
        book.publisher = Publisher.objects.create(name='Another inc.')
        book.year = 1975
        book.isbn10 = '9876543210'
        book.isbn13 = '2109876543210'
        book.description = 'A great historical novel'
        book.save()
        self.assertEqual(book.title, 'Quo Vadis')
        self.assertEqual(book.publisher.name, 'Another inc.')
        self.assertTrue(book.authors.filter(name='Henryk Sienkiewicz').exists())
        self.assertFalse(book.authors.filter(name='J.R.R. Tolkien').exists())
        self.assertTrue(book.categories.filter(name='historical').exists())
        self.assertFalse(book.categories.filter(name='fantasy').exists())


class AuthorCRUDTest(TestCase):
    def setUp(self) -> None:
        self.author = Author.objects.create(name='Henryk Sienkiewicz')

    def test_author_creation(self):
        self.assertIsNotNone(self.author)
        self.assertIsInstance(self.author, Author)
        self.assertEqual(self.author.name, 'Henryk Sienkiewicz')

    def test_author_retrieving(self):
        author_retrieved = Author.objects.get(name='Henryk Sienkiewicz')
        self.assertEqual(self.author.id, author_retrieved.id)

    def test_author_name_update(self):
        self.author.name = 'Witold Gombrowicz'
        self.author.save()
        self.assertEqual(self.author.name, 'Witold Gombrowicz')

    def test_author_deleting(self):
        author_id = self.author.id
        self.author.delete()
        self.assertFalse(Author.objects.filter(name='Henryk Sienkiewicz').exists())
        self.assertFalse(Author.objects.filter(id=author_id).exists())

    def test_author_books_setting(self):
        self.assertFalse(self.author.book_set.exists())
        book1 = Book.objects.create(title='Book One')
        book2 = Book.objects.create(title='Book Two')
        self.author.book_set.set([book1, book2])
        self.assertTrue(self.author.book_set.exists())
        self.assertTrue(self.author.book_set.contains(book1))
        self.assertTrue(self.author.book_set.contains(book2))


class CategoryCRUDTest(TestCase):
    def setUp(self) -> None:
        self.category = Category.objects.create(name='fantasy')

    def test_category_creation(self):
        self.assertIsNotNone(self.category)
        self.assertIsInstance(self.category, Category)
        self.assertEqual(self.category.name, 'fantasy')

    def test_category_retrieving(self):
        category_retrieved = Category.objects.get(name='fantasy')
        self.assertEqual(self.category.id, category_retrieved.id)

    def test_category_name_update(self):
        self.category.name = 'comedy'
        self.category.save()
        self.assertEqual(self.category.name, 'comedy')

    def test_category_books_setting(self):
        self.assertFalse(self.category.book_set.exists())
        book1 = Book.objects.create(title='Book One')
        book2 = Book.objects.create(title='Book Two')
        self.category.book_set.set([book1, book2])
        self.assertTrue(self.category.book_set.exists())
        self.assertTrue(self.category.book_set.contains(book1))
        self.assertTrue(self.category.book_set.contains(book2))

    def test_category_deleting(self):
        category_id = self.category.id
        self.category.delete()
        self.assertFalse(Category.objects.filter(name='fantasy').exists())
        self.assertFalse(Category.objects.filter(id=category_id).exists())


class PublisherCRUDTest(TestCase):
    def setUp(self) -> None:
        self.publisher = Publisher.objects.create(name='Book Pub inc.')

    def test_publisher_creation(self):
        self.assertIsNotNone(self.publisher)
        self.assertIsInstance(self.publisher, Publisher)
        self.assertEqual(self.publisher.name, 'Book Pub inc.')

    def test_publisher_retrieving(self):
        publisher_retrieved = Publisher.objects.get(name='Book Pub inc.')
        self.assertEqual(self.publisher.id, publisher_retrieved.id)

    def test_publisher_name_update(self):
        self.publisher.name = 'Else Pub co.'
        self.publisher.save()
        self.assertEqual(self.publisher.name, 'Else Pub co.')

    def test_publisher_books_setting(self):
        self.assertFalse(self.publisher.book_set.exists())
        book1 = Book.objects.create(title='Book One')
        book2 = Book.objects.create(title='Book Two')
        self.publisher.book_set.set([book1, book2])
        self.assertTrue(self.publisher.book_set.exists())
        self.assertTrue(self.publisher.book_set.contains(book1))
        self.assertTrue(self.publisher.book_set.contains(book2))

    def test_publisher_deleting(self):
        publisher_id = self.publisher.id
        self.publisher.delete()
        self.assertFalse(Publisher.objects.filter(name='Book Pub inc.').exists())
        self.assertFalse(Publisher.objects.filter(id=publisher_id).exists())


class ProfileCRUDTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username='Dummy One', password='secret123')

    def test_profile_creation(self):
        profile = Profile.objects.create(user=self.user, name='Dummy')
        self.assertIsNotNone(profile)
        self.assertIsInstance(profile, Profile)
        self.assertEqual(profile.user, self.user)

    def test_profile_retrieving(self):
        profile_created = Profile.objects.create(user=self.user, name='Dummy')
        profile_retrieved = Profile.objects.get(user=self.user)
        self.assertEqual(profile_created.id, profile_retrieved.id)

    def test_profile_setting_books(self):
        profile = Profile.objects.create(user=self.user, name='Dummy')
        self.assertFalse(profile.books.exists())
        book1 = Book.objects.create(title='Book One')
        book2 = Book.objects.create(title='Book Two')
        profile.books.set([book1, book2])
        self.assertTrue(profile.books.exists())
        self.assertTrue(profile.books.contains(book1))
        self.assertTrue(profile.books.contains(book2))

    def test_profile_deleting_together_with_user_deletion(self):
        user_id = self.user.id
        profile = Profile.objects.create(user=self.user, name='Dummy')
        profile_id = profile.id
        self.assertIsNotNone(profile)
        self.assertTrue(Profile.objects.filter(id=profile_id).exists())
        self.user.delete()
        self.assertFalse(User.objects.filter(id=user_id).exists())
        self.assertFalse(Profile.objects.filter(id=profile_id).exists())


class VoteCRUDTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username='Dummy One', password='secret123')
        self.profile = Profile.objects.create(user=self.user, name='Dummy')
        self.book1 = Book.objects.create(title='Book One')

    def test_vote_creation(self):
        vote = Vote.objects.create(profile=self.profile, book=self.book1, value=7.5)
        self.assertIsNotNone(vote)
        self.assertEqual(vote.value, 7.5)
        self.assertEqual(vote.profile, self.profile)
        self.assertEqual(vote.book, self.book1)

    def test_vote_retrieving(self):
        vote = Vote.objects.create(profile=self.profile, book=self.book1, value=7.5)
        vote_id = vote.id
        self.assertTrue(Vote.objects.all().contains(vote))
        self.assertEqual(Vote.objects.get(profile=self.profile, book=self.book1).id, vote_id)

    def test_vote_updating(self):
        vote = Vote.objects.create(profile=self.profile, book=self.book1, value=7.5)
        book2 = Book.objects.create(title='Book Two')
        vote.value = 5.5
        vote.book = book2
        vote.save()
        self.assertEqual(vote.book, book2)
        self.assertEqual(vote.value, 5.5)

    def test_vote_deletion(self):
        vote = Vote.objects.create(profile=self.profile, book=self.book1, value=7.5)
        vote_id = vote.id
        vote.delete()
        self.assertFalse(Vote.objects.filter(id=vote_id).exists())
        self.assertIsNone(vote.id)
