# candidatures/tests/test_services.py

from datetime import datetime

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from administration.models import DiplomaAccepte, Filiere
from candidatures.models import Document, Dossier, NoteMatiere
from candidatures.services.regles import evaluer_regles
from candidatures.services.scoring import calculer_score_dossier
from scoring.models import ConfigScoring, RegleRejet
from users.models import Candidat, User


class ReglesRejetTest(TestCase):
    def setUp(self):
        self.filiere = Filiere.objects.create(nom="Génie Informatique et Réseaux", code="GIR2", niveau="BAC2")
        self.user = User.objects.create_user(email="cand@test.com", cin="AB123456", password="Test1234!")
        self.candidat = Candidat.objects.create(user=self.user, nom="Benali", prenom="Ahmed")

        DiplomaAccepte.objects.create(filiere=self.filiere, nom_diplome="DUT Informatique", etablissements=[], is_active=True)

        self.rules = {
            "DOUBLON_CIN": RegleRejet.objects.create(
                filiere=self.filiere,
                type_regle=RegleRejet.TypeRegle.DOUBLON_CIN,
                is_active=True,
                message_rejet="Doublon CIN détecté",
                parametre={},
            ),
            "DOCUMENT_MANQUANT": RegleRejet.objects.create(
                filiere=self.filiere,
                type_regle=RegleRejet.TypeRegle.DOCUMENT_MANQUANT,
                is_active=True,
                message_rejet="Documents manquants",
                parametre={},
            ),
            "DIPLOME_INVALIDE": RegleRejet.objects.create(
                filiere=self.filiere,
                type_regle=RegleRejet.TypeRegle.DIPLOME_INVALIDE,
                is_active=True,
                message_rejet="Diplôme non accepté",
                parametre={},
            ),
            "MOYENNE_INSUFFISANTE": RegleRejet.objects.create(
                filiere=self.filiere,
                type_regle=RegleRejet.TypeRegle.MOYENNE_INSUFFISANTE,
                is_active=True,
                message_rejet="Moyenne insuffisante",
                parametre={"seuil": 12.0},
            ),
            "NOTE_ELIMINATOIRE": RegleRejet.objects.create(
                filiere=self.filiere,
                type_regle=RegleRejet.TypeRegle.NOTE_ELIMINATOIRE,
                is_active=True,
                message_rejet="Note éliminatoire",
                parametre={"matiere": "Mathématiques", "seuil": 8.0},
            ),
            "DATE_INCOHERENTE": RegleRejet.objects.create(
                filiere=self.filiere,
                type_regle=RegleRejet.TypeRegle.DATE_INCOHERENTE,
                is_active=True,
                message_rejet="Date incohérente",
                parametre={},
            ),
        }

    def _create_dossier(self, **overrides):
        defaults = {
            "candidat": self.candidat,
            "filiere": self.filiere,
            "diplome_obtenu": "DUT Informatique",
            "etablissement_origine": "EST",
            "annee_obtention": 2022,
            "mention": "B",
            "moyenne_generale": 14,
        }
        defaults.update(overrides)
        return Dossier.objects.create(**defaults)

    def _add_documents(self, dossier, types=None):
        types = types or [
            Document.TypeDocument.DIPLOME,
            Document.TypeDocument.RELEVE,
            Document.TypeDocument.CIN,
            Document.TypeDocument.PHOTO,
        ]
        for type_doc in types:
            Document.objects.create(
                dossier=dossier,
                type_doc=type_doc,
                fichier=SimpleUploadedFile(f"{type_doc}.pdf", b"%PDF-1.4 test"),
            )

    def test_diplome_invalide_rejette(self):
        dossier = self._create_dossier(diplome_obtenu="Licence Physique")
        self._add_documents(dossier)
        result = evaluer_regles(dossier)
        self.assertTrue(result["rejete"])
        self.assertEqual(result["regle"], RegleRejet.TypeRegle.DIPLOME_INVALIDE)

    def test_diplome_valide_passe(self):
        dossier = self._create_dossier()
        self._add_documents(dossier)
        self.assertFalse(evaluer_regles(dossier)["rejete"])

    def test_moyenne_insuffisante_rejette(self):
        dossier = self._create_dossier(moyenne_generale=10)
        self._add_documents(dossier)
        result = evaluer_regles(dossier)
        self.assertTrue(result["rejete"])
        self.assertEqual(result["regle"], RegleRejet.TypeRegle.MOYENNE_INSUFFISANTE)

    def test_moyenne_suffisante_passe(self):
        dossier = self._create_dossier(moyenne_generale=13)
        self._add_documents(dossier)
        self.assertFalse(evaluer_regles(dossier)["rejete"])

    def test_document_manquant_rejette(self):
        dossier = self._create_dossier()
        self._add_documents(dossier, types=[Document.TypeDocument.DIPLOME])
        result = evaluer_regles(dossier)
        self.assertTrue(result["rejete"])
        self.assertEqual(result["statut"], Dossier.Statut.INCOMPLET)

    def test_tous_documents_presents_passe(self):
        dossier = self._create_dossier()
        self._add_documents(dossier)
        self.assertFalse(evaluer_regles(dossier)["rejete"])

    def test_doublon_cin_rejette(self):
        dossier1 = self._create_dossier()
        self._add_documents(dossier1)
        dossier1.statut = Dossier.Statut.EN_ATTENTE
        dossier1.save(update_fields=["statut"])
        dossier2 = self._create_dossier()
        self._add_documents(dossier2)
        result = evaluer_regles(dossier2)
        self.assertTrue(result["rejete"])
        self.assertEqual(result["regle"], RegleRejet.TypeRegle.DOUBLON_CIN)

    def test_date_incoherente_rejette(self):
        dossier = self._create_dossier(annee_obtention=datetime.now().year + 1)
        self._add_documents(dossier)
        result = evaluer_regles(dossier)
        self.assertTrue(result["rejete"])
        self.assertEqual(result["regle"], RegleRejet.TypeRegle.DATE_INCOHERENTE)

    def test_aucune_regle_active_passe_tout(self):
        RegleRejet.objects.update(is_active=False)
        dossier = self._create_dossier()
        self.assertFalse(evaluer_regles(dossier)["rejete"])

    def test_ordre_evaluation_respecte(self):
        dossier = self._create_dossier(moyenne_generale=8)
        self._add_documents(dossier, types=[Document.TypeDocument.DIPLOME])
        result = evaluer_regles(dossier)
        self.assertTrue(result["rejete"])
        self.assertEqual(result["regle"], RegleRejet.TypeRegle.DOCUMENT_MANQUANT)


class ScoringTest(TestCase):
    def setUp(self):
        self.filiere = Filiere.objects.create(nom="Génie Informatique et Réseaux", code="GIR2", niveau="BAC2")
        self.user = User.objects.create_user(email="scoring@test.com", cin="CC123456", password="Test1234!")
        self.candidat = Candidat.objects.create(user=self.user, nom="Test", prenom="User")

        ConfigScoring.objects.create(
            filiere=self.filiere,
            matiere="Mathématiques",
            poids=30,
            bonus_mention={"TB": 2.0, "B": 1.0, "AB": 0.5, "P": 0.0},
        )
        ConfigScoring.objects.create(filiere=self.filiere, matiere="Informatique", poids=30)
        ConfigScoring.objects.create(filiere=self.filiere, matiere="Physique", poids=20)
        ConfigScoring.objects.create(filiere=self.filiere, matiere="Anglais", poids=10)
        ConfigScoring.objects.create(filiere=self.filiere, matiere="Français", poids=10)

    def _create_dossier(self, **overrides):
        defaults = {
            "candidat": self.candidat,
            "filiere": self.filiere,
            "diplome_obtenu": "DUT Informatique",
            "etablissement_origine": "EST",
            "annee_obtention": 2022,
            "mention": "B",
            "moyenne_generale": 14,
            "statut": Dossier.Statut.EN_ATTENTE,
        }
        defaults.update(overrides)
        return Dossier.objects.create(**defaults)

    def _add_notes(self, dossier, notes):
        for matiere, note in notes.items():
            NoteMatiere.objects.create(dossier=dossier, matiere=matiere, note_declaree=note)

    def test_score_calcule_correctement(self):
        dossier = self._create_dossier()
        self._add_notes(
            dossier,
            {
                "Mathématiques": 14,
                "Informatique": 16,
                "Physique": 12,
                "Anglais": 13,
                "Français": 10,
            },
        )
        self.assertAlmostEqual(calculer_score_dossier(dossier), 14.7, places=2)

    def test_bonus_mention_tb_ajoute_2_points(self):
        dossier = self._create_dossier(mention="TB")
        self._add_notes(dossier, {"Mathématiques": 14, "Informatique": 16})
        self.assertAlmostEqual(calculer_score_dossier(dossier), 11.0, places=2)

    def test_score_plafonne_a_20(self):
        dossier = self._create_dossier(mention="TB")
        self._add_notes(
            dossier,
            {
                "Mathématiques": 20,
                "Informatique": 20,
                "Physique": 20,
                "Anglais": 20,
                "Français": 20,
            },
        )
        self.assertEqual(calculer_score_dossier(dossier), 20.0)

    def test_score_zero_si_aucune_config(self):
        ConfigScoring.objects.all().delete()
        dossier = self._create_dossier()
        self._add_notes(dossier, {"Mathématiques": 12})
        self.assertEqual(calculer_score_dossier(dossier), 0.0)

    def test_classement_mis_a_jour_apres_nouveau_dossier(self):
        d1 = self._create_dossier(moyenne_generale=12)
        d2 = self._create_dossier(moyenne_generale=15)
        self._add_notes(d1, {"Mathématiques": 10, "Informatique": 10})
        self._add_notes(d2, {"Mathématiques": 15, "Informatique": 15})
        calculer_score_dossier(d1)
        calculer_score_dossier(d2)
        d1.refresh_from_db()
        d2.refresh_from_db()
        self.assertEqual(d2.classement, 1)
        self.assertEqual(d1.classement, 2)

    def test_egalite_score_tri_par_moyenne(self):
        d1 = self._create_dossier(moyenne_generale=12)
        d2 = self._create_dossier(moyenne_generale=15)
        self._add_notes(d1, {"Mathématiques": 12})
        self._add_notes(d2, {"Mathématiques": 12})
        calculer_score_dossier(d1)
        calculer_score_dossier(d2)
        d1.refresh_from_db()
        d2.refresh_from_db()
        self.assertEqual(d2.classement, 1)
        self.assertEqual(d1.classement, 2)
