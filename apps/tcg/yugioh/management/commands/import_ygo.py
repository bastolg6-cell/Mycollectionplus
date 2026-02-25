import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.tcg.yugioh.models import (
    ygo_base, Rarete_card, langue_card, ygo_extension, 
    Card_Printing, Rarete_Translation, Card_Translation, Catalogue_Public
)

class Command(BaseCommand):
    help = 'Importation séquentielle Yu-Gi-Oh avec tables séparées'

    def handle(self, *args, **options):
        path = os.path.join(settings.BASE_DIR, 'imports_csv')

        # --- 1. LANGUES (Base indispensable) ---
        self.stdout.write("Étape 1 : Langues...")
        f_lang = os.path.join(path, 'langue_card.csv')
        if os.path.exists(f_lang):
            with open(f_lang, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    langue_card.objects.update_or_create(
                        abv_langue=row['abv_langue'].strip(),
                        defaults={'langue_card': row['langue_card'].strip()}
                    )
            self.stdout.write(self.style.SUCCESS("OK"))

        # --- 2. RARETE_CARD (Table technique séparée) ---
        self.stdout.write("Étape 2 : Raretés Techniques...")
        f_rare_tech = os.path.join(path, 'rarete_card.csv')
        if os.path.exists(f_rare_tech):
            with open(f_rare_tech, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    Rarete_card.objects.get_or_create(
                        abv_rarete=row['abv_rarete'].strip()
                    )
            self.stdout.write(self.style.SUCCESS("OK"))

        # --- 3. EXTENSIONS ---
        self.stdout.write("Étape 3 : Extensions...")
        f_ext = os.path.join(path, 'ygo_extension.csv')
        if os.path.exists(f_ext):
            with open(f_ext, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ygo_extension.objects.update_or_create(
                        code_extension=row['code_extension'].strip(),
                        defaults={'name_extension': row['name_extension'].strip()}
                    )
            self.stdout.write(self.style.SUCCESS("OK"))

        # --- 4. BASES (Cartes) ---
        self.stdout.write("Étape 4 : Bases des Cartes...")
        f_base = os.path.join(path, 'ygo_base.csv')
        if os.path.exists(f_base):
            with open(f_base, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ext = ygo_extension.objects.filter(code_extension=row['code_extension'].strip()).first()
                    if ext:
                        ygo_base.objects.update_or_create(
                            base_card=row['base_card'].strip(),
                            defaults={'code_card': row.get('code_card','').strip(), 'extension': ext}
                        )
            self.stdout.write(self.style.SUCCESS("OK"))

        # --- 5. RARETE_TRANSLATION (Lien Rarete <-> Langue) ---
        self.stdout.write("Étape 5 : Traductions des Raretés...")
        f_rar_trad = os.path.join(path, 'rarities_translate.csv')
        if os.path.exists(f_rar_trad):
            with open(f_rar_trad, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    r_obj = Rarete_card.objects.filter(abv_rarete=row['abv_rarete'].strip()).first()
                    l_obj = langue_card.objects.filter(abv_langue=row['abv_langue'].strip()).first()
                    if r_obj and l_obj:
                        Rarete_Translation.objects.update_or_create(
                            abv_rarete=r_obj, abv_langue=l_obj,
                            defaults={'name_rarities': row['name_rarities'].strip()}
                        )
            self.stdout.write(self.style.SUCCESS("OK"))

        # --- 6. CARD_PRINTING (Lien Base <-> Rarete) ---
        self.stdout.write("Étape 6 : Impressions des Cartes...")
        f_print = os.path.join(path, 'card_printing.csv')
        if os.path.exists(f_print):
            with open(f_print, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    base = ygo_base.objects.filter(base_card=row['base_card'].strip()).first()
                    rare = Rarete_card.objects.filter(abv_rarete=row['abv_rarete'].strip()).first()
                    if base and rare:
                        Card_Printing.objects.update_or_create(
                            card_version=row['card_version'].strip(),
                            defaults={
                                'base_card': base, 
                                'abv_rarete': rare,
                                'artwork_card': row.get('artwork_card', '1'),
                                'img_card': f"yugioh/cards/{row['img_card'].strip()}" if row.get('img_card') else ""
                            }
                        )
            self.stdout.write(self.style.SUCCESS("OK"))

        # --- 7. CARD_TRANSLATION (Lien Base <-> Langue) ---
        self.stdout.write("Étape 7 : Traductions des Noms de Cartes...")
        f_trad = os.path.join(path, 'card_translation.csv')
        if os.path.exists(f_trad):
            with open(f_trad, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    base = ygo_base.objects.filter(base_card=row['base_card'].strip()).first()
                    lang = langue_card.objects.filter(abv_langue=row['abv_langue'].strip()).first()
                    if base and lang:
                        Card_Translation.objects.update_or_create(
                            card_translate=row['card_translate'].strip(),
                            defaults={
                                'base_card': base, 
                                'abv_langue': lang, 
                                'name_card': row['name_card'].strip(),
                                'description': row.get('description', '').strip()
                            }
                        )
            self.stdout.write(self.style.SUCCESS("OK"))

        # --- 8. CATALOGUE PUBLIC (Finalisation) ---
        self.stdout.write("Étape 8 : Finalisation Catalogue Public...")
        f_cat = os.path.join(path, 'catalogue_public.csv')
        count = 0
        if os.path.exists(f_cat):
            with open(f_cat, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    trad = Card_Translation.objects.filter(card_translate=row['card_translate'].strip()).first()
                    ver = Card_Printing.objects.filter(card_version=row['card_version'].strip()).first()
                    # Lien avec le code de rareté traduit (ex: QCSR-FR)
                    rare_t = Rarete_Translation.objects.filter(abv_rarete__abv_rarete=row['rarities_translate'].split('-')[0]).first()
                    
                    if trad and ver:
                        Catalogue_Public.objects.update_or_create(
                            card_translate=trad, 
                            card_version=ver,
                            defaults={'reference': row['card_translate'].strip()}
                        )
                        count += 1
            self.stdout.write(self.style.SUCCESS(f"TERMINÉ : {count} lignes créées."))