from django.contrib import admin
from .models import (
    ygo_base, Rarete_card, langue_card, ygo_extension, 
    Card_Printing, Rarete_Translation, Card_Translation, Catalogue_Public
)
from .models import Classeur

# --- CONFIGURATION DES TRADUCTIONS EN LIGNE (INLINES) ---
# Cela permet de voir les traductions directement dans la fiche de la carte de base
class CardTranslationInline(admin.TabularInline):
    model = Card_Translation
    extra = 0

class CardPrintingInline(admin.TabularInline):
    model = Card_Printing
    extra = 0

# --- ADMINISTRATION DES MODÈLES ---

@admin.register(ygo_base)
class YgoBaseAdmin(admin.ModelAdmin):
    list_display = ('base_card', 'code_card', 'extension')
    search_fields = ('base_card', 'code_card')
    list_filter = ('extension',)
    inlines = [CardTranslationInline, CardPrintingInline]

@admin.register(ygo_extension)
class YgoExtensionAdmin(admin.ModelAdmin):
    list_display = ('code_extension', 'name_extension')
    search_fields = ('code_extension', 'name_extension')

@admin.register(langue_card)
class LangueCardAdmin(admin.ModelAdmin):
    list_display = ('abv_langue', 'langue_card')

@admin.register(Rarete_card)
class RareteCardAdmin(admin.ModelAdmin):
    list_display = ('abv_rarete',)

@admin.register(Rarete_Translation)
class RareteTranslationAdmin(admin.ModelAdmin):
    list_display = ('name_rarities', 'abv_rarete', 'abv_langue')
    list_filter = ('abv_langue', 'abv_rarete')

@admin.register(Card_Printing)
class CardPrintingAdmin(admin.ModelAdmin):
    list_display = ('card_version', 'base_card', 'abv_rarete', 'artwork_card')
    search_fields = ('card_version', 'base_card__base_card')
    list_filter = ('abv_rarete',)

@admin.register(Card_Translation)
class CardTranslationAdmin(admin.ModelAdmin):
    list_display = ('card_translate', 'name_card', 'base_card', 'abv_langue')
    search_fields = ('card_translate', 'name_card')
    list_filter = ('abv_langue',)

@admin.register(Catalogue_Public)
class CataloguePublicAdmin(admin.ModelAdmin):
    list_display = ('reference', 'get_card_name', 'get_rarity', 'card_version')
    search_fields = ('reference', 'card_translate__name_card')
    list_filter = ('card_translate__abv_langue', 'card_version__abv_rarete')

    # Fonctions pour afficher des colonnes plus claires
    def get_card_name(self, obj):
        return obj.card_translate.name_card
    get_card_name.short_description = 'Nom de la Carte'

    def get_rarity(self, obj):
        return obj.card_version.abv_rarete
    get_rarity.short_description = 'Rareté'


@admin.register(Classeur)
class ClasseurAdmin(admin.ModelAdmin):
    # Ce qu'on affiche dans la liste des classeurs
    list_display = ('nom', 'user', 'rarete_cible', 'extension_cible', 'get_stats_display')
    
    # Filtres pour s'y retrouver
    list_filter = ('user', 'rarete_cible')
    
    # Recherche par nom de classeur ou nom d'utilisateur
    search_fields = ('nom', 'user__username')

    # Affichage des statistiques dans la liste
    def get_stats_display(self, obj):
        stats = obj.calcul_stats()
        return f"{stats['possedees']} / {stats['total']} ({stats['pourcentage']}%)"
    
    get_stats_display.short_description = "Progression (Possédées / Total)"