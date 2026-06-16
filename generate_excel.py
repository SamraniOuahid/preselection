import os
import django
import pandas as pd
import random

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings") # or preselection.settings, let's check ensa-bm-preselection structure

# Just generating fake data first if django fails
CINs = [f"AB{i}" for i in range(10000, 10050)]
notes_ecrit = [round(random.uniform(10, 20), 2) for _ in CINs]
notes_oral = [round(random.uniform(10, 20), 2) for _ in CINs]

df_ecrit = pd.DataFrame({'CIN': CINs, 'Note': notes_ecrit})
df_oral = pd.DataFrame({'CIN': CINs, 'Note': notes_oral})

df_ecrit.to_excel('test_ecrit_TDI.xlsx', index=False)
df_oral.to_excel('test_oral_TDI.xlsx', index=False)
print("Files generated.")
