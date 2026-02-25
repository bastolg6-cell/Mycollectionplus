from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class BasketballCard(models.Model):
    # On garde tes champs, mais on s'assure qu'ils matchent avec la BDD
    id_card = models.PositiveIntegerField(primary_key=True)
    date_sold = models.CharField(max_length=100, null=True, blank=True)
    marque = models.CharField(max_length=255, null=True, blank=True)
    licence = models.CharField(max_length=50, null=True, blank=True)
    produit = models.CharField(max_length=50, null=True, blank=True)
    saison = models.CharField(max_length=100, null=True, blank=True)
    name = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    name_2 = models.CharField(max_length=255, blank=True, null=True)
    name_3 = models.CharField(max_length=255, blank=True, null=True)
    name_4 = models.CharField(max_length=255, blank=True, null=True)
    name_5 = models.CharField(max_length=255, blank=True, null=True)
    name_6 = models.CharField(max_length=255, blank=True, null=True)
    name_7 = models.CharField(max_length=255, blank=True, null=True)
    name_8 = models.CharField(max_length=255, blank=True, null=True)
    name_9 = models.CharField(max_length=255, blank=True, null=True)
    name_10 = models.CharField(max_length=255, blank=True, null=True)
    name_11 = models.CharField(max_length=255, blank=True, null=True)
    name_12 = models.CharField(max_length=255, blank=True, null=True)
    teams = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    teams_2 = models.CharField(max_length=255, blank=True, null=True)
    teams_3 = models.CharField(max_length=255, blank=True, null=True)
    teams_4 = models.CharField(max_length=255, blank=True, null=True)
    teams_5 = models.CharField(max_length=255, blank=True, null=True)
    teams_6 = models.CharField(max_length=255, blank=True, null=True)
    teams_7 = models.CharField(max_length=255, blank=True, null=True)
    teams_8 = models.CharField(max_length=255, blank=True, null=True)
    teams_9 = models.CharField(max_length=255, blank=True, null=True)
    teams_10 = models.CharField(max_length=255, blank=True, null=True)
    teams_11 = models.CharField(max_length=255, blank=True, null=True)
    teams_12 = models.CharField(max_length=255, blank=True, null=True)
    rc = models.CharField(max_length=100, db_column='RC', null=True, blank=True) 
    categorie = models.CharField(max_length=100, null=True, blank=True)
    type_card = models.CharField(max_length=100, null=True, blank=True)
    parrallel = models.CharField(max_length=100, null=True, blank=True)
    numero_card = models.CharField(max_length=100, null=True, blank=True)
    numerotation_card = models.CharField(max_length=100, null=True, blank=True)
    type_img = models.CharField(max_length=100, null=True, blank=True)
    recto_img = models.CharField(max_length=255, null=True, blank=True)
    verso_img = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return f"{self.produit} - {self.name} ({self.type_card})"

class Library(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='basketball_libraries'
    )
    name = models.CharField(max_length=100, default="Ma Bibliothèque")
    position = models.PositiveIntegerField(default=1) # Pour l'ordre d'affichage
    shelf_count = models.PositiveIntegerField(default=4)
    shelf_sizes = models.JSONField(default=dict, blank=True)
    has_library = models.BooleanField(default=True)

    class Meta:
        ordering = ['position']

    def __str__(self):
        return f"{self.name} - {self.user.username}"

class Binder(models.Model):
    TYPES_RANGEMENT = [
        ('small', 'Petit Classeur (2x2)'),
        ('medium', 'Classeur Standard (3x3)'),
        ('large', 'Grand Portfolio (4x4)'),
        ('extra', 'Méga Album (6x5)'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=10, blank=True) # Ex: "LAK"
    label_text = models.CharField(max_length=50, blank=True)    # Texte sur l'étiquette
    color = models.CharField(max_length=7, default="#d32f2f")
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='binders', null=True, blank=True)
    
    storage_type = models.CharField(max_length=20, choices=TYPES_RANGEMENT, default='medium')
    format_size = models.CharField(max_length=20, default="3x3") # Ex: "2x2", "6x5"
    
    shelf_number = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)

    column_position = models.PositiveIntegerField(default=1)

class UserCard(models.Model):
    binder = models.ForeignKey(Binder, on_delete=models.CASCADE, related_name='slots')
    card = models.ForeignKey(BasketballCard, on_delete=models.CASCADE)
    slot_number = models.PositiveIntegerField()

    class Meta:
        unique_together = ('binder', 'slot_number')

    def __str__(self):
        return f"Slot {self.slot_number} - {self.card.name}"

class BasketCollection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    card = models.ForeignKey(BasketballCard, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.user.username} possède {self.card.name}"

class ViewCollection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="basketball_views")
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default='bi-star-fill')
    players = models.JSONField(default=list, blank=True)
    teams = models.JSONField(default=list, blank=True)
    seasons = models.JSONField(default=list, blank=True)
    products = models.JSONField(default=list, blank=True)
    categories = models.JSONField(default=list, blank=True)
    types = models.JSONField(default=list, blank=True)
    parallels = models.JSONField(default=list, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']
        unique_together = ('user', 'name')




