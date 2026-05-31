# notifications/views.py
# API views pour la gestion des notifications en masse

from django.http import HttpResponse
from django.utils import timezone
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from administration.permissions import IsResponsableOrAdmin
from .models import Notification
from .serializers import NotificationSerializer
from .services import demarrer_notification_masse, compter_a_notifier, generer_apercu_email


class NotifierTousView(APIView):
    """
    Gestion de l'envoi en masse des notifications de présélection.

    GET  → prévisualisation (stats + aperçu email)
    POST → démarrage de l'envoi en arrière-plan (retourne task_id WebSocket)
    """
    permission_classes = [IsResponsableOrAdmin]

    def get(self, request):
        """
        GET /api/notifications/previsualiser/
        Retourne le nombre de candidats à notifier + aperçu email.
        """
        filiere_id = request.query_params.get('filiere_id')
        stats = compter_a_notifier(filiere_id)
        apercu = generer_apercu_email(filiere_id)
        return Response({
            'stats': stats,
            'apercu_email': apercu,
        })

    def post(self, request):
        """
        POST /api/notifications/notifier-tous/
        Démarre l'envoi en arrière-plan.
        Retourne immédiatement le task_id pour le WebSocket.
        """
        filiere_id = request.data.get('filiere_id')
        task_id = demarrer_notification_masse(
            filiere_id=filiere_id,
            envoye_par=request.user
        )
        return Response({
            'task_id': task_id,
            'ws_url': f'ws/notifications/{task_id}/',
            'message': 'Envoi démarré — connectez-vous au WebSocket pour suivre la progression.',
        }, status=202)  # 202 Accepted (traitement en cours)


class MesNotificationsView(generics.ListAPIView):
    """
    GET /api/notifications/mes-notifications/
    Retourne les notifications de l'utilisateur connecté.
    Trié par date décroissante, pagniné 20/page.
    """
    permission_classes = [IsAuthenticated]
    serializer_class   = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(
            destinataire=self.request.user,
            statut='ENVOYEE'
        ).order_by('-envoyee_le')


class NombreNonLuesView(APIView):
    """
    GET /api/notifications/non-lues/
    Retourne le nombre de notifications non lues.
    Utilisé pour le badge rouge dans la navbar.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(
            destinataire=request.user,
            statut='ENVOYEE',
            lue=False
        ).count()
        return Response({'count': count})


class MarquerLueView(APIView):
    """
    POST /api/notifications/<uuid:pk>/marquer-lue/
    Marque une notification comme lue.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, destinataire=request.user)
            if not notification.lue:
                notification.lue = True
                notification.lue_le = timezone.now()
                notification.save()
            return Response({'status': 'success'})
        except Notification.DoesNotExist:
            return Response({'error': 'Notification introuvable'}, status=404)


class MarquerToutesLuesView(APIView):
    """
    POST /api/notifications/marquer-toutes-lues/
    Marque toutes les notifications de l'utilisateur connecté comme lues.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Notification.objects.filter(
            destinataire=request.user,
            statut='ENVOYEE',
            lue=False
        ).update(
            lue=True,
            lue_le=timezone.now()
        )
        return Response({'status': 'success'})


class RenvoyerNotificationView(APIView):
    """
    POST /api/notifications/<uuid:pk>/renvoyer/
    Renvoie l'email pour une notification spécifique (utile pour le débogage/test).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk)
            from django.core.mail import EmailMultiAlternatives
            from django.utils import timezone
            import logging
            logger = logging.getLogger(__name__)

            msg = EmailMultiAlternatives(
                subject=notification.sujet,
                body=notification.contenu_html,
                from_email=None,
                to=[notification.destinataire.email]
            )
            msg.attach_alternative(notification.contenu_html, "text/html")
            msg.send()

            notification.statut = Notification.Statut.ENVOYEE
            notification.envoyee_le = timezone.now()
            notification.erreur = ""
            notification.save()
            return Response({'status': 'success', 'message': f'Email renvoyé avec succès à {notification.destinataire.email}'})
        except Notification.DoesNotExist:
            return Response({'error': 'Notification introuvable'}, status=404)
        except Exception as e:
            notification.statut = Notification.Statut.ECHEC
            notification.erreur = f"RenvoyerError: {type(e).__name__}: {str(e)}"
            notification.save()
            return Response({'error': f'Erreur SMTP lors du renvoi: {str(e)}'}, status=500)


class ConvocationPDFView(APIView):
    """
    GET /api/notifications/convocation/<dossier_id>/
    Génère et retourne le PDF de convocation pour l'épreuve orale.
    Accessible uniquement au candidat propriétaire du dossier.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, dossier_id):
        from candidatures.models import Dossier
        from candidatures.services.invitation_pdf import generer_invitation_oral

        try:
            dossier = Dossier.objects.select_related(
                'candidat', 'candidat__user', 'filiere'
            ).prefetch_related('notes_ecrits__epreuve').get(pk=dossier_id)
        except Dossier.DoesNotExist:
            return Response({'error': 'Dossier introuvable'}, status=404)

        # Vérifier que le candidat est le propriétaire du dossier
        if dossier.candidat.user != request.user:
            return Response({'error': 'Accès refusé'}, status=403)

        # Vérifier que le candidat est admis à l'écrit
        if dossier.statut != 'ADMIS_FINAL':
            return Response(
                {'error': 'La convocation n\'est disponible que pour les candidats admis.'},
                status=400
            )

        buffer = generer_invitation_oral(dossier)

        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="convocation_oral_ENSA_BM_{dossier.id}.pdf"'
        )
        return response
