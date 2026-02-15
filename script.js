// Global variables
let allBooks = [];
let filteredBooks = [];
let currentFile = 'data/latest.csv';					

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    loadManifest();
    setupEventListeners();
});

// Load manifest of available CSV files
async function loadManifest() {
    const fileSelect = document.getElementById('file-select');
    
    try {
        const response = await fetch('data/manifest.json');
        
        if (response.ok) {
            const manifest = await response.json();
            
            // Clear existing options
            fileSelect.innerHTML = '';
            
            // Populate dropdown
            manifest.forEach(file => {
                const option = document.createElement('option');
                option.value = `data/${file.filename}`;
                option.textContent = file.display;
                fileSelect.appendChild(option);
            });
            
            // Load the default (first) file
            currentFile = fileSelect.value;
        } else {
            // Fallback if manifest doesn't exist
            fileSelect.innerHTML = '<option value="data/latest.csv">Latest (Most Recent)</option>';
            currentFile = 'data/latest.csv';
        }
    } catch (error) {
        console.error('Error loading manifest:', error);
        // Fallback
        fileSelect.innerHTML = '<option value="data/latest.csv">Latest (Most Recent)</option>';
        currentFile = 'data/latest.csv';
    }
    
    // Load the initial data
    loadBooksData(currentFile);
}

// Load books data from CSV
async function loadBooksData(filename = 'data/latest.csv') {
    const loadingEl = document.getElementById('loading');
    const errorEl = document.getElementById('error');
    const tableContainer = document.querySelector('.table-container');
    
	    // Show loading state
    loadingEl.style.display = 'block';
    tableContainer.style.display = 'none';
    errorEl.style.display = 'none';
    try {
        // Try to load the specified CSV file
         const response = await fetch(filename);
        
        if (!response.ok) {
            throw new Error('Failed to fetch data');
        }
        
        const csvText = await response.text();
        allBooks = parseCSV(csvText);
        filteredBooks = [...allBooks];
        
        // Hide loading, show table
        loadingEl.style.display = 'none';
        tableContainer.style.display = 'block';
        
        // Populate the UI
        populateCategoryFilter();
        updateStats(filename);
        renderBooks();
        
    } catch (error) {
        console.error('Error loading books:', error);
        loadingEl.style.display = 'none';
        errorEl.style.display = 'block';
    }
}

// Parse CSV text into array of objects
function parseCSV(csvText) {
    const lines = csvText.trim().split('\n');
    const headers = lines[0].split(',').map(h => h.trim());
    
    const books = [];
    
    for (let i = 1; i < lines.length; i++) {
        const line = lines[i];
        if (!line.trim()) continue;
        
        // Simple CSV parser that handles basic cases
        const values = parseCSVLine(line);
        
        const book = {};
        headers.forEach((header, index) => {
            book[header] = values[index] ? values[index].trim().replace(/\$/g, ',') : '';
        });
        
        books.push(book);
    }
    
    // Deduplicate by (title, ISBN) - keep first occurrence
    const seen = new Set();
    return books.filter(book => {
        const key = `${(book.title || '').trim()}|${(book.ISBN || book.isbn || '').trim()}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
    });
}

// Parse a single CSV line, handling quoted fields
function parseCSVLine(line) {
    const values = [];
    let current = '';
    let inQuotes = false;
    
    for (let i = 0; i < line.length; i++) {
        const char = line[i];
        const nextChar = line[i + 1];
        
        if (char === '"' && inQuotes && nextChar === '"') {
            current += '"';
            i++; // Skip next quote
        } else if (char === '"') {
            inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
            values.push(current);
            current = '';
        } else {
            current += char;
        }
    }
    
    values.push(current); // Add last value
    return values;
}

// Populate category filter dropdown
function populateCategoryFilter() {
    const categoryFilter = document.getElementById('category-filter');
    const categories = [...new Set(allBooks.map(book => book.category))].sort();
    
    categories.forEach(category => {
        if (category) {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = category;
            categoryFilter.appendChild(option);
        }
    });
}

// Update header statistics
function updateStats(filename) {
    const totalBooksEl = document.getElementById('total-books');
    const lastUpdatedEl = document.getElementById('last-updated');
    
    totalBooksEl.textContent = allBooks.length.toLocaleString('el-GR');
    
    // Extract date from filename if it's a dated file
    const filenameOnly = filename.split('/').pop();
    
    if (filenameOnly.startsWith('20') && filenameOnly.includes('_sep_data.csv')) {
        // Format: YYYYMMDD_sep_data.csv
        const dateStr = filenameOnly.split('_')[0];
        try {
            const year = dateStr.substring(0, 4);
            const month = dateStr.substring(4, 6);
            const day = dateStr.substring(6, 8);
            const date = new Date(year, parseInt(month) - 1, day);
            
            lastUpdatedEl.textContent = date.toLocaleDateString('el-GR', {
                day: 'numeric',
                month: 'short',
                year: 'numeric'
            });
        } catch (error) {
            const today = new Date();
            lastUpdatedEl.textContent = today.toLocaleDateString('el-GR', {
                day: 'numeric',
                month: 'short',
                year: 'numeric'
            });
        }
    } else {
        // Default to today's date for latest.csv
        const today = new Date();
        lastUpdatedEl.textContent = today.toLocaleDateString('el-GR', {
            day: 'numeric',
            month: 'short',
            year: 'numeric'
        });
    }
}

// Render books in the table
function renderBooks() {
    const tbody = document.getElementById('books-tbody');
    const resultsCount = document.getElementById('results-count');
    
    tbody.innerHTML = '';
    
    if (filteredBooks.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" style="text-align: center; padding: 3rem; color: var(--text-muted);">
                    Δεν βρέθηκαν αποτελέσματα
                </td>
            </tr>
        `;
        resultsCount.textContent = 'Δεν βρέθηκαν βιβλία';
        return;
    }
    
    filteredBooks.forEach((book, index) => {
        const row = document.createElement('tr');
        row.style.animationDelay = `${Math.min(index * 0.05, 0.5)}s`;
        
        row.innerHTML = `
            <td>${escapeHtml(book.title)}</td>
            <td>${escapeHtml(book.author)}</td>
            <td>${escapeHtml(book.publisher)}</td>
            <td>${escapeHtml(book.category)}</td>
            <td>${escapeHtml(book.date)}</td>
            <td>${escapeHtml(book.pages)}</td>
            <td>${escapeHtml(book.ISBN)}</td>
            <td>${formatPrice(book.discount_price || book.price)}</td>
        `;
        
        tbody.appendChild(row);
    });
    
    const countText = filteredBooks.length === allBooks.length
        ? `Εμφάνιση όλων των ${filteredBooks.length.toLocaleString('el-GR')} βιβλίων`
        : `Εμφάνιση ${filteredBooks.length.toLocaleString('el-GR')} από ${allBooks.length.toLocaleString('el-GR')} βιβλία`;
    
    resultsCount.textContent = countText;
}

// Format price with euro symbol
function formatPrice(price) {
    if (!price) return '—';
    
    // Extract numeric value
    const numericPrice = parseFloat(price.replace(/[^\d.,]/g, '').replace(',', '.'));
    
    if (isNaN(numericPrice)) return price;
    
    return `${numericPrice.toFixed(2)}€`;
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Setup event listeners
function setupEventListeners() {
    const searchInput = document.getElementById('search');
    const categoryFilter = document.getElementById('category-filter');
    const sortSelect = document.getElementById('sort-select');
	const fileSelect = document.getElementById('file-select');
    
    // File selector
    fileSelect.addEventListener('change', (e) => {
        currentFile = e.target.value;
        loadBooksData(currentFile);
    });						
    // Search with debounce
    let searchTimeout;
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            applyFilters();
        }, 300);
    });
    
    // Category filter
    categoryFilter.addEventListener('change', applyFilters);
    
    // Sort
    sortSelect.addEventListener('change', applyFilters);
    
    // Table header sorting
    const tableHeaders = document.querySelectorAll('.books-table th[data-sort]');
    tableHeaders.forEach(header => {
        header.addEventListener('click', () => {
            const sortKey = header.dataset.sort;
            const currentSort = sortSelect.value;
            
            // Toggle sort direction if same column
            if (currentSort.startsWith(sortKey)) {
                const direction = currentSort.endsWith('asc') ? 'desc' : 'asc';
                sortSelect.value = `${sortKey}-${direction}`;
            } else {
                sortSelect.value = `${sortKey}-asc`;
            }
            
            applyFilters();
        });
    });
}

// Apply all filters and sorting
function applyFilters() {
    const searchTerm = document.getElementById('search').value.toLowerCase().trim();
    const selectedCategory = document.getElementById('category-filter').value;
    const sortValue = document.getElementById('sort-select').value;
    
    // Start with all books
    filteredBooks = [...allBooks];
    
    // Apply search filter
    if (searchTerm) {
        filteredBooks = filteredBooks.filter(book => {
            const searchFields = [
                book.title,
                book.author,
                book.publisher,
                book.category,
                book.ISBN
            ].join(' ').toLowerCase();
            
            return searchFields.includes(searchTerm);
        });
    }
    
    // Apply category filter
    if (selectedCategory) {
        filteredBooks = filteredBooks.filter(book => book.category === selectedCategory);
    }
    
    // Apply sorting
    const [sortKey, sortDirection] = sortValue.split('-');
    
    filteredBooks.sort((a, b) => {
        let aVal = a[sortKey] || '';
        let bVal = b[sortKey] || '';
        
        // Special handling for price sorting
        if (sortKey === 'price') {
            aVal = parseFloat((a.discount_price || a.price || '0').replace(/[^\d.,]/g, '').replace(',', '.')) || 0;
            bVal = parseFloat((b.discount_price || b.price || '0').replace(/[^\d.,]/g, '').replace(',', '.')) || 0;
        }
        // Special handling for pages sorting
        else if (sortKey === 'pages') {
            aVal = parseInt(aVal) || 0;
            bVal = parseInt(bVal) || 0;
        }
        // String comparison for other fields
        else {
            aVal = aVal.toString().toLowerCase();
            bVal = bVal.toString().toLowerCase();
        }
        
        if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
        if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
        return 0;
    });
    
    renderBooks();
}
