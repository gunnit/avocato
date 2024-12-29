document.addEventListener('DOMContentLoaded', function() {
    const regenerateBtn = document.querySelector('.regenerate-btn');
    if (regenerateBtn) {
        const url = regenerateBtn.dataset.url;
        regenerateBtn.addEventListener('click', function() {
            handleRegenerate(url);
        });
    }
});

function handleRegenerate(url) {
    // Show loading state
    const button = document.querySelector('.regenerate-btn');
    if (button) {
        button.disabled = true;
        button.innerHTML = `
            <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
            <span class="d-flex flex-column align-items-start">
                <span class="fs-5 fw-bolder">Rigenerazione in corso...</span>
                <span class="fs-7">Attendere prego</span>
            </span>
        `;
    }

    // Perform the regeneration
    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        },
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        // Reload the page to show updated analysis
        window.location.reload();
    })
    .catch(error => {
        console.error('Error:', error);
        // Reset button state
        if (button) {
            button.disabled = false;
            button.innerHTML = `
                <span class="symbol symbol-25px me-3">
                    <i class="ki-duotone ki-arrows-circle fs-1">
                        <span class="path1"></span>
                        <span class="path2"></span>
                    </i>
                </span>
                <span class="d-flex flex-column align-items-start">
                    <span class="fs-5 fw-bolder">Rigenera Analisi</span>
                    <span class="fs-7">Aggiorna l'analisi del caso</span>
                </span>
            `;
        }
        // Show error message
        alert('Errore durante la rigenerazione dell\'analisi. Riprova più tardi.');
    });
}

// Helper function to get CSRF token
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
