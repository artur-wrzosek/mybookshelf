from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormMixin, FormView
from django.views.generic.list import ListView
from django.urls import reverse, reverse_lazy
from django.forms.models import model_to_dict
from django.core.exceptions import ObjectDoesNotExist

from . import models
from . import forms

import requests


class RegistrationView(CreateView):
    form_class = forms.UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'finder/register.html'

    def form_valid(self, form):
        user = form.save()
        models.Profile.objects.create(name=form.cleaned_data['username'], user=user)
        return super().form_valid(form)


class UserLoginView(LoginView):
    form_class = forms.AuthenticationForm
    template_name = 'finder/login.html'
    next_page = reverse_lazy('book-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_form_kwargs(self):
        return super().get_form_kwargs()


class UserLogoutView(LogoutView):
    template_name = 'finder/logout.html'
    next_page = reverse_lazy('login')


class ProfileDetailView(LoginRequiredMixin, DetailView):
    model = models.Profile
    login_url = reverse_lazy('login')
    pk_url_kwarg = 'uuid'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object in self.request.user.profile.friends.all():
            context['friends_form'] = forms.ProfileFriendsForm(data={'are_friends': True})
        else:
            context['friends_form'] = forms.ProfileFriendsForm(data={'are_friends': False})
        return context


class ProfileListView(LoginRequiredMixin, ListView):
    model = models.Profile
    login_url = reverse_lazy('login')
    template_name = 'finder/profile_list.html'
    form_class = forms.ProfileSearchForm
    ordering = ['name']
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = self.form_class(self.request.GET)
        context['form'] = form
        q = self.request.GET.copy()
        q.pop(self.page_kwarg, None)
        context['q'] = q.urlencode()
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        if 'name' in self.request.GET:
            queryset = queryset.filter(name__icontains=self.request.GET.get('name'))
        return queryset


class ProfileUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = models.Profile
    form_class = forms.ProfileForm
    pk_url_kwarg = 'uuid'
    login_url = reverse_lazy('login')
    template_name = 'finder/profile_update.html'
    permission_denied_message = 'You have no power here!'

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        elif self.request.user.is_authenticated:
            return self.kwargs['uuid'] == self.request.user.profile.id
        return False

    def get_success_url(self):
        return reverse('profile-detail', args=(self.object.pk,))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def form_valid(self, form):
        profile = form.save(commit=False)
        if 'name' in form.changed_data:
            profile.user.username = form.cleaned_data['name']
            profile.user.save()
        if 'books' in form.changed_data:
            profile.books.set(form.cleaned_data['books'])
        if 'friends' in form.changed_data:
            profile.friends.set(form.cleaned_data['friends'])
        profile.save()
        return redirect(self.get_success_url())

    def get_form_kwargs(self):
        return super().get_form_kwargs()


class ProfileFriendsUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = models.Profile
    form_class = forms.ProfileFriendsForm
    pk_url_kwarg = 'uuid'
    login_url = reverse_lazy('login')

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        elif self.request.user.is_authenticated:
            return self.kwargs['uuid'] == self.request.user.profile.id
        return False

    def get_success_url(self):
        if self.kwargs.get('uuid2', None):
            return reverse('profile-detail', args=(self.kwargs.get('uuid2'),))
        return reverse('profile-detail', args=(self.object.pk,))

    def form_valid(self, form):
        profile = form.save(commit=False)
        if 'are_friends' in self.request.POST:
            if self.request.POST['are_friends'] == 'True':
                profile.friends.add(self.kwargs.get('uuid2'))
            elif self.request.POST['are_friends'] == 'False':
                profile.friends.remove(self.kwargs.get('uuid2'))
        profile.save()
        return redirect(self.get_success_url())


class ProfileBooksOwnedView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = models.Profile
    form_class = forms.ProfileBooksOwnedForm
    pk_url_kwarg = 'uuid'
    login_url = reverse_lazy('login')

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        elif self.request.user.is_authenticated:
            return self.kwargs['uuid'] == self.request.user.profile.id
        return False

    def get_success_url(self):
        if self.kwargs.get('pk', None):
            return reverse('book-detail', args=(self.kwargs.get('pk'),))
        return reverse('profile-detail', args=(self.object.pk,))

    def form_valid(self, form):
        profile = form.save(commit=False)
        if 'owned' in self.request.POST:
            if self.request.POST['owned'] == 'True':
                profile.books.add(self.kwargs.get('pk'))
            elif self.request.POST['owned'] == 'False':
                profile.books.remove(self.kwargs.get('pk'))
        profile.save()
        return redirect(self.get_success_url())


class GoogleBooksSerializerMixin:
    @staticmethod
    def gbooks_serializer(gbook):
        book = dict()
        book['title'] = gbook['volumeInfo'].get('title', '')
        book['authors'] = gbook['volumeInfo'].get('authors', '')
        book['publisher'] = gbook['volumeInfo'].get('publisher', '')
        if 'industryIdentifiers' in gbook['volumeInfo']:
            for identifier in gbook['volumeInfo']['industryIdentifiers']:
                if identifier['type'] == 'ISBN_13':
                    book['isbn'] = identifier['identifier']
                    break
                elif identifier['type'] == 'ISBN_10':
                    book['isbn'] = identifier['identifier']
        else:
            book['isbn'] = ''
        book['description'] = gbook['volumeInfo'].get('description', '')
        if 'imageLinks' in gbook['volumeInfo']:
            book['thumbnail'] = gbook['volumeInfo']['imageLinks'].get('thumbnail', '')
        else:
            book['thumbnail'] = ''
        book['gbooks_rank'] = gbook['volumeInfo'].get('averageRating', '')
        book['gbooks_link'] = gbook['volumeInfo'].get('previewLink', '')
        book['gbooks_id'] = gbook.get('id', '')
        book['year'] = gbook['volumeInfo'].get('publishedDate', '')[:4]
        return book


class BookCreateView(GoogleBooksSerializerMixin, LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = models.Book
    form_class = forms.BookCreateForm
    login_url = reverse_lazy('login')
    success_message = '%(title)s was created successfully!'
    template_name = 'finder/book_create.html'

    def get_success_url(self):
        return reverse('book-detail', args=(self.object.pk,))

    def form_valid(self, form):
        new_book = form.save(commit=False)
        new_book.added_by = self.request.user.profile

        publisher = form.cleaned_data.pop('publisher', None)
        if publisher:
            pub, pub_created = models.Publisher.objects.get_or_create(
                name=publisher,
                defaults={'added_by': self.request.user.profile})
            new_book.publisher_id = pub.pk
        new_book.save()

        authors_list = form.cleaned_data.pop('authors', None)
        if authors_list:
            for author in authors_list.split(sep=','):
                auth, auth_created = models.Author.objects.get_or_create(
                    name=author.strip(),
                    defaults={'added_by': self.request.user.profile})
                new_book.authors.add(auth.id)
            new_book.save()

        categories_list = form.cleaned_data.pop('categories', None)
        if categories_list:
            for category in categories_list.split(sep=','):
                cat, cat_created = models.Category.objects.get_or_create(
                    name=category.strip(),
                    defaults={'added_by': self.request.user.profile})
                new_book.categories.add(cat.id)
            new_book.save()

        if 'owned' in self.request.POST:
            if self.request.POST['owned'] == 'True':
                self.request.user.profile.books.add(new_book.id)

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['owned_form'] = forms.ProfileBooksOwnedForm(data={'owned': False})
        return context

    def get_initial(self):
        initial = super().get_initial()
        if 'gbooks_id' in self.kwargs:
            response = requests.get(url='https://www.googleapis.com/books/v1/volumes/' + self.kwargs.get('gbooks_id'))
            if response.status_code == 200:
                initial = self.gbooks_serializer(response.json())
                initial['authors'] = ','.join(initial['authors'])
        return initial


class BookUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = models.Book
    form_class = forms.BookCreateForm
    template_name = 'finder/book_update.html'
    login_url = reverse_lazy('login')
    success_message = '%(title)s was updated successfully!'
    # permission_denied_message = "Books can be updated only by person who added them to database!"

    def get_success_url(self):
        return reverse('book-detail', args=(self.object.pk,))

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(**self.get_form_kwargs())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_initial(self):
        initial = super().get_initial()
        instance = self.get_object()
        initial['authors'] = ', '.join([author.name for author in getattr(instance, 'authors').all()])
        initial['categories'] = ', '.join([category.name for category in getattr(instance, 'categories').all()])
        initial['publisher'] = getattr(instance, 'publisher').name if getattr(instance, 'publisher', None) else None
        return initial

    def form_valid(self, form):
        updated_book = form.save(commit=False)

        publisher = form.cleaned_data.pop('publisher', None)
        if publisher:
            pub, pub_created = models.Publisher.objects.get_or_create(
                name=publisher,
                defaults={'added_by': self.request.user.profile})
            updated_book.publisher_id = pub.pk
        else:
            updated_book.publisher = None
        updated_book.save()

        authors_list = form.cleaned_data.pop('authors', None)
        if authors_list:
            for author in authors_list.split(sep=','):
                auth, auth_created = models.Author.objects.get_or_create(
                    name=author.strip(),
                    defaults={'added_by': self.request.user.profile})
                updated_book.authors.add(auth.id)
            updated_book.save()
        else:
            updated_book.authors.clear()

        categories_list = form.cleaned_data.pop('categories', None)
        if categories_list:
            for category in categories_list.split(sep=','):
                cat, cat_created = models.Category.objects.get_or_create(
                    name=category.strip(),
                    defaults={'added_by': self.request.user.profile})
                updated_book.categories.add(cat.id)
            updated_book.save()
        else:
            updated_book.categories.clear()
        return super().form_valid(form)


class BookDeleteView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, DeleteView):
    model = models.Book
    login_url = reverse_lazy('login')
    success_message = 'Book was deleted successfully!'
    permission_denied_message = "Books can be deleted only by person who added them to the database!"

    def get_success_url(self):
        return reverse('book-list')

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        elif self.request.user.is_authenticated:
            book = models.Book.objects.get(id=self.kwargs['pk'])
            if book.added_by is None:
                return True
            return book.added_by.id == self.request.user.profile.id
        return False

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, message=self.permission_denied_message)
            return redirect('book-detail', pk=self.kwargs['pk'])
        return super().handle_no_permission()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class BookDetailView(DetailView):
    model = models.Book

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['details'] = model_to_dict(self.object, )
        context['details']['added_by'] = self.object.added_by
        context['details']['publisher'] = getattr(self.object, 'publisher')
        if self.request.user.is_authenticated:
            try:
                vote = self.object.vote_set.get(profile=self.request.user.profile, book=self.object.id)
                context['vote_form'] = forms.VoteForm(data={'value': vote.value})
            except ObjectDoesNotExist:
                context['vote_form'] = forms.VoteForm()

            if self.object in self.request.user.profile.books.all():
                context['owned_form'] = forms.ProfileBooksOwnedForm(data={'owned': True})
            else:
                context['owned_form'] = forms.ProfileBooksOwnedForm(data={'owned': False})
        return context


class BookListView(ListView):
    model = models.Book
    template_name = 'finder/book_list.html'
    success_url = reverse_lazy('book-list')
    form_class = forms.BookSearchForm
    ordering = ['title']
    paginate_by = 10
    page_kwarg = 'page'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = self.form_class(self.request.GET)
        context['form'] = form
        q = self.request.GET.copy()
        q.pop(self.page_kwarg, None)
        context['q'] = q.urlencode()
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        for k, v in self.request.GET.items():
            if k == 'page':
                continue
            if len(self.request.GET.get(k)) > 0:
                key = '{}__icontains'.format(k)
                if k in ['authors', 'categories', 'publisher']:
                    key = '{}__name__icontains'.format(k)
                queryset = queryset.filter(**{key: v})

        return queryset


class VoteCreateUpdateView(LoginRequiredMixin, UpdateView):
    model = models.Vote
    form_class = forms.VoteForm
    login_url = reverse_lazy('login')

    def get_object(self, queryset=None):
        profile = self.request.user.profile
        book = models.Book.objects.get(id=self.kwargs['pk'])
        obj, created = models.Vote.objects.get_or_create(profile=profile, book=book)
        return obj

    def get_success_url(self):
        return reverse('book-detail', args=(self.object.book.pk,))


class PublisherCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = models.Publisher
    fields = ['name']
    login_url = reverse_lazy('login')
    success_message = '%(name)s was created successfully!'
    template_name = 'finder/publisher_create.html'

    def get_success_url(self):
        return reverse('publisher-detail', args=(self.object.pk,))


class PublisherUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = models.Publisher
    fields = ['name']
    login_url = reverse_lazy('login')
    success_message = '%(name)s was updated successfully!'
    template_name = 'finder/publisher_update.html'

    def get_success_url(self):
        return reverse('publisher-detail', args=(self.object.pk,))


class PublisherDeleteView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, DeleteView):
    model = models.Publisher
    login_url = reverse_lazy('login')
    success_message = 'Publisher deleted successfully!'
    permission_denied_message = "Publisher can be deleted only by person who added him to the database!"

    def get_success_url(self):
        return reverse('publisher-list')

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        elif self.request.user.is_authenticated:
            publisher = models.Publisher.objects.get(id=self.kwargs['pk'])
            if publisher.added_by is None:
                return True
            return publisher.added_by.id == self.request.user.profile.id
        return False

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, message=self.permission_denied_message)
            return redirect('publisher-detail', pk=self.kwargs['pk'])
        return super().handle_no_permission()


class PublisherDetailView(DetailView):
    model = models.Publisher


class PublisherListView(ListView):
    model = models.Publisher
    template_name = 'finder/publisher_list.html'
    success_url = reverse_lazy('publisher-list')
    form_class = forms.PublisherSearchForm
    ordering = ['name']
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = self.form_class(self.request.GET)
        context['form'] = form
        q = self.request.GET.copy()
        q.pop(self.page_kwarg, None)
        context['q'] = q.urlencode()
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        if 'name' in self.request.GET:
            queryset = queryset.filter(name__icontains=self.request.GET.get('name'))
        return queryset


class AuthorCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = models.Author
    fields = ['name']
    login_url = reverse_lazy('login')
    success_message = '%(name)s was created successfully!'
    template_name = 'finder/author_create.html'

    def get_success_url(self):
        return reverse('author-detail', args=(self.object.pk,))


class AuthorUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = models.Author
    fields = ['name']
    login_url = reverse_lazy('login')
    success_message = '%(name)s was updated successfully!'
    template_name = 'finder/author_update.html'

    def get_success_url(self):
        return reverse('author-detail', args=(self.object.pk,))


class AuthorDeleteView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, DeleteView):
    model = models.Author
    login_url = reverse_lazy('login')
    success_message = 'Author was deleted successfully!'
    permission_denied_message = "Authors can be deleted only by person who added them to the database!"

    def get_success_url(self):
        return reverse('author-list')

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        elif self.request.user.is_authenticated:
            author = models.Author.objects.get(id=self.kwargs['pk'])
            if author.added_by is None:
                return True
            return author.added_by.id == self.request.user.profile.id
        return False

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, message=self.permission_denied_message)
            return redirect('author-detail', pk=self.kwargs['pk'])
        return super().handle_no_permission()


class AuthorDetailView(DetailView):
    model = models.Author


class AuthorListView(ListView):
    model = models.Author
    template_name = 'finder/author_list.html'
    success_url = reverse_lazy('author-list')
    form_class = forms.AuthorSearchForm
    ordering = ['name']
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super(AuthorListView, self).get_context_data(**kwargs)
        form = self.form_class(self.request.GET)
        context['form'] = form
        q = self.request.GET.copy()
        q.pop(self.page_kwarg, None)
        context['q'] = q.urlencode()
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        if 'name' in self.request.GET:
            queryset = queryset.filter(name__icontains=self.request.GET.get('name'))
        return queryset


class CategoryCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = models.Category
    fields = ['name']
    login_url = reverse_lazy('login')
    success_message = '%(name)s was created successfully!'
    template_name = 'finder/category_create.html'

    def get_success_url(self):
        return reverse('category-detail', args=(self.object.pk,))


class CategoryUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = models.Category
    fields = ['name']
    login_url = reverse_lazy('login')
    success_message = '%(name)s was updated successfully!'
    template_name = 'finder/category_update.html'

    def get_success_url(self):
        return reverse('category-detail', args=(self.object.pk,))


class CategoryDeleteView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, DeleteView):
    model = models.Category
    login_url = reverse_lazy('login')
    success_message = 'Category was deleted successfully!'
    permission_denied_message = "Categories can be deleted only by person who added them to the database!"

    def get_success_url(self):
        return reverse('category-list')

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        elif self.request.user.is_authenticated:
            category = models.Category.objects.get(id=self.kwargs['pk'])
            if category.added_by is None:
                return True
            return category.added_by.id == self.request.user.profile.id
        return False

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, message=self.permission_denied_message)
            return redirect('category-detail', pk=self.kwargs['pk'])
        return super().handle_no_permission()


class CategoryDetailView(DetailView):
    model = models.Category


class CategoryListView(ListView):
    model = models.Category
    template_name = 'finder/category_list.html'
    success_url = reverse_lazy('category-list')
    form_class = forms.CategorySearchForm
    ordering = ['name']
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super(CategoryListView, self).get_context_data(**kwargs)
        form = self.form_class(self.request.GET)
        context['form'] = form
        q = self.request.GET.copy()
        q.pop(self.page_kwarg, None)
        context['q'] = q.urlencode()
        return context

    def get_queryset(self):
        queryset = super(CategoryListView, self).get_queryset()
        if 'name' in self.request.GET:
            queryset = queryset.filter(name__icontains=self.request.GET.get('name'))
        return queryset


class GoogleBooksListView(GoogleBooksSerializerMixin, FormView):
    form_class = forms.GoogleBooksForm
    template_name = 'finder/gbooks_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        response = requests.get(url=self.get_gbooks_url())
        if response.status_code == 200:
            response = response.json()
            if 'items' in response:
                context['gbooks_list'] = [self.gbooks_serializer(book) for book in response['items']]
        return context

    def get_initial(self):
        initial = super().get_initial()
        for field in self.request.GET:
            initial[field] = self.request.GET[field]
        return initial

    def get_gbooks_url(self):
        url = 'https://www.googleapis.com/books/v1/volumes?q='
        if 'title' in self.request.GET and self.request.GET['title'].strip() != '':
            url += '+intitle:' + '+intitle:'.join(self.request.GET['title'].split())
        if 'authors' in self.request.GET and self.request.GET['authors'].strip() != '':
            url += '+inauthor:' + '+inauthor:'.join(self.request.GET['authors'].split())
        if 'publisher' in self.request.GET and self.request.GET['publisher'].strip() != '':
            url += '+inpublisher:' + 'inpublisher:'.join(self.request.GET['publisher'].split())
        if 'isbn' in self.request.GET and self.request.GET['isbn'].strip() != '':
            url += '+isbn:' + self.request.GET['isbn']
        url += '&maxResults=20'
        return url


class GoogleBooksDetailView(GoogleBooksSerializerMixin, TemplateView):
    template_name = 'finder/gbooks_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        response = requests.get(url='https://www.googleapis.com/books/v1/volumes/' + self.kwargs.get('gbooks_id'))
        if response.status_code == 200:
            book = self.gbooks_serializer(response.json())
            context['book'] = book
        return context
