import os
import django
import openpyxl
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from candidatures.models import Dossier

def generate():
    # Retrieve all dossiers for "Transformation Digitale Industrielle"
    dossiers = Dossier.objects.filter(filiere__nom__icontains='Transformation Digitale Industrielle')
    
    if not dossiers.exists():
        print("Aucun dossier TDI trouvé.")
        return

    # Extract unique CINs
    cins = list(set([d.candidat.user.cin for d in dossiers]))
    print(f"Trouvé {len(cins)} candidats uniques pour TDI: {cins}")

    # Generate test_ecrit_TDI.xlsx
    wb_ecrit = openpyxl.Workbook()
    ws_ecrit = wb_ecrit.active
    ws_ecrit.title = "Notes Ecrit TDI"
    ws_ecrit.append(["CIN", "Note"])
    
    for cin in cins:
        # random note between 10 and 19
        note = round(random.uniform(10, 19) * 4) / 4
        ws_ecrit.append([cin, note])
        
    # Add a fictional one to test errors
    ws_ecrit.append(["XX99999", 12.5])
    wb_ecrit.save("test_ecrit_TDI.xlsx")
    print("test_ecrit_TDI.xlsx généré.")

    # Generate test_oral_TDI.xlsx
    wb_oral = openpyxl.Workbook()
    ws_oral = wb_oral.active
    ws_oral.title = "Notes Oral TDI"
    ws_oral.append(["CIN", "Note"])
    
    for cin in cins:
        # random note between 12 and 19
        note = round(random.uniform(12, 19) * 4) / 4
        ws_oral.append([cin, note])
        
    # Add a fictional one to test errors
    ws_oral.append(["YY88888", 15.0])
    wb_oral.save("test_oral_TDI.xlsx")
    print("test_oral_TDI.xlsx généré.")

if __name__ == '__main__':
    generate()
