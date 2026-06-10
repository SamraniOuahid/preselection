# scoring/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import RegleRejet, ConfigScoring
from .serializers import RegleRejetSerializer, ConfigScoringSerializer
from administration.permissions import IsAdminOnly, IsResponsableOrAdmin


class RegleRejetViewSet(viewsets.ModelViewSet):
    """
    GET    /api/regles/?filiere=<id>  → règles d'une filière
    POST   /api/regles/               → créer une règle
    PATCH  /api/regles/{id}/          → modifier (ex: changer le seuil)
    POST   /api/regles/{id}/toggle/   → activer/désactiver
    """
    serializer_class   = RegleRejetSerializer
    permission_classes = [IsAdminOnly]
    filterset_fields   = ['filiere', 'type_regle', 'is_active']

    def get_queryset(self):
        return RegleRejet.objects.select_related('filiere').all()

    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        regle = self.get_object()
        regle.is_active = not regle.is_active
        regle.save()
        return Response({
            "message": f"Règle {'activée' if regle.is_active else 'désactivée'}.",
            "is_active": regle.is_active
        })


class ConfigScoringViewSet(viewsets.ModelViewSet):
    """
    GET  /api/scoring/?filiere=<id>  → config scoring d'une filière
    POST /api/scoring/preview/       → simuler un score sans sauvegarder
    """
    serializer_class   = ConfigScoringSerializer
    permission_classes = [IsAdminOnly]
    filterset_fields   = ['filiere']

    def get_queryset(self):
        return ConfigScoring.objects.select_related('filiere').all()

    @action(detail=False, methods=['post'], permission_classes=[IsResponsableOrAdmin])
    def preview_score(self, request):
        """
        Simule le calcul du score avec des notes données.
        Body: { filiere_id, notes: [{matiere, note}], mention, diplome }
        """
        from candidatures.services.scoring import calculer_score
        from administration.models import Filiere
        filiere_id = request.data.get('filiere_id')
        notes      = request.data.get('notes', [])
        mention    = request.data.get('mention', '')
        diplome    = request.data.get('diplome', '')

        if not filiere_id:
            return Response(
                {"error": "Le champ 'filiere_id' est obligatoire."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not isinstance(notes, list):
            return Response(
                {"error": "Le champ 'notes' doit être une liste."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        filiere_obj = Filiere.objects.filter(id=filiere_id).first()
        configs = ConfigScoring.objects.filter(filiere_id=filiere_id)
        score   = calculer_score(notes, configs, mention, diplome=diplome, filiere_obj=filiere_obj)
        return Response({"score_simule": round(score, 2)})
