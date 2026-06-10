# administration/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FiliereViewSet, DashboardStatsView
from .analytics_views import AdminAnalyticsStatsView
from .views_epreuve import EpreuveEcriteViewSet, NoteEcriteViewSet
from .views_oral import EpreuveOraleViewSet, ConvocationOraleViewSet
from rest_framework import generics

router = DefaultRouter()
router.register('filieres', FiliereViewSet)
router.register('epreuves', EpreuveEcriteViewSet, basename='epreuve')
router.register('notes-ecrites', NoteEcriteViewSet, basename='note-ecrite')
router.register('epreuves-oral', EpreuveOraleViewSet, basename='epreuve-oral')
router.register('convocations', ConvocationOraleViewSet, basename='convocation')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard_stats'),
    path('admin/analytics/stats/', AdminAnalyticsStatsView.as_view(), name='admin_analytics_stats'),
]