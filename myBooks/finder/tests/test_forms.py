from django.test import RequestFactory, TestCase
from ..forms import BookCreateForm, BookSearchForm, NameSearchForm


class BookCreateFormTest(TestCase):
    def test_book_create_form_valid(self):
        form_data = {'title': 'Hobbit', 'year': 2000, 'new_authors': 'J.R.R. Tolkien', 'new_categories': 'fantasy',
                     'new_publisher': 'Book Pub inc.', 'isbn10': '1234567890', 'isbn13': '1234567890123',
                     'description': 'Great book!'}
        form = BookCreateForm(data=form_data)
        self.assertTrue(form.is_valid())


class BookSearchFormTest(TestCase):
    def test_book_search_form_valid(self):
        form_data = {'title': 'Hobbit', 'year': 2000, 'authors': 'J.R.R. Tolkien', 'categories': 'fantasy',
                     'publisher': 'Book Pub inc.', 'isbn10': '1234567890', 'isbn13': '12345678901'}
        form = BookSearchForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_empty_book_search_form(self):
        form = BookSearchForm()
        self.assertFalse(form.is_bound)
        self.assertFalse(form.is_valid())


class NameSearchFormTest(TestCase):
    def test_name_form_valid(self):
        form = NameSearchForm(data={'name': 'J.R.R. Tolkien'})
        self.assertTrue(form.is_valid())
