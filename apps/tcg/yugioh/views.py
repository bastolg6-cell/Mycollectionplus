from django.shortcuts import render, get_object_or_404
import json
from django.views.generic import ListView
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import (
    Catalogue_Public, Rarete_card, Rarete_Translation, 
    Collection, Card_Printing, Classeur, ygo_extension  # <--- Utilise le nom exact ici
)
from django.db.models import Sum, Count, F  # <--- Ajoute , F ici


def yugioh_home(request):
    return render(request, 'yugioh/yugioh_home.html')

@login_required
def catalogue_view(request):
    # 1. On récupère les cartes du catalogue
    cartes = Catalogue_Public.objects.select_related(
        'card_translate', 
        'card_version', 
        'card_version__base_card'
    ).all()

    # 2. Gestion des filtres
    query_name = request.GET.get('nom')
    query_rarete = request.GET.get('rarete')

    if query_name:
        cartes = cartes.filter(card_translate__name_card__icontains=query_name)
    if query_rarete:
        cartes = cartes.filter(card_version__abv_rarete__rarete_translation__id=query_rarete)

    # 3. SOLUTION SANS FILTRE : On crée un dictionnaire temporaire pour mapper les quantités
    user_collection = {
        item.card_printing_id: item.quantite 
        for item in Collection.objects.filter(user=request.user)
    }

    # On ajoute la quantité directement à chaque objet 'c' de la boucle
    for c in cartes:
        # On crée un nouvel attribut 'ma_quantite' à la volée
        c.ma_quantite = user_collection.get(c.card_version.id, 0)

    # 4. Données pour le menu déroulant
    toutes_raretes = Rarete_Translation.objects.all()

    context = {
        'cartes': cartes,
        'toutes_raretes': toutes_raretes,
    }
    return render(request, 'yugioh/catalogue.html', context)

@login_required
def update_collection(request, card_id):
    if request.method == 'POST':
        action = request.POST.get('action')
        
        obj, created = Collection.objects.get_or_create(
            user=request.user, 
            card_printing_id=card_id,
            defaults={'quantite': 0}
        )

        if action == 'plus':
            obj.quantite += 1
        elif action == 'moins' and obj.quantite > 0:
            obj.quantite -= 1
        
        obj.save()
        return JsonResponse({'status': 'ok', 'quantite': obj.quantite})
    
    return JsonResponse({'status': 'error'}, status=400)


def card_detail_view(request, reference):
    carte = get_object_or_404(Catalogue_Public, reference=reference)
    context = {
        'carte': carte,
        'traduction': carte.card_translate,
        'rarete': carte.rarities_translate,
    }
    return render(request, 'yugioh/card_detail.html', context)
@login_required
def ygo_collection(request):
    # 1. Préparation des données de base
    classeurs_liste = Classeur.objects.filter(user=request.user).order_by('id')
    toutes_raretes = Rarete_Translation.objects.select_related('abv_rarete', 'abv_langue').all()
    toutes_extensions = ygo_extension.objects.all().order_by('name_extension')

    # 2. On récupère TOUTE la collection de l'utilisateur
    user_collection = Collection.objects.filter(user=request.user, quantite__gt=0).select_related('card_printing')

    # 3. Calcul des stats dynamiques par classeur
    for classeur in classeurs_liste:
        target_rarete = classeur.rarete_cible
        target_extension = classeur.extension_cible 

        filtres_catalogue = {}
        filtres_possession = {'quantite__gt': 0}

        if target_rarete:
            filtres_catalogue['abv_rarete'] = target_rarete
            filtres_possession['card_printing__abv_rarete'] = target_rarete
        
        if target_extension:
            # CHEMIN VALIDÉ : Card_Printing -> base_card -> extension -> name_extension
            filtres_catalogue['base_card__extension__name_extension'] = target_extension
            filtres_possession['card_printing__base_card__extension__name_extension'] = target_extension

        # --- CETTE PARTIE DOIT ÊTRE INDENTÉE DANS LE FOR ---
        cartes_du_catalogue = Card_Printing.objects.filter(**filtres_catalogue)
        possession_filtree = user_collection.filter(**filtres_possession)

        total_possible = cartes_du_catalogue.count()
        possedees = possession_filtree.count()

        classeur.dynamique_possedees = possedees
        classeur.dynamique_total = total_possible
        classeur.dynamique_absentes = max(0, total_possible - possedees)
        classeur.dynamique_pourcentage = round((possedees / total_possible * 100), 1) if total_possible > 0 else 0
        # --- FIN DU BLOC DANS LE FOR ---

    # 4. Statistiques globales (SORTIE DU FOR)
    total_exemplaires = user_collection.aggregate(Sum('quantite'))['quantite__sum'] or 0
    total_uniques = user_collection.count()
    total_catalogue = Catalogue_Public.objects.count()

    context = {
        'classeurs': classeurs_liste,
        'toutes_raretes': toutes_raretes,
        'toutes_extensions': toutes_extensions,
        'total_exemplaires': total_exemplaires,
        'total_uniques': total_uniques,
        'total_catalogue': total_catalogue,
        'completion_rate': round((total_uniques / total_catalogue * 100), 1) if total_catalogue > 0 else 0,
    }
    return render(request, 'yugioh/ygo_collection.html', context)

@login_required
def ajouter_classeur(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Affichage console pour déboguer (tu le verras dans ton terminal noir)
            print("Données reçues du JS :", data)

            # CREATION DU CLASSEUR
            Classeur.objects.create(
                user=request.user,
                nom=data.get('nom'),
                rarete_cible_id=data.get('rarete_id') if data.get('rarete_id') else None,
                extension_cible=data.get('extension'),
                
                # C'EST ICI : Vérifie que la clé 'nom_carte' correspond au JS
                nom_carte_cible=data.get('nom_carte') 
            )
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            print("Erreur :", e)
            return JsonResponse({'message': str(e)}, status=400)