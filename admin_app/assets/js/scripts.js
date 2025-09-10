// App Usage Admin Dashboard - Main JavaScript File

// Configuration
const API_BASE_URL = 'http://localhost:8000/api/v1';
const API_KEY = 'CyRLgKg-FL7RuTtVvb7BPr8wmUoI1PamDj4Xdb3eT9w'; // Replace with actual API key
const ITEMS_PER_PAGE = 10;

// Global variables
let currentPage = 1;
let totalItems = 0;
let currentData = [];

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    // Load dashboard by default
    loadPage('dashboard');
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Navigation Functions
function loadPage(pageName) {
    const contentArea = document.getElementById('content-area');
    const pageTitle = document.getElementById('page-title');
    
    // Update active navigation
    updateActiveNavigation(pageName);
    
    // Show loading spinner
    showLoading();
    
    // Load page content
    switch(pageName) {
        case 'dashboard':
            pageTitle.textContent = 'Dashboard';
            loadDashboard();
            break;
        case 'app-manager':
            pageTitle.textContent = 'App Manager';
            loadAppManager();
            break;
        default:
            pageTitle.textContent = 'Page Not Found';
            contentArea.innerHTML = '<div class="alert alert-warning">Page not found.</div>';
    }
}

function updateActiveNavigation(activePage) {
    // Remove active class from all nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    // Add active class to current page
    document.querySelectorAll('.nav-link').forEach(link => {
        if (link.onclick && link.onclick.toString().includes(activePage)) {
            link.classList.add('active');
        }
    });
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('show');
}

// Loading Functions
function showLoading() {
    const contentArea = document.getElementById('content-area');
    contentArea.innerHTML = `
        <div class="d-flex justify-content-center align-items-center" style="height: 400px;">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `;
}

// Dashboard Functions
async function loadDashboard() {
    try {
        const contentArea = document.getElementById('content-area');
        
        contentArea.innerHTML = `
            <!-- Date Range Filter -->
            <div class="row mb-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-body py-3">
                            <div class="d-flex justify-content-between align-items-center">
                                <h6 class="mb-0">Analytics Period</h6>
                                <div class="btn-group" role="group" aria-label="Time period selection">
                                    <input type="radio" class="btn-check" name="period" id="period-7d" value="7d" checked>
                                    <label class="btn btn-outline-primary btn-sm" for="period-7d">7 Days</label>
                                    
                                    <input type="radio" class="btn-check" name="period" id="period-30d" value="30d">
                                    <label class="btn btn-outline-primary btn-sm" for="period-30d">30 Days</label>
                                    
                                    <input type="radio" class="btn-check" name="period" id="period-90d" value="90d">
                                    <label class="btn btn-outline-primary btn-sm" for="period-90d">90 Days</label>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- KPI Dashboard Cards -->
            <div class="row mb-4" id="kpi-cards">
                <!-- Cards will be loaded here -->
                <div class="col-12 text-center py-5">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading KPI data...</span>
                    </div>
                </div>
            </div>

            <!-- Additional Analytics -->
            <div class="row mb-4">
                <div class="col-lg-8">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="card-title mb-0">Application Catalog Overview</h5>
                        </div>
                        <div class="card-body">
                            <div id="app-catalog-overview">
                                <div class="text-center">
                                    <div class="spinner-border spinner-border-sm text-primary" role="status">
                                        <span class="visually-hidden">Loading...</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-lg-4">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="card-title mb-0">Quick Actions</h5>
                        </div>
                        <div class="card-body">
                            <div class="d-grid gap-2">
                                <button class="btn btn-primary" onclick="loadPage('app-manager')">
                                    <i class="bi bi-plus me-2"></i>Add Application
                                </button>
                                <button class="btn btn-outline-secondary" onclick="showActiveUsersList()">
                                    <i class="bi bi-people me-2"></i>View Active Users
                                </button>
                                <button class="btn btn-outline-secondary" onclick="showUsageBreakdown()">
                                    <i class="bi bi-bar-chart me-2"></i>Usage Breakdown
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Load KPI data
        loadKPIDashboard();
        
        // Load app catalog overview
        loadAppCatalogOverview();
        
        // Add event listeners for period selection
        document.querySelectorAll('input[name="period"]').forEach(radio => {
            radio.addEventListener('change', function() {
                if (this.checked) {
                    loadKPIDashboard(this.value);
                }
            });
        });
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showError('Failed to load dashboard data');
    }
}

// Load KPI Dashboard with 6 interactive cards
async function loadKPIDashboard(period = '7d') {
    try {
        const kpiContainer = document.getElementById('kpi-cards');
        
        // Show loading state
        kpiContainer.innerHTML = `
            <div class="col-12 text-center py-3">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading KPI data...</span>
                </div>
            </div>
        `;
        
        // Fetch dashboard summary data
        const dashboardData = await fetchDashboardSummary(period);
        
        // Generate KPI cards
        kpiContainer.innerHTML = `
            <!-- Total Applications Tracked -->
            <div class="col-xl-4 col-md-6 mb-4">
                <div class="card dashboard-card bg-light-blue h-100 clickable-card" onclick="handleCardClick('total-apps')">
                    <div class="card-body position-relative">
                        <div class="card-title">Total Applications Tracked</div>
                        <div class="card-value">${dashboardData.total_applications || 0}</div>
                        <div class="card-trend ${dashboardData.total_applications_trend >= 0 ? 'positive' : 'negative'}">
                            <i class="bi ${dashboardData.total_applications_trend >= 0 ? 'bi-arrow-up' : 'bi-arrow-down'}"></i>
                            ${Math.abs(dashboardData.total_applications_trend || 0)}%
                        </div>
                        <i class="bi bi-grid-3x3-gap card-icon"></i>
                    </div>
                </div>
            </div>

            <!-- Active Users -->
            <div class="col-xl-4 col-md-6 mb-4">
                <div class="card dashboard-card bg-light-success h-100 clickable-card" onclick="handleCardClick('active-users', '${period}')">
                    <div class="card-body position-relative">
                        <div class="card-title">Active Users (${period.toUpperCase()})</div>
                        <div class="card-value">${dashboardData.active_users?.count || 0}</div>
                        <div class="card-trend ${(dashboardData.active_users?.trend_percentage || 0) >= 0 ? 'positive' : 'negative'}">
                            <i class="bi ${(dashboardData.active_users?.trend_percentage || 0) >= 0 ? 'bi-arrow-up' : 'bi-arrow-down'}"></i>
                            ${Math.abs(dashboardData.active_users?.trend_percentage || 0).toFixed(1)}%
                        </div>
                        <i class="bi bi-people card-icon"></i>
                    </div>
                </div>
            </div>

            <!-- Total Usage Hours -->
            <div class="col-xl-4 col-md-6 mb-4">
                <div class="card dashboard-card bg-light-info h-100 clickable-card" onclick="handleCardClick('usage-hours', '${period}')">
                    <div class="card-body position-relative">
                        <div class="card-title">Total Usage Hours (${period.toUpperCase()})</div>
                        <div class="card-value">${(dashboardData.total_hours?.total_hours || 0).toFixed(1)}h</div>
                        <div class="card-trend ${(dashboardData.total_hours?.trend_percentage || 0) >= 0 ? 'positive' : 'negative'}">
                            <i class="bi ${(dashboardData.total_hours?.trend_percentage || 0) >= 0 ? 'bi-arrow-up' : 'bi-arrow-down'}"></i>
                            ${Math.abs(dashboardData.total_hours?.trend_percentage || 0).toFixed(1)}%
                        </div>
                        <div class="mini-chart">
                            ${generateSparkline(dashboardData.total_hours?.daily_breakdown || [])}
                        </div>
                        <i class="bi bi-clock card-icon"></i>
                    </div>
                </div>
            </div>

            <!-- New Users -->
            <div class="col-xl-4 col-md-6 mb-4">
                <div class="card dashboard-card bg-light-warning h-100 clickable-card" onclick="handleCardClick('new-users', '${period}')">
                    <div class="card-body position-relative">
                        <div class="card-title">New Users (${period.toUpperCase()})</div>
                        <div class="card-value">${dashboardData.new_users?.count || 0}</div>
                        <div class="card-trend ${(dashboardData.new_users?.growth_rate || 0) >= 0 ? 'positive' : 'negative'}">
                            <i class="bi ${(dashboardData.new_users?.growth_rate || 0) >= 0 ? 'bi-arrow-up' : 'bi-arrow-down'}"></i>
                            ${Math.abs(dashboardData.new_users?.growth_rate || 0).toFixed(1)}%
                        </div>
                        <i class="bi bi-person-plus card-icon"></i>
                    </div>
                </div>
            </div>

            <!-- Top App by Usage -->
            <div class="col-xl-4 col-md-6 mb-4">
                <div class="card dashboard-card bg-light-purple h-100 clickable-card" onclick="handleCardClick('top-app', '${period}')">
                    <div class="card-body position-relative">
                        <div class="card-title">Top App by Usage</div>
                        <div class="card-value text-truncate" title="${dashboardData.top_app?.app_name || 'N/A'}">
                            ${dashboardData.top_app?.app_name || 'N/A'}
                        </div>
                        <div class="card-subtitle">${(dashboardData.top_app?.total_hours || 0).toFixed(1)}h total</div>
                        <div class="mini-chart">
                            ${generateSparkline(dashboardData.top_app?.daily_usage || [])}
                        </div>
                        <i class="bi bi-trophy card-icon"></i>
                    </div>
                </div>
            </div>

            <!-- Churn Rate -->
            <div class="col-xl-4 col-md-6 mb-4">
                <div class="card dashboard-card bg-light-danger h-100 clickable-card" onclick="handleCardClick('churn-rate', '${period}')">
                    <div class="card-body position-relative">
                        <div class="card-title">Churn Rate</div>
                        <div class="card-value">${(dashboardData.churn_rate?.rate || 0).toFixed(1)}%</div>
                        <div class="card-subtitle">
                            <span class="badge ${getChurnHealthBadge(dashboardData.churn_rate?.health_status)}">
                                ${dashboardData.churn_rate?.health_status || 'Unknown'}
                            </span>
                        </div>
                        <i class="bi bi-graph-down card-icon"></i>
                    </div>
                </div>
            </div>
        `;
        
    } catch (error) {
        console.error('Error loading KPI dashboard:', error);
        document.getElementById('kpi-cards').innerHTML = `
            <div class="col-12">
                <div class="alert alert-warning">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    Failed to load KPI data. Some analytics features may not be available yet.
                </div>
            </div>
        `;
    }
}

// Load app catalog overview (existing functionality)
async function loadAppCatalogOverview() {
    try {
        const stats = await fetchAppListSummary();
        const container = document.getElementById('app-catalog-overview');
        
        container.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <div class="mb-3">
                        <h6>Application Types</h6>
                        ${generateAppTypesChart(stats.app_types || {})}
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="mb-3">
                        <h6>Top Publishers</h6>
                        ${generatePublishersList(stats.publishers || {})}
                    </div>
                </div>
            </div>
        `;
        
    } catch (error) {
        console.error('Error loading app catalog overview:', error);
        document.getElementById('app-catalog-overview').innerHTML = `
            <div class="alert alert-warning">
                <i class="bi bi-exclamation-triangle me-2"></i>
                Failed to load application catalog data.
            </div>
        `;
    }
}

async function loadRecentApplications() {
    try {
        const response = await fetchApplications(1, 5); // Get first 5 apps
        const recentAppsContainer = document.getElementById('recent-apps');
        
        if (response.app_list && response.app_list.length > 0) {
            recentAppsContainer.innerHTML = `
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>Application</th>
                                <th>Type</th>
                                <th>Version</th>
                                <th>Publisher</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${response.app_list.map(app => `
                                <tr>
                                    <td><strong>${app.app_name}</strong></td>
                                    <td><span class="badge bg-secondary">${app.app_type}</span></td>
                                    <td>${app.current_version}</td>
                                    <td>${app.publisher}</td>
                                    <td>
                                        <span class="badge ${app.enable_tracking ? 'status-active' : 'status-inactive'}">
                                            ${app.enable_tracking ? 'Active' : 'Inactive'}
                                        </span>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        } else {
            recentAppsContainer.innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-inbox"></i>
                    <p>No applications found. <a href="#" onclick="loadPage('app-manager')">Add your first application</a>.</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading recent applications:', error);
        document.getElementById('recent-apps').innerHTML = `
            <div class="alert alert-warning">
                <i class="bi bi-exclamation-triangle me-2"></i>
                Failed to load recent applications.
            </div>
        `;
    }
}

// App Manager Functions
async function loadAppManager() {
    const contentArea = document.getElementById('content-area');
    
    contentArea.innerHTML = `
        <!-- App Manager Header -->
        <div class="d-flex justify-content-between align-items-center mb-4">
            <div>
                <h4 class="mb-1">Application Management</h4>
                <p class="text-muted mb-0">Manage your applications, add new ones, and update existing entries.</p>
            </div>
            <button class="btn btn-primary" onclick="showAddAppModal()">
                <i class="bi bi-plus me-2"></i>Add Application
            </button>
        </div>

        <!-- Applications Table -->
        <div class="card">
            <div class="card-body">
                <div id="apps-table-container">
                    <div class="text-center py-4">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Loading applications...</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Add/Edit App Modal -->
        <div class="modal fade" id="appModal" tabindex="-1" aria-labelledby="appModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="appModalLabel">Add Application</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <form id="appForm">
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label for="app_name" class="form-label">Application Name *</label>
                                        <input type="text" class="form-control" id="app_name" name="app_name" required>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label for="app_type" class="form-label">Application Type *</label>
                                        <select class="form-select" id="app_type" name="app_type" required>
                                            <option value="">Select Type</option>
                                            <option value="windows">Windows</option>
                                            <option value="web">Web</option>
                                            <option value="mobile">Mobile</option>
                                            <option value="desktop">Desktop</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label for="current_version" class="form-label">Version *</label>
                                        <input type="text" class="form-control" id="current_version" name="current_version" required>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label for="publisher" class="form-label">Publisher *</label>
                                        <input type="text" class="form-control" id="publisher" name="publisher" required>
                                    </div>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label for="released_date" class="form-label">Release Date *</label>
                                        <input type="date" class="form-control" id="released_date" name="released_date" required>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label for="registered_date" class="form-label">Registration Date *</label>
                                        <input type="date" class="form-control" id="registered_date" name="registered_date" required>
                                    </div>
                                </div>
                            </div>
                            <div class="mb-3">
                                <label for="description" class="form-label">Description *</label>
                                <textarea class="form-control" id="description" name="description" rows="3" required></textarea>
                            </div>
                            <div class="mb-3">
                                <label for="download_link" class="form-label">Download Link *</label>
                                <input type="url" class="form-control" id="download_link" name="download_link" required>
                            </div>
                            <div class="mb-3">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" id="enable_tracking" name="enable_tracking" checked>
                                    <label class="form-check-label" for="enable_tracking">
                                        Enable Tracking
                                    </label>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="track_usage" name="track_usage" checked>
                                        <label class="form-check-label" for="track_usage">
                                            Track Usage
                                        </label>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="track_location" name="track_location">
                                        <label class="form-check-label" for="track_location">
                                            Track Location
                                        </label>
                                    </div>
                                </div>
                            </div>
                            <div class="row mt-3">
                                <div class="col-md-6">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="track_cm" name="track_cm">
                                        <label class="form-check-label" for="track_cm">
                                            Track CPU/Memory
                                        </label>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label for="track_intr" class="form-label">Track Interval (minutes)</label>
                                        <input type="number" class="form-control" id="track_intr" name="track_intr" value="1" min="1">
                                    </div>
                                </div>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" onclick="saveApplication()">Save Application</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Load applications table
    loadApplicationsTable();
}

async function loadApplicationsTable() {
    try {
        const response = await fetchApplications(currentPage, ITEMS_PER_PAGE);
        const container = document.getElementById('apps-table-container');
        
        if (response.app_list && response.app_list.length > 0) {
            totalItems = response.total;
            currentData = response.app_list;
            
            container.innerHTML = `
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>Application</th>
                                <th>Type</th>
                                <th>Version</th>
                                <th>Publisher</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${response.app_list.map(app => `
                                <tr>
                                    <td>
                                        <div>
                                            <strong>${app.app_name}</strong>
                                            <br>
                                            <small class="text-muted">${app.description.substring(0, 50)}...</small>
                                        </div>
                                    </td>
                                    <td><span class="badge bg-secondary">${app.app_type}</span></td>
                                    <td>${app.current_version}</td>
                                    <td>${app.publisher}</td>
                                    <td>
                                        <span class="badge ${app.enable_tracking ? 'status-active' : 'status-inactive'}">
                                            ${app.enable_tracking ? 'Active' : 'Inactive'}
                                        </span>
                                    </td>
                                    <td>
                                        <button class="btn btn-sm btn-outline-primary btn-action me-1" onclick="editApplication(${app.app_id})" title="Edit">
                                            <i class="bi bi-pencil"></i>
                                        </button>
                                        <button class="btn btn-sm btn-outline-danger btn-action" onclick="deleteApplication(${app.app_id}, '${app.app_name}')" title="Delete">
                                            <i class="bi bi-trash"></i>
                                        </button>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
                ${generatePagination()}
            `;
        } else {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-inbox"></i>
                    <h5>No Applications Found</h5>
                    <p>Get started by adding your first application.</p>
                    <button class="btn btn-primary" onclick="showAddAppModal()">
                        <i class="bi bi-plus me-2"></i>Add Application
                    </button>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading applications:', error);
        document.getElementById('apps-table-container').innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle me-2"></i>
                Failed to load applications. Please try again.
            </div>
        `;
    }
}

// Modal Functions
function showAddAppModal() {
    document.getElementById('appModalLabel').textContent = 'Add Application';
    document.getElementById('appForm').reset();
    document.getElementById('registered_date').value = new Date().toISOString().split('T')[0];
    const modal = new bootstrap.Modal(document.getElementById('appModal'));
    modal.show();
}

async function editApplication(appId) {
    try {
        const app = await fetchApplicationById(appId);
        
        // Populate form
        document.getElementById('app_name').value = app.app_name;
        document.getElementById('app_type').value = app.app_type;
        document.getElementById('current_version').value = app.current_version;
        document.getElementById('publisher').value = app.publisher;
        document.getElementById('released_date').value = app.released_date;
        document.getElementById('registered_date').value = app.registered_date;
        document.getElementById('description').value = app.description;
        document.getElementById('download_link').value = app.download_link;
        document.getElementById('enable_tracking').checked = app.enable_tracking;
        document.getElementById('track_usage').checked = app.track_usage;
        document.getElementById('track_location').checked = app.track_location;
        document.getElementById('track_cm').checked = app.track_cm;
        document.getElementById('track_intr').value = app.track_intr;
        
        // Store app ID for update
        document.getElementById('appForm').dataset.appId = appId;
        
        document.getElementById('appModalLabel').textContent = 'Edit Application';
        const modal = new bootstrap.Modal(document.getElementById('appModal'));
        modal.show();
    } catch (error) {
        console.error('Error loading application for edit:', error);
        showError('Failed to load application data');
    }
}

async function saveApplication() {
    const form = document.getElementById('appForm');
    const formData = new FormData(form);
    const appId = form.dataset.appId;
    
    // Validate required fields
    const requiredFields = ['app_name', 'app_type', 'current_version', 'publisher', 'released_date', 'registered_date', 'description', 'download_link'];
    const missingFields = [];
    
    for (const field of requiredFields) {
        const value = formData.get(field);
        if (!value || value.trim() === '') {
            missingFields.push(field.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()));
        }
    }
    
    if (missingFields.length > 0) {
        showError(`Please fill in all required fields: ${missingFields.join(', ')}`);
        return;
    }
    
    // Validate and format download link
    let downloadLink = formData.get('download_link').trim();
    if (!downloadLink.startsWith('http://') && !downloadLink.startsWith('https://')) {
        downloadLink = 'https://' + downloadLink;
    }
    
    // Build application object with proper validation
    const appData = {
        app_name: formData.get('app_name').trim(),
        app_type: formData.get('app_type').trim(),
        current_version: formData.get('current_version').trim(),
        publisher: formData.get('publisher').trim(),
        released_date: formData.get('released_date'),
        registered_date: formData.get('registered_date'),
        description: formData.get('description').trim(),
        download_link: downloadLink,
        enable_tracking: formData.has('enable_tracking'),
        track: {
            usage: formData.has('track_usage'),
            location: formData.has('track_location'),
            cpu_memory: {
                track_cm: formData.has('track_cm'),
                track_intr: parseInt(formData.get('track_intr')) || 1
            }
        }
    };
    
    // Additional validation
    if (appData.description.length > 500) {
        showError('Description must be 500 characters or less');
        return;
    }
    
    if (appData.app_name.length > 100) {
        showError('Application name must be 100 characters or less');
        return;
    }
    
    try {
        if (appId) {
            // Update existing application
            await updateApplication(appId, appData);
            showSuccess('Application updated successfully');
        } else {
            // Create new application
            await createApplication(appData);
            showSuccess('Application created successfully');
        }
        
        // Close modal and refresh table
        bootstrap.Modal.getInstance(document.getElementById('appModal')).hide();
        loadApplicationsTable();
        
        // Refresh dashboard if we're adding the first app
        if (currentData.length === 0) {
            loadRecentApplications();
        }
        
    } catch (error) {
        console.error('Error saving application:', error);
        
        // Parse error response for better user feedback
        if (error.message.includes('422')) {
            showError('Validation error: Please check all fields are filled correctly');
        } else if (error.message.includes('400')) {
            showError('Bad request: Please check your input data');
        } else {
            showError('Failed to save application. Please try again.');
        }
    }
}

async function deleteApplication(appId, appName) {
    if (confirm(`Are you sure you want to delete "${appName}"? This action cannot be undone.`)) {
        try {
            await deleteApplicationById(appId);
            showSuccess('Application deleted successfully');
            loadApplicationsTable();
        } catch (error) {
            console.error('Error deleting application:', error);
            showError('Failed to delete application');
        }
    }
}

// Pagination Functions
function generatePagination() {
    const totalPages = Math.ceil(totalItems / ITEMS_PER_PAGE);
    
    if (totalPages <= 1) return '';
    
    let pagination = '<nav aria-label="Applications pagination"><ul class="pagination justify-content-center mt-3">';
    
    // Previous button
    pagination += `
        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage - 1})">Previous</a>
        </li>
    `;
    
    // Page numbers
    for (let i = 1; i <= totalPages; i++) {
        if (i === currentPage || i === 1 || i === totalPages || (i >= currentPage - 1 && i <= currentPage + 1)) {
            pagination += `
                <li class="page-item ${i === currentPage ? 'active' : ''}">
                    <a class="page-link" href="#" onclick="changePage(${i})">${i}</a>
                </li>
            `;
        } else if (i === currentPage - 2 || i === currentPage + 2) {
            pagination += '<li class="page-item disabled"><span class="page-link">...</span></li>';
        }
    }
    
    // Next button
    pagination += `
        <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage + 1})">Next</a>
        </li>
    `;
    
    pagination += '</ul></nav>';
    return pagination;
}

function changePage(page) {
    if (page >= 1 && page <= Math.ceil(totalItems / ITEMS_PER_PAGE)) {
        currentPage = page;
        loadApplicationsTable();
    }
}

// API Functions
async function fetchApplications(page = 1, limit = ITEMS_PER_PAGE) {
    const skip = (page - 1) * limit;
    const response = await fetch(`${API_BASE_URL}/app_list/?skip=${skip}&limit=${limit}`, {
        headers: {
            'X-API-Key-725d9439': API_KEY
        }
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
}

async function fetchApplicationById(appId) {
    const response = await fetch(`${API_BASE_URL}/app_list/${appId}`, {
        headers: {
            'X-API-Key-725d9439': API_KEY
        }
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
}

async function fetchAppListSummary() {
    const response = await fetch(`${API_BASE_URL}/app_list/summary/stats`, {
        headers: {
            'X-API-Key-725d9439': API_KEY
        }
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
}

async function createApplication(appData) {
    const response = await fetch(`${API_BASE_URL}/app_list/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key-725d9439': API_KEY
        },
        body: JSON.stringify(appData)
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
}

async function updateApplication(appId, appData) {
    const response = await fetch(`${API_BASE_URL}/app_list/${appId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key-725d9439': API_KEY
        },
        body: JSON.stringify(appData)
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
}

async function deleteApplicationById(appId) {
    const response = await fetch(`${API_BASE_URL}/app_list/${appId}`, {
        method: 'DELETE',
        headers: {
            'X-API-Key-725d9439': API_KEY
        }
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
}

// Chart and Display Functions
function generateAppTypesChart(appTypes) {
    if (Object.keys(appTypes).length === 0) {
        return '<div class="empty-state"><i class="bi bi-pie-chart"></i><p>No data available</p></div>';
    }
    
    let html = '<div class="row">';
    Object.entries(appTypes).forEach(([type, count]) => {
        const percentage = (count / Object.values(appTypes).reduce((a, b) => a + b, 0) * 100).toFixed(1);
        html += `
            <div class="col-md-6 mb-3">
                <div class="d-flex justify-content-between align-items-center">
                    <span class="text-capitalize">${type}</span>
                    <span class="badge bg-primary">${count}</span>
                </div>
                <div class="progress mt-1" style="height: 8px;">
                    <div class="progress-bar" role="progressbar" style="width: ${percentage}%" aria-valuenow="${percentage}" aria-valuemin="0" aria-valuemax="100"></div>
                </div>
            </div>
        `;
    });
    html += '</div>';
    return html;
}

function generatePublishersList(publishers) {
    if (Object.keys(publishers).length === 0) {
        return '<div class="empty-state"><i class="bi bi-building"></i><p>No publishers found</p></div>';
    }
    
    let html = '<div class="list-group list-group-flush">';
    Object.entries(publishers).slice(0, 5).forEach(([publisher, count]) => {
        html += `
            <div class="list-group-item d-flex justify-content-between align-items-center px-0">
                <span>${publisher}</span>
                <span class="badge bg-primary rounded-pill">${count}</span>
            </div>
        `;
    });
    html += '</div>';
    return html;
}

// KPI Dashboard Helper Functions
async function handleCardClick(cardType, period = '7d') {
    console.log(`Card clicked: ${cardType} for period: ${period}`);
    
    switch(cardType) {
        case 'total-apps':
            // Navigate to App Manager filtered to show all apps
            loadPage('app-manager');
            break;
            
        case 'active-users':
            await showActiveUsersList(period);
            break;
            
        case 'usage-hours':
            await showUsageBreakdown(period);
            break;
            
        case 'new-users':
            await showOnboardingTrend(period);
            break;
            
        case 'top-app':
            await showTopAppDetails(period);
            break;
            
        case 'churn-rate':
            await showChurnAnalysis(period);
            break;
            
        default:
            console.log('Unknown card type:', cardType);
    }
}

async function showActiveUsersList(period = '7d') {
    try {
        const data = await fetchActiveUsersAnalytics(period);
        
        // Create modal content
        const modalContent = `
            <div class="modal fade" id="activeUsersModal" tabindex="-1" aria-labelledby="activeUsersModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="activeUsersModalLabel">Active Users (${period.toUpperCase()})</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row mb-3">
                                <div class="col-md-4">
                                    <div class="text-center">
                                        <h3 class="text-primary">${data.count || 0}</h3>
                                        <p class="text-muted">Total Active Users</p>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="text-center">
                                        <h3 class="text-success">${data.previous_count || 0}</h3>
                                        <p class="text-muted">Previous Period</p>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="text-center">
                                        <h3 class="${(data.trend_percentage || 0) >= 0 ? 'text-success' : 'text-danger'}">
                                            ${(data.trend_percentage || 0) >= 0 ? '+' : ''}${(data.trend_percentage || 0).toFixed(1)}%
                                        </h3>
                                        <p class="text-muted">Change</p>
                                    </div>
                                </div>
                            </div>
                            ${data.users && data.users.length > 0 ? `
                                <div class="table-responsive">
                                    <table class="table table-sm">
                                        <thead>
                                            <tr>
                                                <th>User ID</th>
                                                <th>Last Active</th>
                                                <th>Total Sessions</th>
                                                <th>Total Hours</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            ${data.users.slice(0, 10).map(user => `
                                                <tr>
                                                    <td>${user.user_id}</td>
                                                    <td>${new Date(user.last_active).toLocaleDateString()}</td>
                                                    <td>${user.session_count || 0}</td>
                                                    <td>${(user.total_hours || 0).toFixed(1)}h</td>
                                                </tr>
                                            `).join('')}
                                        </tbody>
                                    </table>
                                    ${data.users.length > 10 ? `<p class="text-muted small">Showing first 10 of ${data.users.length} users</p>` : ''}
                                </div>
                            ` : '<p class="text-muted">No active users found for this period.</p>'}
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if any
        const existingModal = document.getElementById('activeUsersModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Add modal to body and show
        document.body.insertAdjacentHTML('beforeend', modalContent);
        const modal = new bootstrap.Modal(document.getElementById('activeUsersModal'));
        modal.show();
        
    } catch (error) {
        console.error('Error showing active users:', error);
        showError('Failed to load active users data');
    }
}

async function showUsageBreakdown(period = '7d') {
    try {
        const data = await fetchTotalHoursAnalytics(period);
        
        const modalContent = `
            <div class="modal fade" id="usageBreakdownModal" tabindex="-1" aria-labelledby="usageBreakdownModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="usageBreakdownModalLabel">Usage Hours Breakdown (${period.toUpperCase()})</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row mb-3">
                                <div class="col-md-4">
                                    <div class="text-center">
                                        <h3 class="text-primary">${(data.total_hours || 0).toFixed(1)}h</h3>
                                        <p class="text-muted">Total Hours</p>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="text-center">
                                        <h3 class="text-info">${(data.average_daily || 0).toFixed(1)}h</h3>
                                        <p class="text-muted">Daily Average</p>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="text-center">
                                        <h3 class="${(data.trend_percentage || 0) >= 0 ? 'text-success' : 'text-danger'}">
                                            ${(data.trend_percentage || 0) >= 0 ? '+' : ''}${(data.trend_percentage || 0).toFixed(1)}%
                                        </h3>
                                        <p class="text-muted">Change</p>
                                    </div>
                                </div>
                            </div>
                            ${data.daily_breakdown && data.daily_breakdown.length > 0 ? `
                                <div class="mb-3">
                                    <h6>Daily Usage Trend</h6>
                                    <div class="chart-container">
                                        ${generateDailyUsageChart(data.daily_breakdown)}
                                    </div>
                                </div>
                            ` : ''}
                            ${data.app_breakdown && data.app_breakdown.length > 0 ? `
                                <div>
                                    <h6>Top Applications by Usage</h6>
                                    <div class="table-responsive">
                                        <table class="table table-sm">
                                            <thead>
                                                <tr>
                                                    <th>Application</th>
                                                    <th>Hours</th>
                                                    <th>Percentage</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                ${data.app_breakdown.slice(0, 10).map(app => `
                                                    <tr>
                                                        <td>${app.app_name}</td>
                                                        <td>${(app.hours || 0).toFixed(1)}h</td>
                                                        <td>
                                                            <div class="d-flex align-items-center">
                                                                <div class="progress flex-grow-1 me-2" style="height: 8px;">
                                                                    <div class="progress-bar" style="width: ${app.percentage || 0}%"></div>
                                                                </div>
                                                                <small>${(app.percentage || 0).toFixed(1)}%</small>
                                                            </div>
                                                        </td>
                                                    </tr>
                                                `).join('')}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            ` : '<p class="text-muted">No usage data available for this period.</p>'}
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        const existingModal = document.getElementById('usageBreakdownModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        document.body.insertAdjacentHTML('beforeend', modalContent);
        const modal = new bootstrap.Modal(document.getElementById('usageBreakdownModal'));
        modal.show();
        
    } catch (error) {
        console.error('Error showing usage breakdown:', error);
        showError('Failed to load usage breakdown data');
    }
}

async function showOnboardingTrend(period = '7d') {
    try {
        const data = await fetchNewUsersAnalytics(period);
        
        const modalContent = `
            <div class="modal fade" id="onboardingTrendModal" tabindex="-1" aria-labelledby="onboardingTrendModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="onboardingTrendModalLabel">New Users & Onboarding Trend (${period.toUpperCase()})</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row mb-3">
                                <div class="col-md-3">
                                    <div class="text-center">
                                        <h3 class="text-primary">${data.count || 0}</h3>
                                        <p class="text-muted">New Users</p>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="text-center">
                                        <h3 class="text-info">${(data.daily_average || 0).toFixed(1)}</h3>
                                        <p class="text-muted">Daily Average</p>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="text-center">
                                        <h3 class="${(data.growth_rate || 0) >= 0 ? 'text-success' : 'text-danger'}">
                                            ${(data.growth_rate || 0) >= 0 ? '+' : ''}${(data.growth_rate || 0).toFixed(1)}%
                                        </h3>
                                        <p class="text-muted">Growth Rate</p>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="text-center">
                                        <h3 class="text-warning">${data.previous_count || 0}</h3>
                                        <p class="text-muted">Previous Period</p>
                                    </div>
                                </div>
                            </div>
                            <p class="text-muted">New users are identified by their first recorded usage session within the selected time period.</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        const existingModal = document.getElementById('onboardingTrendModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        document.body.insertAdjacentHTML('beforeend', modalContent);
        const modal = new bootstrap.Modal(document.getElementById('onboardingTrendModal'));
        modal.show();
        
    } catch (error) {
        console.error('Error showing onboarding trend:', error);
        showError('Failed to load onboarding trend data');
    }
}

async function showTopAppDetails(period = '7d') {
    try {
        const data = await fetchTopAppAnalytics(period);
        
        const modalContent = `
            <div class="modal fade" id="topAppModal" tabindex="-1" aria-labelledby="topAppModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="topAppModalLabel">Top Application Details (${period.toUpperCase()})</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            ${data.app_name ? `
                                <div class="row mb-3">
                                    <div class="col-md-6">
                                        <h4>${data.app_name}</h4>
                                        <p class="text-muted">${data.app_type || 'Unknown Type'} • ${data.publisher || 'Unknown Publisher'}</p>
                                    </div>
                                    <div class="col-md-6 text-end">
                                        <h3 class="text-primary">${(data.total_hours || 0).toFixed(1)}h</h3>
                                        <p class="text-muted">Total Usage Hours</p>
                                    </div>
                                </div>
                                <div class="row mb-3">
                                    <div class="col-md-4">
                                        <div class="text-center">
                                            <h5 class="text-info">${data.unique_users || 0}</h5>
                                            <p class="text-muted small">Unique Users</p>
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="text-center">
                                            <h5 class="text-success">${(data.average_session_length || 0).toFixed(1)}h</h5>
                                            <p class="text-muted small">Avg Session</p>
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="text-center">
                                            <h5 class="text-warning">${data.total_sessions || 0}</h5>
                                            <p class="text-muted small">Total Sessions</p>
                                        </div>
                                    </div>
                                </div>
                                ${data.daily_usage && data.daily_usage.length > 0 ? `
                                    <div class="mb-3">
                                        <h6>Daily Usage Pattern</h6>
                                        <div class="chart-container">
                                            ${generateDailyUsageChart(data.daily_usage)}
                                        </div>
                                    </div>
                                ` : ''}
                            ` : '<p class="text-muted">No application data available for this period.</p>'}
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        const existingModal = document.getElementById('topAppModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        document.body.insertAdjacentHTML('beforeend', modalContent);
        const modal = new bootstrap.Modal(document.getElementById('topAppModal'));
        modal.show();
        
    } catch (error) {
        console.error('Error showing top app details:', error);
        showError('Failed to load top application data');
    }
}

async function showChurnAnalysis(period = '7d') {
    try {
        const data = await fetchChurnRateAnalytics(period);
        
        const modalContent = `
            <div class="modal fade" id="churnAnalysisModal" tabindex="-1" aria-labelledby="churnAnalysisModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="churnAnalysisModalLabel">Churn Rate Analysis</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row mb-3">
                                <div class="col-md-4">
                                    <div class="text-center">
                                        <h3 class="text-danger">${(data.rate || 0).toFixed(1)}%</h3>
                                        <p class="text-muted">Churn Rate</p>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="text-center">
                                        <h3 class="text-warning">${data.churned_users || 0}</h3>
                                        <p class="text-muted">Churned Users</p>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="text-center">
                                        <span class="badge ${getChurnHealthBadge(data.health_status)} fs-6">
                                            ${data.health_status || 'Unknown'}
                                        </span>
                                        <p class="text-muted">Health Status</p>
                                    </div>
                                </div>
                            </div>
                            <div class="alert alert-info">
                                <i class="bi bi-info-circle me-2"></i>
                                <strong>Churn Definition:</strong> Users who were active in the previous period but have not been active in the current period.
                            </div>
                            ${data.cohort_analysis && data.cohort_analysis.length > 0 ? `
                                <div>
                                    <h6>Cohort Analysis</h6>
                                    <div class="table-responsive">
                                        <table class="table table-sm">
                                            <thead>
                                                <tr>
                                                    <th>Cohort</th>
                                                    <th>Total Users</th>
                                                    <th>Churned</th>
                                                    <th>Churn Rate</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                ${data.cohort_analysis.map(cohort => `
                                                    <tr>
                                                        <td>${cohort.period}</td>
                                                        <td>${cohort.total_users}</td>
                                                        <td>${cohort.churned_users}</td>
                                                        <td>
                                                            <span class="badge ${cohort.churn_rate > 20 ? 'bg-danger' : cohort.churn_rate > 10 ? 'bg-warning' : 'bg-success'}">
                                                                ${cohort.churn_rate.toFixed(1)}%
                                                            </span>
                                                        </td>
                                                    </tr>
                                                `).join('')}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        const existingModal = document.getElementById('churnAnalysisModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        document.body.insertAdjacentHTML('beforeend', modalContent);
        const modal = new bootstrap.Modal(document.getElementById('churnAnalysisModal'));
        modal.show();
        
    } catch (error) {
        console.error('Error showing churn analysis:', error);
        showError('Failed to load churn analysis data');
    }
}

// Analytics API Functions
async function fetchDashboardSummary(period = '7d') {
    const response = await fetch(`${API_BASE_URL}/app_usage/analytics/dashboard-summary?period=${period}`, {
        headers: {
            'X-API-Key-725d9439': API_KEY
        }
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
}

async function fetchActiveUsersAnalytics(period = '7d') {
    const response = await fetch(`${API_BASE_URL}/app_usage/analytics/active-users?period=${period}`, {
        headers: {
            'X-API-Key-725d9439': API_KEY
        }
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
}

async function fetchTotalHoursAnalytics(period = '7d') {
    const response = await fetch(`${API_BASE_URL}/app_usage/analytics/total-hours?period=${period}`, {
        headers: {
            'X-API-Key-725d9439': API_KEY
        }
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
}

async function fetchNewUsersAnalytics(period = '7d') {
    const response = await fetch(`${API_BASE_URL}/app_usage/analytics/new-users?period=${period}`, {
        headers: {
            'X-API-Key-725d9439': API_KEY
        }
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
}

async function fetchTopAppAnalytics(period = '7d') {
    const response = await fetch(`${API_BASE_URL}/app_usage/analytics/top-app?period=${period}`, {
        headers: {
            'X-API-Key-725d9439': API_KEY
        }
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
}

async function fetchChurnRateAnalytics(period = '7d') {
    const response = await fetch(`${API_BASE_URL}/app_usage/analytics/churn-rate?period=${period}`, {
        headers: {
            'X-API-Key-725d9439': API_KEY
        }
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
}

// Chart Generation Functions
function generateSparkline(data) {
    if (!data || data.length === 0) {
        return '<div class="text-muted small">No data</div>';
    }
    
    const maxValue = Math.max(...data.map(d => d.value || 0));
    const minValue = Math.min(...data.map(d => d.value || 0));
    const range = maxValue - minValue || 1;
    
    const points = data.map((d, i) => {
        const x = (i / (data.length - 1)) * 100;
        const y = 100 - (((d.value || 0) - minValue) / range) * 100;
        return `${x},${y}`;
    }).join(' ');
    
    return `
        <svg class="sparkline" width="60" height="20" viewBox="0 0 100 100" preserveAspectRatio="none">
            <polyline points="${points}" fill="none" stroke="currentColor" stroke-width="2" opacity="0.7"/>
        </svg>
    `;
}

function generateDailyUsageChart(data) {
    if (!data || data.length === 0) {
        return '<div class="text-muted">No daily usage data available</div>';
    }
    
    const maxValue = Math.max(...data.map(d => d.hours || 0));
    
    return `
        <div class="daily-usage-chart">
            ${data.map(day => `
                <div class="chart-bar-container">
                    <div class="chart-bar" style="height: ${maxValue > 0 ? ((day.hours || 0) / maxValue) * 100 : 0}%"></div>
                    <div class="chart-label">${new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</div>
                    <div class="chart-value">${(day.hours || 0).toFixed(1)}h</div>
                </div>
            `).join('')}
        </div>
    `;
}

function getChurnHealthBadge(status) {
    switch(status?.toLowerCase()) {
        case 'healthy':
            return 'bg-success';
        case 'warning':
            return 'bg-warning';
        case 'critical':
            return 'bg-danger';
        default:
            return 'bg-secondary';
    }
}

// Notification Functions
function showSuccess(message) {
    showNotification(message, 'success');
}

function showError(message) {
    showNotification(message, 'danger');
}

function showNotification(message, type = 'info') {
    const toast = document.getElementById('notification-toast');
    const toastMessage = document.getElementById('toast-message');
    const toastHeader = toast.querySelector('.toast-header i');
    
    // Update icon and color based on type
    toastHeader.className = `bi me-2 ${type === 'success' ? 'bi-check-circle text-success' : type === 'danger' ? 'bi-exclamation-triangle text-danger' : 'bi-info-circle text-primary'}`;
    
    // Set message
    toastMessage.textContent = message;
    
    // Show toast
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}
