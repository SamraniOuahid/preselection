# administration/views_epreuve.py
# Views pour la gestion des épreuves écrites

import io
from decimal import Decimal, InvalidOperation

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from django.db.models import Min, Max, Avg, Count, Q
from django.http import HttpResponse

from .models import EpreuveEcrite, NoteEcrite, HistoriqueAction
from .serializers_epreuve import (
    EpreuveEcriteSerializer, EpreuveEcriteDetailSerializer,
    NoteEcriteSerializer, NoteEcriteUpdateSerializer,
    ImportRapportSerializer,
)
from .permissions import IsResponsableOrAdmin
from .services.import_excel import (
    importer_notes_excel, recalculer_apres_changement_seuil,
    previsualiser_excel, generer_template_excel,
)
from .services.export_resultats import exporter_resultats_excel


class EpreuveEcriteViewSet(viewsets.ModelViewSet):
    """
    CRUD des épreuves écrites.
    Réservé aux Responsables et Admins.

    Endpoints générés :
        GET    /api/epreuves/
        POST   /api/epreuves/
        GET    /api/epreuves/{id}/
        PUT    /api/epreuves/{id}/
        DELETE /api/epreuves/{id}/

    Actions custom :
        POST /api/epreuves/{id}/importer_notes/
        POST /api/epreuves/{id}/changer_seuil/
        POST /api/epreuves/{id}/publier_resultats/
        GET  /api/epreuves/{id}/exporter_resultats/
        GET  /api/epreuves/{id}/statistiques/
        POST /api/epreuves/{id}/previsualiser_excel/
        GET  /api/epreuves/template_excel/
    """
    permission_classes = [IsResponsableOrAdmin]
    filterset_fields = ['filiere', 'statut']
    ordering_fields = ['created_at', 'date_epreuve', 'nom']
    ordering = ['-created_at']

    def get_queryset(self):
        return EpreuveEcrite.objects.select_related('filiere', 'created_by').all()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return EpreuveEcriteDetailSerializer
        return EpreuveEcriteSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    # ── Import des notes Excel ──

    @action(detail=True, methods=['post'],
            parser_classes=[MultiPartParser, FormParser])
    def importer_notes(self, request, pk=None):
        """
        Upload du fichier Excel et import des notes.
        Accepte multipart/form-data avec :
            fichier      : fichier Excel (.xlsx)
            colonne_cin  : 'A' (défaut)
            colonne_note : 'B' (défaut)
            ligne_debut  : 2 (défaut)
        """
        epreuve = self.get_object()
        fichier = request.FILES.get('fichier')

        if not fichier:
            return Response(
                {'error': 'Le fichier Excel est obligatoire.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Vérifier l'extension
        if not fichier.name.lower().endswith(('.xlsx', '.xls')):
            return Response(
                {'error': 'Format invalide. Seuls les fichiers .xlsx et .xls sont acceptés.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Vérifier la taille (10 Mo max)
        if fichier.size > 10 * 1024 * 1024:
            return Response(
                {'error': 'Le fichier dépasse la taille maximale de 10 Mo.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        colonne_cin = request.data.get('colonne_cin', 'A')
        colonne_note = request.data.get('colonne_note', 'B')
        ligne_debut = int(request.data.get('ligne_debut', 2))

        rapport = importer_notes_excel(
            fichier=fichier,
            epreuve_id=epreuve.id,
            colonne_cin=colonne_cin,
            colonne_note=colonne_note,
            ligne_debut=ligne_debut,
        )

        # Enregistrer l'action dans l'historique
        HistoriqueAction.objects.create(
            dossier=None,  # pas de dossier spécifique
            acteur=request.user,
            action=HistoriqueAction.TypeAction.MODIFICATION,
            commentaire=(
                f"Import notes Excel pour {epreuve.nom}: "
                f"{rapport['importees']} importées, "
                f"{len(rapport['erreurs'])} erreurs"
            )
        ) if rapport['succes'] else None

        return Response(
            ImportRapportSerializer(rapport).data,
            status=status.HTTP_200_OK if rapport['succes'] else status.HTTP_400_BAD_REQUEST
        )

    # ── Changer le seuil d'admission ──

    @action(detail=True, methods=['post'])
    def changer_seuil(self, request, pk=None):
        """
        Modifie le seuil d'admission dynamiquement.
        Body : { "seuil": 12.5 }
        """
        epreuve = self.get_object()
        seuil_str = request.data.get('seuil')

        if seuil_str is None:
            return Response(
                {'error': 'Le paramètre seuil est obligatoire.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            nouveau_seuil = Decimal(str(seuil_str))
        except (InvalidOperation, ValueError):
            return Response(
                {'error': 'Le seuil doit être un nombre valide.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if nouveau_seuil < 0 or nouveau_seuil > epreuve.note_sur:
            return Response(
                {'error': f'Le seuil doit être entre 0 et {epreuve.note_sur}.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ancien_seuil = epreuve.seuil_admission
        epreuve.seuil_admission = nouveau_seuil
        epreuve.save()

        # Recalculer tous les résultats
        result = recalculer_apres_changement_seuil(epreuve)

        # Historique
        HistoriqueAction.objects.create(
            dossier=None,
            acteur=request.user,
            action=HistoriqueAction.TypeAction.MODIFICATION,
            commentaire=(
                f"Seuil changé de {ancien_seuil} à {nouveau_seuil} "
                f"pour {epreuve.nom}. "
                f"Anciens admis: {result['anciens_admis']}, "
                f"Nouveaux admis: {result['nouveaux_admis']}"
            )
        )

        return Response({
            'ancien_seuil': float(ancien_seuil),
            'nouveau_seuil': float(nouveau_seuil),
            **result,
        })

    # ── Simuler un seuil (sans modification en base) ──

    @action(detail=True, methods=['get'])
    def simuler_seuil(self, request, pk=None):
        """
        Simule un changement de seuil sans modifier la base.
        Param: ?seuil=12.5
        """
        epreuve = self.get_object()
        seuil_str = request.query_params.get('seuil')

        if not seuil_str:
            return Response(
                {'error': 'Le paramètre seuil est obligatoire.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            seuil_test = Decimal(str(seuil_str))
        except (InvalidOperation, ValueError):
            return Response(
                {'error': 'Le seuil doit être un nombre valide.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Compter sans modifier
        nb_admis_actuel = epreuve.nb_admis
        nb_admis_simule = epreuve.notes.filter(
            note__isnull=False, note__gte=seuil_test
        ).count()
        nb_recales_simule = epreuve.notes.filter(
            note__isnull=False, note__lt=seuil_test
        ).count()

        return Response({
            'seuil_teste': float(seuil_test),
            'seuil_actuel': float(epreuve.seuil_admission),
            'nb_admis_actuel': nb_admis_actuel,
            'nb_admis_simule': nb_admis_simule,
            'nb_recales_simule': nb_recales_simule,
            'difference': nb_admis_simule - nb_admis_actuel,
        })

    # ── Publier les résultats ──

    @action(detail=True, methods=['post'])
    def publier_resultats(self, request, pk=None):
        """
        Publie les résultats et notifie tous les candidats.
        Irréversible — vérifie que statut = NOTES_IMPORTEES.
        """
        from notifications.services import envoyer_notification

        epreuve = self.get_object()

        if epreuve.statut != EpreuveEcrite.Statut.NOTES_IMPORTEES:
            return Response(
                {'error': 'Les résultats ne peuvent être publiés que si les notes sont importées.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Notifier tous les candidats
        notes = epreuve.notes.select_related(
            'dossier', 'dossier__candidat', 'dossier__candidat__user'
        ).all()

        for note in notes:
            if note.resultat == NoteEcrite.Resultat.ADMIS:
                envoyer_notification(note.dossier, 'ADMIS_FINAL')
            elif note.resultat == NoteEcrite.Resultat.RECALE:
                envoyer_notification(note.dossier, 'RECALE_FINAL')

        # Changer le statut
        epreuve.statut = EpreuveEcrite.Statut.RESULTATS_PUBLIES
        epreuve.save()

        return Response({
            'message': 'Résultats publiés avec succès. Tous les candidats ont été notifiés.',
            'nb_notifications': notes.count(),
        })

    # ── Exporter les résultats ──

    @action(detail=True, methods=['get'])
    def exporter_resultats(self, request, pk=None):
        """Télécharge le fichier Excel des résultats."""
        epreuve = self.get_object()
        return exporter_resultats_excel(epreuve.id)

    # ── Statistiques ──

    @action(detail=True, methods=['get'])
    def statistiques(self, request, pk=None):
        """Retourne les statistiques complètes de l'épreuve."""
        epreuve = self.get_object()

        notes_qs = epreuve.notes.filter(note__isnull=False)
        stats = notes_qs.aggregate(
            note_min=Min('note'),
            note_max=Max('note'),
            note_moyenne=Avg('note'),
        )

        total = epreuve.notes.count()
        nb_admis = epreuve.nb_admis
        nb_recales = epreuve.nb_recales
        nb_absents = epreuve.nb_absents
        taux_admission = round((nb_admis / total * 100), 1) if total > 0 else 0

        # Distribution par tranches de 2 points
        note_sur = float(epreuve.note_sur)
        distribution = []
        step = 2 if note_sur <= 20 else 5 if note_sur <= 50 else 10
        i = 0
        while i < note_sur:
            borne_inf = i
            borne_sup = min(i + step, note_sur)
            count = notes_qs.filter(note__gte=borne_inf, note__lt=borne_sup).count()
            # Inclure la borne sup pour la dernière tranche
            if borne_sup == note_sur:
                count = notes_qs.filter(note__gte=borne_inf, note__lte=borne_sup).count()
            distribution.append({
                'tranche': f'{borne_inf}-{borne_sup}',
                'borne_inf': borne_inf,
                'borne_sup': borne_sup,
                'count': count,
            })
            i += step

        return Response({
            'nb_admis': nb_admis,
            'nb_recales': nb_recales,
            'nb_absents': nb_absents,
            'taux_admission': taux_admission,
            'note_min': float(stats['note_min'] or 0),
            'note_max': float(stats['note_max'] or 0),
            'note_moyenne': round(float(stats['note_moyenne'] or 0), 2),
            'seuil_actuel': float(epreuve.seuil_admission),
            'note_sur': float(epreuve.note_sur),
            'total_candidats': total,
            'distribution': distribution,
        })

    # ── Prévisualiser le fichier Excel ──

    @action(detail=True, methods=['post'],
            parser_classes=[MultiPartParser, FormParser])
    def previsualiser_excel(self, request, pk=None):
        """
        Retourne un aperçu des premières lignes du fichier Excel
        pour que le responsable confirme les colonnes.
        """
        fichier = request.FILES.get('fichier')
        if not fichier:
            return Response(
                {'error': 'Le fichier Excel est obligatoire.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        colonne_cin = request.data.get('colonne_cin', 'A')
        colonne_note = request.data.get('colonne_note', 'B')
        ligne_debut = int(request.data.get('ligne_debut', 2))

        apercu = previsualiser_excel(
            fichier=fichier,
            colonne_cin=colonne_cin,
            colonne_note=colonne_note,
            ligne_debut=ligne_debut,
        )

        return Response(apercu)

    # ── Template Excel téléchargeable ──

    @action(detail=False, methods=['get'])
    def template_excel(self, request):
        """
        Retourne un fichier Excel template pour l'import des notes.
        GET /api/epreuves/template_excel/
        """
        wb = generer_template_excel()
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="template_notes.xlsx"'
        wb.save(response)
        return response


class NoteEcriteViewSet(viewsets.ModelViewSet):
    """
    CRUD des notes individuelles pour correction manuelle.
    Accessible en lecture à tous les staff, en écriture aux admins/responsables.
    """
    permission_classes = [IsResponsableOrAdmin]
    serializer_class = NoteEcriteSerializer
    filterset_fields = ['epreuve', 'resultat']
    search_fields = ['dossier__candidat__nom', 'dossier__candidat__user__cin']
    ordering_fields = ['note', 'rang_final']
    ordering = ['-note']

    def get_queryset(self):
        return NoteEcrite.objects.select_related(
            'epreuve', 'dossier', 'dossier__candidat',
            'dossier__candidat__user', 'dossier__filiere'
        ).all()

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return NoteEcriteUpdateSerializer
        return NoteEcriteSerializer

    def perform_update(self, serializer):
        """Après modification d'une note, recalculer le résultat."""
        note_ecrite = serializer.save()
        note_ecrite.calculer_resultat()
        # Recalculer le classement
        from .services.import_excel import recalculer_classement_final
        recalculer_classement_final(note_ecrite.epreuve)
