# candidatures/views.py

from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from .models import Dossier, Document
from .serializers import (
    DossierListSerializer, DossierDetailSerializer,
    DossierCreateUpdateSerializer, DocumentSerializer
)
from administration.permissions import IsResponsableOrAdmin
from users.models import User


class DossierViewSet(viewsets.ModelViewSet):
    """
    Endpoints principaux :
    GET    /api/dossiers/                → liste (candidat: ses dossiers | responsable: tous)
    POST   /api/dossiers/                → créer un dossier (brouillon)
    GET    /api/dossiers/{id}/           → détail complet
    PUT    /api/dossiers/{id}/           → modifier (si brouillon)
    POST   /api/dossiers/{id}/soumettre/ → soumettre → déclenche l'analyse automatique
    POST   /api/dossiers/{id}/valider/   → responsable valide
    POST   /api/dossiers/{id}/rejeter/   → responsable rejette
    GET    /api/dossiers/export/         → export Excel (responsable)
    """
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']
    filterset_fields   = ['statut', 'filiere', 'is_suspect']
    search_fields      = ['candidat__nom', 'candidat__prenom', 'candidat__user__cin']
    ordering_fields    = [
        'score', 'classement', 'date_soumission', 'moyenne_generale',
        'candidat__nom', 'candidat__prenom', 'candidat__user__cin', 'created_at',
    ]
    ordering           = ['-score']

    def get_queryset(self):
        user = self.request.user
        qs   = Dossier.objects.select_related(
            'candidat', 'candidat__user', 'filiere'
        ).prefetch_related('documents', 'notes_semestres', 'historique')

        # Un candidat ne voit que ses propres dossiers
        if user.is_candidat:
            profil = getattr(user, 'profil', None)
            return qs.filter(candidat=profil) if profil else qs.none()
        # Un responsable/admin voit tous les dossiers
        return qs.all()

    def get_serializer_class(self):
        if self.action in ['list']:
            return DossierListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return DossierCreateUpdateSerializer
        return DossierDetailSerializer

    def perform_create(self, serializer):
        # Le candidat est automatiquement lié à l'utilisateur connecté
        profil = getattr(self.request.user, 'profil', None)
        if not profil:
            raise PermissionDenied("Seuls les candidats peuvent créer un dossier.")
        serializer.save(candidat=profil)

    def update(self, request, *args, **kwargs):
        dossier = self.get_object()
        if not request.user.is_candidat or dossier.candidat_id != getattr(request.user, 'profil_id', None):
            return Response(
                {"error": "Seul le candidat propriétaire peut modifier ce dossier."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if dossier.statut not in (Dossier.Statut.BROUILLON, Dossier.Statut.INCOMPLET):
            return Response(
                {"error": "Ce dossier ne peut plus être modifié (déjà soumis et en cours de traitement)."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def soumettre(self, request, pk=None):
        """
        Déclenche la chaîne complète :
        1. Passer statut → EN_TRAITEMENT
        2. Lancer l'analyse (OCR, règles, scoring) en arrière-plan
        3. Retourner une réponse immédiate
        """
        import threading
        from .services.extraction import extraire_donnees_dossier
        from .services.regles     import evaluer_regles
        from .services.scoring    import calculer_score_dossier
        from notifications.services import envoyer_notification

        dossier = self.get_object()

        if not request.user.is_candidat or dossier.candidat_id != getattr(request.user, 'profil_id', None):
            return Response(
                {"error": "Seul le candidat propriétaire peut soumettre ce dossier."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if dossier.statut not in [Dossier.Statut.BROUILLON, Dossier.Statut.INCOMPLET]:
            return Response(
                {"error": "Ce dossier a déjà été soumis."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Étape 1 — Passer en traitement
        dossier.changer_statut(Dossier.Statut.EN_TRAITEMENT, acteur=request.user)

        def process_dossier_background(dossier_id):
            from .models import Dossier
            try:
                # Reload dossier to avoid thread issues
                dossier_bg = Dossier.objects.get(id=dossier_id)
            except Dossier.DoesNotExist:
                return

            # Étape 2 — Extraction PDF
            extraction_result = extraire_donnees_dossier(dossier_bg)
            if not extraction_result['succes']:
                dossier_bg.changer_statut(Dossier.Statut.INCOMPLET, commentaire=extraction_result['erreur'])
                envoyer_notification(dossier_bg, 'INCOMPLET')
                return

            # Étape 2b — Vérification authenticité des documents
            from .services.verification_document import analyser_dossier_complet
            verification = analyser_dossier_complet(dossier_bg)

            # Si CRITIQUE → rejet automatique proposé (on le marque suspect)
            if verification['recommandation'] == 'REJETER':
                dossier_bg.motif_rejet = (
                    "Documents non conformes — "
                    "Authenticité insuffisante. "
                    "Alertes : " + ", ".join(verification['alertes_critiques'])
                )
                dossier_bg.is_suspect = True
                dossier_bg.save(update_fields=['motif_rejet', 'is_suspect'])

            # Si VERIF_MANUELLE → marquer suspect mais continuer
            if verification['recommandation'] == 'VERIF_MANUELLE':
                dossier_bg.is_suspect = True
                dossier_bg.save(update_fields=['is_suspect'])

            # Étape 3 — Règles de rejet
            rejet = evaluer_regles(dossier_bg)
            if rejet['rejete']:
                dossier_bg.motif_rejet = rejet['motif']
                dossier_bg.save(update_fields=['motif_rejet'])
                if rejet.get("statut") == Dossier.Statut.INCOMPLET:
                    dossier_bg.changer_statut(Dossier.Statut.INCOMPLET, commentaire=rejet['motif'])
                    envoyer_notification(dossier_bg, 'INCOMPLET')
                    return

            # Étape 4 — Statut final puis scoring
            if dossier_bg.is_suspect:
                dossier_bg.changer_statut(Dossier.Statut.SUSPECT)
            else:
                dossier_bg.changer_statut(Dossier.Statut.EN_ATTENTE)

            calculer_score_dossier(dossier_bg)

            # Étape 5 — Notification
            envoyer_notification(dossier_bg, 'SOUMISSION')
            
            # Close db connections used in this thread
            from django.db import connection
            connection.close()

        # Lancer le traitement en arrière-plan
        thread = threading.Thread(target=process_dossier_background, args=(dossier.id,))
        thread.start()

        return Response({
            "status": "success",
            "statut": "EN_TRAITEMENT",
            "message": "Dossier soumis avec succès. En cours d'examen."
        })

    @action(detail=True, methods=['post'], permission_classes=[IsResponsableOrAdmin])
    def valider(self, request, pk=None):
        from notifications.services import envoyer_notification
        dossier = self.get_object()
        if dossier.statut not in [Dossier.Statut.EN_ATTENTE, Dossier.Statut.SUSPECT]:
            return Response({"error": "Action impossible pour ce statut."}, status=400)
        dossier.changer_statut(
            Dossier.Statut.PRESELECTIONNE,
            acteur=request.user,
            commentaire=request.data.get('commentaire', '')
        )
        envoyer_notification(dossier, 'PRESELECTION')
        return Response({"message": "Candidat présélectionné.", "statut": "PRESELECTIONNE"})

    @action(detail=True, methods=['post'], permission_classes=[IsResponsableOrAdmin])
    def rejeter(self, request, pk=None):
        from notifications.services import envoyer_notification
        dossier     = self.get_object()
        commentaire = request.data.get('commentaire', '')
        if not commentaire:
            return Response({"error": "Un commentaire est obligatoire pour le rejet."}, status=400)
        dossier.changer_statut(
            Dossier.Statut.REJETE_FINAL,
            acteur=request.user,
            commentaire=commentaire
        )
        envoyer_notification(dossier, 'REJET_MANUEL')
        return Response({"message": "Dossier rejeté.", "statut": "REJETE_FINAL"})

    @action(detail=True, methods=['post'], permission_classes=[IsResponsableOrAdmin])
    def rejeter_auto(self, request, pk=None):
        from notifications.services import envoyer_notification
        dossier = self.get_object()
        if dossier.statut not in [Dossier.Statut.EN_ATTENTE, Dossier.Statut.SUSPECT]:
            return Response({"error": "Action impossible pour ce statut."}, status=400)
        
        # Appliquer la décision de rejet automatique
        if not dossier.motif_rejet:
            dossier.motif_rejet = request.data.get('commentaire', 'Rejet automatique validé par le responsable.')
        else:
            if request.data.get('commentaire'):
                dossier.motif_rejet += f" - {request.data.get('commentaire')}"
        
        dossier.changer_statut(
            Dossier.Statut.REJETE_AUTO,
            acteur=request.user,
            commentaire=dossier.motif_rejet
        )
        envoyer_notification(dossier, 'REJET_AUTO')
        return Response({"message": "Dossier rejeté automatiquement.", "statut": "REJETE_AUTO"})

    @action(detail=False, methods=['get'], permission_classes=[IsResponsableOrAdmin])
    def export(self, request):
        """Export Excel de la liste des présélectionnés."""
        import openpyxl
        from django.http import HttpResponse

        filiere_id = request.query_params.get('filiere_id')
        dossiers   = Dossier.objects.filter(
            statut='PRESELECTIONNE',
            **({"filiere_id": filiere_id} if filiere_id else {})
        ).select_related('candidat', 'filiere').order_by('-score')

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Présélectionnés"
        ws.append(['#', 'Nom', 'Prénom', 'CIN', 'Email', 'Filière', 'Diplôme', 'Moyenne', 'Score'])

        for i, d in enumerate(dossiers, 1):
            ws.append([
                i, d.candidat.nom, d.candidat.prenom,
                d.candidat.user.cin, d.candidat.user.email,
                d.filiere.nom, d.diplome_obtenu,
                float(d.moyenne_generale or 0),
                float(d.score or 0)
            ])

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="preselectionnes.xlsx"'
        wb.save(response)
        return response

    @action(detail=True, methods=['get'], permission_classes=[IsResponsableOrAdmin])
    def rapport_verification(self, request, pk=None):
        """
        GET /api/dossiers/{id}/rapport_verification/
        Retourne le rapport complet de vérification d'authenticité.
        """
        dossier = self.get_object()
        return Response({
            'score_authenticite': dossier.score_authenticite,
            'alertes': dossier.alertes_verification,
            'par_document': [
                {
                    'type': doc.type_doc,
                    'qualite_ocr': doc.qualite_ocr,
                    'nom_fichier': doc.fichier.name if doc.fichier else '',
                    'taille_ko': doc.taille_ko,
                }
                for doc in dossier.documents.all()
            ]
        })



    @action(detail=True, methods=['get'])
    def convocation_ecrit(self, request, pk=None):
        """
        Génère et télécharge la convocation PDF pour l'épreuve écrite.
        Disponible pour le candidat concerné ou le responsable si le dossier est PRESELECTIONNE ou ADMIS_FINAL.
        """
        from django.http import HttpResponse
        from .services.invitation_pdf import generer_invitation_ecrit
        
        dossier = self.get_object()
        
        if dossier.statut not in [Dossier.Statut.PRESELECTIONNE, Dossier.Statut.ADMIS_FINAL]:
            return Response(
                {"error": "La convocation écrite est uniquement disponible pour les candidats présélectionnés ou admis à l'écrit."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        pdf_buffer = generer_invitation_ecrit(dossier)
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="convocation_ecrit_{dossier.candidat.user.cin or dossier.id}.pdf"'
        return response

    @action(detail=True, methods=['get'])
    def convocation_oral(self, request, pk=None):
        """
        Génère et télécharge la convocation PDF pour l'épreuve orale.
        Disponible pour le candidat concerné ou le responsable si le dossier est ADMIS_FINAL.
        """
        from django.http import HttpResponse
        from .services.invitation_pdf import generer_invitation_oral
        
        dossier = self.get_object()
        
        if dossier.statut != Dossier.Statut.ADMIS_FINAL:
            return Response(
                {"error": "La convocation orale est uniquement disponible pour les candidats admis à l'épreuve écrite."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        pdf_buffer = generer_invitation_oral(dossier)
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="convocation_oral_{dossier.candidat.user.cin or dossier.id}.pdf"'
        return response


class DocumentUploadView(generics.CreateAPIView):
    """
    POST /api/documents/upload/
    Upload d'un document pour un dossier existant.
    Accepte multipart/form-data.
    """
    serializer_class   = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes     = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        dossier_id = self.request.data.get('dossier_id')
        profil = getattr(self.request.user, 'profil', None)
        if not profil:
            raise PermissionDenied("Seuls les candidats peuvent téléverser des documents.")
        dossier    = get_object_or_404(Dossier, id=dossier_id, candidat=profil)
        fichier    = self.request.FILES.get('fichier')
        serializer.save(
            dossier=dossier,
            mime_type=fichier.content_type if fichier else ''
        )
