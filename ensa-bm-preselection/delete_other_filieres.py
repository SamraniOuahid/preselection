import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from administration.models import Filiere

# The only filieres that belong to ENSA BM
ensa_bm_filieres = ['TDI', 'IACS', 'IAA', 'G2ER']

# Find all filieres not in this list
other_filieres = Filiere.objects.exclude(code__in=ensa_bm_filieres)

count = other_filieres.count()
if count > 0:
    print(f"Found {count} filieres to delete: {[f.code for f in other_filieres]}")
    # Delete them
    other_filieres.delete()
    print("Deleted successfully.")
else:
    print("No extra filieres found. Database only contains ENSA BM filieres.")

# List the remaining filieres
print("\nRemaining Filieres in DB:")
for f in Filiere.objects.all():
    print(f"- {f.code} : {f.nom}")
