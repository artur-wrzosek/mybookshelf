from django.urls import path, include
from . import views
from rest_framework import routers

# router = routers.DefaultRouter()
# router.register('books', views.BookViewSet)


urlpatterns = [
    path('', views.BookListView.as_view(), name='main'),
    path('api/', include('finder.api.urls')),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('register/', views.RegistrationView.as_view(), name='register'),

    path('book/list/', views.BookListView.as_view(), name='book-list'),
    path('book/create/', views.BookCreateView.as_view(), name='book-create'),
    path('book/create/<gbooks_id>/', views.BookCreateView.as_view(), name='book-create'),
    path('book/<pk>/', views.BookDetailView.as_view(), name='book-detail'),
    path('book/<pk>/update/', views.BookUpdateView.as_view(), name='book-update'),
    path('book/<pk>/delete/', views.BookDeleteView.as_view(), name='book-delete'),
    path('book/<pk>/vote/', views.VoteCreateUpdateView.as_view(), name='vote-create'),

    path('publisher/create/', views.PublisherCreateView.as_view(), name='publisher-create'),
    path('publisher/list/', views.PublisherListView.as_view(), name='publisher-list'),
    path('publisher/<pk>/', views.PublisherDetailView.as_view(), name='publisher-detail'),
    path('publisher/<pk>/update/', views.PublisherUpdateView.as_view(), name='publisher-update'),
    path('publisher/<pk>/delete/', views.PublisherDeleteView.as_view(), name='publisher-delete'),

    path('author/create/', views.AuthorCreateView.as_view(), name='author-create'),
    path('author/list/', views.AuthorListView.as_view(), name='author-list'),
    path('author/<pk>/', views.AuthorDetailView.as_view(), name='author-detail'),
    path('author/<pk>/update/', views.AuthorUpdateView.as_view(), name='author-update'),
    path('author/<pk>/delete/', views.AuthorDeleteView.as_view(), name='author-delete'),

    path('category/create/', views.CategoryCreateView.as_view(), name='category-create'),
    path('category/list/', views.CategoryListView.as_view(), name='category-list'),
    path('category/<pk>/', views.CategoryDetailView.as_view(), name='category-detail'),
    path('category/<pk>/update/', views.CategoryUpdateView.as_view(), name='category-update'),
    path('category/<pk>/delete/', views.CategoryDeleteView.as_view(), name='category-delete'),

    path('profile/list/', views.ProfileListView.as_view(), name='profile-list'),
    path('profile/<uuid:uuid>/', views.ProfileDetailView.as_view(), name='profile-detail'),
    path('profile/<uuid:uuid>/update/', views.ProfileUpdateView.as_view(), name='profile-update'),
    path('profile/<uuid:uuid>/owned/<int:pk>/', views.ProfileBooksOwnedView.as_view(), name='profile-owned'),
    path('profile/<uuid:uuid>/friends/<uuid:uuid2>', views.ProfileFriendsUpdateView.as_view(), name='profile-friends'),

    path('gbooks/', views.GoogleBooksListView.as_view(), name='gbooks-list'),
    path('gbooks/<gbooks_id>/', views.GoogleBooksDetailView.as_view(), name='gbooks-detail'),

]

