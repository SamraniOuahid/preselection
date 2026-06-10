import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from administration.models import Filiere

# Update exactly as requested
filiere_updates = {
    'TDI': "Technologies Digitales pour l'Ingénieur",
    'IACS': "Intelligence Artificielle & Cybersécurité",
    'IAA': "Ingénierie de l'Automobile et de l'Aéronautique",
    'G2ER': "Génie de l'Énergie et de l'Environnement Renouvelable"
}

for code, nom in filiere_updates.items():
    f, created = Filiere.objects.update_or_create(
        code=code,
        defaults={'nom': nom}
    )
    print(f"Updated {f.code} -> {f.nom}")
