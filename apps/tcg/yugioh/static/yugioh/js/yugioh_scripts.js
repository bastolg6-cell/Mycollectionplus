document.addEventListener('DOMContentLoaded', function() {
    const handle = document.querySelector('#sidebar-handle');
    const wrapper = document.querySelector('#wrapper');

    if (handle) {
        handle.addEventListener('click', function() {
            wrapper.classList.toggle('toggled');
        });
    }
});

function initCollectionButtons(csrfToken) {
    document.querySelectorAll('.btn-update').forEach(button => {
        button.onclick = function(e) {
            e.preventDefault();
            const cardId = this.dataset.id;
            const action = this.dataset.action;
            const qtySpan = document.getElementById('qty-' + cardId);

            fetch(`/update-collection/${cardId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `action=${action}`
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'ok') {
                    qtySpan.innerText = data.quantite;
                }
            })
            .catch(error => console.error('Erreur:', error));
        };
    });
}