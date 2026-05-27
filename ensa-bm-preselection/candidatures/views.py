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
        ).prefetch_related('documents', 'notes', 'historique')

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
        2. Extraire les données des PDFs
        3. Appliquer les règles de rejet
        4. Calculer le score si non rejeté
        5. Envoyer la notification email
        """
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

        # Étape 2 — Extraction PDF
        extraction_result = extraire_donnees_dossier(dossier)
        if not extraction_result['succes']:
            dossier.changer_statut(Dossier.Statut.INCOMPLET, commentaire=extraction_result['erreur'])
            envoyer_notification(dossier, 'INCOMPLET')
            return Response({"statut": "INCOMPLET", "message": extraction_result['erreur']})

        # Étape 2b — Vérification authenticité des documents
        from .services.verification_document import analyser_dossier_complet
        verification = analyser_dossier_complet(dossier)

        # Si CRITIQUE → rejet automatique immédiat
        if verification['recommandation'] == 'REJETER':
            dossier.motif_rejet = (
                "Documents non conformes — "
                "Authenticité insuffisante. "
                "Alertes : " + ", ".join(verification['alertes_critiques'])
            )
            dossier.save()
            dossier.changer_statut(Dossier.Statut.REJETE_AUTO)
            envoyer_notification(dossier, 'REJET_AUTO')
            return Response({
                'statut': 'REJETE_AUTO',
                'motif': dossier.motif_rejet,
                'score_authenticite': verification['score_global']
            })

        # Si VERIF_MANUELLE → marquer suspect mais continuer
        if verification['recommandation'] == 'VERIF_MANUELLE':
            dossier.is_suspect = True
            dossier.save()

        # Étape 3 — Règles de rejet
        rejet = evaluer_regles(dossier)
        if rejet['rejete']:
            dossier.motif_rejet = rejet['motif']
            dossier.save()
            if rejet.get("statut") == Dossier.Statut.INCOMPLET:
                dossier.changer_statut(Dossier.Statut.INCOMPLET, commentaire=rejet['motif'])
                envoyer_notification(dossier, 'INCOMPLET')
                return Response({"statut": "INCOMPLET", "message": rejet['motif']})
            dossier.changer_statut(Dossier.Statut.REJETE_AUTO, commentaire=rejet['motif'])
            envoyer_notification(dossier, 'REJET_AUTO')
            return Response({"statut": "REJETE_AUTO", "motif": rejet['motif']})

        # Étape 4 — Statut final puis scoring
        if dossier.is_suspect:
            dossier.changer_statut(Dossier.Statut.SUSPECT)
        else:
            dossier.changer_statut(Dossier.Statut.EN_ATTENTE)

        calculer_score_dossier(dossier)

        # Étape 5 — Notification
        envoyer_notification(dossier, 'SOUMISSION')

        final_statut = "SUSPECT" if dossier.is_suspect else "EN_ATTENTE"
        return Response({
            "statut": final_statut,
            "score": float(dossier.score) if dossier.score else None,
            "message": "Dossier soumis avec succès. Vous serez notifié par email."
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
            'massar_verifie': dossier.massar_verifie,
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

    @action(detail=True, methods=['post'], permission_classes=[IsResponsableOrAdmin])
    def marquer_massar_verifie(self, request, pk=None):
        """
        POST /api/dossiers/{id}/marquer_massar_verifie/
        Le responsable confirme la vérification manuelle via Massar.
        """
        from administration.models import HistoriqueAction
        dossier = self.get_object()
        dossier.massar_verifie = True
        dossier.is_suspect = False
        dossier.save()
        HistoriqueAction.objects.create(
            dossier=dossier,
            acteur=request.user,
            action='VALIDATION',
            commentaire='Vérification Massar confirmée manuellement'
        )
        return Response({'message': 'Dossier vérifié via Massar.'})


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
