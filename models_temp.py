# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class MaTable(models.Model):
    number_card = models.FloatField(blank=True, null=True)
    date_sold = models.TextField(blank=True, null=True)
    marque = models.TextField(blank=True, null=True)
    licence = models.TextField(blank=True, null=True)
    produit = models.TextField(blank=True, null=True)
    saison = models.TextField(blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    name_2 = models.TextField(blank=True, null=True)
    name_3 = models.TextField(blank=True, null=True)
    teams = models.TextField(blank=True, null=True)
    teams_2 = models.TextField(blank=True, null=True)
    teams_3 = models.TextField(blank=True, null=True)
    rc = models.TextField(db_column='RC', blank=True, null=True)  # Field name made lowercase.
    categorie = models.TextField(blank=True, null=True)
    type_card = models.TextField(blank=True, null=True)
    parrallel = models.TextField(blank=True, null=True)
    numero_card = models.TextField(blank=True, null=True)
    numerotation_card = models.TextField(blank=True, null=True)
    type_img = models.FloatField(blank=True, null=True)
    recto_img = models.TextField(blank=True, null=True)
    verso_img = models.TextField(blank=True, null=True)
    key_card = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ma_table'
