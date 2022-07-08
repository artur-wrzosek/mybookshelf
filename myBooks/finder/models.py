from django.db import models
from datetime import date
from django.conf import settings
from django.contrib.auth.models import User, AnonymousUser
import uuid


class AddedBy(models.Model):
    added_by = models.ForeignKey('Profile', on_delete=models.SET_NULL, null=True)
    added_date = models.DateField(default=date.today)

    class Meta:
        abstract = True


class Category(AddedBy):
    name = models.CharField(max_length=50, blank=True, null=True, unique=True)

    def __str__(self):
        return self.name


class Author(AddedBy):
    name = models.CharField(max_length=50, blank=True, null=True, unique=True)

    def __str__(self):
        return self.name


class Publisher(AddedBy):
    name = models.CharField(max_length=50, blank=True, null=True, unique=True)

    def __str__(self):
        return self.name


class Book(AddedBy):
    title = models.CharField(max_length=200, blank=True, null=True)
    year = models.PositiveSmallIntegerField(blank=True, null=True)
    g_rank = models.FloatField(blank=True, null=True)
    thumbnail = models.URLField(max_length=500, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    isbn = models.CharField(max_length=13, blank=True, null=True)
    authors = models.ManyToManyField(Author, blank=True)
    categories = models.ManyToManyField(Category, blank=True)
    publisher = models.ForeignKey(Publisher, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return self.title


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, blank=False, null=False, unique=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    books = models.ManyToManyField(Book, blank=True)
    friends = models.ManyToManyField('self', blank=True)

    def __str__(self):
        return '_'.join([self.name, 'profile'])


class Vote(models.Model):
    VOTE_CHOICES = [(i, str(i)) for i in range(1, 11)]
    value = models.SmallIntegerField(null=True, choices=VOTE_CHOICES)
    date = models.DateField(default=date.today)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)

    def __str__(self):
        return '_'.join([self.profile.name[:10], 'vote_on', self.book.title[:10]])
