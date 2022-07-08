from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .. import models


class AuthorSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=50, min_length=None)
    id = serializers.CharField()

    def create(self, validated_data):
        books_list = []
        if 'book_set' in validated_data:
            books = validated_data.pop('book_set')
            for book in books:
                book_found = models.Book.objects.get(id=book.get('id'))[0]
                if book_found:
                    books_list.append(book_found)
        author = models.Author.objects.create(**validated_data)
        author.book_set.set(books_list)
        author.save()
        return author

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.book_set.set(validated_data.get('book_set', instance.book_set.all()))
        instance.save()
        return instance


class PublisherSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=50, min_length=None, validators=None)
    id = serializers.CharField()

    def create(self, validated_data):
        books_list = []
        if 'book_set' in validated_data:
            books = validated_data.pop('book_set')
            for book in books:
                book_found = models.Book.objects.get(id=book.get('id'))[0]
                if book_found:
                    books_list.append(book_found)
        publisher = models.Publisher.objects.create(**validated_data)
        publisher.book_set.set(books_list)
        publisher.save()
        return publisher

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.book_set.set(validated_data.get('book_set', instance.book_set.all()))
        instance.save()
        return instance


class CategorySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=50, min_length=None)
    id = serializers.CharField()

    def create(self, validated_data):
        books_list = []
        if 'book_set' in validated_data:
            books = validated_data.pop('book_set')
            for book in books:
                book_found = models.Book.objects.get(id=book.get('id'))[0]
                if book_found:
                    books_list.append(book_found)
        category = models.Category.objects.create(**validated_data)
        category.book_set.set(books_list)
        category.save()
        return category

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.book_set.set(validated_data.get('book_set', instance.book_set.all()))
        instance.save()
        return instance


class BookSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=50, required=False)
    id = serializers.CharField(read_only=True)
    authors = AuthorSerializer(many=True, required=False)
    categories = CategorySerializer(many=True, required=False)
    publisher = PublisherSerializer(many=False, required=False)

    def create(self, validated_data):
        auth_list = []
        cat_list = []
        pub = None
        if 'authors' in validated_data:
            authors = validated_data.pop('authors')
            for author in authors:
                auth_list.append(models.Author.objects.get_or_create(id=author.get('id'))[0])
        if 'categories' in validated_data:
            categories = validated_data.pop('categories')
            for category in categories:
                cat_list.append(models.Category.objects.get_or_create(id=category.get('id'))[0])
        if 'publisher' in validated_data:
            publisher = validated_data.pop('publisher')
            pub, _ = models.Publisher.objects.get_or_create(id=publisher.get('id'))

        book = models.Book.objects.create(**validated_data)
        book.publisher = pub
        book.authors.set(auth_list)
        book.categories.set(cat_list)
        book.save()
        return book

    def update(self, instance, validated_data):
        if 'authors' in validated_data:
            auth_list = []
            authors = validated_data.pop('authors')
            for author in authors:
                auth_list.append(models.Author.objects.get_or_create(id=author.get('id'))[0])
            instance.authors.set(auth_list)
        if 'categories' in validated_data:
            cat_list = []
            categories = validated_data.pop('categories')
            for category in categories:
                cat_list.append(models.Category.objects.get_or_create(id=category.get('id'))[0])
            instance.categories.set(cat_list)
        if 'publisher' in validated_data:
            publisher = validated_data.pop('publisher')
            instance.publisher, _ = models.Publisher.objects.get_or_create(id=publisher.get('id'))

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password', ]
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        profile = models.Profile.objects.create(name=user.username, user=user)
        return user


class ProfileSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField()
    books = BookSerializer(many=True, required=False)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.book_set.set(validated_data.get('book_set', instance.book_set.all()))
        instance.save()
        return instance


class VoteSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    book = serializers.CharField(allow_blank=True, required=False)
    book_id = serializers.IntegerField(required=False)
    date = serializers.DateField(read_only=True)
    value = serializers.ChoiceField(choices=models.Vote.VOTE_CHOICES, required=True)
    profile = serializers.CharField(allow_blank=True, required=False)
    profile_id = serializers.UUIDField(required=False)

    def create(self, validated_data):
        if 'book_id' in validated_data:
            validated_data.pop('book')
            book = models.Book.objects.get(id=validated_data.pop('book_id'))
            vote = models.Vote.objects.create(book=book, **validated_data)
            return vote
        else:
            raise serializers.ValidationError('Book id number is required.')

    def update(self, instance, validated_data):
        instance.value = validated_data.get('value', instance.value)
        # instance.book = models.validated_data.get('book_id', instance.book))
        instance.save()
        return instance
