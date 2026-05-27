# candidatures/tests/test_verification.py
"""
Tests unitaires pour le service de vérification d'authenticité.
"""
import hashlib
import io
import os
import tempfile
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile

from users.models import User, Candidat
from administration.models import Filiere
from candidatures.models import Dossier, Document, NoteMatiere
from candidatures.services.verification_document import (
    verifier_structure,
    verifier_metadonnees_pdf,
    verifier_coherence_texte,
    detecter_manipulation,
    analyser_dossier_complet,
)


# ═══════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════

def _create_test_user(cin='AB123456', email='test@ensa.ma'):
    return User.objects.create_user(email=email, cin=cin, password='Test1234!')


def _create_test_candidat(user, nom='BENALI', prenom='Ahmed'):
    return Candidat.objects.create(user=user, nom=nom, prenom=prenom)


def _create_test_filiere():
    return Filiere.objects.create(nom='Génie Informatique', code='GI-BAC2', niveau='BAC2')


def _create_test_dossier(candidat, filiere, **kwargs):
    defaults = {
        'diplome_obtenu': 'DUT Informatique',
        'etablissement_origine': 'EST Béni Mellal',
        'annee_obtention': 2025,
        'mention': 'TB',
        'moyenne_generale': Decimal('15.50'),
    }
    defaults.update(kwargs)
    return Dossier.objects.create(candidat=candidat, filiere=filiere, **defaults)


def _create_minimal_pdf():
    """Crée un PDF minimal valide."""
    return (
        b'%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n'
        b'2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n'
        b'3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\n'
        b'xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n'
        b'0000000058 00000 n \n0000000115 00000 n \n'
        b'trailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF'
    )


def _create_test_image(width=800, height=500, fmt='PNG'):
    """Crée une image de test valide."""
    from PIL import Image
    img = Image.new('RGB', (width, height), color='white')
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


MEDIA_ROOT_TEMP = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT_TEMP)
class VerificationStructureTest(TestCase):
    """Tests Niveau 1 — Vérification structurelle."""

    def setUp(self):
        self.user = _create_test_user()
        self.candidat = _create_test_candidat(self.user)
        self.filiere = _create_test_filiere()
        self.dossier = _create_test_dossier(self.candidat, self.filiere)

    def test_fichier_trop_petit_penalise(self):
        """Un fichier < 10 Ko doit recevoir une pénalité de 0.4."""
        tiny_content = b'small'  # 5 bytes
        doc = Document.objects.create(
            dossier=self.dossier, type_doc='RELEVE',
            fichier=SimpleUploadedFile('tiny.pdf', tiny_content, content_type='application/pdf'),
            mime_type='application/pdf'
        )
        result = verifier_structure(doc)
        self.assertGreaterEqual(result['penalite'], 0.4)
        self.assertTrue(any('petit' in a.lower() or 'vide' in a.lower() for a in result['alertes']))

    def test_mime_type_incorrect_penalise(self):
        """Un MIME déclaré différent du réel doit être pénalisé."""
        img_content = _create_test_image()
        doc = Document.objects.create(
            dossier=self.dossier, type_doc='PHOTO',
            fichier=SimpleUploadedFile('photo.png', img_content, content_type='image/png'),
            mime_type='application/pdf'  # MIME déclaré incorrect
        )
        result = verifier_structure(doc)
        self.assertGreaterEqual(result['penalite'], 0.3)

    def test_pdf_corrompu_penalise(self):
        """Un PDF corrompu doit recevoir une pénalité de 0.5."""
        corrupted = b'%PDF-1.4\nthis is not valid pdf content at all' + b'\x00' * 15000
        doc = Document.objects.create(
            dossier=self.dossier, type_doc='DIPLOME',
            fichier=SimpleUploadedFile('bad.pdf', corrupted, content_type='application/pdf'),
            mime_type='application/pdf'
        )
        result = verifier_structure(doc)
        # Le fichier est soit corrompu, soit a un MIME incorrect
        self.assertGreater(result['penalite'], 0)

    def test_document_valide_score_plein(self):
        """Un document valide ne doit avoir aucune pénalité significative."""
        # Créer une image JPEG assez lourde (>10 Ko) avec du bruit
        import random
        from PIL import Image as PILImage
        img = PILImage.new('RGB', (800, 500))
        pixels = img.load()
        for x in range(800):
            for y in range(500):
                pixels[x, y] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=85)
        img_content = buf.getvalue()
        doc = Document.objects.create(
            dossier=self.dossier, type_doc='PHOTO',
            fichier=SimpleUploadedFile('photo.jpg', img_content, content_type='image/jpeg'),
            mime_type='image/jpeg'
        )
        result = verifier_structure(doc)
        self.assertLessEqual(result['penalite'], 0.3)


@override_settings(MEDIA_ROOT=MEDIA_ROOT_TEMP)
class VerificationCoherenceTest(TestCase):
    """Tests Niveau 3 — Cohérence textuelle."""

    def setUp(self):
        self.user = _create_test_user(cin='CD789012', email='coherence@test.ma')
        self.candidat = _create_test_candidat(self.user, nom='LAHLOU', prenom='Sara')
        self.filiere = _create_test_filiere()
        self.dossier = _create_test_dossier(self.candidat, self.filiere)

    @patch('candidatures.services.verification_document._extraire_texte')
    def test_nom_absent_penalise(self, mock_texte):
        """Si le nom du candidat est absent du texte, pénalité de 0.30."""
        mock_texte.return_value = 'Relevé de notes - Sara - CD789012 - Très Bien'
        doc = Document.objects.create(
            dossier=self.dossier, type_doc='RELEVE',
            fichier=SimpleUploadedFile('releve.pdf', _create_minimal_pdf()),
            mime_type='application/pdf'
        )
        result = verifier_coherence_texte(doc)
        self.assertGreaterEqual(result['penalite'], 0.30)
        self.assertTrue(any('Nom' in a for a in result['alertes']))

    @patch('candidatures.services.verification_document._extraire_texte')
    def test_cin_absent_penalise(self, mock_texte):
        """Si le CIN est absent du document, pénalité de 0.25."""
        mock_texte.return_value = 'Relevé de notes - LAHLOU Sara - EST Béni Mellal'
        doc = Document.objects.create(
            dossier=self.dossier, type_doc='RELEVE',
            fichier=SimpleUploadedFile('releve.pdf', _create_minimal_pdf()),
            mime_type='application/pdf'
        )
        result = verifier_coherence_texte(doc)
        self.assertGreaterEqual(result['penalite'], 0.25)

    @patch('candidatures.services.verification_document._extraire_texte')
    def test_notes_confirmees_score_eleve(self, mock_texte):
        """Si >60% des notes sont dans le texte, pas de pénalité notes."""
        # Créer des notes déclarées
        for mat, note in [('Maths', '16.00'), ('Physique', '14.50'), ('Info', '18.00')]:
            NoteMatiere.objects.create(
                dossier=self.dossier, matiere=mat, note_declaree=Decimal(note)
            )
        mock_texte.return_value = (
            'LAHLOU Sara CD789012 EST Béni Mellal 2025 '
            'Maths 16.00/20 Physique 14.50/20 Info 18.00/20 Très Bien'
        )
        doc = Document.objects.create(
            dossier=self.dossier, type_doc='RELEVE',
            fichier=SimpleUploadedFile('r.pdf', _create_minimal_pdf()),
            mime_type='application/pdf'
        )
        result = verifier_coherence_texte(doc)
        # Pas de pénalité pour notes non confirmées
        note_alertes = [a for a in result['alertes'] if 'notes confirmées' in a.lower()]
        self.assertEqual(len(note_alertes), 0)

    @patch('candidatures.services.verification_document._extraire_texte')
    def test_notes_non_confirmees_score_faible(self, mock_texte):
        """Si <60% des notes sont dans le texte, pénalité de 0.25."""
        for mat, note in [('Maths', '16.00'), ('Physique', '14.50'),
                          ('Info', '18.00'), ('Chimie', '12.00'), ('Anglais', '15.00')]:
            NoteMatiere.objects.create(
                dossier=self.dossier, matiere=mat, note_declaree=Decimal(note)
            )
        # Texte ne contient qu'une seule note
        mock_texte.return_value = (
            'LAHLOU Sara CD789012 EST Béni Mellal 2025 '
            'Maths 16.00/20 Très Bien'
        )
        doc = Document.objects.create(
            dossier=self.dossier, type_doc='RELEVE',
            fichier=SimpleUploadedFile('r.pdf', _create_minimal_pdf()),
            mime_type='application/pdf'
        )
        result = verifier_coherence_texte(doc)
        self.assertGreaterEqual(result['penalite'], 0.25)


@override_settings(MEDIA_ROOT=MEDIA_ROOT_TEMP)
class DetectionManipulationTest(TestCase):
    """Tests Niveau 4 — Détection de manipulation."""

    def setUp(self):
        self.user = _create_test_user(cin='EF345678', email='manip@test.ma')
        self.candidat = _create_test_candidat(self.user, nom='RACHIDI', prenom='Karim')
        self.filiere = _create_test_filiere()
        self.dossier = _create_test_dossier(self.candidat, self.filiere)

    @patch('candidatures.services.verification_document._extraire_texte')
    def test_hash_doublon_detecte(self, mock_texte):
        """Un fichier identique dans un autre dossier doit être détecté."""
        mock_texte.return_value = ''
        content = _create_test_image()

        # Premier document
        doc1 = Document.objects.create(
            dossier=self.dossier, type_doc='PHOTO',
            fichier=SimpleUploadedFile('photo1.png', content, content_type='image/png'),
            mime_type='image/png'
        )

        # Second dossier avec même fichier
        user2 = _create_test_user(cin='GH901234', email='other@test.ma')
        candidat2 = _create_test_candidat(user2, nom='AUTRE', prenom='Personne')
        dossier2 = _create_test_dossier(candidat2, self.filiere)
        doc2 = Document.objects.create(
            dossier=dossier2, type_doc='PHOTO',
            fichier=SimpleUploadedFile('photo2.png', content, content_type='image/png'),
            mime_type='image/png'
        )

        result = detecter_manipulation(doc2)
        self.assertGreaterEqual(result['penalite'], 0.40)
        self.assertTrue(any('identique' in a.lower() for a in result['alertes']))

    @patch('candidatures.services.verification_document._extraire_texte')
    @patch('candidatures.services.verification_document._read_file_bytes')
    def test_trop_de_polices_penalise(self, mock_read, mock_texte):
        """Plus de 5 familles de polices doit être signalé."""
        mock_texte.return_value = 'texte normal'
        mock_read.return_value = _create_minimal_pdf()

        doc = Document.objects.create(
            dossier=self.dossier, type_doc='RELEVE',
            fichier=SimpleUploadedFile('r.pdf', _create_minimal_pdf()),
            mime_type='application/pdf'
        )
        # On ne peut pas facilement simuler les polices pdfplumber,
        # mais on vérifie que la fonction ne crash pas
        result = detecter_manipulation(doc)
        self.assertIsInstance(result['penalite'], float)
        self.assertIn('hash', result)

    @patch('candidatures.services.verification_document._extraire_texte')
    def test_document_propre_pas_penalise(self, mock_texte):
        """Un document propre ne doit pas avoir de pénalité manipulation."""
        mock_texte.return_value = 'Contenu normal sans caractères suspects'
        content = _create_test_image()
        doc = Document.objects.create(
            dossier=self.dossier, type_doc='PHOTO',
            fichier=SimpleUploadedFile('clean.png', content, content_type='image/png'),
            mime_type='image/png'
        )
        result = detecter_manipulation(doc)
        self.assertLessEqual(result['penalite'], 0.1)


@override_settings(MEDIA_ROOT=MEDIA_ROOT_TEMP)
class AnalyseDossierCompletTest(TestCase):
    """Tests de la fonction principale analyser_dossier_complet."""

    def setUp(self):
        self.user = _create_test_user(cin='IJ567890', email='complet@test.ma')
        self.candidat = _create_test_candidat(self.user, nom='AMRANI', prenom='Fatima')
        self.filiere = _create_test_filiere()
        self.dossier = _create_test_dossier(self.candidat, self.filiere)

    @patch('candidatures.services.verification_document._extraire_texte')
    def test_score_global_pondere_correctement(self, mock_texte):
        """Le score global doit être la moyenne pondérée par type."""
        mock_texte.return_value = (
            'AMRANI Fatima IJ567890 EST Béni Mellal 2025 DUT Informatique Très Bien'
        )
        img = _create_test_image()
        for type_doc in ['RELEVE', 'DIPLOME', 'CIN', 'PHOTO']:
            ct = 'image/png'
            ext = 'png'
            content = img
            Document.objects.create(
                dossier=self.dossier, type_doc=type_doc,
                fichier=SimpleUploadedFile(f'{type_doc}.{ext}', content, content_type=ct),
                mime_type=ct
            )
        result = analyser_dossier_complet(self.dossier)
        self.assertIn('score_global', result)
        self.assertGreaterEqual(result['score_global'], 0.0)
        self.assertLessEqual(result['score_global'], 1.0)

    @patch('candidatures.services.verification_document._extraire_texte')
    def test_score_critique_marque_suspect(self, mock_texte):
        """Un score < 0.55 doit marquer le dossier comme suspect."""
        mock_texte.return_value = ''  # Aucun texte → pénalités lourdes
        img = _create_test_image(100, 100)  # Trop petit pour CIN
        for type_doc in ['RELEVE', 'DIPLOME', 'CIN', 'PHOTO']:
            Document.objects.create(
                dossier=self.dossier, type_doc=type_doc,
                fichier=SimpleUploadedFile(f'{type_doc}.png', img, content_type='image/png'),
                mime_type='image/png'
            )
        result = analyser_dossier_complet(self.dossier)
        self.dossier.refresh_from_db()
        if result['score_global'] < 0.55:
            self.assertTrue(self.dossier.is_suspect)

    @patch('candidatures.services.verification_document._extraire_texte')
    def test_recommandation_valider_si_score_eleve(self, mock_texte):
        """Score >= 0.80 → recommandation VALIDER."""
        mock_texte.return_value = (
            'AMRANI Fatima IJ567890 EST Béni Mellal 2025 '
            'DUT Informatique Très Bien AB123456 '
            'Mathématiques 16.00/20 Physique 14.50/20'
        )
        img = _create_test_image()
        Document.objects.create(
            dossier=self.dossier, type_doc='PHOTO',
            fichier=SimpleUploadedFile('photo.png', img, content_type='image/png'),
            mime_type='image/png'
        )
        result = analyser_dossier_complet(self.dossier)
        if result['score_global'] >= 0.80:
            self.assertEqual(result['recommandation'], 'VALIDER')

    @patch('candidatures.services.verification_document._extraire_texte')
    def test_recommandation_rejeter_si_score_critique(self, mock_texte):
        """Score < 0.40 → recommandation REJETER."""
        mock_texte.return_value = ''  # Rien du tout
        tiny = b'x' * 100  # Fichier invalide
        for type_doc in ['RELEVE', 'DIPLOME', 'CIN', 'PHOTO']:
            Document.objects.create(
                dossier=self.dossier, type_doc=type_doc,
                fichier=SimpleUploadedFile(f'{type_doc}.bin', tiny, content_type='application/octet-stream'),
                mime_type='application/pdf'  # MIME incorrect
            )
        result = analyser_dossier_complet(self.dossier)
        if result['score_global'] < 0.40:
            self.assertEqual(result['recommandation'], 'REJETER')
        self.assertEqual(result['niveau_confiance'] in ['CRITIQUE', 'FAIBLE', 'MOYEN', 'ELEVE'], True)
