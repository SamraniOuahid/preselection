# candidatures/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DossierViewSet, DocumentUploadView

router = DefaultRouter()
router.register('dossiers', DossierViewSet, basename='dossier')

urlpatterns = [
    path('', include(router.urls)),
    path('documents/upload/', DocumentUploadView.as_view(), name='document_upload'),
]