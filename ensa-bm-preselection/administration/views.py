# administration/views.py

from rest_framework import viewsets, generics, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Avg
from .models import Filiere, DiplomaAccepte, HistoriqueAction
from .serializers import FiliereSerializer, DiplomaAccepteSerializer, HistoriqueActionSerializer
from .permissions import IsResponsableOrAdmin, IsAdminOnly


class FiliereViewSet(viewsets.ModelViewSet):
    """
    CRUD complet des filières.
    GET    /api/filieres/         → liste toutes les filières
    POST   /api/filieres/         → créer une filière (admin)
    GET    /api/filieres/{id}/    → détail filière
    PUT    /api/filieres/{id}/    → modifier filière (admin)
    DELETE /api/filieres/{id}/    → supprimer filière (admin)
    POST   /api/filieres/{id}/toggle_status/ → activer/désactiver
    """
    queryset           = Filiere.objects.all()
    serializer_class   = FiliereSerializer

    def get_permissions(self):
        # Lecture autorisée pour tout le monde (y compris candidats)
        # Écriture réservée aux admins
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [IsAdminOnly()]

    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        filiere = self.get_object()
        filiere.is_active = not filiere.is_active
        filiere.save()
        etat = "activée" if filiere.is_active else "désactivée"
        return Response({"message": f"Filière {etat}.", "is_active": filiere.is_active})

    @action(detail=True, methods=['post'])
    def ajouter_diplome(self, request, pk=None):
        filiere    = self.get_object()
        serializer = DiplomaAccepteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(filiere=filiere)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def retirer_diplome(self, request, pk=None):
        filiere = self.get_object()
        diplome_id = request.data.get('diplome_id')
        if not diplome_id:
            return Response({"error": "Le paramètre diplome_id est obligatoire."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            diplome = DiplomaAccepte.objects.get(id=diplome_id, filiere=filiere)
            diplome.delete()
            return Response({"message": "Diplôme retiré de la filière."}, status=status.HTTP_200_OK)
        except DiplomaAccepte.DoesNotExist:
            return Response({"error": "Diplôme non trouvé pour cette filière."}, status=status.HTTP_404_NOT_FOUND)


class DashboardStatsView(generics.GenericAPIView):
    """
    GET /api/dashboard/stats/
    Retourne toutes les statistiques pour les graphiques du dashboard.
    """
    permission_classes = [IsResponsableOrAdmin]

    def get(self, request):
        from candidatures.models import Dossier
        from candidatures.serializers import DossierListSerializer

        # Statistiques globales
        total        = Dossier.objects.count()
        en_attente   = Dossier.objects.filter(statut='EN_ATTENTE').count()
        preselection = Dossier.objects.filter(statut='PRESELECTIONNE').count()
        rejetes      = Dossier.objects.filter(statut__in=['REJETE_AUTO', 'REJETE_FINAL']).count()
        suspects     = Dossier.objects.filter(is_suspect=True).count()

        # Répartition par filière
        par_filiere = list(
            Dossier.objects.values('filiere__nom')
                           .annotate(count=Count('id'))
                           .order_by('-count')
        )

        # Répartition par statut
        par_statut = list(
            Dossier.objects.values('statut')
                           .annotate(count=Count('id'))
                           .order_by('-count')
        )

        # Score moyen par filière
        scores = list(
            Dossier.objects.filter(score__isnull=False)
                           .values('filiere__nom')
                           .annotate(score_moyen=Avg('score'))
        )

        derniers_dossiers = Dossier.objects.select_related(
            'candidat', 'candidat__user', 'filiere'
        ).order_by('-date_soumission', '-created_at')[:10]

        return Response({
            "global": {
                "total": total,
                "en_attente": en_attente,
                "preselectionnes": preselection,
                "rejetes": rejetes,
                "suspects": suspects,
            },
            "par_filiere": par_filiere,
            "par_statut":  par_statut,
            "scores_moyens": scores,
            "derniers_dossiers": DossierListSerializer(derniers_dossiers, many=True).data,
        })
