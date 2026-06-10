# administration/analytics_views.py
# Endpoint d'Analytics avancé pour le tableau de bord administrateur.
# Agrégations ORM optimisées — données directement consommables par Recharts.

from rest_framework import generics
from rest_framework.response import Response
from django.db.models import Count, Avg, Q
from django.db.models.functions import TruncDate
from .permissions import IsResponsableOrAdmin


class AdminAnalyticsStatsView(generics.GenericAPIView):
    """
    GET /api/admin/analytics/stats/
    Retourne toutes les statistiques d'analytics pour le tableau de bord
    Data Science destiné aux administrateurs et responsables pédagogiques.
    """
    permission_classes = [IsResponsableOrAdmin]

    def get(self, request):
        from candidatures.models import Dossier, Document, NoteMatiere
        from users.models import User, Candidat
        from administration.models import Filiere

        # ════════════════════════════════════════════════
        # 1. KPIs FLASH
        # ════════════════════════════════════════════════
        total_comptes = User.objects.filter(role=User.Role.CANDIDAT).count()
        total_dossiers = Dossier.objects.count()

        dossiers_complets = Dossier.objects.exclude(
            statut__in=['BROUILLON']
        ).count()

        taux_completion = round(
            (dossiers_complets / total_dossiers * 100) if total_dossiers > 0 else 0, 1
        )

        rejets_auto = Dossier.objects.filter(statut='REJETE_AUTO').count()
        alertes_fraudes = Dossier.objects.filter(is_suspect=True).count()

        # Dossiers validés (présélectionnés)
        preselectionnes = Dossier.objects.filter(statut='PRESELECTIONNE').count()

        # Dossiers en attente de décision
        en_attente = Dossier.objects.filter(statut='EN_ATTENTE').count()

        kpis = {
            'total_comptes': total_comptes,
            'total_inscriptions': total_dossiers,
            'dossiers_complets': dossiers_complets,
            'taux_completion': taux_completion,
            'rejets_auto': rejets_auto,
            'alertes_fraudes': alertes_fraudes,
            'preselectionnes': preselectionnes,
            'en_attente': en_attente,
        }

        # ════════════════════════════════════════════════
        # 2. ENTONNOIR DE RECRUTEMENT (Pipeline Funnel)
        # ════════════════════════════════════════════════
        # Comptes créés → Dossiers remplis → Pièces téléversées → Candidatures validées
        dossiers_remplis = Dossier.objects.exclude(statut='BROUILLON').count()

        # Dossiers ayant au moins un document
        dossiers_avec_docs = Dossier.objects.filter(
            documents__isnull=False
        ).distinct().count()

        # Candidatures validées = hors brouillon, en_traitement, incomplet
        candidatures_validees = Dossier.objects.filter(
            statut__in=['EN_ATTENTE', 'PRESELECTIONNE', 'SUSPECT',
                        'ADMIS_FINAL', 'REJETE_FINAL', 'RECALE_FINAL',
                        'ABSENT_ECRIT']
        ).count()

        entonnoir = [
            {'etape': 'Comptes créés', 'valeur': total_comptes},
            {'etape': 'Dossiers remplis', 'valeur': dossiers_remplis},
            {'etape': 'Pièces téléversées', 'valeur': dossiers_avec_docs},
            {'etape': 'Candidatures validées', 'valeur': candidatures_validees},
        ]

        # ════════════════════════════════════════════════
        # 3. CARTOGRAPHIE DES ORIGINES
        # ════════════════════════════════════════════════

        # 3a. Répartition par type de diplôme (Donut)
        diplomes_raw = list(
            Dossier.objects.exclude(diplome_obtenu='')
            .values('diplome_obtenu')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        # Regrouper les diplômes similaires
        diplome_groups = {}
        for d in diplomes_raw:
            nom = (d['diplome_obtenu'] or '').strip().upper()
            # Normalisation : extraire le type de diplôme principal
            mapped = 'Autre'
            for key in ['DUT', 'DEUG', 'BTS', 'DTS', 'LP', 'LEF', 'LICENCE']:
                if key in nom:
                    mapped = 'LP' if key == 'LICENCE' else key
                    break
            diplome_groups[mapped] = diplome_groups.get(mapped, 0) + d['count']

        par_diplome = [
            {'name': k, 'value': v}
            for k, v in sorted(diplome_groups.items(), key=lambda x: -x[1])
        ]

        # 3b. Top 5 villes/établissements d'origine (Bar chart)
        top_etablissements = list(
            Dossier.objects.exclude(etablissement_origine='')
            .values('etablissement_origine')
            .annotate(count=Count('id'))
            .order_by('-count')[:7]
        )
        par_etablissement = [
            {
                'name': e['etablissement_origine'][:30],
                'candidats': e['count']
            }
            for e in top_etablissements
        ]

        # ════════════════════════════════════════════════
        # 4. COMPÉTITIVITÉ PAR FILIÈRE
        # ════════════════════════════════════════════════
        filieres = Filiere.objects.filter(is_active=True)
        competitivite = []
        for f in filieres:
            nb_candidats = Dossier.objects.filter(filiere=f).exclude(
                statut='BROUILLON'
            ).count()
            places = f.places_disponibles or 1
            ratio = round(nb_candidats / places, 2) if places > 0 else 0
            competitivite.append({
                'filiere': f.code,
                'candidats': nb_candidats,
                'places': places,
                'ratio': ratio,
            })

        # Tri par nombre de candidats desc
        competitivite.sort(key=lambda x: -x['candidats'])

        # ════════════════════════════════════════════════
        # 5. CORRÉLATION & DÉTECTION FRAUDES (Scatter)
        # ════════════════════════════════════════════════
        # Croiser note_declaree vs note_extraite (NoteMatiere legacy)
        scatter_data = list(
            NoteMatiere.objects.filter(
                note_declaree__isnull=False,
                note_extraite__isnull=False
            ).values(
                'note_declaree', 'note_extraite', 'is_suspect', 'matiere', 'ecart'
            )[:500]  # Limiter pour la performance
        )

        fraude_scatter = [
            {
                'note_declaree': float(d['note_declaree']),
                'note_extraite': float(d['note_extraite']),
                'is_suspect': d['is_suspect'],
                'matiere': d['matiere'],
                'ecart': float(d['ecart']) if d['ecart'] is not None else 0,
            }
            for d in scatter_data
        ]

        # ════════════════════════════════════════════════
        # 6. COURBE DE CROISSANCE DES INSCRIPTIONS (par jour)
        # ════════════════════════════════════════════════
        inscriptions_par_jour = list(
            Dossier.objects.filter(date_soumission__isnull=False)
            .annotate(jour=TruncDate('date_soumission'))
            .values('jour')
            .annotate(count=Count('id'))
            .order_by('jour')
        )

        croissance = [
            {
                'date': d['jour'].strftime('%d/%m') if d['jour'] else '',
                'inscriptions': d['count'],
            }
            for d in inscriptions_par_jour
        ]

        # Calculer le cumul
        cumul = 0
        for c in croissance:
            cumul += c['inscriptions']
            c['cumul'] = cumul

        # ════════════════════════════════════════════════
        # 7. RÉPARTITION PAR STATUT (pour Donut secondaire)
        # ════════════════════════════════════════════════
        par_statut = list(
            Dossier.objects.values('statut')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        # ════════════════════════════════════════════════
        # 8. SCORE MOYEN PAR FILIÈRE
        # ════════════════════════════════════════════════
        scores_moyens = list(
            Dossier.objects.filter(score__isnull=False)
            .values('filiere__code')
            .annotate(
                score_moyen=Avg('score'),
                score_max=Avg('score'),  # On pourrait utiliser Max
            )
            .order_by('filiere__code')
        )
        scores_filieres = [
            {
                'filiere': s['filiere__code'],
                'score_moyen': round(float(s['score_moyen']), 2) if s['score_moyen'] else 0,
            }
            for s in scores_moyens
        ]

        return Response({
            'kpis': kpis,
            'entonnoir': entonnoir,
            'par_diplome': par_diplome,
            'par_etablissement': par_etablissement,
            'competitivite': competitivite,
            'fraude_scatter': fraude_scatter,
            'croissance': croissance,
            'par_statut': par_statut,
            'scores_filieres': scores_filieres,
        })
