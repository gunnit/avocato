document.addEventListener('DOMContentLoaded', function() {
    // Initialize variables
    let currentPage = 1;
    let pageSize = 12;
    let totalPages = 1;
    let articles = [];
    let books = [];

    // Initialize components
    const bookFilter = document.getElementById('bookFilter');
    const pageSizeSelect = document.getElementById('pageSizeSelect');
    const articlesCardGrid = document.getElementById('articlesCardGrid');
    const pagination = document.getElementById('pagination');
    const articleCardTemplate = document.getElementById('articleCardTemplate');
    const articleSearch = document.getElementById('articleSearch');

    // Load initial data
    loadBooks();
    loadArticles();

    // Event Listeners
    if (bookFilter) {
        bookFilter.addEventListener('change', handleBookFilterChange);
    }
    if (pageSizeSelect) {
        pageSizeSelect.addEventListener('change', handlePageSizeChange);
    }
    if (articleSearch) {
        articleSearch.addEventListener('input', debounce(handleArticleSearch, 300));
    }

    // Debounce function to limit API calls
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

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
            
            renderArticlesCards();
            renderPagination();
        } catch (error) {
            console.error('Error loading articles:', error);
            articlesCardGrid.innerHTML = '<div class="alert alert-danger">Si è verificato un errore durante il caricamento degli articoli.</div>';
        }
    }

    // UI Rendering Functions
    function populateBookFilter() {
        if (!bookFilter) return;
        bookFilter.innerHTML = '<option value="">Tutti i Libri</option>';
        books.forEach(book => {
            bookFilter.innerHTML += `<option value="${book.id}">Libro ${book.number} - ${book.name}</option>`;
        });
    }

    function renderArticlesCards() {
        if (!articlesCardGrid || !articleCardTemplate) return;
        
        if (articles.length === 0) {
            articlesCardGrid.innerHTML = '<div class="col-12"><div class="alert alert-info">Nessun articolo trovato.</div></div>';
            return;
        }

        articlesCardGrid.innerHTML = '';
        articles.forEach(article => {
            const template = articleCardTemplate.innerHTML
                .replace('{article_number}', article.number)
                .replace('{title}', article.heading || '')
                .replace('{book}', article.book_name || '');
            
            articlesCardGrid.innerHTML += template;
        });

        // Add click handlers to view buttons
        document.querySelectorAll('.article-card .btn-light-primary').forEach((btn, index) => {
            btn.onclick = () => showArticleDetail(articles[index].id);
        });
    }

    function renderPagination() {
        if (!pagination) return;
        
        pagination.innerHTML = '';
        
        if (totalPages <= 1) return;

        // Previous button
        pagination.innerHTML += `
            <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="event.preventDefault(); changePage(${currentPage - 1})">
                    <i class="fas fa-chevron-left"></i>
                </a>
            </li>
        `;

        // Page numbers
        for (let i = 1; i <= totalPages; i++) {
            if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {
                pagination.innerHTML += `
                    <li class="page-item ${i === currentPage ? 'active' : ''}">
                        <a class="page-link" href="#" onclick="event.preventDefault(); changePage(${i})">${i}</a>
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
                <a class="page-link" href="#" onclick="event.preventDefault(); changePage(${currentPage + 1})">
                    <i class="fas fa-chevron-right"></i>
                </a>
            </li>
        `;
    }

    // Event Handlers
    function handleBookFilterChange() {
        const bookId = bookFilter.value;
        currentPage = 1;
        loadArticles({ book: bookId });
    }

    function handlePageSizeChange() {
        pageSize = parseInt(pageSizeSelect.value);
        currentPage = 1;
        loadArticles(getActiveFilters());
    }

    function handleArticleSearch(event) {
        const searchValue = event.target.value.trim();
        currentPage = 1;
        loadArticles({
            ...getActiveFilters(),
            search: searchValue
        });
    }

    function getActiveFilters() {
        const filters = {};
        if (bookFilter && bookFilter.value) {
            filters.book = bookFilter.value;
        }
        if (articleSearch && articleSearch.value.trim()) {
            filters.search = articleSearch.value.trim();
        }
        return filters;
    }

    // Article Detail Functions
    window.showArticleDetail = async function(articleId) {
        try {
            const response = await fetch(`/legal-rag/articles/${articleId}/`);
            const article = await response.json();
            
            const detailModal = document.getElementById('articleDetailModal');
            if (!detailModal) {
                console.error('Article detail modal not found');
                return;
            }

            document.getElementById('articleDetailTitle').textContent = `Articolo ${article.number}`;
            document.getElementById('articleDetailBook').textContent = article.book_name;
            document.getElementById('articleDetailTitleSection').textContent = article.title_name;
            document.getElementById('articleDetailSection').textContent = article.section_name || 'N/A';
            document.getElementById('articleDetailHeading').textContent = article.heading;
            
            // Directly insert HTML content for enhanced formatting
            const contentElement = document.getElementById('articleDetailContent');
            contentElement.innerHTML = article.content;
            
            new bootstrap.Modal(detailModal).show();
        } catch (error) {
            console.error('Error loading article details:', error);
        }
    }

    // Expose pagination function to window
    window.changePage = function(newPage) {
        if (newPage >= 1 && newPage <= totalPages) {
            currentPage = newPage;
            loadArticles(getActiveFilters());
        }
    }
});
