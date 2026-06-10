# administration/management/commands/seed_data.py
"""
Commande Django pour insérer des données de test réalistes.

Usage : python manage.py seed_data
        python manage.py seed_data --flush   (vider avant de remplir)
"""

import random
from decimal import Decimal
from datetime import date

from django.core.management.base import BaseCommand
from django.utils import timezone

from users.models import User, Candidat
from administration.models import Filiere, DiplomaAccepte, HistoriqueAction
from candidatures.models import Dossier, Document, NoteMatiere
from scoring.models import RegleRejet, ConfigScoring
from notifications.models import Notification


# ── Données réalistes marocaines ────────────────────────────────

PRENOMS = [
    'Ouahid', 'Yassine', 'Amine', 'Fatima', 'Khadija', 'Mohamed',
    'Sara', 'Hamza', 'Imane', 'Rachid', 'Nadia', 'Ayoub',
    'Zineb', 'Omar', 'Houda', 'Mehdi', 'Salma', 'Khalid',
    'Asmaa', 'Ilyas', 'Mariam', 'Soufiane', 'Hajar', 'Badr',
]

NOMS = [
    'SAMRANI', 'EL IDRISSI', 'BENALI', 'OUAZZANI', 'TAZI',
    'ALAMI', 'BENNANI', 'CHRAIBI', 'EL FASSI', 'LAHLOU',
    'BOUZIDI', 'AMRANI', 'JAIDI', 'HASSANI', 'BERRADA',
    'MOUSSAOUI', 'KADIRI', 'EL MALKI', 'SEFRIOUI', 'ZIANI',
]

ETABLISSEMENTS = [
    'EST Béni Mellal', 'FST Béni Mellal', 'ENSA Marrakech',
    'EST Casablanca', 'FST Mohammedia', 'ENSAM Meknès',
    'EST Fès', 'ENSA Kenitra', 'FST Settat', 'EST Agadir',
    'ENCG Settat', 'FST Errachidia', 'EST Safi',
]

# Catalogue officiel synchronisé avec seed_diplomes
DIPLOMES_BAC2 = [
    ("DEUG SMA",                         "1.00"),
    ("DEUG SMI",                         "1.00"),
    ("DEUG SMP",                         "1.00"),
    ("DEUG SMC",                         "0.95"),
    ("DUT (EST)",                        "1.00"),
    ("BTS Filières industrielles",       "1.00"),
    ("BTS Filières techniques",          "1.00"),
    ("DTS (OFPPT) Filières techniques",  "0.95"),
]
DIPLOMES_BAC3 = [
    ("Licence d'Études Fondamentales - LEF (Filières scientifiques)", "1.00"),
    ("Licence Professionnelle - LP (Filières techniques/ingénierie)", "1.00"),
    ("Bachelor",                                                       "0.95"),
]
# Noms seuls pour usage aléatoire dans les dossiers
DIPLOMES_BAC2_NOMS = [n for n, _ in DIPLOMES_BAC2]
DIPLOMES_BAC3_NOMS = [n for n, _ in DIPLOMES_BAC3]

MATIERES_GI = ['Mathématiques', 'Informatique', 'Physique', 'Anglais', 'Français']
MATIERES_GE = ['Mathématiques', 'Physique', 'Électronique', 'Anglais', 'Français']
MATIERES_GC = ['Mathématiques', 'Physique', 'Mécanique', 'Anglais', 'Français']


class Command(BaseCommand):
    help = 'Insère des données de test réalistes dans la base de données'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush', action='store_true',
            help='Vider toutes les données avant de remplir',
        )

    def handle(self, *args, **options):
        if options['flush']:
            self.stdout.write(self.style.WARNING('🗑️  Suppression des données existantes...'))
            Notification.objects.all().delete()
            HistoriqueAction.objects.all().delete()
            NoteMatiere.objects.all().delete()
            Document.objects.all().delete()
            Dossier.objects.all().delete()
            ConfigScoring.objects.all().delete()
            RegleRejet.objects.all().delete()
            DiplomaAccepte.objects.all().delete()
            Filiere.objects.all().delete()
            Candidat.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()

        self.stdout.write(self.style.MIGRATE_HEADING('🌱 Insertion des données de test...'))

        # ── 1. Créer les comptes admin et responsable ──
        admin = self._create_user('admin@ensa-bm.ma', 'ADMIN000', 'ADMIN', 'Admin2025!')
        resp = self._create_user('responsable@ensa-bm.ma', 'RESP001', 'RESPONSABLE', 'Resp2025!')
        self.stdout.write(f'  ✅ Admin: admin@ensa-bm.ma / Admin2025!')
        self.stdout.write(f'  ✅ Responsable: responsable@ensa-bm.ma / Resp2025!')

        # ── 2. Créer les filières ──
        filieres = self._create_filieres()
        self.stdout.write(f'  ✅ {len(filieres)} filières créées')

        # ── 3. Diplômes acceptés ──
        self._create_diplomes(filieres)
        self.stdout.write(f'  ✅ Diplômes acceptés configurés')

        # ── 4. Règles de rejet ──
        self._create_regles(filieres)
        self.stdout.write(f'  ✅ Règles de rejet configurées')

        # ── 5. Configuration scoring ──
        self._create_scoring_configs(filieres)
        self.stdout.write(f'  ✅ Configurations de scoring créées')

        # ── 6. Candidats + Dossiers ──
        nb_candidats = self._create_candidats_et_dossiers(filieres)
        self.stdout.write(f'  ✅ {nb_candidats} candidats avec dossiers créés')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('═' * 50))
        self.stdout.write(self.style.SUCCESS('✅ Données de test insérées avec succès !'))
        self.stdout.write(self.style.SUCCESS('═' * 50))
        self.stdout.write('')
        self.stdout.write('  📧 Comptes de connexion :')
        self.stdout.write(f'     Admin       → admin@ensa-bm.ma / Admin2025!')
        self.stdout.write(f'     Responsable → responsable@ensa-bm.ma / Resp2025!')
        self.stdout.write(f'     Candidat    → candidat1@gmail.com / Cand2025!')
        self.stdout.write(f'                   (candidat1 à candidat{nb_candidats})')
        self.stdout.write('')

    def _create_user(self, email, cin, role, password):
        if User.objects.filter(email=email).exists():
            return User.objects.get(email=email)
        user = User.objects.create_user(
            email=email, cin=cin, password=password, role=role,
        )
        if role == 'ADMIN':
            user.is_staff = True
            user.is_superuser = True
            user.save()
        return user

    def _create_filieres(self):
        data = [
            ('Génie Informatique', 'GI-BAC2', 'BAC2', 30),
            ('Génie Électrique', 'GE-BAC2', 'BAC2', 25),
            ('Génie Civil', 'GC-BAC2', 'BAC2', 25),
            ('Génie Informatique', 'GI-BAC3', 'BAC3', 20),
            ('Génie Électrique', 'GE-BAC3', 'BAC3', 15),
        ]
        filieres = []
        now = timezone.now()
        for nom, code, niveau, places in data:
            f, _ = Filiere.objects.get_or_create(
                code=code,
                defaults={
                    'nom': nom, 'niveau': niveau,
                    'places_disponibles': places, 'is_active': True,
                    'description': f'Filière {nom} — Niveau {niveau}',
                    'date_ouverture': now - timezone.timedelta(days=30),
                    'date_fermeture': now + timezone.timedelta(days=60),
                },
            )
            filieres.append(f)
        return filieres

    def _create_diplomes(self, filieres):
        for f in filieres:
            catalogue = DIPLOMES_BAC2 if f.niveau == 'BAC2' else DIPLOMES_BAC3
            coef_autre = '0.80'
            f.coef_autre_diplome = coef_autre
            f.save(update_fields=['coef_autre_diplome'])
            for nom_diplome, coefficient in catalogue:
                DiplomaAccepte.objects.get_or_create(
                    filiere=f, nom_diplome=nom_diplome,
                    defaults={'coefficient': coefficient, 'is_active': True, 'etablissements': []},
                )

    def _create_regles(self, filieres):
        for f in filieres:
            regles = [
                ('DOUBLON_CIN', 'Candidature en double détectée (même CIN).', {}),
                ('DOCUMENT_MANQUANT', 'Un ou plusieurs documents obligatoires sont manquants.', {}),
                ('DIPLOME_INVALIDE', 'Le diplôme déclaré n\'est pas accepté pour cette filière.', {}),
                ('MOYENNE_INSUFFISANTE', 'La moyenne générale est inférieure au seuil requis.', {'seuil': 10.0}),
                ('NOTE_ELIMINATOIRE', 'Note éliminatoire en Mathématiques.', {'matiere': 'Mathématiques', 'seuil': 8.0}),
                ('DATE_INCOHERENTE', 'L\'année d\'obtention du diplôme est incohérente.', {}),
            ]
            for type_r, msg, params in regles:
                RegleRejet.objects.get_or_create(
                    filiere=f, type_regle=type_r,
                    defaults={'message_rejet': msg, 'parametre': params, 'is_active': True},
                )

    def _create_scoring_configs(self, filieres):
        configs = {
            'GI-BAC2': MATIERES_GI,
            'GE-BAC2': MATIERES_GE,
            'GC-BAC2': MATIERES_GC,
            'GI-BAC3': MATIERES_GI,
            'GE-BAC3': MATIERES_GE,
        }
        poids = [30, 25, 20, 15, 10]  # Total = 100%
        bonus = {'TB': 2.0, 'B': 1.0, 'AB': 0.5, 'P': 0.0}

        for f in filieres:
            matieres = configs.get(f.code, MATIERES_GI)
            for i, mat in enumerate(matieres):
                ConfigScoring.objects.get_or_create(
                    filiere=f, matiere=mat,
                    defaults={'poids': Decimal(str(poids[i])), 'bonus_mention': bonus},
                )

    def _create_candidats_et_dossiers(self, filieres):
        statuts_distribution = [
            # (statut, count) — distribution réaliste
            (Dossier.Statut.PRESELECTIONNE, 5),
            (Dossier.Statut.EN_ATTENTE, 4),
            (Dossier.Statut.REJETE_AUTO, 3),
            (Dossier.Statut.SUSPECT, 2),
            (Dossier.Statut.INCOMPLET, 2),
            (Dossier.Statut.BROUILLON, 2),
            (Dossier.Statut.REJETE_FINAL, 2),
        ]

        mentions = ['TB', 'B', 'AB', 'P', '']
        count = 0

        for statut, nb in statuts_distribution:
            for i in range(nb):
                count += 1
                prenom = random.choice(PRENOMS)
                nom = random.choice(NOMS)
                cin = f'B{random.choice("JKELM")}{random.randint(100000, 999999)}'
                email = f'candidat{count}@gmail.com'

                # Vérifier unicité
                if User.objects.filter(email=email).exists():
                    continue

                # Créer User + Candidat
                user = User.objects.create_user(
                    email=email, cin=cin, password='Cand2025!',
                    role='CANDIDAT',
                )
                candidat = Candidat.objects.create(
                    user=user, nom=nom, prenom=prenom,
                    telephone=f'06{random.randint(10000000, 99999999)}',
                    date_naissance=date(
                        random.randint(1998, 2004),
                        random.randint(1, 12),
                        random.randint(1, 28),
                    ),
                )

                # Choisir une filière aléatoire
                filiere = random.choice(filieres)
                diplomes = DIPLOMES_BAC2_NOMS if filiere.niveau == 'BAC2' else DIPLOMES_BAC3_NOMS
                mention = random.choice(mentions)

                # Moyenne réaliste selon le statut
                if statut in [Dossier.Statut.PRESELECTIONNE]:
                    moyenne = Decimal(str(round(random.uniform(14.0, 18.0), 2)))
                elif statut in [Dossier.Statut.EN_ATTENTE]:
                    moyenne = Decimal(str(round(random.uniform(12.0, 16.0), 2)))
                elif statut in [Dossier.Statut.REJETE_AUTO]:
                    moyenne = Decimal(str(round(random.uniform(7.0, 10.0), 2)))
                else:
                    moyenne = Decimal(str(round(random.uniform(10.0, 15.0), 2)))

                # Calculer un score réaliste
                score = None
                classement = None
                motif = ''

                if statut == Dossier.Statut.PRESELECTIONNE:
                    score = Decimal(str(round(random.uniform(14.0, 18.5), 2)))
                elif statut == Dossier.Statut.EN_ATTENTE:
                    score = Decimal(str(round(random.uniform(11.0, 15.0), 2)))
                elif statut == Dossier.Statut.REJETE_AUTO:
                    motif = random.choice([
                        'La moyenne générale est inférieure au seuil requis.',
                        'Le diplôme déclaré n\'est pas accepté pour cette filière.',
                        'Note éliminatoire en Mathématiques.',
                    ])

                is_suspect = statut == Dossier.Statut.SUSPECT

                dossier = Dossier.objects.create(
                    candidat=candidat,
                    filiere=filiere,
                    statut=statut,
                    diplome_obtenu=random.choice(diplomes),
                    etablissement_origine=random.choice(ETABLISSEMENTS),
                    annee_obtention=random.choice([2023, 2024, 2025]),
                    mention=mention,
                    moyenne_generale=moyenne,
                    score=score,
                    classement=classement,
                    motif_rejet=motif,
                    score_confiance_ocr=Decimal(str(round(random.uniform(0.7, 1.0), 2))) if score else None,
                    is_suspect=is_suspect,
                    date_soumission=timezone.now() - timezone.timedelta(days=random.randint(1, 20)) if statut != Dossier.Statut.BROUILLON else None,
                )

                # Créer les notes par matière
                matieres_filiere = {
                    'GI-BAC2': MATIERES_GI, 'GE-BAC2': MATIERES_GE,
                    'GC-BAC2': MATIERES_GC, 'GI-BAC3': MATIERES_GI,
                    'GE-BAC3': MATIERES_GE,
                }.get(filiere.code, MATIERES_GI)

                for mat in matieres_filiere:
                    note_dec = Decimal(str(round(random.uniform(8.0, 18.0), 2)))

                    # Notes extraites : proches ou avec écart si suspect
                    if is_suspect and mat == matieres_filiere[0]:
                        note_ext = note_dec + Decimal(str(round(random.uniform(1.0, 3.0), 2)))
                        ecart = abs(float(note_ext) - float(note_dec))
                        suspect_note = True
                    elif score:
                        note_ext = note_dec + Decimal(str(round(random.uniform(-0.3, 0.3), 2)))
                        note_ext = max(Decimal('0'), min(Decimal('20'), note_ext))
                        ecart = abs(float(note_ext) - float(note_dec))
                        suspect_note = ecart > 0.5
                    else:
                        note_ext = None
                        ecart = None
                        suspect_note = False

                    NoteMatiere.objects.create(
                        dossier=dossier,
                        matiere=mat,
                        note_declaree=note_dec,
                        note_extraite=note_ext,
                        ecart=Decimal(str(round(ecart, 2))) if ecart is not None else None,
                        is_suspect=suspect_note,
                    )

        # Recalculer les classements par filière
        for f in filieres:
            dossiers_eligibles = Dossier.objects.filter(
                filiere=f,
                statut__in=[Dossier.Statut.EN_ATTENTE, Dossier.Statut.PRESELECTIONNE],
                score__isnull=False,
            ).order_by('-score', '-moyenne_generale')

            for rang, d in enumerate(dossiers_eligibles, 1):
                d.classement = rang
                d.save(update_fields=['classement'])

        return count
