"""Crée les comptes de démonstration pour tester la connexion."""

from django.core.management.base import BaseCommand
from users.models import User, Candidat


ACCOUNTS = [
    {
        'email': 'admin@ensa-bm.ma',
        'cin': 'AD000001',
        'password': 'Admin1234!',
        'role': User.Role.ADMIN,
        'is_staff': True,
        'is_superuser': True,
        'candidat': None,
    },
    {
        'email': 'scolarite@ensa-bm.ma',
        'cin': 'SC000001',
        'password': 'Scolarite1234!',
        'role': User.Role.RESPONSABLE,
        'is_staff': True,
        'candidat': None,
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
    help = 'Crée ou met à jour les comptes de test (admin, responsable, candidats).'

    def handle(self, *args, **options):
        for acc in ACCOUNTS:
            user, created = User.objects.get_or_create(
                email=acc['email'],
                defaults={
                    'cin': acc['cin'],
                    'role': acc['role'],
                    'is_staff': acc.get('is_staff', False),
                    'is_superuser': acc.get('is_superuser', False),
                    'email_verified': True,
                },
            )
            user.cin = acc['cin']
            user.role = acc['role']
            user.is_staff = acc.get('is_staff', False)
            user.is_superuser = acc.get('is_superuser', False)
            user.set_password(acc['password'])
            user.save()

            if acc['candidat']:
                Candidat.objects.update_or_create(
                    user=user,
                    defaults=acc['candidat'],
                )

            status = 'créé' if created else 'mis à jour'
            self.stdout.write(self.style.SUCCESS(f"  {acc['email']} — {status}"))

        self.stdout.write(self.style.SUCCESS('\nComptes prêts. Exemples :'))
        self.stdout.write('  admin@ensa-bm.ma / Admin1234!')
        self.stdout.write('  scolarite@ensa-bm.ma / Scolarite1234!')
        self.stdout.write('  ahmed.benali@gmail.com / Test1234!')
