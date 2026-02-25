from django.db import models
from django.contrib.auth.models import User

# --- TABLES FIXES (LES RÉFÉRENCES) ---

class ygo_extension(models.Model):
    code_extension = models.CharField(max_length=20, unique=True) # ex: "LOB"
    name_extension = models.CharField(max_length=100) # ex: "La Légende du Dragon Blanc"

    def __str__(self):
        return self.name_extension

class ygo_base(models.Model):
    base_card = models.CharField(max_length=50)
    extension = models.ForeignKey(ygo_extension, on_delete=models.CASCADE,to_field='code_extension',db_column='code_extension')
    alpha_card = models.CharField(max_length=50)
    level_card = models.CharField(max_length=50)
    nbr_link = models.CharField(max_length=50)
    cross_link = models.CharField(max_length=50)
    artwork_card = models.CharField(max_length=50, blank=True, null=True)
    code_card = models.CharField(max_length=50)
    attack_card = models.CharField(max_length=50)
    defense_card = models.CharField(max_length=50)
    passcode_card = models.CharField(max_length=50)

    def __str__(self):
        return self.base_card

class Rarete_card(models.Model):
    code_rarete = models.CharField(max_length=50, blank=True)
    abv_rarete = models.CharField(max_length=10, blank=True)
    group_rarete = models.CharField(max_length=10, blank=True) 
    family_rarete = models.CharField(max_length=10, blank=True) 

    def __str__(self):
        return self.abv_rarete

class langue_card(models.Model):
    code_langue = models.CharField(max_length=200)
    abv_langue = models.CharField(max_length=20)  
    langue_card = models.CharField(max_length=20)
    
    def __str__(self):
        return self.abv_langue

# --- TABLES DE TRADUCTION ET ÉDITION ---

class Card_Translation(models.Model):
    card_translate = models.CharField(max_length=255)
    base_card = models.ForeignKey(ygo_base, on_delete=models.CASCADE, related_name='translations')
    abv_langue = models.ForeignKey(langue_card, on_delete=models.CASCADE)
    type_card = models.CharField(max_length=100, blank=True)
    name_card = models.CharField(max_length=255)
    attribut_card = models.CharField(max_length=50, blank=True)
    family_card = models.CharField(max_length=100, blank=True)
    sous_family = models.CharField(max_length=100, blank=True)
    nature_card = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ('base_card', 'abv_langue')

class Card_Printing(models.Model):
    card_version = models.CharField(max_length=255, null=True, blank=True)
    base_card = models.ForeignKey(ygo_base, on_delete=models.CASCADE)
    abv_rarete = models.ForeignKey(Rarete_card, on_delete=models.CASCADE)
    artwork_card = models.CharField(max_length=255, null=True, blank=True)
    img_card = models.ImageField(max_length=255, null=True, blank=True)

    class Meta:
        unique_together = ('base_card', 'abv_rarete')
    
    def __str__(self):
        return f"{self.base_card} - {self.abv_rarete}"

class Rarete_Translation(models.Model):
    rarities_translate = models.CharField(max_length=100, blank=True)
    abv_rarete = models.ForeignKey(Rarete_card, on_delete=models.CASCADE, blank=True)
    abv_langue = models.ForeignKey(langue_card, on_delete=models.CASCADE, blank=True)
    name_rarities = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = ('abv_rarete', 'abv_langue')

    def __str__(self):
        return f"{self.name_rarities} ({self.abv_langue.abv_langue})"

class Catalogue_Public(models.Model):
    card_translate = models.ForeignKey(Card_Translation, on_delete=models.CASCADE)
    card_version = models.ForeignKey(Card_Printing, on_delete=models.CASCADE)
    rarities_translate = models.ForeignKey(Rarete_Translation, on_delete=models.CASCADE, null=True, blank=True)
    reference = models.CharField(max_length=100, blank=True)
    class Meta:
        ordering = ['reference', 'id']
        
    def __str__(self):
        return self.reference

# --- GESTION DE LA COLLECTION UTILISATEUR ---

class Collection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    card_printing = models.ForeignKey(Card_Printing, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('user', 'card_printing')

# --- LE CLASSEUR INTELLIGENT ---

class Classeur(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nom = models.CharField(max_length=100)
    extension_cible = models.CharField(max_length=100, null=True, blank=True)
    # Filtres liés à tes tables existantes
    rarete_cible = models.ForeignKey(Rarete_card, on_delete=models.SET_NULL, null=True, blank=True)
    # Si tu as une table Extension_card plus tard, tu pourras l'ajouter ici
    nom_carte_cible = models.CharField(max_length=255, null=True, blank=True, help_text="Ex: Magicien Sombre")

    def __str__(self):
        return f"{self.nom} ({self.user.username})"
    
    def calcul_stats(self):
        # 1. On commence par toutes les impressions
        requete_catalogue = Card_Printing.objects.all()

        # 2. FILTRE PAR NOM (Méthode robuste par IDs)
        if self.nom_carte_cible and self.nom_carte_cible.strip():
            nom_nettoye = self.nom_carte_cible.strip()
        
            # On récupère d'abord les IDs des cartes de base qui correspondent au nom
            # On importe ici pour éviter les imports circulaires si nécessaire
            from .models import Card_Translation
        
            base_ids = Card_Translation.objects.filter(
               name_card__icontains=nom_nettoye
            ).values_list('base_card_id', flat=True)
        
            # On filtre le catalogue : seulement les impressions de ces cartes
            requete_catalogue = requete_catalogue.filter(base_card_id__in=base_ids)

        # 3. FILTRE PAR RARETÉ
        if self.rarete_cible:
            # On compare avec l'objet rareté directement
            requete_catalogue = requete_catalogue.filter(abv_rarete=self.rarete_cible)

        # 4. COMPTAGE DU TOTAL
        total_possible = requete_catalogue.count()

        # 5. CROISEMENT AVEC LA COLLECTION
        # On récupère les IDs des impressions filtrées
        ids_vrais = requete_catalogue.values_list('id', flat=True)
    
        possedees = Collection.objects.filter(
            user=self.user, 
            card_printing_id__in=ids_vrais, 
            quantite__gt=0
        ).count()

        # 6. CALCUL DU POURCENTAGE
        pourcentage = round((possedees / total_possible * 100), 1) if total_possible > 0 else 0

        return {
            'possedees': possedees,
            'total': total_possible,
            'absentes': max(0, total_possible - possedees),
            'pourcentage': pourcentage
        }