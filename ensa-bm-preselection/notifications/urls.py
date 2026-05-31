# notifications/urls.py
# URL patterns for notification API endpoints

from django.urls import path
from .views import (
    NotifierTousView,
    MesNotificationsView,
    NombreNonLuesView,
    MarquerLueView,
    MarquerToutesLuesView,
    RenvoyerNotificationView,
    ConvocationPDFView,
)

urlpatterns = [
    # GET  → prévisualiser les stats + aperçu email
    path('notifications/previsualiser/', NotifierTousView.as_view(), name='notif-previsualiser'),
    # POST → démarrer l'envoi en masse (retourne task_id WebSocket)
    path('notifications/notifier-tous/', NotifierTousView.as_view(), name='notif-notifier-tous'),
    
    # Espace candidat
    path('notifications/mes-notifications/', MesNotificationsView.as_view(), name='notif-mes-notifications'),
    path('notifications/non-lues/', NombreNonLuesView.as_view(), name='notif-non-lues'),
    path('notifications/<uuid:pk>/marquer-lue/', MarquerLueView.as_view(), name='notif-marquer-lue'),
    path('notifications/marquer-toutes-lues/', MarquerToutesLuesView.as_view(), name='notif-marquer-toutes-lues'),
    path('notifications/<uuid:pk>/renvoyer/', RenvoyerNotificationView.as_view(), name='notif-renvoyer'),

    # Convocation PDF
    path('notifications/convocation/<uuid:dossier_id>/', ConvocationPDFView.as_view(), name='notif-convocation-pdf'),
]
