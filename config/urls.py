from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth import login
from django.conf import settings
from django.conf.urls.static import static

# Imports des vues avec alias pour éviter les conflits
from apps.tcg.yugioh import views as yugioh_views
from apps.sports.basketball import views as basket_views

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Inscription réussie !")
            return redirect('/') 
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.accueil.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('register/', register, name='register'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    ## --- PARTIE YU-GI-OH --- ##
    path('yugioh/', yugioh_views.yugioh_home, name='yugioh_home'),
    path('yugioh/catalogue/', yugioh_views.catalogue_view, name='yugioh_catalogue'),
    path('yugioh/update-collection/<int:card_id>/', yugioh_views.update_collection, name='update_collection'),
    path('yugioh/ygo_collection/', yugioh_views.ygo_collection, name='ygo_collection'),
    path('yugioh/ajouter-classeur/', yugioh_views.ajouter_classeur, name='ajouter_classeur'),

## --- PARTIE BASKETBALL --- ##
    
    # 1. Requêtes AJAX / API
    path('basketball/get-collection-stats/', basket_views.get_collection_stats, name='get_collection_stats'),
    path('basketball/preview-count/', basket_views.preview_collection_count, name='preview_collection_count'),
    path('basketball/save-new-view/', basket_views.save_new_collection_view, name='save_new_collection_view'),
    path('save-library-config/', basket_views.save_library_config, name='save_library_config'),
    path('add-binder/', basket_views.add_binder, name='add_binder'),

    # On garde UNIQUEMENT celle qui correspond au nom de la fonction créée ci-dessus
    path('basketball/update-order/', basket_views.reorder_collections, name='update_collection_order'),
    path('bibliotheque/creer/', basket_views.create_library, name='create_library'),

    path('basketball/delete-view/', basket_views.delete_collection_view, name='delete_collection_view'),
    path('binder_detail/<int:binder_id>/', basket_views.binder_detail, name='binder_detail'),
    path('search_cards/', basket_views.search_cards, name='search_cards'),
    path('delete-library/', basket_views.toggle_library, name='delete_library'),

    # 2. Vues principales (Pages HTML)
    path('basketball/', basket_views.basketball_home, name='basketball_home'),
    path('basketball/catalogue/', basket_views.basketball_catalog, name='basket_catalogue'),
    path('basketball/ma-collection/', basket_views.my_basket_collection, name='my_basket_collection'),
    path('basketball/bibliotheque/', basket_views.basket_biblio, name='basket_biblio'),
    
    # 3. Actions sur les objets
    path('basketball/add-to-collection/<str:card_id>/', basket_views.add_card_to_collection, name='add_to_collection'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)