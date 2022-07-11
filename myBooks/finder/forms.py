from datetime import date
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from . import models


class BookCreateForm(forms.ModelForm):
    authors = forms.CharField(label='Author', max_length=100, required=False,
                              widget=forms.TextInput(attrs={'placeholder': 'J.R.R. Tolkien',
                                                            'extra': models.Author.objects.all()}))
    categories = forms.CharField(label='Category', max_length=100, required=False,
                                 widget=forms.TextInput(attrs={'placeholder': 'fantasy, children',
                                                               'extra': models.Category.objects.all()}))
    publisher = forms.CharField(label='Publisher', max_length=100, required=False,
                                widget=forms.TextInput(attrs={'placeholder': 'Mordor Inc.',
                                                              'extra': models.Publisher.objects.all()}))

    class Meta:
        model = models.Book
        fields = ['title', 'year', 'isbn', 'description', 'thumbnail']
        labels = {
            'isbn': 'ISBN',
        }
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Hobbit'}),
            'isbn': forms.TextInput(attrs={'placeholder': '1234567890123'}),
            'year': forms.NumberInput(attrs={'placeholder': '1937'}),
            'description': forms.Textarea(attrs={'placeholder': 'A great tale!'}),
            'thumbnail': forms.Textarea(attrs={'placeholder': 'https://example.jpg'}),
        }

    field_order = ['title', 'authors', 'categories', 'publisher', 'year', 'isbn', 'description', 'thumbnail']


class BookSearchForm(forms.Form):
    title = forms.CharField(label='Title', max_length=100, required=False, widget=forms.TextInput(
        attrs={'placeholder': 'Hobbit'}))
    authors = forms.CharField(label='Authors:', max_length=100, required=False, widget=forms.TextInput(
        attrs={'placeholder': 'J.R.R. Tolkien', 'extra': models.Author.objects.all()}))
    categories = forms.CharField(label='Categories', max_length=100, required=False, widget=forms.TextInput(
        attrs={'placeholder': 'fantasy, children', 'extra': models.Category.objects.all()}))
    publisher = forms.CharField(label='Publisher', max_length=100, required=False, widget=forms.TextInput(
        attrs={'placeholder': 'Mordor Inc.', 'extra': models.Publisher.objects.all()}))
    year = forms.IntegerField(label='Year', min_value=1800, max_value=date.today().year, required=False,
                              widget=forms.NumberInput(attrs={'placeholder': '1937'}))
    isbn = forms.CharField(label='ISBN', required=False, widget=forms.TextInput(
        attrs={'placeholder': '1234567890123'}))


class NameSearchForm(forms.Form):
    name = forms.CharField(label='Name', max_length=100, required=False)


class AuthorSearchForm(forms.Form):
    name = forms.CharField(label='Name', max_length=100, required=False,
                           widget=forms.TextInput(attrs={'placeholder': 'J.R.R. Tolkien',
                                                         'extra': models.Author.objects.all()}))


class PublisherSearchForm(forms.Form):
    name = forms.CharField(label='Publisher', max_length=100, required=False,
                           widget=forms.TextInput(attrs={'placeholder': 'Mordor Inc.',
                                                         'extra': models.Publisher.objects.all()}))


class CategorySearchForm(forms.Form):
    name = forms.CharField(label='Category', max_length=100, required=False,
                           widget=forms.TextInput(attrs={'placeholder': 'fantasy, children',
                                                         'extra': models.Category.objects.all()}))


class ProfileSearchForm(forms.Form):
    name = forms.CharField(label='Profile', max_length=100, required=False,
                           widget=forms.TextInput(attrs={'placeholder': '',
                                                         'extra': models.Profile.objects.all()}))


class VoteForm(forms.ModelForm):
    class Meta:
        model = models.Vote
        fields = ['value']


class ProfileForm(forms.ModelForm):
    class Meta:
        model = models.Profile
        fields = ['name', 'books', 'friends']


class ProfileFriendsForm(forms.ModelForm):
    FRIENDS_CHOICES = [(False, 'No'), (True, 'Yes')]
    are_friends = forms.BooleanField(required=False, label='Friends', widget=forms.Select(choices=FRIENDS_CHOICES))

    class Meta:
        model = models.Profile
        fields = []


class ProfileBooksOwnedForm(forms.ModelForm):
    OWNED_CHOICES = [(False, 'No'), (True, 'Yes')]
    owned = forms.BooleanField(required=False, label='Owned', widget=forms.Select(choices=OWNED_CHOICES))

    class Meta:
        model = models.Profile
        fields = []


class GoogleBooksForm(forms.Form):
    title = forms.CharField(label='Title', max_length=100, required=False,
                            widget=forms.TextInput(attrs={'placeholder': 'Hobbit'}))
    authors = forms.CharField(label='Authors', max_length=100, required=False,
                              widget=forms.TextInput(attrs={'placeholder': 'J.R.R. Tolkien'}))
    publisher = forms.CharField(label='Publisher', max_length=100, required=False,
                                widget=forms.TextInput(attrs={'placeholder': 'Mordor Inc.'}))
    isbn = forms.CharField(label='ISBN', max_length=13, required=False,
                           widget=forms.TextInput(attrs={'placeholder': '9876543210123'}))


# class CreateUserForm(UserCreationForm):
#     class Meta:
#         model = User
#         fields = ['username']
#         widgets = {
#             'username': forms.TextInput(
#                 attrs={'style': 'max-width: 300px;', 'class': 'form-control'})}
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields['password1'].widget.attrs.update(
#             {'style': 'max-width: 300px', 'class': 'form-control'})
#         self.fields['password2'].widget.attrs.update(
#             {'style': 'max-width: 300px', 'class': 'form-control'})
#
#
# class LoginForm(AuthenticationForm):
#     def __init__(self, request=None, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields['username'].widget.attrs.update(
#             {'style': 'max-width: 300px', 'class': 'form-control'})
#         self.fields['password'].widget.attrs.update(
#             {'style': 'max-width: 300px', 'class': 'form-control'})
