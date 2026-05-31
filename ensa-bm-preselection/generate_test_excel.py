# generate_test_excel.py
import os
import django
import openpyxl
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from candidatures.models import Dossier
from users.models import User

def generate():
    # Récupérer les dossiers présélectionnés
    dossiers = Dossier.objects.filter(statut=Dossier.Statut.PRESELECTIONNE)
    
    if not dossiers.exists():
        print("Aucun dossier présélectionné (PRESELECTIONNE) trouvé dans la base de données.")
        print("Génération de dossiers fictifs pour le test...")
        # Si aucun, on prend tous les dossiers, ou on en crée.
        dossiers = Dossier.objects.all()[:10]
        if not dossiers.exists():
            print("Aucun dossier trouvé en base de données. Créez des dossiers d'abord.")
            return

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Notes Epreuve Ecrite"
    
    # Headers : Compatible par défaut (CIN en A, Note en B)
    ws.append(["CIN", "Note"])
    
    count = 0
    for d in dossiers:
        cin = d.candidat.user.cin
        # Generer une note aleatoire entre 5 et 19 avec des pas de 0.25 ou 0.5
        note = round(random.uniform(5, 19) * 4) / 4
        
        ws.append([cin, note])
        count += 1
    
    # Ajouter un CIN fictif pour tester la gestion des erreurs
    ws.append(["XX99999", 12.5])
    
    output_path = "notes_test.xlsx"
    wb.save(output_path)
    print(f"Fichier créé avec succès : {output_path} ({count} candidats réels + 1 fictif).")

if __name__ == '__main__':
    generate()
