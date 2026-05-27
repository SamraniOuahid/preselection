from django.test import TestCase
from rest_framework.test import APIClient

from administration.models import Filiere
from candidatures.models import Dossier
from users.models import Candidat, User


class UserRegistrationTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def _register_payload(self, **overrides):
        payload = {
            "email": "ahmed.benali@gmail.com",
            "cin": "AB123456",
            "password": "Test1234!",
            "password_confirm": "Test1234!",
            "nom": "Benali",
            "prenom": "Ahmed",
            "telephone": "0612345678",
            "date_naissance": "2002-01-01",
        }
        payload.update(overrides)
        return payload

    def _auth_header_for(self, user, password="Test1234!"):
        res = self.client.post(
            "/api/auth/login/",
            {"email": user.email, "password": password},
            format="json",
        )
        return {"HTTP_AUTHORIZATION": f"Bearer {res.data['access']}"}

    def test_register_creates_user_and_candidat(self):
        res = self.client.post("/api/auth/register/", self._register_payload(), format="json")
        self.assertEqual(res.status_code, 201)
        user = User.objects.get(email="ahmed.benali@gmail.com")
        self.assertTrue(Candidat.objects.filter(user=user).exists())
        self.assertIn("tokens", res.data)
        self.assertIn("access", res.data["tokens"])
        self.assertIn("refresh", res.data["tokens"])

    def test_register_duplicate_email_returns_400(self):
        User.objects.create_user(email="dup@test.com", cin="ZZ111111", password="Test1234!")
        res = self.client.post("/api/auth/register/", self._register_payload(email="dup@test.com"), format="json")
        self.assertEqual(res.status_code, 400)

    def test_register_duplicate_cin_returns_400(self):
        User.objects.create_user(email="a@test.com", cin="AB123456", password="Test1234!")
        res = self.client.post("/api/auth/register/", self._register_payload(email="new@test.com"), format="json")
        self.assertEqual(res.status_code, 400)

    def test_register_password_mismatch_returns_400(self):
        res = self.client.post(
            "/api/auth/register/",
            self._register_payload(password_confirm="Mismatch123!"),
            format="json",
        )
        self.assertEqual(res.status_code, 400)

    def test_login_returns_jwt_tokens(self):
        User.objects.create_user(email="login@test.com", cin="BC123456", password="Test1234!")
        res = self.client.post(
            "/api/auth/login/",
            {"email": "login@test.com", "password": "Test1234!"},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)
        self.assertIn("user", res.data)
        self.assertEqual(res.data["user"]["email"], "login@test.com")

    def test_login_wrong_password_returns_401(self):
        User.objects.create_user(email="login2@test.com", cin="BC123457", password="Test1234!")
        res = self.client.post(
            "/api/auth/login/",
            {"email": "login2@test.com", "password": "Wrong1234!"},
            format="json",
        )
        self.assertEqual(res.status_code, 401)

    def test_me_returns_user_with_profil(self):
        user = User.objects.create_user(email="me@test.com", cin="BC123458", password="Test1234!")
        Candidat.objects.create(user=user, nom="Test", prenom="User")
        res = self.client.get("/api/auth/me/", **self._auth_header_for(user))
        self.assertEqual(res.status_code, 200)
        self.assertIn("profil", res.data)
        self.assertEqual(res.data["profil"]["nom"], "Test")

    def test_candidat_cannot_see_other_candidat_data(self):
        filiere = Filiere.objects.create(nom="GIR2", code="GIR2", niveau="BAC2")
        user1 = User.objects.create_user(email="c1@test.com", cin="AA111111", password="Test1234!")
        user2 = User.objects.create_user(email="c2@test.com", cin="BB222222", password="Test1234!")
        cand1 = Candidat.objects.create(user=user1, nom="C1", prenom="Test")
        cand2 = Candidat.objects.create(user=user2, nom="C2", prenom="Test")
        Dossier.objects.create(
            candidat=cand1,
            filiere=filiere,
            diplome_obtenu="DUT Informatique",
            etablissement_origine="EST",
            annee_obtention=2022,
            moyenne_generale=14,
        )
        Dossier.objects.create(
            candidat=cand2,
            filiere=filiere,
            diplome_obtenu="DUT Informatique",
            etablissement_origine="EST",
            annee_obtention=2022,
            moyenne_generale=14,
        )
        res = self.client.get("/api/dossiers/", **self._auth_header_for(user1))
        self.assertEqual(res.status_code, 200)
        results = res.data.get("results", res.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["candidat_cin"], "AA111111")
