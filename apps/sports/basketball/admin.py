from django.contrib import admin
from .models import BasketballCard

@admin.register(BasketballCard)
class BasketballCardAdmin(admin.ModelAdmin):
    # Les colonnes qui vont s'afficher dans la liste
    list_display = ('name', 'teams', 'marque', 'saison', 'type_card')
    # Une barre de recherche pour fouiller dans tes 82 000 cartes
    search_fields = ('name', 'teams', 'marque')
    # Des filtres sur le côté pour trier rapidement
    list_filter = ('marque', 'saison', 'type_card')
    # Pour ne pas charger 80 000 lignes d'un coup (on en affiche 50 par page)
    list_per_page = 50

    