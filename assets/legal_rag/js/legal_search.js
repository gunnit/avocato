// Legal Search functionality
function performLegalSearch(caseId) {
    // Show loading state
    const searchButton = document.querySelector('.legal-search-btn');
    if (searchButton) {
        searchButton.disabled = true;
        searchButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Ricerca in corso...';
    }

    // Clear any existing error messages
    const existingAlert = document.querySelector('#searchErrorAlert');
    if (existingAlert) {
        existingAlert.remove();
    }

    // Perform the search
    fetch(`/legal-rag/api/case/${caseId}/perform-legal-search/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        },
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'error') {
            // Handle error response
            showSearchError(data.message, data.details);
        } else {
            // Handle success
            window.location.href = `/legal-rag/case/${caseId}/legal-search/${data.search_id}/`;
        }
    })
    .catch(error => {
        showSearchError('Si è verificato un errore durante la ricerca', error.message);
    })
    .finally(() => {
        // Reset button state
        if (searchButton) {
            searchButton.disabled = false;
            searchButton.innerHTML = '<i class="ki-duotone ki-search fs-2"><span class="path1"></span><span class="path2"></span></i>Avvia Ricerca';
        }
    });
}

function showSearchError(message, details) {
    const alertHtml = `
        <div id="searchErrorAlert" class="alert alert-danger alert-dismissible fade show" role="alert">
            <strong>Errore!</strong> ${message}
            ${details ? `<br><small class="text-muted">${details}</small>` : ''}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;

    // Insert the alert before the search results section
    const searchResults = document.querySelector('#searchResults');
    if (searchResults) {
        searchResults.insertAdjacentHTML('beforebegin', alertHtml);
    }

    // Log error to console for debugging
    console.error('Search Error:', { message, details });
}

// Handle CSRF token expiration
document.addEventListener('DOMContentLoaded', function() {
    // Refresh CSRF token periodically
    setInterval(function() {
        const csrfToken = getCookie('csrftoken');
        if (!csrfToken) {
            showSearchError('Sessione scaduta', 'Ricaricare la pagina per continuare.');
        }
    }, 300000); // Check every 5 minutes
});

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
