# candidatures/tests/test_integration.py

from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase

from administration.models import DiplomaAccepte, Filiere
from candidatures.models import Dossier
from scoring.models import ConfigScoring, RegleRejet
from users.models import User


class FluxCompletIntegrationTest(APITestCase):
    """Simule le parcours complet de A à Z : inscription → dépôt → soumission → scoring → décision."""

    def setUp(self):
        self.filiere = Filiere.objects.create(nom="Génie Informatique et Réseaux", code="GIR2", niveau="BAC2")
        DiplomaAccepte.objects.create(filiere=self.filiere, nom_diplome="DUT Informatique", etablissements=[], is_active=True)
        RegleRejet.objects.create(filiere=self.filiere, type_regle=RegleRejet.TypeRegle.DOCUMENT_MANQUANT, is_active=True, message_rejet="Documents manquants", parametre={})
        RegleRejet.objects.create(filiere=self.filiere, type_regle=RegleRejet.TypeRegle.DIPLOME_INVALIDE, is_active=True, message_rejet="Diplôme non accepté", parametre={})
        RegleRejet.objects.create(filiere=self.filiere, type_regle=RegleRejet.TypeRegle.MOYENNE_INSUFFISANTE, is_active=True, message_rejet="Moyenne insuffisante", parametre={"seuil": 12.0})
        RegleRejet.objects.create(filiere=self.filiere, type_regle=RegleRejet.TypeRegle.DOUBLON_CIN, is_active=True, message_rejet="Doublon CIN", parametre={})
        ConfigScoring.objects.create(filiere=self.filiere, matiere="Mathématiques", poids=50, bonus_mention={"TB": 2.0, "B": 1.0, "AB": 0.5, "P": 0.0})
        ConfigScoring.objects.create(filiere=self.filiere, matiere="Informatique", poids=50)
        self.resp = User.objects.create_user(email="resp@test.com", cin="RR123456", password="Test1234!", role=User.Role.RESPONSABLE)

    def _register(self, email, cin):
        res = self.client.post(
            "/api/auth/register/",
            {
                "email": email,
                "cin": cin,
                "password": "Test1234!",
                "password_confirm": "Test1234!",
                "nom": "Test",
                "prenom": "User",
            },
            format="json",
        )
        return res.data["tokens"]["access"]

    def _login(self, email):
        res = self.client.post("/api/auth/login/", {"email": email, "password": "Test1234!"}, format="json")
        return res.data["access"]

    def _headers(self, token):
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def _create_dossier(self, token, **overrides):
        payload = {
            "filiere": str(self.filiere.id),
            "diplome_obtenu": "DUT Informatique",
            "etablissement_origine": "EST",
            "annee_obtention": 2022,
            "mention": "B",
            "moyenne_generale": 14,
            "notes": [
                {"matiere": "Mathématiques", "note_declaree": 14},
                {"matiere": "Informatique", "note_declaree": 16},
            ],
        }
        payload.update(overrides)
        res = self.client.post("/api/dossiers/", payload, format="json", **self._headers(token))
        return res.data["id"]

    def _upload_docs(self, token, dossier_id):
        for type_doc in ["DIPLOME", "RELEVE", "CIN", "PHOTO"]:
            self.client.post(
                "/api/documents/upload/",
                {"dossier_id": dossier_id, "type_doc": type_doc, "fichier": SimpleUploadedFile(f"{type_doc}.pdf", b"%PDF-1.4 test")},
                format="multipart",
                **self._headers(token),
            )

    @patch("notifications.services.envoyer_notification")
    @patch("candidatures.services.extraction.extraire_donnees_dossier")
    def test_flux_complet_candidat_preselectionne(self, mock_extract, _mock_notif):
        mock_extract.return_value = {"succes": True, "notes_extraites": 0, "score_confiance": 1.0, "erreur": None}
        token = self._register("cand1@test.com", "AA123456")
        dossier_id = self._create_dossier(token)
        self._upload_docs(token, dossier_id)
        res = self.client.post(f"/api/dossiers/{dossier_id}/soumettre/", **self._headers(token))
        self.assertEqual(res.data["statut"], "EN_ATTENTE")

        resp_token = self._login("resp@test.com")
        res = self.client.post(f"/api/dossiers/{dossier_id}/valider/", {}, format="json", **self._headers(resp_token))
        self.assertEqual(res.data["statut"], "PRESELECTIONNE")

    @patch("notifications.services.envoyer_notification")
    @patch("candidatures.services.extraction.extraire_donnees_dossier")
    def test_flux_complet_candidat_rejete_diplome(self, mock_extract, _mock_notif):
        mock_extract.return_value = {"succes": True, "notes_extraites": 0, "score_confiance": 1.0, "erreur": None}
        token = self._register("cand2@test.com", "BB123456")
        dossier_id = self._create_dossier(token, diplome_obtenu="Licence Physique")
        self._upload_docs(token, dossier_id)
        res = self.client.post(f"/api/dossiers/{dossier_id}/soumettre/", **self._headers(token))
        self.assertEqual(res.data["statut"], "REJETE_AUTO")

    @patch("notifications.services.envoyer_notification")
    @patch("candidatures.services.extraction.extraire_donnees_dossier")
    def test_flux_complet_candidat_rejete_moyenne(self, mock_extract, _mock_notif):
        mock_extract.return_value = {"succes": True, "notes_extraites": 0, "score_confiance": 1.0, "erreur": None}
        token = self._register("cand3@test.com", "CC123456")
        dossier_id = self._create_dossier(token, moyenne_generale=10)
        self._upload_docs(token, dossier_id)
        res = self.client.post(f"/api/dossiers/{dossier_id}/soumettre/", **self._headers(token))
        self.assertEqual(res.data["statut"], "REJETE_AUTO")

    @patch("notifications.services.envoyer_notification")
    @patch("candidatures.services.extraction.extraire_donnees_dossier")
    def test_flux_deux_candidats_classement_correct(self, mock_extract, _mock_notif):
        mock_extract.return_value = {"succes": True, "notes_extraites": 0, "score_confiance": 1.0, "erreur": None}
        token1 = self._register("cand4@test.com", "DD123456")
        token2 = self._register("cand5@test.com", "EE123456")
        dossier1 = self._create_dossier(token1, moyenne_generale=12)
        dossier2 = self._create_dossier(token2, moyenne_generale=15)
        self._upload_docs(token1, dossier1)
        self._upload_docs(token2, dossier2)
        self.client.post(f"/api/dossiers/{dossier1}/soumettre/", **self._headers(token1))
        self.client.post(f"/api/dossiers/{dossier2}/soumettre/", **self._headers(token2))

        resp_token = self._login("resp@test.com")
        d1 = self.client.get(f"/api/dossiers/{dossier1}/", **self._headers(resp_token)).data
        d2 = self.client.get(f"/api/dossiers/{dossier2}/", **self._headers(resp_token)).data
        self.assertLess(d2["classement"], d1["classement"])
