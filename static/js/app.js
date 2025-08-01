// Global application state
const App = {
    currentPage: 'dashboard',
    sidebarCollapsed: false,
    charts: {},
    
    // Initialize the application
    init() {
        this.setupEventListeners();
        this.setupSidebar();
        this.setupToasts();
        this.setupDatePickers();
        this.loadPage('dashboard');
    },
    
    // Setup global event listeners
    setupEventListeners() {
        // Sidebar toggle
        document.getElementById('toggleSidebar')?.addEventListener('click', () => {
            this.toggleSidebar();
        });
        
        // Sidebar navigation
        document.querySelectorAll('.sidebar-item[data-page]').forEach(item => {
            item.addEventListener('click', (e) => {
                const page = e.currentTarget.dataset.page;
                this.loadPage(page);
            });
        });
        
        // Form submissions
        document.addEventListener('submit', (e) => {
            if (e.target.matches('form[data-ajax]')) {
                e.preventDefault();
                this.handleFormSubmission(e.target);
            }
        });
        
        // Loading state management
        document.addEventListener('fetch-start', () => {
            this.showLoading();
        });
        
        document.addEventListener('fetch-end', () => {
            this.hideLoading();
        });
    },
    
    // Setup sidebar functionality
    setupSidebar() {
        const sidebar = document.getElementById('sidebar');
        const mainContent = document.getElementById('mainContent');
        
        // Handle responsive sidebar
        const handleResize = () => {
            if (window.innerWidth <= 992) {
                sidebar.classList.remove('sidebar-collapsed');
                mainContent.classList.remove('expanded');
            }
        };
        
        window.addEventListener('resize', handleResize);
        handleResize();
    },
    
    // Toggle sidebar collapsed state
    toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        const mainContent = document.getElementById('mainContent');
        
        if (window.innerWidth <= 992) {
            // Mobile: show/hide sidebar
            sidebar.classList.toggle('show');
        } else {
            // Desktop: collapse/expand
            sidebar.classList.toggle('sidebar-collapsed');
            mainContent.classList.toggle('expanded');
            this.sidebarCollapsed = !this.sidebarCollapsed;
        }
    },
    
    // Setup toast notifications
    setupToasts() {
        const toasts = document.querySelectorAll('.toast');
        toasts.forEach(toast => {
            const bsToast = new bootstrap.Toast(toast, {
                autohide: true,
                delay: 5000
            });
            bsToast.show();
        });
    },
    
    // Setup date pickers
    setupDatePickers() {
        if (typeof flatpickr !== 'undefined') {
            flatpickr('.date-picker', {
                dateFormat: 'd/m/Y',
                locale: 'pt'
            });
            
            flatpickr('.datetime-picker', {
                dateFormat: 'd/m/Y H:i',
                enableTime: true,
                locale: 'pt'
            });
        }
    },
    
    // Load a specific page
    loadPage(page) {
        // Update sidebar active state
        document.querySelectorAll('.sidebar-item').forEach(item => {
            item.classList.remove('active');
        });
        
        const activeItem = document.querySelector(`.sidebar-item[data-page="${page}"]`);
        if (activeItem) {
            activeItem.classList.add('active');
        }
        
        // Update page containers
        document.querySelectorAll('.page-container').forEach(container => {
            container.classList.remove('active');
        });
        
        const pageContainer = document.getElementById(page);
        if (pageContainer) {
            pageContainer.classList.add('active');
        }
        
        this.currentPage = page;
        
        // Load page-specific functionality
        this.loadPageSpecific(page);
    },
    
    // Load page-specific functionality
    loadPageSpecific(page) {
        switch (page) {
            case 'dashboard':
                this.loadDashboard();
                break;
            case 'products':
                this.loadProducts();
                break;
            case 'sales':
                this.loadSales();
                break;
            case 'customers':
                this.loadCustomers();
                break;
            default:
                break;
        }
    },
    
    // Dashboard specific functionality
    loadDashboard() {
        this.setPageTitle('Dashboard');
        this.loadDashboardCharts();
    },
    
    // Load dashboard charts
    loadDashboardCharts() {
        fetch('/api/dashboard/charts')
            .then(response => response.json())
            .then(data => {
                this.renderSalesChart(data.sales);
                this.renderProductsChart(data.products);
            })
            .catch(error => {
                console.error('Error loading dashboard charts:', error);
                this.showToast('Erro ao carregar gráficos', 'error');
            });
    },
    
    // Render sales chart
    renderSalesChart(data) {
        const ctx = document.getElementById('salesChart');
        if (!ctx) return;
        
        // Destroy existing chart
        if (this.charts.sales) {
            this.charts.sales.destroy();
        }
        
        this.charts.sales = new Chart(ctx.getContext('2d'), {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Vendas (€)',
                    data: data.data,
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return App.formatCurrency(value);
                            }
                        }
                    }
                }
            }
        });
    },
    
    // Render products chart
    renderProductsChart(data) {
        const ctx = document.getElementById('productsChart');
        if (!ctx) return;
        
        // Destroy existing chart
        if (this.charts.products) {
            this.charts.products.destroy();
        }
        
        this.charts.products = new Chart(ctx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.revenues,
                    backgroundColor: [
                        '#2563eb',
                        '#22c55e',
                        '#eab308',
                        '#ef4444',
                        '#0ea5e9'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.label + ': ' + App.formatCurrency(context.raw);
                            }
                        }
                    }
                }
            }
        });
    },
    
    // Handle AJAX form submissions
    handleFormSubmission(form) {
        const formData = new FormData(form);
        const url = form.action || window.location.href;
        const method = form.method || 'POST';
        
        this.showLoading();
        
        fetch(url, {
            method: method,
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showToast(data.message || 'Operação realizada com sucesso!', 'success');
                if (data.redirect) {
                    window.location.href = data.redirect;
                } else {
                    this.refreshCurrentPage();
                }
            } else {
                this.showToast(data.message || 'Erro ao processar solicitação', 'error');
            }
        })
        .catch(error => {
            console.error('Form submission error:', error);
            this.showToast('Erro ao processar solicitação', 'error');
        })
        .finally(() => {
            this.hideLoading();
        });
    },
    
    // Show loading indicator
    showLoading() {
        const loading = document.querySelector('.loading');
        if (loading) {
            loading.classList.add('active');
        }
    },
    
    // Hide loading indicator
    hideLoading() {
        const loading = document.querySelector('.loading');
        if (loading) {
            loading.classList.remove('active');
        }
    },
    
    // Show toast notification
    showToast(message, type = 'info') {
        const toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) return;
        
        const toastHtml = `
            <div class="toast" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-header">
                    <i class="fas fa-${this.getToastIcon(type)} text-${type} me-2"></i>
                    <strong class="me-auto">GestVendas</strong>
                    <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
                </div>
                <div class="toast-body">${message}</div>
            </div>
        `;
        
        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        
        const newToast = toastContainer.lastElementChild;
        const bsToast = new bootstrap.Toast(newToast, {
            autohide: true,
            delay: 5000
        });
        bsToast.show();
        
        // Remove toast after it's hidden
        newToast.addEventListener('hidden.bs.toast', () => {
            newToast.remove();
        });
    },
    
    // Get appropriate icon for toast type
    getToastIcon(type) {
        const icons = {
            'success': 'check-circle',
            'error': 'times-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    },
    
    // Format currency values
    formatCurrency(value) {
        return new Intl.NumberFormat('pt-PT', {
            style: 'currency',
            currency: 'EUR'
        }).format(value);
    },
    
    // Set page title
    setPageTitle(title) {
        document.title = `${title} - GestVendas`;
    },
    
    // Refresh current page
    refreshCurrentPage() {
        this.loadPageSpecific(this.currentPage);
    },
    
    // Initialize DataTables
    initDataTables(selector, options = {}) {
        if (typeof $ !== 'undefined' && $.fn.DataTable) {
            const defaultOptions = {
                language: {
                    url: '//cdn.datatables.net/plug-ins/1.13.5/i18n/pt-PT.json'
                },
                responsive: true,
                pageLength: 25,
                order: [[0, 'desc']]
            };
            
            return $(selector).DataTable({...defaultOptions, ...options});
        }
    },
    
    // Product search functionality
    setupProductSearch() {
        const searchInput = document.getElementById('productSearch');
        if (!searchInput) return;
        
        let searchTimeout;
        
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.searchProducts(e.target.value);
            }, 300);
        });
    },
    
    // Search products via API
    searchProducts(query) {
        if (query.length < 2) return;
        
        fetch(`/api/products/search?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(products => {
                this.displayProductSearchResults(products);
            })
            .catch(error => {
                console.error('Product search error:', error);
            });
    },
    
    // Display product search results
    displayProductSearchResults(products) {
        const resultsContainer = document.getElementById('productSearchResults');
        if (!resultsContainer) return;
        
        if (products.length === 0) {
            resultsContainer.innerHTML = '<p class="text-muted">Nenhum produto encontrado</p>';
            return;
        }
        
        const resultsHtml = products.map(product => `
            <div class="product-result" data-product-id="${product.id}">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${product.name}</strong>
                        <br>
                        <small class="text-muted">Código: ${product.code}</small>
                    </div>
                    <div class="text-end">
                        <div class="fw-bold">${this.formatCurrency(product.sale_price)}</div>
                        <small class="text-muted">Stock: ${product.stock_quantity} ${product.unit}</small>
                    </div>
                </div>
            </div>
        `).join('');
        
        resultsContainer.innerHTML = resultsHtml;
        
        // Add click handlers for product results
        resultsContainer.querySelectorAll('.product-result').forEach(result => {
            result.addEventListener('click', (e) => {
                const productId = e.currentTarget.dataset.productId;
                this.selectProduct(productId, products);
            });
        });
    },
    
    // Select a product from search results
    selectProduct(productId, products) {
        const product = products.find(p => p.id == productId);
        if (!product) return;
        
        // Trigger custom event for product selection
        document.dispatchEvent(new CustomEvent('productSelected', {
            detail: product
        }));
    }
};

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    App.init();
});

// Global utility functions
window.formatCurrency = App.formatCurrency.bind(App);
window.showToast = App.showToast.bind(App);
window.showLoading = App.showLoading.bind(App);
window.hideLoading = App.hideLoading.bind(App);
