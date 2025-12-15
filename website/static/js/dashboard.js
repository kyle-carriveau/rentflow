/**
 * RentFlow Dashboard JavaScript
 * Handles AJAX refresh, chart management, and UI interactions
 */

// Configuration
const REFRESH_INTERVAL = 300000; // 5 minutes
const MAX_RETRY_DELAY = 60000; // 1 minute max backoff
let retryCount = 0;
let refreshTimer = null;

/**
 * Show toast notification
 * @param {string} message - Message to display
 * @param {string} type - Toast type (success, error, info, warning)
 */
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        console.warn('Toast container not found');
        return;
    }

    const toastId = `toast-${Date.now()}`;
    const iconMap = {
        success: 'check-circle',
        error: 'times-circle',
        info: 'info-circle',
        warning: 'exclamation-circle'
    };
    const bgMap = {
        success: 'bg-success',
        error: 'bg-danger',
        info: 'bg-info',
        warning: 'bg-warning'
    };

    const toastHTML = `
        <div id="${toastId}" class="toast align-items-center text-white ${bgMap[type]} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    <span class="fas fa-${iconMap[type]} me-2"></span>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;

    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { delay: 5000 });
    toast.show();

    // Remove from DOM after hidden
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

/**
 * Show loading state on dashboard
 */
function showLoadingState() {
    const metrics = document.querySelectorAll('.metric-card');
    metrics.forEach(card => {
        card.classList.add('loading');
    });
}

/**
 * Hide loading state on dashboard
 */
function hideLoadingState() {
    const metrics = document.querySelectorAll('.metric-card');
    metrics.forEach(card => {
        card.classList.remove('loading');
    });
}

/**
 * Calculate exponential backoff delay
 * @returns {number} Delay in milliseconds
 */
function getBackoffDelay() {
    const delay = Math.min(1000 * Math.pow(2, retryCount), MAX_RETRY_DELAY);
    return delay;
}

/**
 * Update metric cards with new data
 * @param {object} metrics - Metrics data from API
 */
function updateMetrics(metrics) {
    // Total Revenue
    if (metrics.total_revenue !== undefined) {
        const revenueEl = document.querySelector('[data-metric="total-revenue"]');
        if (revenueEl) {
            revenueEl.textContent = `$${parseFloat(metrics.total_revenue).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        }
    }

    // Active Leases
    if (metrics.active_leases !== undefined) {
        const leasesEl = document.querySelector('[data-metric="active-leases"]');
        if (leasesEl) {
            leasesEl.textContent = metrics.active_leases;
        }
    }

    // Occupancy Rate
    if (metrics.occupancy_rate !== undefined) {
        const occupancyEl = document.querySelector('[data-metric="occupancy-rate"]');
        if (occupancyEl) {
            occupancyEl.textContent = `${parseFloat(metrics.occupancy_rate).toFixed(1)}%`;
        }
    }

    // Maintenance Items
    if (metrics.maintenance_items !== undefined) {
        const maintenanceEl = document.querySelector('[data-metric="maintenance-items"]');
        if (maintenanceEl) {
            maintenanceEl.textContent = metrics.maintenance_items;
        }
    }
}

/**
 * Update charts with new data
 * @param {object} chartData - Chart data from API
 */
function updateCharts(chartData) {
    // Update revenue chart if data provided
    if (chartData.revenue_chart && window.revenueChart) {
        try {
            window.revenueChart.data.labels = chartData.revenue_chart.labels;
            window.revenueChart.data.datasets[0].data = chartData.revenue_chart.data;
            window.revenueChart.update('none'); // Update without animation for smoother UX
        } catch (error) {
            console.error('Error updating revenue chart:', error);
            showChartError('revenue-chart', 'Failed to update revenue chart');
        }
    }

    // Update occupancy chart if data provided
    if (chartData.occupancy_chart && window.occupancyChart) {
        try {
            window.occupancyChart.data.labels = chartData.occupancy_chart.labels;
            window.occupancyChart.data.datasets[0].data = chartData.occupancy_chart.data;
            window.occupancyChart.update('none');
        } catch (error) {
            console.error('Error updating occupancy chart:', error);
            showChartError('occupancy-chart', 'Failed to update occupancy chart');
        }
    }
}

/**
 * Update activity feed with new items
 * @param {array} activities - Activity items from API
 */
function updateActivityFeed(activities) {
    const feedContainer = document.querySelector('[data-component="activity-feed"]');
    if (!feedContainer || !activities) return;

    // Update activity items (implementation depends on current HTML structure)
    console.log('Activity feed update:', activities);
}

/**
 * Refresh dashboard data via AJAX
 */
async function refreshDashboard() {
    try {
        showLoadingState();

        const response = await fetch('/profile/dashboard/data', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();

        // Update UI components
        if (data.metrics) {
            updateMetrics(data.metrics);
        }

        if (data.charts) {
            updateCharts(data.charts);
        }

        if (data.activity) {
            updateActivityFeed(data.activity);
        }

        // Reset retry count on success
        retryCount = 0;

        hideLoadingState();

    } catch (error) {
        console.error('Dashboard refresh failed:', error);
        hideLoadingState();

        // Show error toast
        showToast('Failed to refresh dashboard data. Retrying...', 'error');

        // Implement exponential backoff
        retryCount++;
        const delay = getBackoffDelay();
        console.log(`Retrying in ${delay}ms (attempt ${retryCount})`);

        setTimeout(() => {
            refreshDashboard();
        }, delay);
    }
}

/**
 * Start automatic dashboard refresh
 */
function startAutoRefresh() {
    // Clear existing timer if any
    if (refreshTimer) {
        clearInterval(refreshTimer);
    }

    // Set up new refresh timer
    refreshTimer = setInterval(() => {
        refreshDashboard();
    }, REFRESH_INTERVAL);

    console.log(`Auto-refresh started (every ${REFRESH_INTERVAL / 1000}s)`);
}

/**
 * Stop automatic dashboard refresh
 */
function stopAutoRefresh() {
    if (refreshTimer) {
        clearInterval(refreshTimer);
        refreshTimer = null;
        console.log('Auto-refresh stopped');
    }
}

/**
 * Show chart error message
 * @param {string} chartId - Chart container ID
 * @param {string} message - Error message to display
 */
function showChartError(chartId, message) {
    const container = document.getElementById(chartId);
    if (!container) return;

    const errorHTML = `
        <div class="alert alert-danger text-center" role="alert">
            <span class="fas fa-exclamation-triangle me-2"></span>
            ${message}
        </div>
    `;

    container.innerHTML = errorHTML;
}

/**
 * Safe chart initialization with error handling
 * @param {string} canvasId - Canvas element ID
 * @param {object} config - Chart.js configuration
 * @param {string} chartName - Chart name for error messages
 * @returns {Chart|null} Chart instance or null on error
 */
function createChartSafely(canvasId, config, chartName) {
    try {
        const ctx = document.getElementById(canvasId);
        if (!ctx) {
            throw new Error(`Canvas element #${canvasId} not found`);
        }

        // Validate data
        if (!config.data || !config.data.datasets || config.data.datasets.length === 0) {
            throw new Error('Invalid chart data: missing datasets');
        }

        return new Chart(ctx, config);
    } catch (error) {
        console.error(`Error creating ${chartName}:`, error);
        showChartError(canvasId, `Failed to load ${chartName}`);
        return null;
    }
}

/**
 * Initialize dashboard
 */
function initializeDashboard() {
    console.log('Initializing dashboard...');

    // Start auto-refresh
    startAutoRefresh();

    // Stop refresh when user leaves page
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            stopAutoRefresh();
        } else {
            startAutoRefresh();
        }
    });

    // Manual refresh button (if exists)
    const refreshBtn = document.getElementById('dashboard-refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', (e) => {
            e.preventDefault();
            showToast('Refreshing dashboard...', 'info');
            refreshDashboard();
        });
    }

    console.log('Dashboard initialized successfully');
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeDashboard);
} else {
    initializeDashboard();
}
