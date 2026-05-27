# scoring/serializers.py

from rest_framework import serializers
from .models import RegleRejet, ConfigScoring


class RegleRejetSerializer(serializers.ModelSerializer):
    type_regle_label = serializers.CharField(source='get_type_regle_display', read_only=True)

    class Meta:
        model  = RegleRejet
        fields = ['id', 'filiere', 'type_regle', 'type_regle_label',
                  'is_active', 'message_rejet', 'parametre']
        read_only_fields = ['id']

    def validate_parametre(self, value):
        # Vérifier que le JSON paramètre est cohérent avec le type de règle
        type_regle = self.initial_data.get('type_regle')
        if type_regle == 'MOYENNE_INSUFFISANTE' and 'seuil' not in value:
            raise serializers.ValidationError("Ce type de règle nécessite un paramètre 'seuil'.")
        if type_regle == 'NOTE_ELIMINATOIRE':
            if 'matiere' not in value or 'seuil' not in value:
                raise serializers.ValidationError("Paramètres 'matiere' et 'seuil' requis.")
        return value


class ConfigScoringSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ConfigScoring
        fields = ['id', 'filiere', 'matiere', 'poids', 'bonus_mention']
        read_only_fields = ['id']

    def validate(self, attrs):
        # Vérifier que le total des poids pour une filière ne dépasse pas 100
        filiere = attrs.get('filiere')
        poids   = float(attrs.get('poids', 0))
        instance = self.instance

        configs_existantes = ConfigScoring.objects.filter(filiere=filiere)
        if instance:
            configs_existantes = configs_existantes.exclude(pk=instance.pk)

        total = sum(float(c.poids) for c in configs_existantes) + poids
        if total > 100:
            raise serializers.ValidationError(
                f"Le total des poids dépasse 100% (actuellement {total}%)."
            )
        return attrs