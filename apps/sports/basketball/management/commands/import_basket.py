import csv
import os
from django.core.management.base import BaseCommand
from apps.sports.basketball.models import BasketballCard

class Command(BaseCommand):
    help = 'Mise à jour du catalogue sans perte des données utilisateur'

    def handle(self, *args, **kwargs):
        path = 'imports_csv/basketball/basket_catalogue.csv' 
        
        if not os.path.exists(path):
            self.stdout.write(self.style.ERROR(f"Fichier non trouvé : {path}"))
            return

        # --- ÉTAPE 1 : ON NE SUPPRIME PLUS RIEN ---
        # BasketballCard.objects.all().delete()  <-- SUPPRIMÉ POUR GARDER LES DONNÉES

        with open(path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count_created = 0
            count_updated = 0
            skipped = 0
            
            self.stdout.write("Analyse et synchronisation des données...")
            
            for row in reader:
                raw_key = row.get('key_card')
                key = str(raw_key).strip() if raw_key else ""

                if not key or key.lower() == "none":
                    skipped += 1
                    continue
                
                # --- ÉTAPE 2 : UPDATE_OR_CREATE ---
                # On utilise key_card comme identifiant unique pour savoir si on crée ou on met à jour
                card, created = BasketballCard.objects.update_or_create(
                    key_card=key,
                    defaults={
                        'number_card': row.get('number_card', ''),
                        'date_sold': row.get('date_sold', ''),
                        'marque': row.get('marque', ''),
                        'licence': row.get('licence', ''),
                        'produit': row.get('produit', ''),
                        'saison': row.get('saison', ''),
                        'name': row.get('name', ''),
                        'name_2': row.get('name_2', ''),
                        'name_3': row.get('name_3', ''),
                        'teams': row.get('teams', ''),
                        'teams_2': row.get('teams_2', ''),
                        'teams_3': row.get('teams_3', ''),
                        'is_rc': str(row.get('RC')).lower() in ['1', 'true', 'yes'],
                        'categorie': row.get('categorie', ''),
                        'type_card': row.get('type_card', ''),
                        'parrallel': row.get('parrallel', ''),
                        'numero_card': row.get('numero_card', ''),
                        'numerotation_card': row.get('numerotation_card', ''),
                        'type_img': row.get('type_img', ''),
                        'recto_img': row.get('recto_img', ''),
                        'verso_img': row.get('verso_img', ''),
                    }
                )

                if created:
                    count_created += 1
                else:
                    count_updated += 1

                if (count_created + count_updated) % 500 == 0:
                    self.stdout.write(f"Progression : {count_created + count_updated} lignes traitées...")

        self.stdout.write(self.style.SUCCESS(
            f"TERMINÉ ! {count_created} nouvelles cartes, {count_updated} mises à jour."
        ))
        if skipped > 0:
            self.stdout.write(self.style.WARNING(f"{skipped} lignes ignorées."))