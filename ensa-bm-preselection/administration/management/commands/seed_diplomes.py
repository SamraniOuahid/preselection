# administration/management/commands/seed_diplomes.py
"""
Commande Django pour injecter la liste officielle des diplômes acceptés
dans toutes les filières existantes, selon leur niveau (BAC2 / BAC3).

Usage :
    python manage.py seed_diplomes
    python manage.py seed_diplomes --clear    (supprime les anciens avant d'injecter)
    python manage.py seed_diplomes --filiere GI-BAC2  (cible une filière spécifique)
"""

from django.core.management.base import BaseCommand, CommandError
from administration.models import Filiere, DiplomaAccepte


# ─── Catalogue officiel des diplômes ─────────────────────────────────────────
#
#  coefficient = pondération appliquée au score final du candidat.
#    1.00 → diplôme principal, aucune pénalité
#    0.95 → légèrement moins valorisé
#    0.90 → valorisé mais avec une légère réduction
#
#  IMPORTANT : 'autre' est géré par le champ `coef_autre_diplome` de la Filière
#  et non via DiplomaAccepte.

DIPLOMES_BAC2 = [
    # (intitulé affiché, coefficient)
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
    # (intitulé affiché, coefficient)
    ("Licence d'Études Fondamentales - LEF (Filières scientifiques)", "1.00"),
    ("Licence Professionnelle - LP (Filières techniques/ingénierie)", "1.00"),
    ("Bachelor",                                                       "0.95"),
]

CATALOGUE = {
    "BAC2": DIPLOMES_BAC2,
    "BAC3": DIPLOMES_BAC3,
}

# Coefficient par défaut pour un diplôme "Autre" non répertorié
COEF_AUTRE_BAC2 = "0.80"
COEF_AUTRE_BAC3 = "0.80"
COEF_AUTRE = {
    "BAC2": COEF_AUTRE_BAC2,
    "BAC3": COEF_AUTRE_BAC3,
}


class Command(BaseCommand):
    help = "Injecte la liste officielle des diplômes dans les filières existantes."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Supprimer les diplômes existants avant d'injecter la nouvelle liste.",
        )
        parser.add_argument(
            "--filiere",
            type=str,
            default=None,
            help="Code d'une filière spécifique (ex: GI-BAC2). Si absent, toutes les filières sont traitées.",
        )

    def handle(self, *args, **options):
        clear = options["clear"]
        filiere_code = options["filiere"]

        # Sélection des filières
        if filiere_code:
            qs = Filiere.objects.filter(code=filiere_code)
            if not qs.exists():
                raise CommandError(f"Aucune filière trouvée avec le code '{filiere_code}'.")
        else:
            qs = Filiere.objects.all()

        if not qs.exists():
            self.stdout.write(self.style.WARNING("Aucune filière trouvée dans la base."))
            return

        total_crees = 0
        total_ignores = 0
        total_supprimes = 0

        for filiere in qs:
            catalogue = CATALOGUE.get(filiere.niveau)
            if not catalogue:
                self.stdout.write(
                    self.style.WARNING(f"  ⚠  Filière '{filiere.code}' — niveau '{filiere.niveau}' non géré, ignorée.")
                )
                continue

            self.stdout.write(
                self.style.MIGRATE_HEADING(f"\n📚 Filière : {filiere.code} — {filiere.nom} ({filiere.niveau})")
            )

            # Suppression des anciens diplômes si --clear
            if clear:
                nb_del, _ = DiplomaAccepte.objects.filter(filiere=filiere).delete()
                total_supprimes += nb_del
                self.stdout.write(f"   🗑  {nb_del} anciens diplôme(s) supprimé(s).")

            # Mise à jour du coef_autre_diplome
            coef_autre = COEF_AUTRE.get(filiere.niveau, "0.80")
            filiere.coef_autre_diplome = coef_autre
            filiere.save(update_fields=["coef_autre_diplome"])

            # Injection des diplômes du catalogue
            for nom_diplome, coefficient in catalogue:
                obj, created = DiplomaAccepte.objects.get_or_create(
                    filiere=filiere,
                    nom_diplome=nom_diplome,
                    defaults={
                        "coefficient": coefficient,
                        "is_active": True,
                        "etablissements": [],
                    },
                )
                if created:
                    total_crees += 1
                    self.stdout.write(f"   ✅  [{coefficient}] {nom_diplome}")
                else:
                    total_ignores += 1
                    self.stdout.write(
                        self.style.WARNING(f"   ⚡  Déjà présent : {nom_diplome}")
                    )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("═" * 55))
        self.stdout.write(self.style.SUCCESS("✅ Injection terminée !"))
        self.stdout.write(self.style.SUCCESS("═" * 55))
        if clear:
            self.stdout.write(f"   Supprimés  : {total_supprimes}")
        self.stdout.write(f"   Créés      : {total_crees}")
        self.stdout.write(f"   Ignorés    : {total_ignores}  (déjà présents)")
        self.stdout.write("")
