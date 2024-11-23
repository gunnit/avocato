document.addEventListener('DOMContentLoaded', function() {
    // Initialize variables
    let currentPage = 1;
    let pageSize = 10;
    let totalPages = 1;
    let articles = [];
    let books = [];
    let titles = [];

    // Initialize components
    const searchForm = document.getElementById('penalCodeSearchForm');
    const searchResults = document.getElementById('searchResults');
    const resultsContent = document.getElementById('resultsContent');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const bookFilter = document.getElementById('bookFilter');
    const titleFilter = document.getElementById('titleFilter');
    const pageSizeSelect = document.getElementById('pageSizeSelect');
    const articlesTableBody = document.getElementById('articlesTableBody');
    const pagination = document.getElementById('pagination');

    // Load initial data
    loadBooks();
    loadArticles();

    // Event Listeners
    bookFilter.addEventListener('change', handleBookFilterChange);
    titleFilter.addEventListener('change', handleTitleFilterChange);
    pageSizeSelect.addEventListener('change', handlePageSizeChange);

    // Functions to handle data loading
    async function loadBooks() {
        try {
            const response = await fetch('/legal-rag/books/');
            books = await response.json();
            populateBookFilter();
        } catch (error) {
            console.error('Error loading books:', error);
        }
    }

    async function loadArticles(filters = {}) {
        try {
            const queryParams = new URLSearchParams({
                page: currentPage,
                page_size: pageSize,
                ...filters
            });
            
            const response = await fetch(`/legal-rag/articles/?${queryParams}`);
            const data = await response.json();
            
            articles = data.results;
            totalPages = Math.ceil(data.count / pageSize);
            
            renderArticlesTable();
            renderPagination();
        } catch (error) {
            console.error('Error loading articles:', error);
        }
    }

    // UI Rendering Functions
    function populateBookFilter() {
        bookFilter.innerHTML = '<option value="">Tutti i Libri</option>';
        books.forEach(book => {
            bookFilter.innerHTML += `<option value="${book.id}">Libro ${book.number} - ${book.name}</option>`;
        });
    }

    function renderArticlesTable() {
        articlesTableBody.innerHTML = '';
        articles.forEach(article => {
            articlesTableBody.innerHTML += `
                <tr>
                    <td>Art. ${article.number}</td>
                    <td>${article.heading}</td>
                    <td>${article.book_name}</td>
                    <td class="text-end">
                        <button class="btn btn-sm btn-icon btn-light-primary" onclick="showArticleDetail(${article.id})">
                            <i class="fas fa-eye"></i>
                        </button>
                    </td>
                </tr>
            `;
        });
    }

    function renderPagination() {
        pagination.innerHTML = '';
        
        // Previous button
        pagination.innerHTML += `
            <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="changePage(${currentPage - 1})">
                    <i class="fas fa-chevron-left"></i>
                </a>
            </li>
        `;

        // Page numbers
        for (let i = 1; i <= totalPages; i++) {
            if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {
                pagination.innerHTML += `
                    <li class="page-item ${i === currentPage ? 'active' : ''}">
                        <a class="page-link" href="#" onclick="changePage(${i})">${i}</a>
                    </li>
                `;
            } else if (i === currentPage - 3 || i === currentPage + 3) {
                pagination.innerHTML += `
                    <li class="page-item disabled">
                        <span class="page-link">...</span>
                    </li>
                `;
            }
        }

        // Next button
        pagination.innerHTML += `
            <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="changePage(${currentPage + 1})">
                    <i class="fas fa-chevron-right"></i>
                </a>
            </li>
        `;
    }

    // Event Handlers
    function handleBookFilterChange() {
        const bookId = bookFilter.value;
        currentPage = 1;
        loadArticles({ book_id: bookId });
        
        // Load titles for selected book
        if (bookId) {
            loadTitles(bookId);
        } else {
            titleFilter.innerHTML = '<option value="">Tutti i Titoli</option>';
            titleFilter.disabled = true;
        }
    }

    function handleTitleFilterChange() {
        const titleId = titleFilter.value;
        currentPage = 1;
        loadArticles({
            book_id: bookFilter.value,
            title_id: titleId
        });
    }

    function handlePageSizeChange() {
        pageSize = parseInt(pageSizeSelect.value);
        currentPage = 1;
        loadArticles();
    }

    // Article Detail Functions
    window.showArticleDetail = async function(articleId) {
        try {
            const response = await fetch(`/legal-rag/articles/${articleId}/`);
            const article = await response.json();
            
            document.getElementById('articleDetailTitle').textContent = `Articolo ${article.number}`;
            document.getElementById('articleDetailBook').textContent = article.book_name;
            document.getElementById('articleDetailTitleSection').textContent = article.title_name;
            document.getElementById('articleDetailSection').textContent = article.section_name || 'N/A';
            document.getElementById('articleDetailHeading').textContent = article.heading;
            document.getElementById('articleDetailContent').innerHTML = formatText(article.content);
            
            new bootstrap.Modal(document.getElementById('articleDetailModal')).show();
        } catch (error) {
            console.error('Error loading article details:', error);
        }
    }

    // Helper Functions
    function formatText(text) {
        return text.split('. ')
            .filter(sentence => sentence.trim() !== '')
            .map(sentence => `<p class="mb-2">${escapeHtml(sentence.trim())}${sentence.trim().endsWith('.') ? '' : '.'}</p>`)
            .join('');
    }

    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

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

    // Search Form Handler
    searchForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const articleNumber = document.getElementById('articleNumber').value;
        if (!articleNumber) return;

        searchResults.classList.remove('d-none');
        loadingSpinner.classList.remove('d-none');
        resultsContent.innerHTML = '';

        try {
            const response = await fetch('/legal-rag/penal-code-search/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ article_number: articleNumber })
            });

            const data = await response.json();
            loadingSpinner.classList.add('d-none');

            if (data.error) {
                resultsContent.innerHTML = `<div class="alert alert-danger">${escapeHtml(data.error)}</div>`;
                return;
            }

            if (data.results && data.results.length > 0) {
                resultsContent.innerHTML = data.results.map(result => `
                    <div class="border rounded p-5 mb-5">
                        <div class="mb-3">
                            <h3 class="text-dark fw-bold text-hover-primary mb-1 fs-5">
                                ${escapeHtml(result.title || 'Articolo del Codice Penale')}
                            </h3>
                        </div>
                        <div class="text-gray-600 fw-semibold fs-7 mb-4">
                            ${formatText(result.snippet)}
                        </div>
                        <div class="d-flex flex-stack">
                            <div class="d-flex align-items-center">
                                <button class="btn btn-sm btn-light" onclick="showArticleDetail(${result.id})">
                                    <i class="fas fa-eye me-2"></i>Visualizza Dettagli
                                </button>
                            </div>
                        </div>
                    </div>
                `).join('');
            } else {
                resultsContent.innerHTML = '<div class="alert alert-info">Nessun risultato trovato.</div>';
            }
        } catch (error) {
            loadingSpinner.classList.add('d-none');
            resultsContent.innerHTML = '<div class="alert alert-danger">Si è verificato un errore durante la ricerca.</div>';
        }
    });

    // Expose pagination function to window
    window.changePage = function(newPage) {
        if (newPage >= 1 && newPage <= totalPages) {
            currentPage = newPage;
            loadArticles({
                book_id: bookFilter.value,
                title_id: titleFilter.value
            });
        }
    }
});
