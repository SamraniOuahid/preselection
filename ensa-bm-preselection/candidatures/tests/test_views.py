# candidatures/tests/test_views.py

from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase

from administration.models import DiplomaAccepte, Filiere
from candidatures.models import Dossier, Document
from scoring.models import ConfigScoring, RegleRejet
from users.models import Candidat, User


class DossierAPITest(APITestCase):
    def setUp(self):
        self.filiere = Filiere.objects.create(nom="Génie Informatique et Réseaux", code="GIR2", niveau="BAC2")
        DiplomaAccepte.objects.create(filiere=self.filiere, nom_diplome="DUT Informatique", etablissements=[], is_active=True)
        RegleRejet.objects.create(
            filiere=self.filiere,
            type_regle=RegleRejet.TypeRegle.DOCUMENT_MANQUANT,
            is_active=True,
            message_rejet="Documents manquants",
            parametre={},
        )
        RegleRejet.objects.create(
            filiere=self.filiere,
            type_regle=RegleRejet.TypeRegle.DIPLOME_INVALIDE,
            is_active=True,
            message_rejet="Diplôme non accepté",
            parametre={},
        )
        RegleRejet.objects.create(
            filiere=self.filiere,
            type_regle=RegleRejet.TypeRegle.MOYENNE_INSUFFISANTE,
            is_active=True,
            message_rejet="Moyenne insuffisante",
            parametre={"seuil": 12.0},
        )
        RegleRejet.objects.create(
            filiere=self.filiere,
            type_regle=RegleRejet.TypeRegle.DOUBLON_CIN,
            is_active=True,
            message_rejet="Doublon CIN",
            parametre={},
        )

        ConfigScoring.objects.create(filiere=self.filiere, matiere="Mathématiques", poids=50, bonus_mention={"TB": 2.0, "B": 1.0, "AB": 0.5, "P": 0.0})
        ConfigScoring.objects.create(filiere=self.filiere, matiere="Informatique", poids=50)

        self.user = User.objects.create_user(email="cand@test.com", cin="AB123456", password="Test1234!")
        self.candidat = Candidat.objects.create(user=self.user, nom="Benali", prenom="Ahmed")
        self.resp_user = User.objects.create_user(email="resp@test.com", cin="RR123456", password="Test1234!", role=User.Role.RESPONSABLE)

    def _token(self, user, password="Test1234!"):
        res = self.client.post("/api/auth/login/", {"email": user.email, "password": password}, format="json")
        return res.data["access"]

    def _auth_headers(self, user):
        return {"HTTP_AUTHORIZATION": f"Bearer {self._token(user)}"}

    def _dossier_payload(self, **overrides):
        payload = {
            "filiere": str(self.filiere.id),
            "diplome_obtenu": "DUT Informatique",
            "etablissement_origine": "EST",
            "annee_obtention": 2022,
            "mention": "B",
            "moyenne_generale": 14,
            "notes": [{"matiere": "Mathématiques", "note_declaree": 14}, {"matiere": "Informatique", "note_declaree": 16}],
        }
        payload.update(overrides)
        return payload

    def _add_documents(self, dossier, types=None):
        types = types or [Document.TypeDocument.DIPLOME, Document.TypeDocument.RELEVE, Document.TypeDocument.CIN, Document.TypeDocument.PHOTO]
        for type_doc in types:
            Document.objects.create(
                dossier=dossier,
                type_doc=type_doc,
                fichier=SimpleUploadedFile(f"{type_doc}.pdf", b"%PDF-1.4 test"),
            )

    def test_candidat_peut_creer_dossier(self):
        res = self.client.post("/api/dossiers/", self._dossier_payload(), format="json", **self._auth_headers(self.user))
        self.assertEqual(res.status_code, 201)
        self.assertEqual(Dossier.objects.count(), 1)

    def test_candidat_ne_voit_que_ses_dossiers(self):
        user2 = User.objects.create_user(email="cand2@test.com", cin="CD123456", password="Test1234!")
        cand2 = Candidat.objects.create(user=user2, nom="C2", prenom="Test")
        Dossier.objects.create(candidat=self.candidat, filiere=self.filiere, diplome_obtenu="DUT Informatique", etablissement_origine="EST", annee_obtention=2022, moyenne_generale=14)
        Dossier.objects.create(candidat=cand2, filiere=self.filiere, diplome_obtenu="DUT Informatique", etablissement_origine="EST", annee_obtention=2022, moyenne_generale=14)
        res = self.client.get("/api/dossiers/", **self._auth_headers(self.user))
        results = res.data.get("results", res.data)
        self.assertEqual(len(results), 1)

    @patch("notifications.services.envoyer_notification")
    @patch("candidatures.services.extraction.extraire_donnees_dossier")
    def test_soumettre_dossier_incomplet_retourne_incomplet(self, mock_extract, _mock_notif):
        mock_extract.return_value = {"succes": True, "notes_extraites": 0, "score_confiance": 1.0, "erreur": None}
        dossier_id = self.client.post("/api/dossiers/", self._dossier_payload(), format="json", **self._auth_headers(self.user)).data["id"]
        dossier = Dossier.objects.get(id=dossier_id)
        self._add_documents(dossier, types=[Document.TypeDocument.DIPLOME])
        res = self.client.post(f"/api/dossiers/{dossier_id}/soumettre/", **self._auth_headers(self.user))
        self.assertEqual(res.data["statut"], "INCOMPLET")

    @patch("notifications.services.envoyer_notification")
    @patch("candidatures.services.extraction.extraire_donnees_dossier")
    def test_soumettre_dossier_diplome_invalide_retourne_rejete(self, mock_extract, _mock_notif):
        mock_extract.return_value = {"succes": True, "notes_extraites": 0, "score_confiance": 1.0, "erreur": None}
        dossier_id = self.client.post("/api/dossiers/", self._dossier_payload(diplome_obtenu="Licence Physique"), format="json", **self._auth_headers(self.user)).data["id"]
        dossier = Dossier.objects.get(id=dossier_id)
        self._add_documents(dossier)
        res = self.client.post(f"/api/dossiers/{dossier_id}/soumettre/", **self._auth_headers(self.user))
        self.assertEqual(res.data["statut"], "REJETE_AUTO")

    @patch("notifications.services.envoyer_notification")
    @patch("candidatures.services.extraction.extraire_donnees_dossier")
    def test_soumettre_dossier_valide_retourne_en_attente(self, mock_extract, _mock_notif):
        mock_extract.return_value = {"succes": True, "notes_extraites": 0, "score_confiance": 1.0, "erreur": None}
        dossier_id = self.client.post("/api/dossiers/", self._dossier_payload(), format="json", **self._auth_headers(self.user)).data["id"]
        dossier = Dossier.objects.get(id=dossier_id)
        self._add_documents(dossier)
        res = self.client.post(f"/api/dossiers/{dossier_id}/soumettre/", **self._auth_headers(self.user))
        self.assertEqual(res.data["statut"], "EN_ATTENTE")

    def test_responsable_peut_valider_dossier(self):
        dossier = Dossier.objects.create(candidat=self.candidat, filiere=self.filiere, diplome_obtenu="DUT Informatique", etablissement_origine="EST", annee_obtention=2022, moyenne_generale=14, statut=Dossier.Statut.EN_ATTENTE)
        res = self.client.post(f"/api/dossiers/{dossier.id}/valider/", {}, **self._auth_headers(self.resp_user))
        dossier.refresh_from_db()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(dossier.statut, Dossier.Statut.PRESELECTIONNE)

    def test_responsable_peut_rejeter_avec_commentaire(self):
        dossier = Dossier.objects.create(candidat=self.candidat, filiere=self.filiere, diplome_obtenu="DUT Informatique", etablissement_origine="EST", annee_obtention=2022, moyenne_generale=14, statut=Dossier.Statut.EN_ATTENTE)
        res = self.client.post(f"/api/dossiers/{dossier.id}/rejeter/", {"commentaire": "Refus"}, format="json", **self._auth_headers(self.resp_user))
        dossier.refresh_from_db()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(dossier.statut, Dossier.Statut.REJETE_FINAL)

    def test_rejet_sans_commentaire_retourne_400(self):
        dossier = Dossier.objects.create(candidat=self.candidat, filiere=self.filiere, diplome_obtenu="DUT Informatique", etablissement_origine="EST", annee_obtention=2022, moyenne_generale=14, statut=Dossier.Statut.EN_ATTENTE)
        res = self.client.post(f"/api/dossiers/{dossier.id}/rejeter/", {}, format="json", **self._auth_headers(self.resp_user))
        self.assertEqual(res.status_code, 400)

    def test_candidat_ne_peut_pas_valider_dossier(self):
        dossier = Dossier.objects.create(candidat=self.candidat, filiere=self.filiere, diplome_obtenu="DUT Informatique", etablissement_origine="EST", annee_obtention=2022, moyenne_generale=14, statut=Dossier.Statut.EN_ATTENTE)
        res = self.client.post(f"/api/dossiers/{dossier.id}/valider/", {}, **self._auth_headers(self.user))
        self.assertEqual(res.status_code, 403)

    def test_export_excel_retourne_fichier(self):
        Dossier.objects.create(candidat=self.candidat, filiere=self.filiere, diplome_obtenu="DUT Informatique", etablissement_origine="EST", annee_obtention=2022, moyenne_generale=14, statut=Dossier.Statut.PRESELECTIONNE, score=15)
        res = self.client.get("/api/dossiers/export/", **self._auth_headers(self.resp_user))
        self.assertEqual(res.status_code, 200)
        self.assertIn("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", res["Content-Type"])
