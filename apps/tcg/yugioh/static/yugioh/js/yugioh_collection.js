// Fonction pour récupérer le token CSRF (Indispensable pour Django)
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

async function ajouterCollection() {
    // 1. Récupération des éléments HTML
    const inputNom = document.getElementById('input-nom');
    const selectRarete = document.getElementById('select-rarete');
    const selectLangue = document.getElementById('select-langue');
    const selectExtension = document.getElementById('select-extension');
    const selectNameCard = document.getElementById('input-nom-carte'); // On utilise l'ID du nouveau champ

    // 2. Validation de base
    if (!inputNom.value.trim()) {
        alert("Veuillez saisir un nom pour votre classeur.");
        return;
    }

    // 3. Préparation des données
    const payload = {
        nom: inputNom.value.trim(),
        rarete_id: selectRarete ? selectRarete.value : null,
        langue_id: selectLangue ? selectLangue.value : null,
        extension: selectExtension ? selectExtension.value : null,
        nom_carte: selectNameCard ? selectNameCard.value : null // AJOUT ICI
    };

    console.log("Envoi des données :", payload);

    try {
        const response = await fetch('/yugioh/ajouter-classeur/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            location.reload();
        } else {
            const errorData = await response.json();
            alert("Erreur : " + (errorData.message || "Problème côté serveur"));
        }
    } catch (error) {
        console.error("Erreur réseau :", error);
        alert("Impossible de contacter le serveur.");
    }
}