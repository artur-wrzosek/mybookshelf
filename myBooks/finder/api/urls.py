from django.urls import path
from rest_framework import routers
from rest_framework.authtoken import views
from . import viewsets

router = routers.DefaultRouter()
router.register(r'books', viewsets.BookModelViewSet)
router.register(r'authors', viewsets.AuthorModelViewSet)
router.register(r'categories', viewsets.CategoryModelViewSet)
router.register(r'publishers', viewsets.PublisherModelViewSet)
router.register(r'votes', viewsets.VoteModelViewSet)
router.register(r'register', viewsets.RegisterView)
router.register(r'profiles', viewsets.ProfileViewSet)
urlpatterns = router.urls
urlpatterns.append(path('api-token-auth/', views.obtain_auth_token))
