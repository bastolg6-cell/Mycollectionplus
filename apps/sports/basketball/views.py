from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import BasketballCard, BasketCollection, ViewCollection
from django.db.models import IntegerField, Count, Q, Exists, OuterRef, Subquery, Value, Case, When
from django.db.models.functions import Coalesce, Cast
from django.views.decorators.http import require_POST
import json

# --- ACCUEIL ---
def basketball_home(request):
    return render(request, 'basketball/basketball_home.html')

def basketball_catalog(request):
    # 1. Préparation de la sous-requête pour la quantité (si connecté)
    qty_subquery = 0
    if request.user.is_authenticated:
        qty_subquery = BasketCollection.objects.filter(
            user=request.user, 
            card_id=OuterRef('pk')
        ).values('quantity')

    # 2. Base complète avec injection de la quantité
    cards_list = BasketballCard.objects.annotate(
        num_entier=Cast('numero_card', output_field=IntegerField()),
        qty_in_collection=Coalesce(
            Subquery(qty_subquery[:1]) if request.user.is_authenticated else None, 
            0, 
            output_field=IntegerField()
        )
    ).order_by('-saison', 'produit', 'num_entier')

    # 3. Récupération des filtres
    v_search = request.GET.get('q', '')
    v_season = request.GET.get('v_season', '')
    v_cat = request.GET.get('v_cat', '')
    v_type_card = request.GET.get('v_type_card', '')
    v_parallel = request.GET.get('v_parallel', '')
    v_produit = request.GET.get('v_produit', '')

    # 4. Application des filtres
    if v_search: cards_list = cards_list.filter(name__icontains=v_search)
    if v_season: cards_list = cards_list.filter(saison=v_season)
    if v_cat: cards_list = cards_list.filter(categorie=v_cat)
    if v_type_card: cards_list = cards_list.filter(type_card=v_type_card)
    if v_parallel: cards_list = cards_list.filter(parrallel=v_parallel)
    if v_produit: cards_list = cards_list.filter(produit=v_produit)

    # 5. Pagination
    paginator = Paginator(cards_list, 100) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'collection_cards': page_obj, 
        'seasons': BasketballCard.objects.values_list('saison', flat=True).distinct().order_by('-saison'),
        'categories': BasketballCard.objects.values_list('categorie', flat=True).distinct().exclude(categorie=""),
        'type_cards': BasketballCard.objects.values_list('type_card', flat=True).distinct().exclude(type_card=""),
        'parallels': BasketballCard.objects.values_list('parrallel', flat=True).distinct().exclude(parrallel=""),
        'produits': BasketballCard.objects.values_list('produit', flat=True).distinct().order_by('produit'),
    }
    return render(request, 'basketball/basket_catalogue.html', context)

@login_required
def preview_collection_count(request):
    if request.method == "POST":
        query = Q()
        players = request.POST.getlist('v_players[]') or request.POST.getlist('v_players')
        if players: query &= Q(name__in=players)
        
        teams = request.POST.getlist('v_teams')
        if teams: query &= Q(teams__in=teams)
        
        seasons = request.POST.getlist('v_seasons')
        if seasons: query &= Q(saison__in=seasons)
        
        products = request.POST.getlist('v_products')
        if products: query &= Q(produit__in=products)

        categories = request.POST.getlist('v_categories')
        if categories: query &= Q(categorie__in=categories)

        total = BasketballCard.objects.filter(query).count()
        
        return JsonResponse({
            'status': 'success',
            'count': total,
            'message': f"Cette configuration contient {total} cartes."
        })

@login_required
@require_POST
def add_card_to_collection(request, card_id):
    # Sécurité : On force le delta à être soit 1 soit -1 pour éviter les injections de grosses quantités
    try:
        delta = int(request.POST.get('delta', 1))
        if delta not in [1, -1]:
            return JsonResponse({'status': 'error', 'message': 'Action non autorisée'}, status=400)
    except ValueError:
        return JsonResponse({'status': 'error', 'message': 'Valeur invalide'}, status=400)
    
    card = get_object_or_404(BasketballCard, pk=card_id)
    obj, created = BasketCollection.objects.get_or_create(
        user=request.user, 
        card=card, 
        defaults={'quantity': 0}
    )
    
    obj.quantity += delta
    
    if obj.quantity <= 0:
        obj.delete()
        return JsonResponse({'status': 'success', 'quantity': 0})
    
    obj.save()
    return JsonResponse({'status': 'success', 'quantity': obj.quantity})

@login_required
def my_basket_collection(request):
    # --- PARTIE 1 : BARRE LATÉRALE ---
    db_views = ViewCollection.objects.filter(user=request.user).order_by('order', 'created_at')
    collections_stats = []
    owned_card_ids = BasketCollection.objects.filter(user=request.user).values_list('card_id', flat=True)

    for view in db_views:
        query = Q()
        if view.players: query &= Q(name__in=view.players)
        if view.products: query &= Q(produit__in=view.products)
        if view.seasons: query &= Q(saison__in=view.seasons)
        if view.teams: query &= Q(teams__in=view.teams)
        if view.categories: query &= Q(categorie__in=view.categories)
        if view.types: query &= Q(type_card__in=view.types)
        if view.parallels: query &= Q(parrallel__in=view.parallels)

        cards_in_view = BasketballCard.objects.filter(query)
        total = cards_in_view.count()
        owned = cards_in_view.filter(pk__in=owned_card_ids).count()
        
        missing = total - owned
        percent = (owned / total * 100) if total > 0 else 0

        config_dict = {
            'v_custom_name': view.name,
            'v_icon': view.icon,
            'v_players': view.players,
            'v_teams': view.teams,
            'v_seasons': view.seasons,
            'v_products': view.products,
            'v_categories': view.categories,
            'v_types': view.types,
            'v_parallels': view.parallels,
        }

        collections_stats.append({
            'id': view.id,
            'name': view.name,
            'icon': view.icon,
            'owned': owned,
            'missing': missing,
            'total': total,
            'percent': percent,
            'config': config_dict,
            'config_json': json.dumps(config_dict),
        })

    # --- PARTIE 2 : LISTES DÉROULANTES ---
    base_qs = BasketballCard.objects.all()
    context = {
        'collections_stats': collections_stats,
        'names': base_qs.values_list('name', flat=True).distinct().order_by('name'),
        'teams': base_qs.values_list('teams', flat=True).distinct().exclude(teams="").order_by('teams'),
        'seasons': base_qs.values_list('saison', flat=True).distinct().order_by('-saison'),
        'products_list': base_qs.values_list('produit', flat=True).distinct().order_by('produit'),
        'categories': base_qs.values_list('categorie', flat=True).distinct().exclude(categorie="").order_by('categorie'),
        'types': base_qs.values_list('type_card', flat=True).distinct().exclude(type_card="").order_by('type_card'),
        'parallels': base_qs.values_list('parrallel', flat=True).distinct().exclude(parrallel="").order_by('parrallel'),
    }

    # --- PARTIE 3 : STATISTIQUES GÉNÉRALES ---
    user_collection = BasketCollection.objects.filter(user=request.user)
    top_p = user_collection.values('card__name').annotate(total=Count('card__name')).order_by('-total').first()
    top_t = user_collection.values('card__teams').annotate(total=Count('card__teams')).order_by('-total').first()

    context['stats_generales'] = {
        'total_cards': user_collection.count(),
        'count_base': user_collection.filter(card__categorie="Base").count(),
        'count_inserts': user_collection.filter(card__categorie="Insert").count(),
        'count_memo': user_collection.filter(card__categorie="Memorabilia").count(),
        'count_autos': user_collection.filter(card__categorie="Autograph").count(),
        'top_player': top_p['card__name'] if top_p else None,
        'top_team': top_t['card__teams'] if top_t else None,
    }

    # --- PARTIE 4 : LA GRILLE CENTRALE ---
    cards_queryset = BasketballCard.objects.all()
    active_view_id = request.GET.get('view_set')
    active_set_name = "Toute ma collection"

    if active_view_id:
        active_view = ViewCollection.objects.filter(id=active_view_id, user=request.user).first()
        if active_view:
            active_set_name = active_view.name
            q_view = Q()
            if active_view.players: q_view &= Q(name__in=active_view.players)
            if active_view.products: q_view &= Q(produit__in=active_view.products)
            if active_view.seasons: q_view &= Q(saison__in=active_view.seasons)
            if active_view.teams: q_view &= Q(teams__in=active_view.teams)
            if active_view.categories: q_view &= Q(categorie__in=active_view.categories)
            if active_view.types: q_view &= Q(type_card__in=active_view.types)
            if active_view.parallels: q_view &= Q(parrallel__in=active_view.parallels)
            cards_queryset = cards_queryset.filter(q_view)

    is_owned_subquery = BasketCollection.objects.filter(user=request.user, card=OuterRef('pk'))
    cards_queryset = cards_queryset.annotate(is_owned=Exists(is_owned_subquery))

    status_filter = request.GET.get('status')
    if status_filter == 'owned': cards_queryset = cards_queryset.filter(is_owned=True)
    elif status_filter == 'missing': cards_queryset = cards_queryset.filter(is_owned=False)

    if request.GET.get('v_name'): cards_queryset = cards_queryset.filter(name=request.GET.get('v_name'))
    if request.GET.get('v_team'): cards_queryset = cards_queryset.filter(teams=request.GET.get('v_team'))
    if request.GET.get('v_season'): cards_queryset = cards_queryset.filter(saison=request.GET.get('v_season'))
    if request.GET.get('v_products'): cards_queryset = cards_queryset.filter(produit=request.GET.get('v_products'))
    if request.GET.get('v_category'): cards_queryset = cards_queryset.filter(categorie=request.GET.get('v_category'))
    if request.GET.get('v_type'): cards_queryset = cards_queryset.filter(type_card=request.GET.get('v_type'))
    if request.GET.get('v_parallel'): cards_queryset = cards_queryset.filter(parrallel=request.GET.get('v_parallel'))
    if request.GET.get('v_search'): cards_queryset = cards_queryset.filter(name__icontains=request.GET.get('v_search'))

    cards_queryset = cards_queryset.annotate(
        num_entier=Cast('numero_card', output_field=IntegerField())
    ).order_by('-saison', 'num_entier')

    paginator = Paginator(cards_queryset, 200) 
    page_obj = paginator.get_page(request.GET.get('page'))

    context['collection_cards'] = page_obj
    context['active_set_name'] = active_set_name
    context['active_view_id'] = int(active_view_id) if active_view_id and active_view_id.isdigit() else None

    return render(request, 'basketball/my_collection.html', context)

@login_required
@require_POST
def save_new_collection_view(request):
    try:
        name = request.POST.get('v_custom_name')
        if not name:
            return JsonResponse({'status': 'error', 'message': 'Le nom est obligatoire'}, status=400)

        view, created = ViewCollection.objects.update_or_create(
            user=request.user,
            name=name,
            defaults={
                'players': request.POST.getlist('v_players'),
                'teams': request.POST.getlist('v_teams'),
                'seasons': request.POST.getlist('v_seasons'),
                'products': request.POST.getlist('v_products'),
                'categories': request.POST.getlist('v_categories'),
                'types': request.POST.getlist('v_types'),
                'parallels': request.POST.getlist('v_parallels'),
                'icon': request.POST.get('v_icon', 'bi-collection'),
            }
        )
        return JsonResponse({'status': 'success', 'message': 'Collection enregistrée !'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@require_POST
def reorder_collections(request):
    try:
        data = json.loads(request.body)
        ordered_ids = data.get('order', [])
        for index, view_id in enumerate(ordered_ids):
            ViewCollection.objects.filter(id=view_id, user=request.user).update(order=index)
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
@require_POST
def delete_collection_view(request):
    # On supprime MAINTENANT en base de données, pas juste en session
    name_to_delete = request.POST.get('name', '').strip()
    deleted_count, _ = ViewCollection.objects.filter(user=request.user, name__iexact=name_to_delete).delete()
    
    if deleted_count > 0:
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Collection non trouvée'}, status=404)

@login_required
def get_collection_stats(request):
    collection_name = request.GET.get('collection_name')
    try:
        view_config = ViewCollection.objects.get(user=request.user, name__iexact=collection_name)
        owned_card_ids = BasketCollection.objects.filter(user=request.user).values_list('card_id', flat=True)
        cards = BasketballCard.objects.all()

        if view_config.players: cards = cards.filter(name__in=view_config.players)
        if view_config.teams: cards = cards.filter(teams__in=view_config.teams)
        if view_config.seasons: cards = cards.filter(saison__in=view_config.seasons)
        if view_config.products: cards = cards.filter(produit__in=view_config.products)
        if view_config.categories: cards = cards.filter(categorie__in=view_config.categories)
        if view_config.types: cards = cards.filter(type_card__in=view_config.types)
        if view_config.parallels: cards = cards.filter(parrallel__in=view_config.parallels)

        stats = cards.aggregate(
            count_base=Count('id', filter=Q(categorie='Base', id__in=owned_card_ids)),
            count_inserts=Count('id', filter=Q(categorie='Insert', id__in=owned_card_ids)),
            count_memo=Count('id', filter=Q(categorie='Memorabilia', id__in=owned_card_ids)),
            count_autos=Count('id', filter=Q(categorie='Autograph', id__in=owned_card_ids)),
            total_cards=Count('id', filter=Q(id__in=owned_card_ids))
        )

        return JsonResponse({
            'count_base': stats['count_base'] or 0,
            'count_inserts': stats['count_inserts'] or 0,
            'count_memo': stats['count_memo'] or 0,
            'count_autos': stats['count_autos'] or 0,
            'total_cards': stats['total_cards'] or 0,
            'top_player': view_config.players[0] if view_config.players else "Tous",
            'top_team': view_config.teams[0] if view_config.teams else "Toutes",
        })
    except ViewCollection.DoesNotExist:
        return JsonResponse({'error': 'Collection non trouvée'}, status=404)

import json
import math
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Binder, BasketballCard, UserCard, Library, BasketCollection, ViewCollection
from django.db.models import F # <--- AJOUTE CETTE LIGNE EN HAUT
from django.contrib import messages

 # --- Bibliotheque ---
def create_library(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        
        # 1. Créer la bibliothèque
        library = Library.objects.create(
            user=request.user,
            name=name
        )
        
        # 2. Récupérer dynamiquement les tailles des étagères
        shelf_sizes = {}
        # On boucle sur les clés du POST pour trouver celles qui commencent par shelf_size_
        for key in request.POST:
            if key.startswith('shelf_size_'):
                shelf_num = key.split('_')[-1] # Récupère le "1", "2", etc.
                size_value = request.POST.get(key)
                shelf_sizes[shelf_num] = size_value
        
        # 3. Enregistrer les tailles dans le JSONField de ton modèle
        library.shelf_sizes = shelf_sizes
        
        # 4. Déterminer le nombre d'étages total
        if shelf_sizes:
            library.shelf_count = max(int(k) for k in shelf_sizes.keys())
        
        library.save()
        messages.success(request, f"La bibliothèque '{name}' a été créée avec {library.shelf_count} étages.")
        
    return redirect('basket_biblio')
    
@login_required
def basket_biblio(request):
    # 1. Récupérer toutes les bibliothèques de l'utilisateur
    libraries = Library.objects.filter(user=request.user).order_by('position')
    
    libraries_data = []
    
    for lib in libraries:
        # 2. Récupérer UNIQUEMENT les classeurs liés à CETTE bibliothèque précise
        # C'est ici que se joue la correction : binder.library = lib
        binders = Binder.objects.filter(library=lib).order_by('shelf_number', 'column_position')
        
        # 3. Organiser les classeurs par étage pour le template
        shelves = {}
        for binder in binders:
            s_num = str(binder.shelf_number)
            if s_num not in shelves:
                shelves[s_num] = []
            shelves[s_num].append(binder)
            
        libraries_data.append({
            'instance': lib,
            'shelves': shelves,
            'shelf_sizes': lib.shelf_sizes or {},
            'shelves_range': range(1, lib.shelf_count + 1)
        })

    return render(request, 'basketball/basket_biblio.html', {
        'libraries_data': libraries_data,
    })

@login_required
def add_binder(request):
    if request.method == 'POST':
        # 1. Récupérer l'ID de la bibliothèque choisie dans le formulaire
        library_id = request.POST.get('library_id')
        
        if not library_id:
            messages.error(request, "Veuillez sélectionner une bibliothèque.")
            return redirect('basket_biblio')

        try:
            # 2. Récupérer la bibliothèque spécifique (on vérifie l'ID ET l'utilisateur par sécurité)
            target_library = Library.objects.get(id=library_id, user=request.user)
            
            # 3. Créer le classeur avec les données du formulaire
            Binder.objects.create(
                user=request.user,
                library=target_library, # On lie le classeur à la bonne bibliothèque
                name=request.POST.get('name'),
                shelf_number=request.POST.get('shelf_number', 1),
                storage_type=request.POST.get('storage_type', 'medium'),
                color=request.POST.get('color', '#4A90E2'),
                column_position=1 # Position par défaut au début de l'étagère
            )
            messages.success(request, "Classeur ajouté avec succès !")
            
        except Library.DoesNotExist:
            messages.error(request, "Bibliothèque introuvable.")
        
    return redirect('basket_biblio')

@csrf_exempt
def save_library_config(request):
    """Sauvegarde AJAX des positions et des configurations par bibliothèque."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # On s'attend à recevoir une liste de bibliothèques (voir le JS plus bas)
            libraries_data = data.get('libraries', [])

            for lib_data in libraries_data:
                lib_id = lib_data.get('id')
                
                # 1. Mise à jour de la Bibliothèque (Tailles des étagères)
                # On stocke les tailles directement dans l'instance Library concernée
                library = Library.objects.get(id=lib_id, user=request.user)
                library.shelf_sizes = lib_data.get('shelf_sizes', {})
                library.shelf_widths = lib_data.get('shelf_widths', {})
                library.save()

                # 2. Mise à jour des classeurs pour CETTE bibliothèque
                for b_data in lib_data.get('binders', []):
                    # .update() est efficace, et on change aussi le library_id !
                    Binder.objects.filter(id=b_data['id'], user=request.user).update(
                        shelf_number=b_data['shelf'],
                        column_position=b_data['column'],
                        library=library # <--- CRUCIAL : On rattache au bon meuble
                    )

            return JsonResponse({'status': 'success'})
        except Exception as e:
            print(f"Erreur save_library: {e}") # Pour ton terminal
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée'}, status=400)

def toggle_library(request):
    """ Cette vue sert maintenant à supprimer une bibliothèque """
    if request.method == 'POST':
        library_id = request.POST.get('library_id')
        # On supprime uniquement si la biblio appartient bien à l'utilisateur
        Library.objects.filter(id=library_id, user=request.user).delete()
    return redirect('basket_biblio')





def binder_detail(request, binder_id):
    """Affiche le détail des pages d'un classeur spécifique."""
    binder = get_object_or_404(Binder, id=binder_id, user=request.user)
    
    # Configuration du format
    try:
        dimensions = binder.format_size.split('x')
        cols = int(dimensions[0])
        rows = int(dimensions[1])
        slots_per_page = cols * rows
    except (ValueError, AttributeError, IndexError):
        cols, rows, slots_per_page = 3, 3, 9

    # Récupération de la collection (UserCard utilise BasketballCard)
    user_collection = UserCard.objects.filter(binder=binder).select_related('card')
    collection_dict = {uc.slot_number: uc for uc in user_collection}

    total_capacity = 180 
    num_pages = math.ceil(total_capacity / slots_per_page)
    
    cards_owned_count = user_collection.count()
    completion_percent = round((cards_owned_count / total_capacity) * 100, 1) if total_capacity > 0 else 0

    # On utilise BasketballCard et on trie par 'name'
    card_database = BasketballCard.objects.all().order_by('name')[:100]

    context = {
        'binder': binder,
        'cols': cols,
        'rows': rows,
        'slots_per_page': slots_per_page,
        'num_pages': num_pages,
        'total_capacity': total_capacity,
        'cards_owned_count': cards_owned_count,
        'completion_percent': completion_percent,
        'card_database': card_database,
        'collection_dict': collection_dict, 
    }
    return render(request, 'basketball/binder_detail.html', context)


def search_cards(request):
    query = request.GET.get('q', '')
    team = request.GET.get('team', '')
    saison = request.GET.get('saison', '')
    marque = request.GET.get('marque', '')
    produit = request.GET.get('produit', '')
    parallel = request.GET.get('parallel', '')
    num = request.GET.get('num', '')
    rc = request.GET.get('rc', '')

    cards = BasketballCard.objects.all()

    if query:
        cards = cards.filter(name__icontains=query)
    if team:
        cards = cards.filter(teams__icontains=team)
    if saison:
        cards = cards.filter(saison__icontains=saison)
    if marque:
        cards = cards.filter(marque__icontains=marque)
    if produit:
        cards = cards.filter(produit__icontains=produit)
    if parallel:
        cards = cards.filter(parrallel__icontains=parallel) # Attention au double 'r'
    if num:
        cards = cards.filter(numero_card=num)
    if rc == '1':
        cards = cards.exclude(rc__isnull=True).exclude(rc='')

    results = []
    for card in cards[:50]:
        results.append({
            'id': card.id_card,
            'name': card.name,
            'saison': card.saison,
            'marque': card.marque,
            'parallel': card.parrallel,
            'rc': bool(card.rc),
            'image': card.recto_img,
        })
    
    return JsonResponse({'results': results})