# administration/tests.py
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch
import openpyxl
import io
from decimal import Decimal

from users.models import User, Candidat
from candidatures.models import Dossier
from administration.models import Filiere, EpreuveEcrite, NoteEcrite
from administration.services.import_excel import importer_notes_excel, recalculer_apres_changement_seuil


class EpreuveEcriteAPITestCase(APITestCase):
    def setUp(self):
        # Création des utilisateurs
        self.admin = User.objects.create_superuser(
            email="admin@test.com", cin="ADMIN1", password="password123"
        )
        self.responsable = User.objects.create_user(
            email="resp@test.com", cin="RESP1", password="password123", role=User.Role.RESPONSABLE
        )
        self.candidat_user_1 = User.objects.create_user(
            email="candidat1@test.com", cin="CIN1", password="password123"
        )
        self.candidat_user_2 = User.objects.create_user(
            email="candidat2@test.com", cin="CIN2", password="password123"
        )

        self.candidat_1 = Candidat.objects.create(user=self.candidat_user_1, nom="N1", prenom="P1")
        self.candidat_2 = Candidat.objects.create(user=self.candidat_user_2, nom="N2", prenom="P2")

        # Filière
        self.filiere = Filiere.objects.create(nom="Génie Informatique", code="GI", niveau="BAC2")

        # Dossiers présélectionnés
        self.dossier_1 = Dossier.objects.create(
            candidat=self.candidat_1,
            filiere=self.filiere,
            statut=Dossier.Statut.PRESELECTIONNE,
            score=15.00
        )
        self.dossier_2 = Dossier.objects.create(
            candidat=self.candidat_2,
            filiere=self.filiere,
            statut=Dossier.Statut.PRESELECTIONNE,
            score=14.00
        )

        # Épreuve écrite
        self.epreuve = EpreuveEcrite.objects.create(
            filiere=self.filiere,
            nom="Épreuve Écrite GI 2026",
            date_epreuve=timezone.now().date(),
            seuil_admission=Decimal("10.00"),
            note_sur=Decimal("20.00"),
            coefficient=Decimal("1.0"),
            statut=EpreuveEcrite.Statut.NON_COMMENCEE,
            created_by=self.admin
        )

    def _token(self, user):
        res = self.client.post("/api/auth/login/", {"email": user.email, "password": "password123"}, format="json")
        return res.data["access"]

    def _auth_headers(self, user):
        return {"HTTP_AUTHORIZATION": f"Bearer {self._token(user)}"}

    def test_responsable_peut_voir_epreuves(self):
        res = self.client.get("/api/epreuves/", **self._auth_headers(self.responsable))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_candidat_ne_peut_pas_voir_epreuves(self):
        res = self.client.get("/api/epreuves/", **self._auth_headers(self.candidat_user_1))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_creer_epreuve(self):
        payload = {
            "filiere": str(self.filiere.id),
            "nom": "Nouvelle Épreuve Test",
            "date_epreuve": "2026-06-01",
            "note_sur": 20,
            "coefficient": 1.5,
            "seuil_admission": 12
        }
        res = self.client.post("/api/epreuves/", payload, format="json", **self._auth_headers(self.responsable))
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(EpreuveEcrite.objects.filter(nom="Nouvelle Épreuve Test").count(), 1)

    def test_simuler_seuil(self):
        # Création des notes pour simulation
        NoteEcrite.objects.create(epreuve=self.epreuve, dossier=self.dossier_1, note=Decimal("14.00"), resultat="ADMIS")
        NoteEcrite.objects.create(epreuve=self.epreuve, dossier=self.dossier_2, note=Decimal("8.00"), resultat="RECALE")

        res = self.client.get(
            f"/api/epreuves/{self.epreuve.id}/simuler_seuil/?seuil=12",
            **self._auth_headers(self.responsable)
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["nb_admis_simule"], 1)
        self.assertEqual(res.data["nb_recales_simule"], 1)

    def test_changer_seuil(self):
        NoteEcrite.objects.create(epreuve=self.epreuve, dossier=self.dossier_1, note=Decimal("11.00"), resultat="ADMIS")
        NoteEcrite.objects.create(epreuve=self.epreuve, dossier=self.dossier_2, note=Decimal("9.00"), resultat="RECALE")

        payload = {"seuil": "12.00"}
        res = self.client.post(
            f"/api/epreuves/{self.epreuve.id}/changer_seuil/",
            payload,
            format="json",
            **self._auth_headers(self.responsable)
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        self.epreuve.refresh_from_db()
        self.assertEqual(self.epreuve.seuil_admission, Decimal("12.00"))
        
        # Le dossier 1 doit maintenant être recalé car sa note est 11 < 12
        self.dossier_1.refresh_from_db()
        self.assertEqual(self.dossier_1.statut, Dossier.Statut.RECALE_FINAL)

    @patch("notifications.services.envoyer_notification")
    def test_publier_resultats(self, mock_envoyer_notification):
        NoteEcrite.objects.create(epreuve=self.epreuve, dossier=self.dossier_1, note=Decimal("12.00"), resultat="ADMIS")
        NoteEcrite.objects.create(epreuve=self.epreuve, dossier=self.dossier_2, note=Decimal("8.00"), resultat="RECALE")
        
        self.epreuve.statut = EpreuveEcrite.Statut.NOTES_IMPORTEES
        self.epreuve.save()

        res = self.client.post(
            f"/api/epreuves/{self.epreuve.id}/publier_resultats/",
            {},
            format="json",
            **self._auth_headers(self.responsable)
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        self.epreuve.refresh_from_db()
        self.assertEqual(self.epreuve.statut, EpreuveEcrite.Statut.RESULTATS_PUBLIES)
        self.assertEqual(mock_envoyer_notification.call_count, 2)

    def test_exporter_resultats(self):
        NoteEcrite.objects.create(epreuve=self.epreuve, dossier=self.dossier_1, note=Decimal("12.00"), resultat="ADMIS")
        NoteEcrite.objects.create(epreuve=self.epreuve, dossier=self.dossier_2, note=Decimal("8.00"), resultat="RECALE")

        res = self.client.get(
            f"/api/epreuves/{self.epreuve.id}/exporter_resultats/",
            **self._auth_headers(self.responsable)
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", res["Content-Type"])


class ExcelImportServiceTestCase(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email="admin@test.com", cin="ADMIN1", password="password123"
        )
        self.candidat_user_1 = User.objects.create_user(
            email="candidat1@test.com", cin="CIN1", password="password123"
        )
        self.candidat_user_2 = User.objects.create_user(
            email="candidat2@test.com", cin="CIN2", password="password123"
        )

        self.candidat_1 = Candidat.objects.create(user=self.candidat_user_1, nom="N1", prenom="P1")
        self.candidat_2 = Candidat.objects.create(user=self.candidat_user_2, nom="N2", prenom="P2")

        self.filiere = Filiere.objects.create(nom="Génie Informatique", code="GI", niveau="BAC2")

        self.dossier_1 = Dossier.objects.create(
            candidat=self.candidat_1,
            filiere=self.filiere,
            statut=Dossier.Statut.PRESELECTIONNE,
            score=15.00
        )
        self.dossier_2 = Dossier.objects.create(
            candidat=self.candidat_2,
            filiere=self.filiere,
            statut=Dossier.Statut.PRESELECTIONNE,
            score=14.00
        )

        self.epreuve = EpreuveEcrite.objects.create(
            filiere=self.filiere,
            nom="Épreuve Écrite GI 2026",
            date_epreuve=timezone.now().date(),
            seuil_admission=Decimal("10.00"),
            note_sur=Decimal("20.00"),
            coefficient=Decimal("1.0"),
            statut=EpreuveEcrite.Statut.NON_COMMENCEE,
            created_by=self.admin
        )

    def _generer_excel_mock(self, data):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["CIN", "Note"])
        for cin, note in data:
            ws.append([cin, note])
        
        stream = io.BytesIO()
        wb.save(stream)
        stream.seek(0)
        return SimpleUploadedFile("notes.xlsx", stream.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    def test_import_excel_succes(self):
        data = [
            ("CIN1", "15.5"),
            ("CIN2", "8.0"),
        ]
        file_mock = self._generer_excel_mock(data)
        
        rapport = importer_notes_excel(
            fichier=file_mock,
            epreuve_id=self.epreuve.id,
            colonne_cin="A",
            colonne_note="B",
            ligne_debut=2
        )
        
        self.assertTrue(rapport["succes"])
        self.assertEqual(rapport["importees"], 2)
        self.assertEqual(rapport["nb_admis"], 1)
        self.assertEqual(rapport["nb_recales"], 1)

        # Vérification en base de données
        n1 = NoteEcrite.objects.get(epreuve=self.epreuve, dossier=self.dossier_1)
        n2 = NoteEcrite.objects.get(epreuve=self.epreuve, dossier=self.dossier_2)
        
        self.assertEqual(n1.note, Decimal("15.5"))
        self.assertEqual(n1.resultat, NoteEcrite.Resultat.ADMIS)
        self.assertEqual(n2.note, Decimal("8.0"))
        self.assertEqual(n2.resultat, NoteEcrite.Resultat.RECALE)
