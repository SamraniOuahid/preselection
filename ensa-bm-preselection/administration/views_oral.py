# administration/views_oral.py

import datetime
import logging

from django.utils import timezone
from django.db import transaction
from django.http import HttpResponse
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response

from .models import EpreuveOrale, ConvocationOrale
from candidatures.models import Dossier
from .serializers_oral import (
    EpreuveOraleSerializer,
    EpreuveOraleDetailSerializer,
    ConvocationOraleSerializer,
)
from .permissions import IsResponsableOrAdmin
from .services.generation_pdf import generer_convocation_pdf
from .services.import_excel_oral import importer_admis_oral_depuis_fichier
from notifications.services import envoyer_notification

logger = logging.getLogger(__name__)


class EpreuveOraleViewSet(viewsets.ModelViewSet):
    queryset = EpreuveOrale.objects.select_related('filiere').all()
    serializer_class = EpreuveOraleSerializer
    permission_classes = [IsResponsableOrAdmin]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filterset_fields = ['filiere', 'statut']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return EpreuveOraleDetailSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    # ─────────────────────────────────────────────────────────────────
    # convoquer_admis — lit l'heure depuis filiere.date_oral
    # ─────────────────────────────────────────────────────────────────
    @action(detail=True, methods=['post'])
    def convoquer_admis(self, request, pk=None):
        epreuve = self.get_object()
        filiere = epreuve.filiere

        if epreuve.statut != EpreuveOrale.Statut.PLANIFIEE:
            return Response(
                {'error': "L'épreuve n'est pas en statut PLANIFIEE."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        dossiers_admis = (
            Dossier.objects
            .filter(filiere=filiere, statut=Dossier.Statut.ADMIS_FINAL)
            .order_by('-score_final', '-score')
        )

        if not dossiers_admis.exists():
            return Response(
                {'error': 'Aucun candidat admis trouvé pour cette filière.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Source unique de vérité : filiere.date_oral (DateTimeField) ──
        if filiere.date_oral:
            tz = timezone.get_current_timezone()
            dt_local = filiere.date_oral.astimezone(tz)
            heure_debut = dt_local.time().replace(second=0, microsecond=0)
        else:
            heure_debut = datetime.time(9, 0)

        duree = epreuve.duree_minutes
        convoques = 0
        pdfs_generes = 0

        with transaction.atomic():
            for i, dossier in enumerate(dossiers_admis):
                delta = datetime.timedelta(minutes=i * duree)
                heure_passage = (
                    datetime.datetime.combine(datetime.date.today(), heure_debut) + delta
                ).time()

                convocation, _ = ConvocationOrale.objects.get_or_create(
                    epreuve_oral=epreuve,
                    dossier=dossier,
                    defaults={
                        'numero_passage': i + 1,
                        'heure_passage': heure_passage,
                        'decision': ConvocationOrale.Decision.EN_ATTENTE,
                    },
                )

                dossier.changer_statut(Dossier.Statut.CONVOQUE_ORAL, acteur=request.user)

                try:
                    generer_convocation_pdf(convocation)
                    pdfs_generes += 1
                except Exception as exc:
                    logger.warning("PDF non généré pour %s : %s", dossier, exc)

                convoques += 1
                try:
                    envoyer_notification(dossier, 'CONVOCATION_ORAL')
                except Exception as exc:
                    logger.warning("Email non envoyé pour %s : %s", dossier, exc)

            epreuve.statut = EpreuveOrale.Statut.EN_COURS
            epreuve.save(update_fields=['statut'])

        return Response({
            'message': 'Convocations générées avec succès.',
            'convoques': convoques,
            'pdfs_generes': pdfs_generes,
        }, status=status.HTTP_200_OK)

    # ─────────────────────────────────────────────────────────────────
    # importer_admis_oral — upload Excel/CSV
    # ─────────────────────────────────────────────────────────────────
    @action(
        detail=True,
        methods=['post'],
        url_path='importer-admis-oral',
        parser_classes=[MultiPartParser, FormParser],
    )
    def importer_admis_oral(self, request, pk=None):
        """
        Reçoit un fichier Excel (.xlsx/.xls) ou CSV (.csv) contenant
        une colonne « cne », « code_massar » ou « id ».

        Pour chaque ligne valide (candidat trouvé dans la filière) :
          • Statut → CONVOQUE_ORAL
          • ConvocationOrale créée (horaires depuis filiere.date_oral)
          • PDF généré + e-mail envoyé

        Réponse :
        {
          "traites":    <int>,
          "convoques":  <int>,
          "pdfs_generes": <int>,
          "ignores":    <int>,
          "erreurs":    [<str>, ...]
        }
        """
        epreuve = self.get_object()

        fichier = request.FILES.get('fichier')
        if not fichier:
            return Response(
                {'error': "Aucun fichier fourni. Utilisez le champ 'fichier'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        extension = fichier.name.rsplit('.', 1)[-1].lower()
        if extension not in ('xlsx', 'xls', 'csv'):
            return Response(
                {'error': "Format non supporté. Utilisez .xlsx, .xls ou .csv."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            resultat = importer_admis_oral_depuis_fichier(
                fichier=fichier,
                extension=extension,
                epreuve=epreuve,
                acteur=request.user,
            )
        except ValidationError as exc:
            return Response({'error': exc.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.exception("Erreur inattendue lors de l'import oral")
            return Response(
                {'error': f"Erreur interne : {str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(resultat, status=status.HTTP_200_OK)

    # ─────────────────────────────────────────────────────────────────
    # liste_passage
    # ─────────────────────────────────────────────────────────────────
    @action(detail=True, methods=['get'])
    def liste_passage(self, request, pk=None):
        epreuve = self.get_object()
        convocations = epreuve.convocations.all().order_by('numero_passage')
        return Response(ConvocationOraleSerializer(convocations, many=True).data)

    # ─────────────────────────────────────────────────────────────────
    # enregistrer_decision
    # ─────────────────────────────────────────────────────────────────
    @action(detail=True, methods=['post'])
    def enregistrer_decision(self, request, pk=None):
        epreuve = self.get_object()
        dossier_id = request.data.get('dossier_id')
        decision = request.data.get('decision')
        commentaire = request.data.get('commentaire', '')

        bac_verifie     = request.data.get('bac_verifie', False)
        diplome_verifie = request.data.get('diplome_verifie', False)
        releve_verifie  = request.data.get('releve_verifie', False)
        cin_verifie     = request.data.get('cin_verifie', False)

        if not dossier_id or not decision:
            return Response(
                {'error': 'dossier_id et decision sont obligatoires.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            convocation = ConvocationOrale.objects.get(
                epreuve_oral=epreuve, dossier_id=dossier_id
            )
        except ConvocationOrale.DoesNotExist:
            return Response(
                {'error': 'Convocation non trouvée.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        dossier_complet = bool(bac_verifie and diplome_verifie and releve_verifie and cin_verifie)

        if decision == ConvocationOrale.Decision.ACCEPTE and not dossier_complet:
            return Response(
                {'error': "Impossible d'accepter un dossier incomplet. Tous les documents doivent être vérifiés."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        dossier = convocation.dossier

        with transaction.atomic():
            convocation.decision = decision
            convocation.commentaire_jury = commentaire
            convocation.bac_verifie = bac_verifie
            convocation.diplome_verifie = diplome_verifie
            convocation.releve_notes_verifie = releve_verifie
            convocation.cin_verifie = cin_verifie
            convocation.dossier_complet = dossier_complet
            convocation.date_decision = timezone.now()
            convocation.decide_par = request.user
            convocation.save()

            if decision == ConvocationOrale.Decision.ACCEPTE:
                dossier.changer_statut(Dossier.Statut.ORAL_ACCEPTE, acteur=request.user, commentaire=commentaire)
                envoyer_notification(dossier, 'ORAL_ACCEPTE')
            elif decision == ConvocationOrale.Decision.REFUSE:
                dossier.changer_statut(Dossier.Statut.ORAL_REFUSE, acteur=request.user, commentaire=commentaire)
                envoyer_notification(dossier, 'ORAL_REFUSE')
            elif decision == ConvocationOrale.Decision.ABSENT:
                dossier.changer_statut(
                    Dossier.Statut.ORAL_REFUSE, acteur=request.user,
                    commentaire="Absent à l'oral",
                )

        return Response(ConvocationOraleSerializer(convocation).data)

    # ─────────────────────────────────────────────────────────────────
    # inscrire_acceptes
    # ─────────────────────────────────────────────────────────────────
    @action(detail=True, methods=['post'])
    def inscrire_acceptes(self, request, pk=None):
        epreuve = self.get_object()
        inscrits = 0
        with transaction.atomic():
            for conv in epreuve.convocations.filter(decision=ConvocationOrale.Decision.ACCEPTE):
                dossier = conv.dossier
                if dossier.statut == Dossier.Statut.ORAL_ACCEPTE:
                    dossier.changer_statut(Dossier.Statut.INSCRIT, acteur=request.user)
                    inscrits += 1

            epreuve.statut = EpreuveOrale.Statut.RESULTATS_PUBLIES
            epreuve.save(update_fields=['statut'])

        return Response({
            'message': f'{inscrits} candidats inscrits définitivement.',
            'inscrits': inscrits,
        })

    # ─────────────────────────────────────────────────────────────────
    # statistiques
    # ─────────────────────────────────────────────────────────────────
    @action(detail=True, methods=['get'])
    def statistiques(self, request, pk=None):
        epreuve = self.get_object()
        return Response({
            'total_convoques': epreuve.nb_convoques,
            'presents': epreuve.convocations.exclude(
                decision=ConvocationOrale.Decision.ABSENT
            ).count(),
            'absents': epreuve.nb_absents,
            'acceptes': epreuve.nb_acceptes,
            'refuses': epreuve.nb_refuses,
            'taux_acceptation': round(
                (epreuve.nb_acceptes / max(epreuve.nb_convoques, 1)) * 100, 2
            ),
            'dossiers_incomplets': epreuve.convocations.filter(dossier_complet=False).count(),
        })


# ─────────────────────────────────────────────────────────────────────────────
# ConvocationOraleViewSet
# ─────────────────────────────────────────────────────────────────────────────

class ConvocationOraleViewSet(viewsets.ModelViewSet):
    queryset = ConvocationOrale.objects.select_related(
        'epreuve_oral__filiere', 'dossier__candidat__user', 'dossier__filiere'
    ).all()
    serializer_class = ConvocationOraleSerializer
    permission_classes = [IsResponsableOrAdmin]

    @action(detail=True, methods=['get'],
            permission_classes=[permissions.IsAuthenticated])
    def telecharger_pdf(self, request, pk=None):
        convocation = self.get_object()

        if (
            getattr(request.user, 'role', '') == 'CANDIDAT'
            and convocation.dossier.candidat.user != request.user
        ):
            return Response({'error': 'Accès non autorisé.'}, status=status.HTTP_403_FORBIDDEN)

        if not convocation.convocation_pdf:
            return Response({'error': 'PDF non généré.'}, status=status.HTTP_404_NOT_FOUND)

        response = HttpResponse(
            convocation.convocation_pdf.open('rb'),
            content_type='application/pdf',
        )
        nom = convocation.dossier.candidat.nom
        response['Content-Disposition'] = (
            f'attachment; filename="Convocation_{nom}_ENSA_BM.pdf"'
        )
        return response

    @action(detail=False, methods=['get'],
            permission_classes=[permissions.IsAuthenticated])
    def ma_convocation(self, request):
        if getattr(request.user, 'role', '') != 'CANDIDAT':
            return Response(
                {'error': 'Accessible uniquement aux candidats.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            dossier = request.user.profil.dossiers.filter(
                statut__in=[
                    Dossier.Statut.CONVOQUE_ORAL,
                    Dossier.Statut.ORAL_ACCEPTE,
                    Dossier.Statut.ORAL_REFUSE,
                    Dossier.Statut.INSCRIT,
                ]
            ).latest('created_at')
            convocation = dossier.convocations_oral.latest('date_generation')
        except (Dossier.DoesNotExist, ConvocationOrale.DoesNotExist, AttributeError):
            return Response(
                {'error': 'Aucune convocation trouvée.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(ConvocationOraleSerializer(convocation).data)
