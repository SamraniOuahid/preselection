"""
Insère toutes les données de démonstration (filières, règles, scoring, comptes, dossiers).
Idempotent : peut être relancé sans erreur.
"""

from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import User, Candidat
from administration.models import Filiere, DiplomaAccepte
from scoring.models import RegleRejet, ConfigScoring
from candidatures.models import Dossier, NoteMatiere


FILIERES = [
    {
        'code': 'GIR2',
        'nom': 'Génie Informatique et Réseaux',
        'niveau': 'BAC2',
        'places': 35,
        'description': 'Filière Bac+2 en informatique et réseaux.',
    },
    {
        'code': 'GI2',
        'nom': 'Génie Industriel',
        'niveau': 'BAC2',
        'places': 30,
        'description': 'Filière Bac+2 en génie industriel.',
    },
    {
        'code': 'GI3',
        'nom': 'Génie Informatique',
        'niveau': 'BAC3',
        'places': 25,
        'description': 'Filière Bac+3 en informatique.',
    },
    {
        'code': 'GE3',
        'nom': 'Génie Électrique',
        'niveau': 'BAC3',
        'places': 25,
        'description': 'Filière Bac+3 en génie électrique.',
    },
]

GIR2_DIPLOMES = [
    'DUT Informatique',
    'DUT Réseaux et Télécommunications',
    'BTS Informatique',
    'DUT Génie Électrique',
]

GIR2_REGLES = [
    ('MOYENNE_INSUFFISANTE', 'La moyenne générale est insuffisante.', {'seuil': 12.0}),
    ('NOTE_ELIMINATOIRE', 'Note éliminatoire en Mathématiques.', {'matiere': 'Mathématiques', 'seuil': 8.0}),
    ('DOCUMENT_MANQUANT', 'Document obligatoire manquant.', {}),
    ('DIPLOME_INVALIDE', 'Diplôme non accepté pour cette filière.', {}),
    ('DOUBLON_CIN', 'Un dossier existe déjà pour ce CIN.', {}),
]

GIR2_SCORING = [
    ('Mathématiques', '30.00', {'TB': 2.0, 'B': 1.0, 'AB': 0.5, 'P': 0.0}),
    ('Informatique', '30.00', {}),
    ('Physique', '20.00', {}),
    ('Anglais', '10.00', {}),
    ('Français', '10.00', {}),
]

ACCOUNTS = [
    {
        'email': 'admin@ensa-bm.ma',
        'cin': 'AD000001',
        'password': 'Admin1234!',
        'role': User.Role.ADMIN,
        'is_staff': True,
        'is_superuser': True,
    },
    {
        'email': 'scolarite@ensa-bm.ma',
        'cin': 'SC000001',
        'password': 'Scolarite1234!',
        'role': User.Role.RESPONSABLE,
        'is_staff': True,
    },
    {
        'email': 'ahmed.benali@gmail.com',
        'cin': 'AB123456',
        'password': 'Test1234!',
        'role': User.Role.CANDIDAT,
        'candidat': {'nom': 'Benali', 'prenom': 'Ahmed', 'telephone': '0612345678'},
    },
    {
        'email': 'fatima.elhassani@gmail.com',
        'cin': 'CD789012',
        'password': 'Test1234!',
        'role': User.Role.CANDIDAT,
        'candidat': {'nom': 'Elhassani', 'prenom': 'Fatima', 'telephone': '0612345679'},
    },
]


class Command(BaseCommand):
    help = 'Insère les données de démo (filières, règles, comptes, dossiers exemples).'

    def handle(self, *args, **options):
        self.stdout.write('Insertion des données de démonstration...\n')

        filieres = {}
        for f in FILIERES:
            filiere, _ = Filiere.objects.update_or_create(
                code=f['code'],
                defaults={
                    'nom': f['nom'],
                    'niveau': f['niveau'],
                    'places_disponibles': f['places'],
                    'description': f['description'],
                    'is_active': True,
                },
            )
            filieres[f['code']] = filiere
            self.stdout.write(self.style.SUCCESS(f'  Filière {f["code"]} — OK'))

        gir2 = filieres['GIR2']

        for nom in GIR2_DIPLOMES:
            DiplomaAccepte.objects.update_or_create(
                filiere=gir2,
                nom_diplome=nom,
                defaults={'etablissements': [], 'is_active': True},
            )
        self.stdout.write(self.style.SUCCESS(f'  {len(GIR2_DIPLOMES)} diplômes GIR2 — OK'))

        for type_regle, message, parametre in GIR2_REGLES:
            RegleRejet.objects.update_or_create(
                filiere=gir2,
                type_regle=type_regle,
                defaults={
                    'is_active': True,
                    'message_rejet': message,
                    'parametre': parametre,
                },
            )
        self.stdout.write(self.style.SUCCESS(f'  {len(GIR2_REGLES)} règles GIR2 — OK'))

        for matiere, poids, bonus in GIR2_SCORING:
            ConfigScoring.objects.update_or_create(
                filiere=gir2,
                matiere=matiere,
                defaults={
                    'poids': Decimal(poids),
                    'bonus_mention': bonus,
                },
            )
        self.stdout.write(self.style.SUCCESS(f'  {len(GIR2_SCORING)} configs scoring GIR2 — OK'))

        users = {}
        for acc in ACCOUNTS:
            user, created = User.objects.update_or_create(
                email=acc['email'],
                defaults={
                    'cin': acc['cin'],
                    'role': acc['role'],
                    'is_staff': acc.get('is_staff', False),
                    'is_superuser': acc.get('is_superuser', False),
                    'email_verified': True,
                    'is_active': True,
                },
            )
            user.cin = acc['cin']
            user.role = acc['role']
            user.is_staff = acc.get('is_staff', False)
            user.is_superuser = acc.get('is_superuser', False)
            user.set_password(acc['password'])
            user.save()
            users[acc['email']] = user

            if acc.get('candidat'):
                Candidat.objects.update_or_create(user=user, defaults=acc['candidat'])

            self.stdout.write(self.style.SUCCESS(
                f'  Compte {acc["email"]} — {"créé" if created else "mis à jour"}'
            ))

        ahmed = Candidat.objects.get(user=users['ahmed.benali@gmail.com'])
        fatima = Candidat.objects.get(user=users['fatima.elhassani@gmail.com'])
        now = timezone.now()

        dossiers_demo = [
            {
                'candidat': ahmed,
                'filiere': gir2,
                'statut': Dossier.Statut.EN_ATTENTE,
                'diplome': 'DUT Informatique',
                'etablissement': 'EST Béni Mellal',
                'annee': 2024,
                'mention': 'B',
                'moyenne': Decimal('14.50'),
                'score': Decimal('15.20'),
                'classement': 1,
                'notes': [
                    ('Mathématiques', 14),
                    ('Informatique', 16),
                    ('Physique', 13),
                    ('Anglais', 12),
                    ('Français', 15),
                ],
            },
            {
                'candidat': fatima,
                'filiere': gir2,
                'statut': Dossier.Statut.EN_ATTENTE,
                'diplome': 'BTS Informatique',
                'etablissement': 'EST Khouribga',
                'annee': 2024,
                'mention': 'AB',
                'moyenne': Decimal('13.80'),
                'score': Decimal('14.10'),
                'classement': 2,
                'notes': [
                    ('Mathématiques', 13),
                    ('Informatique', 15),
                    ('Physique', 12),
                    ('Anglais', 14),
                    ('Français', 13),
                ],
            },
            {
                'candidat': ahmed,
                'filiere': filieres['GI2'],
                'statut': Dossier.Statut.BROUILLON,
                'diplome': 'DUT Génie Industriel',
                'etablissement': 'EST Béni Mellal',
                'annee': 2024,
                'mention': '',
                'moyenne': Decimal('13.00'),
                'score': None,
                'classement': None,
                'notes': [],
            },
            {
                'candidat': fatima,
                'filiere': filieres['GI3'],
                'statut': Dossier.Statut.PRESELECTIONNE,
                'diplome': 'Licence Sciences Informatiques',
                'etablissement': 'FS Béni Mellal',
                'annee': 2023,
                'mention': 'TB',
                'moyenne': Decimal('16.20'),
                'score': Decimal('17.50'),
                'classement': 1,
                'notes': [],
            },
            {
                'candidat': ahmed,
                'filiere': filieres['GE3'],
                'statut': Dossier.Statut.REJETE_AUTO,
                'diplome': 'Licence Physique',
                'etablissement': 'FS Béni Mellal',
                'annee': 2024,
                'mention': '',
                'moyenne': Decimal('11.00'),
                'score': None,
                'classement': None,
                'motif': 'Diplôme non accepté pour cette filière.',
                'notes': [],
            },
        ]

        for i, d in enumerate(dossiers_demo):
            dossier, created = Dossier.objects.update_or_create(
                candidat=d['candidat'],
                filiere=d['filiere'],
                defaults={
                    'statut': d['statut'],
                    'diplome_obtenu': d['diplome'],
                    'etablissement_origine': d['etablissement'],
                    'annee_obtention': d['annee'],
                    'mention': d.get('mention', ''),
                    'moyenne_generale': d['moyenne'],
                    'score': d['score'],
                    'classement': d['classement'],
                    'motif_rejet': d.get('motif', ''),
                    'date_soumission': now if d['statut'] != Dossier.Statut.BROUILLON else None,
                    'score_confiance_ocr': Decimal('0.92') if d['score'] else None,
                },
            )

            NoteMatiere.objects.filter(dossier=dossier).delete()
            for matiere, note in d.get('notes', []):
                NoteMatiere.objects.create(
                    dossier=dossier,
                    matiere=matiere,
                    note_declaree=Decimal(str(note)),
                )

            self.stdout.write(self.style.SUCCESS(
                f'  Dossier {d["candidat"].prenom} → {d["filiere"].code} [{d["statut"]}] — OK'
            ))

        self.stdout.write(self.style.SUCCESS('\n=== Données prêtes pour les tests ===\n'))
        self.stdout.write('Comptes :')
        self.stdout.write('  Admin        admin@ensa-bm.ma / Admin1234!')
        self.stdout.write('  Responsable  scolarite@ensa-bm.ma / Scolarite1234!')
        self.stdout.write('  Candidat 1   ahmed.benali@gmail.com / Test1234!')
        self.stdout.write('  Candidat 2   fatima.elhassani@gmail.com / Test1234!')
        self.stdout.write('\nFilières : GIR2, GI2, GI3, GE3 (GIR2 configurée avec règles + scoring)')
        self.stdout.write('Dossiers : 5 exemples (EN_ATTENTE, BROUILLON, PRESELECTIONNE, REJETE_AUTO)')
        self.stdout.write('\nLancez : python manage.py runserver  puis  npm run dev')
