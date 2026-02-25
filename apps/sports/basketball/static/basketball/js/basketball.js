(function() {
    // Variables globales pour gérer l'état
    let collectionChart = null;
    let sortableInstance = null;
    let isReorderMode = false;


    /**
     * Fonction pour initialiser ou mettre à jour le graphique Chart.js
     */
    function initOrUpdateChart(base, inserts, memo, autos) {
        const canvas = document.getElementById('collectionChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        
        if (collectionChart) {
            collectionChart.destroy();
        }

        const total = base + inserts + memo + autos;
        const dataValues = total > 0 ? [base, inserts, memo, autos] : [1];
        const bgColors = total > 0 
            ? ['#0066cc', '#5ac8fa', '#ffcc00', '#ff3b30'] 
            : ['#e9ecef'];

        collectionChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Base', 'Inserts', 'Memo', 'Autos'],
                datasets: [{
                    data: dataValues,
                    backgroundColor: bgColors,
                    borderWidth: 0,
                    cutout: '84%',
                    hoverOffset: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    animateScale: true,
                    animateRotate: true
                },
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: total > 0 }
                }
            }
        });
    }

    /**
     * Fonction pour mettre à jour les textes et chiffres du dashboard
     */
    function updateDashboardStats(data) {
        $('#stat-base').text(data.count_base || 0);
        $('#stat-inserts').text(data.count_inserts || 0);
        $('#stat-memo').text(data.count_memo || 0);
        $('#stat-autos').text(data.count_autos || 0);
        $('#stat-total').text(data.total_cards || 0);
        $('#stat-player').text(data.top_player || '-');
        $('#stat-team').text(data.top_team || '-');
    }

    // --- DÉBUT DU DOCUMENT READY ---
    $(document).ready(function() {
        console.log("Basketball JS chargé"); // Debug pour vérifier que le fichier est lu
        const $config = $('#dashboard-config');
        const csrfToken = $('[name=csrfmiddlewaretoken]').val();

        // 1. Initialisation de Select2
        if ($.fn.select2) {
            $('.select2-multiple').select2({
                theme: "bootstrap-5",
                width: '100%',
                placeholder: "Sélectionner...",
                closeOnSelect: false,
                allowClear: true
            });
        }

        // 2. Préparation des données par défaut
        const defaultData = {
            count_base: parseInt($config.data('base-default')) || 0,
            count_inserts: parseInt($config.data('inserts-default')) || 0,
            count_memo: parseInt($config.data('memo-default')) || 0,
            count_autos: parseInt($config.data('autos-default')) || 0,
            total_cards: parseInt($config.data('total-default')) || 0,
            top_player: $config.data('player-default'),
            top_team: $config.data('team-default')
        };

        updateDashboardStats(defaultData);
        initOrUpdateChart(
            defaultData.count_base,
            defaultData.count_inserts,
            defaultData.count_memo,
            defaultData.count_autos
        );

        // 3. LOGIQUE PRINCIPALE : Clic sur une collection
        $(document).on('click', '.collection-selector', function(e) {
            if (isReorderMode) return;
            e.preventDefault();
            
            $('.collection-selector').removeClass('active-collection border-primary bg-light');
            $(this).addClass('active-collection border-primary bg-light');

            const collectionName = $(this).data('id');
            const ajaxUrl = $config.data('ajax-url'); 

            $.ajax({
                url: ajaxUrl,
                method: 'GET',
                data: { 'collection_name': collectionName },
                beforeSend: function() {
                    $('#collectionChart').css('opacity', '0.5');
                },
                success: function(response) {
                    $('#collectionChart').css('opacity', '1');
                    initOrUpdateChart(
                        response.count_base,
                        response.count_inserts,
                        response.count_memo,
                        response.count_autos
                    );
                    updateDashboardStats(response);
                    $('h5.text-uppercase').first().text(collectionName);
                },
                error: function(err) {
                    console.error("Erreur AJAX :", err);
                    $('#collectionChart').css('opacity', '1');
                }
            });
        });

        // 4. BOUTON CALCULER (Modal Ajout)
        $(document).on('click', '#btn-previsualiser', function() {
            const formData = $('#form-nouvelle-vue').serialize();
            const previewUrl = $config.data('preview-url');

            fetch(previewUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                $('#preview-result-container').removeClass('d-none');
                $('#preview-text').html(`Cette sélection contient <strong>${data.count}</strong> cartes.`);
            })
            .catch(err => console.error("Erreur calcul :", err));
        });

        // 5. BOUTON CONFIRMER AJOUT
        $(document).on('click', '#btn-confirmer-ajout', function() {
            const formData = $('#form-nouvelle-vue').serialize();
            const saveUrl = $config.data('save-url');

            fetch(saveUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    location.reload(); 
                } else {
                    alert("Erreur : " + data.message);
                }
            })
            .catch(err => console.error("Erreur sauvegarde :", err));
        });

        // 6. MODE ORGANISATION
        $(document).on('click', '#btn-modifier-vues', function(e) {
            e.preventDefault();
            const list = document.getElementById('sortable-list');
            const $btn = $(this);
            const $handles = $('.drag-handle');
            const $deleteBtns = $('.btn-delete-collection');
            const $editBtns = $('.btn-edit-collection'); 

            if (!isReorderMode) {
                isReorderMode = true;
                $btn.html('<i class="bi bi-check-lg text-success"></i> Terminer');
                $handles.attr('style', 'display: block !important; cursor: move; font-size: 1.5rem;');
                $editBtns.attr('style', 'display: block !important;');
                $deleteBtns.attr('style', 'display: block !important;');
                $('.collection-selector').css('cursor', 'default');

                if (typeof Sortable !== 'undefined') {
                    sortableInstance = new Sortable(list, {
                        animation: 150,
                        handle: '.drag-handle',
                        ghostClass: 'bg-light-subtle'
                    });
                }
            } else {
                const newOrder = [];
                $('#sortable-list .collection-selector').each(function() {
                    newOrder.push($(this).data('view-id')); 
                });

                fetch($config.data('reorder-url'), {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({ 'order': newOrder })
                })
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'success') {
                        location.reload(); 
                    } else {
                        alert("Erreur lors de la sauvegarde de l'ordre");
                    }
                })
                .catch(err => console.error("Erreur:", err));
            }
        });

        // 7. SUPPRESSION
        $(document).on('click', '.btn-delete-collection', function(e) {
            e.preventDefault(); 
            e.stopPropagation();
            const nameToDelete = $(this).data('name');
            if (confirm(`Voulez-vous vraiment supprimer la vue "${nameToDelete}" ?`)) {
                $.ajax({
                    url: $config.data('delete-url'),
                    method: 'POST',
                    data: { 'name': nameToDelete, 'csrfmiddlewaretoken': csrfToken },
                    success: (res) => { 
                        if (res.status === 'success') {
                            $(`[data-id="${nameToDelete}"]`).slideUp(function() { $(this).remove(); });
                        }
                    }
                });
            }
        });

        // 8. ÉDITION (Modale)
        $(document).on('click', '.btn-edit-collection', function(e) {
            e.preventDefault(); 
            e.stopPropagation();
            const $btn = $(this);
            const $modal = $('#editCollectionViewModal');
            $modal.appendTo('body');
            
            const name = $btn.attr('data-name');
            $modal.find('#edit-old-name-input').val(name); 
            $modal.find('input[name="v_custom_name"]').val(name);
            $modal.find('select[name="v_icon"]').val($btn.attr('data-icon'));

            const getList = (attr) => {
                let val = $btn.attr(attr);
                return (val && val !== "") ? val.split(',') : [];
            };

            $modal.find('select[name="v_players"]').val(getList('data-players')).trigger('change');
            $modal.find('select[name="v_teams"]').val(getList('data-teams')).trigger('change');
            $modal.find('select[name="v_seasons"]').val(getList('data-seasons')).trigger('change');
            $modal.find('select[name="v_products"]').val(getList('data-products')).trigger('change');
            $modal.find('select[name="v_categories"]').val(getList('data-categories')).trigger('change');
            $modal.find('select[name="v_types"]').val(getList('data-types')).trigger('change');
            $modal.find('select[name="v_parallels"]').val(getList('data-parallels')).trigger('change');

            const modalInstance = new bootstrap.Modal(document.getElementById('editCollectionViewModal'));
            modalInstance.show();
        });

        // 9. SAUVEGARDER L'ÉDITION
        $(document).on('click', '#btn-sauvegarder-edit', function() {
            const formData = $('#form-modifier-vue').serialize();
            $.ajax({
                url: $config.data('save-url'),
                method: 'POST',
                data: formData,
                success: function(data) {
                    if (data.status === 'success') location.reload();
                    else alert("Erreur : " + data.message);
                }
            });
        });

        // --- AJOUT D'UNE CARTE À LA COLLECTION (Version Corrigée) ---
$(document).off('click', '.add-card-btn').on('click', '.add-card-btn', function(e) {
    e.preventDefault();
    e.stopImmediatePropagation();

    const $btn = $(this);
    
    if ($btn.prop('disabled')) return false;

    const cardId = $btn.attr('data-card-id');
    const token = $('[name=csrfmiddlewaretoken]').val() || (document.querySelector('[name=csrfmiddlewaretoken]') ? document.querySelector('[name=csrfmiddlewaretoken]').value : null);

    if (!cardId) {
        console.error("ID de carte introuvable");
        return false;
    }

    $.ajax({
        url: '/basketball/add-to-collection/' + cardId + '/',
        method: 'POST',
        headers: { 'X-CSRFToken': token },
        beforeSend: function() {
            $btn.prop('disabled', true).addClass('is-loading');
            $btn.css('opacity', '0.5');
        },
        success: function(response) {
            if (response.status === 'success') {
                // On cible le conteneur de cette carte spécifique
                const $container = $(`.qty-container[data-card-id="${cardId}"]`);
                
                // NOUVELLE STRUCTURE : Chiffre à gauche, boutons à droite
                const controlHtml = `
                    <div class="qty-control-horizontal">
                        <span class="qty-val">${response.quantity}</span>
                        <div class="qty-actions">
                            <button type="button" onclick="updateQty('${cardId}', 1)" class="qty-btn plus">
                                <i class="bi bi-chevron-up"></i>
                            </button>
                            <button type="button" onclick="updateQty('${cardId}', -1)" class="qty-btn minus">
                                <i class="bi bi-chevron-down"></i>
                            </button>
                        </div>
                    </div>
                `;

                // On remplace le bouton "+" par le nouveau sélecteur horizontal
                $container.html(controlHtml);
            }
        },
        error: function(xhr) {
            console.error("Détails erreur :", xhr.status, xhr.responseText);
            $btn.addClass('btn-danger').html('<i class="bi bi-exclamation-triangle"></i>');
        },
        complete: function() {
            // Pas de changement ici, on nettoie l'état de chargement
            setTimeout(() => {
                $btn.prop('disabled', false).removeClass('is-loading').css('opacity', '1');
            }, 1000);
        }
    });

    return false;
});


/* BIBLIOTHEQUE //////// **/
