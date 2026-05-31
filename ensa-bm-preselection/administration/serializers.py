# administration/serializers.py

from rest_framework import serializers
from .models import Filiere, DiplomaAccepte, HistoriqueAction


class DiplomaAccepteSerializer(serializers.ModelSerializer):
    class Meta:
        model  = DiplomaAccepte
        fields = ['id', 'nom_diplome', 'etablissements', 'is_active']


class FiliereSerializer(serializers.ModelSerializer):
    diplomes_acceptes  = DiplomaAccepteSerializer(many=True, required=False)
    candidatures_count = serializers.ReadOnlyField()
    est_ouverte        = serializers.ReadOnlyField()
    epreuve_info       = serializers.SerializerMethodField()

    class Meta:
        model  = Filiere
        fields = [
            'id', 'nom', 'code', 'niveau', 'description',
            'places_disponibles', 'is_active', 'est_ouverte',
            'date_ouverture', 'date_fermeture',
            'diplomes_acceptes', 'candidatures_count',
            'date_ecrit', 'heure_ecrit', 'lieu_ecrit',
            'date_oral', 'heure_oral', 'lieu_oral',
            'epreuve_info',
        ]
        read_only_fields = ['id']

    def get_epreuve_info(self, obj):
        """
        Retourne les dates et informations de la dernière épreuve liée à cette filière.
        Cela permet aux candidats de connaître les dates écrit/oral avant de postuler.
        """
        # Prendre l'épreuve la plus récente
        epreuve = obj.epreuves.order_by('-created_at').first()
        
        # Obtenir les dates de l'écrit définies sur la filière
        filiere_date_ecrit = obj.date_ecrit.strftime('%d/%m/%Y') if obj.date_ecrit else None
        filiere_heure_ecrit = obj.heure_ecrit
        filiere_lieu_ecrit = obj.lieu_ecrit

        # Obtenir les dates de l'oral définies sur la filière
        filiere_date_oral = obj.date_oral.strftime('%d/%m/%Y') if obj.date_oral else None
        filiere_heure_oral = obj.heure_oral
        filiere_lieu_oral = obj.lieu_oral

        if not epreuve:
            return {
                'date_ecrit': filiere_date_ecrit,
                'heure_ecrit': filiere_heure_ecrit,
                'lieu_ecrit': filiere_lieu_ecrit,
                'date_oral': filiere_date_oral,
                'heure_oral': filiere_heure_oral,
                'lieu_oral': filiere_lieu_oral,
                'seuil_admission': None,
                'note_sur': None,
                'statut': None,
            }
        
        return {
            'date_ecrit':  epreuve.date_epreuve.strftime('%d/%m/%Y') if epreuve.date_epreuve else filiere_date_ecrit,
            'heure_ecrit': filiere_heure_ecrit, # de la filière
            'lieu_ecrit':  filiere_lieu_ecrit,  # de la filière
            'date_oral':   epreuve.date_oral.strftime('%d/%m/%Y')   if epreuve.date_oral   else filiere_date_oral,
            'heure_oral':  epreuve.heure_oral or filiere_heure_oral,
            'lieu_oral':   epreuve.lieu_oral or filiere_lieu_oral,
            'seuil_admission': float(epreuve.seuil_admission),
            'note_sur':    float(epreuve.note_sur),
            'statut':      epreuve.statut,
        }

    def create(self, validated_data):
        diplomes_data = validated_data.pop('diplomes_acceptes', [])
        filiere = Filiere.objects.create(**validated_data)
        for d_data in diplomes_data:
            DiplomaAccepte.objects.create(filiere=filiere, **d_data)
        return filiere

    def update(self, instance, validated_data):
        diplomes_data = validated_data.pop('diplomes_acceptes', None)
        
        # Mettre à jour les champs de base de la filière
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Si la liste des diplômes est fournie, on la met à jour
        if diplomes_data is not None:
            # Supprimer les anciens
            instance.diplomes_acceptes.all().delete()
            # Créer les nouveaux
            for d_data in diplomes_data:
                DiplomaAccepte.objects.create(filiere=instance, **d_data)

        return instance


class HistoriqueActionSerializer(serializers.ModelSerializer):
    acteur_nom = serializers.SerializerMethodField()

    class Meta:
        model  = HistoriqueAction
        fields = ['id', 'action', 'commentaire', 'timestamp', 'acteur_nom']

    def get_acteur_nom(self, obj):
        if obj.acteur:
            profil = getattr(obj.acteur, 'profil', None)
            return profil.nom_complet if profil else obj.acteur.email
        return "Système automatique"