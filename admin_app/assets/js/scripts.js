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
        const stats = await fetchAppListSummary();
        const contentArea = document.getElementById('content-area');
        
        contentArea.innerHTML = `
            <!-- Dashboard Overview Cards -->
            <div class="row mb-4">
                <div class="col-xl-3 col-md-6 mb-4">
                    <div class="card dashboard-card bg-light-blue">
                        <div class="card-body position-relative">
                            <div class="card-title">Total Applications</div>
                            <div class="card-value">${stats.total_apps || 0}</div>
                            <i class="bi bi-grid-3x3-gap card-icon"></i>
                        </div>
                    </div>
                </div>
                <div class="col-xl-3 col-md-6 mb-4">
                    <div class="card dashboard-card bg-light-success">
                        <div class="card-body position-relative">
                            <div class="card-title">Tracking Enabled</div>
                            <div class="card-value">${stats.enabled_tracking || 0}</div>
                            <i class="bi bi-check-circle card-icon"></i>
                        </div>
                    </div>
                </div>
                <div class="col-xl-3 col-md-6 mb-4">
                    <div class="card dashboard-card bg-light-warning">
                        <div class="card-body position-relative">
                            <div class="card-title">Tracking Disabled</div>
                            <div class="card-value">${stats.disabled_tracking || 0}</div>
                            <i class="bi bi-x-circle card-icon"></i>
                        </div>
                    </div>
                </div>
                <div class="col-xl-3 col-md-6 mb-4">
                    <div class="card dashboard-card bg-light-danger">
                        <div class="card-body position-relative">
                            <div class="card-title">App Types</div>
                            <div class="card-value">${Object.keys(stats.app_types || {}).length}</div>
                            <i class="bi bi-tags card-icon"></i>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Charts Row -->
            <div class="row mb-4">
                <div class="col-lg-8">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="card-title mb-0">Application Types Distribution</h5>
                        </div>
                        <div class="card-body">
                            <div id="app-types-chart" class="chart-container">
                                ${generateAppTypesChart(stats.app_types || {})}
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-lg-4">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="card-title mb-0">Top Publishers</h5>
                        </div>
                        <div class="card-body">
                            <div id="publishers-list">
                                ${generatePublishersList(stats.publishers || {})}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Recent Applications -->
            <div class="row">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <h5 class="card-title mb-0">Recent Applications</h5>
                            <button class="btn btn-primary btn-sm" onclick="loadPage('app-manager')">
                                <i class="bi bi-plus me-1"></i>Manage Apps
                            </button>
                        </div>
                        <div class="card-body">
                            <div id="recent-apps">
                                <div class="text-center">
                                    <div class="spinner-border spinner-border-sm text-primary" role="status">
                                        <span class="visually-hidden">Loading...</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Load recent applications
        loadRecentApplications();
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showError('Failed to load dashboard data');
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
