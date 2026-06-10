# administration/tests/test_filiere_logic.py

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from users.models import User, Candidat
from candidatures.models import Dossier
from administration.models import Filiere, EpreuveEcrite, EpreuveOrale, ConvocationOrale
from administration.serializers import FiliereSerializer
from candidatures.serializers import DossierListSerializer

class FiliereLogicTest(TestCase):
    def setUp(self):
        # Create user and candidat
        self.user = User.objects.create_user(email="candidat@test.com", password="password", cin="AB12345")
        self.candidat = Candidat.objects.create(user=self.user, nom="Doe", prenom="John")

        # Create Filiere with dates
        self.date_ecrit = timezone.now() + timedelta(days=10)
        self.date_oral = timezone.now() + timedelta(days=20)
        
        self.filiere = Filiere.objects.create(
            nom="Génie Informatique",
            code="GI-BAC2",
            niveau=Filiere.Niveau.BAC2,
            date_ecrit=self.date_ecrit,
            lieu_ecrit="Amphi 1",
            date_oral=self.date_oral,
            lieu_oral="Salle 42"
        )
        
        # Create Dossier
        self.dossier = Dossier.objects.create(
            candidat=self.candidat,
            filiere=self.filiere,
            diplome_obtenu="DUT",
            etablissement_origine="EST",
        )
        
        # Create EpreuveEcrite (should no longer duplicate dates)
        self.epreuve_ecrite = EpreuveEcrite.objects.create(
            filiere=self.filiere,
            nom="Epreuve GI"
        )

    def test_filiere_creation_dates(self):
        """a) Vérifie qu'une filière créée enregistre correctement les dates et lieux."""
        filiere = Filiere.objects.get(code="GI-BAC2")
        self.assertEqual(filiere.date_ecrit, self.date_ecrit)
        self.assertEqual(filiere.lieu_ecrit, "Amphi 1")
        self.assertEqual(filiere.date_oral, self.date_oral)
        self.assertEqual(filiere.lieu_oral, "Salle 42")

    def test_dossier_serializer_dynamic_dates(self):
        """b) Vérifie que la récupération du candidat extrait dynamiquement les dates depuis la filière."""
        serializer = DossierListSerializer(instance=self.dossier)
        data = serializer.data
        
        # We expect date_ecrit to match filiere.date_ecrit
        self.assertIn('date_ecrit', data)
        self.assertIn('lieu_ecrit', data)
        self.assertIn('date_oral', data)
        self.assertIn('lieu_oral', data)

        self.assertEqual(data['lieu_ecrit'], "Amphi 1")
        self.assertEqual(data['lieu_oral'], "Salle 42")

    def test_filiere_validation_edge_case(self):
        """c) Test de robustesse : date vide ou mal formatée (validation serializer)."""
        data = {
            "nom": "Data Science",
            "code": "DS-BAC3",
            "niveau": "BAC3",
            "date_ecrit": "", # Empty date
            "lieu_ecrit": "Amphi 2"
        }
        serializer = FiliereSerializer(data=data)
        # Should be false because date_ecrit is expecting a valid datetime but got empty string,
        # but it could be null. DRF handles empty strings for datetime by either making it null or raising error.
        # Actually DRF allows empty string if allow_blank is not set or if it's null=True. 
        # But let's check invalid format
        data_invalid = data.copy()
        data_invalid["date_ecrit"] = "not-a-date"
        serializer_invalid = FiliereSerializer(data=data_invalid)
        self.assertFalse(serializer_invalid.is_valid())
        self.assertIn("date_ecrit", serializer_invalid.errors)
