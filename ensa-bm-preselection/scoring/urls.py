# scoring/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegleRejetViewSet, ConfigScoringViewSet

router = DefaultRouter()
router.register('regles', RegleRejetViewSet, basename='regles')
router.register('config', ConfigScoringViewSet, basename='config-scoring')

urlpatterns = [
    path('', include(router.urls)),
]
