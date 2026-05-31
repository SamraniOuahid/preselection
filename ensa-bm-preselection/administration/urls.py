# administration/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FiliereViewSet, DashboardStatsView
from .views_epreuve import EpreuveEcriteViewSet, NoteEcriteViewSet
from rest_framework import generics

router = DefaultRouter()
router.register('filieres', FiliereViewSet)
router.register('epreuves', EpreuveEcriteViewSet, basename='epreuve')
router.register('notes-ecrites', NoteEcriteViewSet, basename='note-ecrite')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard_stats'),
]