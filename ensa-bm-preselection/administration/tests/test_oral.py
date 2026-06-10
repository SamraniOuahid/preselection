# administration/tests/test_oral.py

import datetime
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from administration.models import Filiere, EpreuveEcrite, EpreuveOrale, ConvocationOrale
from candidatures.models import Dossier
from users.models import User, Candidat

class EpreuveOraleTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Admin
        self.admin = User.objects.create_superuser(email="admin@ensa.ma", cin="ADMIN001", password="test")
        self.client.force_authenticate(user=self.admin)

        self.filiere = Filiere.objects.create(nom="Test Filiere", code="TEST-BAC2", niveau=Filiere.Niveau.BAC2)
        self.epreuve_orale = EpreuveOrale.objects.create(
            filiere=self.filiere,
            nom="Oral Test",
            date_oral=datetime.date.today(),
            heure_debut=datetime.time(9, 0),
            duree_minutes=20,
            lieu="Salle de test"
        )
        
        # Candidat 1
        self.user1 = User.objects.create_user(email="c1@ensa.ma", cin="C1", password="test")
        self.candidat1 = Candidat.objects.create(user=self.user1, nom="Doe", prenom="John")
        self.dossier1 = Dossier.objects.create(candidat=self.candidat1, filiere=self.filiere, statut=Dossier.Statut.ADMIS_FINAL, score=15.00)

        # Candidat 2
        self.user2 = User.objects.create_user(email="c2@ensa.ma", cin="C2", password="test")
        self.candidat2 = Candidat.objects.create(user=self.user2, nom="Smith", prenom="Jane")
        self.dossier2 = Dossier.objects.create(candidat=self.candidat2, filiere=self.filiere, statut=Dossier.Statut.ADMIS_FINAL, score=14.00)

    def test_convocation_generee_pour_admis_final(self):
        url = reverse('epreuve-oral-convoquer-admis', args=[self.epreuve_orale.id])
        res = self.client.post(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['convoques'], 2)
        
        self.epreuve_orale.refresh_from_db()
        self.assertEqual(self.epreuve_orale.statut, EpreuveOrale.Statut.EN_COURS)
        self.assertEqual(self.epreuve_orale.nb_convoques, 2)
        
        self.dossier1.refresh_from_db()
        self.assertEqual(self.dossier1.statut, Dossier.Statut.CONVOQUE_ORAL)

    def test_heure_passage_calculee_correctement(self):
        self.client.post(reverse('epreuve-oral-convoquer-admis', args=[self.epreuve_orale.id]))
        
        c1 = ConvocationOrale.objects.get(dossier=self.dossier1)
        c2 = ConvocationOrale.objects.get(dossier=self.dossier2)
        
        # John (score 15) is first
        self.assertEqual(c1.numero_passage, 1)
        self.assertEqual(c1.heure_passage, datetime.time(9, 0))
        
        # Jane (score 14) is second
        self.assertEqual(c2.numero_passage, 2)
        self.assertEqual(c2.heure_passage, datetime.time(9, 20))

    def test_pdf_convocation_genere_sans_erreur(self):
        self.client.post(reverse('epreuve-oral-convoquer-admis', args=[self.epreuve_orale.id]))
        c1 = ConvocationOrale.objects.get(dossier=self.dossier1)
        self.assertTrue(c1.convocation_generee)
        self.assertTrue(bool(c1.convocation_pdf))

    def test_decision_accepte_avec_docs_complets(self):
        self.client.post(reverse('epreuve-oral-convoquer-admis', args=[self.epreuve_orale.id]))
        
        url = reverse('epreuve-oral-enregistrer-decision', args=[self.epreuve_orale.id])
        res = self.client.post(url, {
            'dossier_id': self.dossier1.id,
            'decision': ConvocationOrale.Decision.ACCEPTE,
            'bac_verifie': True,
            'diplome_verifie': True,
            'releve_verifie': True,
            'cin_verifie': True,
            'commentaire': 'Très bien'
        }, format='json')
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.dossier1.refresh_from_db()
        self.assertEqual(self.dossier1.statut, Dossier.Statut.ORAL_ACCEPTE)

    def test_decision_accepte_refuse_si_docs_incomplets(self):
        self.client.post(reverse('epreuve-oral-convoquer-admis', args=[self.epreuve_orale.id]))
        
        url = reverse('epreuve-oral-enregistrer-decision', args=[self.epreuve_orale.id])
        res = self.client.post(url, {
            'dossier_id': self.dossier1.id,
            'decision': ConvocationOrale.Decision.ACCEPTE,
            'bac_verifie': True,
            'diplome_verifie': False,  # Missing one doc
            'releve_verifie': True,
            'cin_verifie': True
        }, format='json')
        
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_decision_refuse_change_statut_dossier(self):
        self.client.post(reverse('epreuve-oral-convoquer-admis', args=[self.epreuve_orale.id]))
        
        url = reverse('epreuve-oral-enregistrer-decision', args=[self.epreuve_orale.id])
        res = self.client.post(url, {
            'dossier_id': self.dossier1.id,
            'decision': ConvocationOrale.Decision.REFUSE,
        }, format='json')
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.dossier1.refresh_from_db()
        self.assertEqual(self.dossier1.statut, Dossier.Statut.ORAL_REFUSE)

    def test_absent_marque_comme_refuse(self):
        self.client.post(reverse('epreuve-oral-convoquer-admis', args=[self.epreuve_orale.id]))
        
        url = reverse('epreuve-oral-enregistrer-decision', args=[self.epreuve_orale.id])
        res = self.client.post(url, {
            'dossier_id': self.dossier1.id,
            'decision': ConvocationOrale.Decision.ABSENT,
        }, format='json')
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.dossier1.refresh_from_db()
        self.assertEqual(self.dossier1.statut, Dossier.Statut.ORAL_REFUSE)

    def test_inscription_definitive_oral_accepte(self):
        self.client.post(reverse('epreuve-oral-convoquer-admis', args=[self.epreuve_orale.id]))
        
        # Accept candidate 1
        self.client.post(reverse('epreuve-oral-enregistrer-decision', args=[self.epreuve_orale.id]), {
            'dossier_id': self.dossier1.id,
            'decision': ConvocationOrale.Decision.ACCEPTE,
            'bac_verifie': True,
            'diplome_verifie': True,
            'releve_verifie': True,
            'cin_verifie': True
        }, format='json')
        
        # Run inscription
        res = self.client.post(reverse('epreuve-oral-inscrire-acceptes', args=[self.epreuve_orale.id]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['inscrits'], 1)
        
        self.dossier1.refresh_from_db()
        self.assertEqual(self.dossier1.statut, Dossier.Statut.INSCRIT)
        
        self.epreuve_orale.refresh_from_db()
        self.assertEqual(self.epreuve_orale.statut, EpreuveOrale.Statut.RESULTATS_PUBLIES)
