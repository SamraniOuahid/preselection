# candidatures/admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import Dossier, Document, NoteMatiere


class DocumentInline(admin.TabularInline):
    model   = Document
    extra   = 0
    fields  = ['type_doc', 'fichier', 'taille_ko', 'qualite_ocr']
    readonly_fields = ['taille_ko', 'qualite_ocr']


class NoteMatiereInline(admin.TabularInline):
    model   = NoteMatiere
    extra   = 0
    fields  = ['matiere', 'note_declaree', 'note_extraite', 'ecart', 'is_suspect']
    readonly_fields = ['note_extraite', 'ecart', 'is_suspect']


@admin.register(Dossier)
class DossierAdmin(admin.ModelAdmin):
    list_display   = ['candidat', 'filiere', 'statut_badge', 'score', 'classement',
                      'is_suspect', 'score_authenticite', 'date_soumission']
    list_filter    = ['statut', 'filiere', 'is_suspect', 'mention', 'massar_verifie']
    search_fields  = ['candidat__nom', 'candidat__prenom', 'candidat__user__cin',
                      'code_massar', 'cne']
    readonly_fields = ['score', 'classement', 'score_confiance_ocr', 'is_suspect',
                       'score_authenticite', 'massar_verifie',
                       'date_soumission', 'created_at', 'updated_at',
                       'rapport_verification']
    inlines        = [DocumentInline, NoteMatiereInline]
    ordering       = ['-score']

    fieldsets = (
        ('Informations générales', {
            'fields': ('candidat', 'filiere', 'statut', 'code_massar', 'cne')
        }),
        ('Académique', {
            'fields': ('diplome_obtenu', 'etablissement_origine',
                       'annee_obtention', 'mention', 'moyenne_generale')
        }),
        ('Résultats analyse', {
            'fields': ('score', 'classement', 'score_confiance_ocr',
                       'is_suspect', 'motif_rejet')
        }),
        ('Rapport de vérification', {
            'fields': ('rapport_verification',),
            'classes': ('collapse',),
        }),
        ('Dates', {
            'fields': ('date_soumission', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def statut_badge(self, obj):
        couleurs = {
            'BROUILLON':      'gray',
            'EN_TRAITEMENT':  'blue',
            'EN_ATTENTE':     'orange',
            'PRESELECTIONNE': 'green',
            'REJETE_AUTO':    'red',
            'REJETE_FINAL':   'darkred',
            'INCOMPLET':      'purple',
            'SUSPECT':        'brown',
        }
        couleur = couleurs.get(obj.statut, 'gray')
        return format_html(
            '<span style="color:white; background:{}; padding:3px 8px; border-radius:4px">{}</span>',
            couleur, obj.get_statut_display()
        )
    statut_badge.short_description = 'Statut'

    def rapport_verification(self, obj):
        """Affiche le rapport de vérification d'authenticité en HTML."""
        score = obj.score_authenticite
        alertes = obj.alertes_verification or []
        massar = obj.massar_verifie

        if score is None:
            return format_html('<em style="color:gray">Aucune vérification effectuée</em>')

        score_f = float(score)

        # Couleur de la barre
        if score_f >= 0.80:
            couleur, niveau = '#2ecc71', 'ÉLEVÉ'
        elif score_f >= 0.60:
            couleur, niveau = '#f39c12', 'MOYEN'
        elif score_f >= 0.40:
            couleur, niveau = '#e67e22', 'FAIBLE'
        else:
            couleur, niveau = '#e74c3c', 'CRITIQUE'

        # Recommandation
        if score_f >= 0.80:
            reco = '✅ VALIDER'
        elif score_f >= 0.40:
            reco = '⚠️ VÉRIFICATION MANUELLE'
        else:
            reco = '❌ REJETER'

        # Barre de score
        html = f'''
        <div style="max-width:500px">
            <div style="margin-bottom:8px">
                <strong>Score d'authenticité :</strong>
                <span style="font-size:1.3em; font-weight:bold; color:{couleur}">
                    {score_f:.0%}
                </span>
            </div>
            <div style="background:#ecf0f1; border-radius:6px; height:20px; margin-bottom:10px">
                <div style="background:{couleur}; width:{score_f*100:.0f}%;
                     height:100%; border-radius:6px; transition:width 0.3s"></div>
            </div>
            <div style="margin-bottom:8px">
                <strong>Niveau :</strong>
                <span style="background:{couleur}; color:white; padding:2px 8px;
                       border-radius:4px; font-size:0.85em">{niveau}</span>
                &nbsp;&nbsp;
                <strong>Massar :</strong>
                {"✅ Vérifié" if massar else "❌ Non vérifié"}
            </div>
            <div style="margin-bottom:8px">
                <strong>Recommandation :</strong> {reco}
            </div>
        '''

        if alertes:
            html += '<details><summary><strong>Alertes détectées ({}) :</strong></summary><ul style="margin-top:5px">'.format(len(alertes))
            for alerte in alertes:
                icon = '🔴' if any(k in alerte.lower() for k in ['critique', 'corrompu', 'identique']) else '🟡'
                html += f'<li>{icon} {alerte}</li>'
            html += '</ul></details>'

        html += '</div>'
        return format_html(html)

    rapport_verification.short_description = 'Rapport de vérification'