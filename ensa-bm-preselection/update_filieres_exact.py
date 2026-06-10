import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from administration.models import Filiere

# The EXACT names based on the official site
exact_updates = {
    'TDI': "Transformation Digitale Industrielle",
    'IACS': "Intelligence Artificielle et Cybersécurité",
    'IAA': "Industries Agroalimentaires",
    'G2ER': "Génie Électrique et Énergies Renouvelables"
}

for code, nom in exact_updates.items():
    f, created = Filiere.objects.update_or_create(
        code=code,
        defaults={'nom': nom}
    )
    print(f"Updated {f.code} -> {f.nom}")
