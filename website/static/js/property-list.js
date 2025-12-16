/**
 * RentFlow Property List JavaScript
 * Handles search, filter, sort, and AJAX delete functionality
 * Integrates with dashboard.js toast notifications
 */

// Global state
let allProperties = [];
let filteredProperties = [];

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  initializePropertyList();
  initializeSearchAndFilter();
  initializeDropdownMenus();
  initializeDeleteHandlers();
});

/**
 * Initialize property list and store property data
 */
function initializePropertyList() {
  const propertyCards = document.querySelectorAll('.property-card');

  allProperties = Array.from(propertyCards).map(card => ({
    element: card,
    id: card.dataset.propertyId,
    name: card.dataset.propertyName?.toLowerCase() || '',
    address: card.dataset.propertyAddress?.toLowerCase() || '',
    city: card.dataset.propertyCity?.toLowerCase() || '',
    portfolio: card.dataset.portfolioId || '',
    occupancy: parseFloat(card.dataset.occupancyRate) || 0
  }));

  filteredProperties = [...allProperties];
  updateResultsCount();
}

/**
 * Initialize search and filter functionality
 */
function initializeSearchAndFilter() {
  const searchInput = document.getElementById('propertySearch');
  const portfolioFilter = document.getElementById('portfolioFilter');
  const occupancyFilter = document.getElementById('occupancyFilter');

  if (searchInput) {
    // Real-time search with debounce
    let searchTimeout;
    searchInput.addEventListener('input', function() {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => {
        applyFilters();
      }, 300);
    });
  }

  if (portfolioFilter) {
    portfolioFilter.addEventListener('change', applyFilters);
  }

  if (occupancyFilter) {
    occupancyFilter.addEventListener('change', applyFilters);
  }
}

/**
 * Apply all active filters
 */
function applyFilters() {
  const searchTerm = document.getElementById('propertySearch')?.value.toLowerCase() || '';
  const portfolioId = document.getElementById('portfolioFilter')?.value || '';
  const occupancyRange = document.getElementById('occupancyFilter')?.value || '';

  filteredProperties = allProperties.filter(property => {
    // Search filter
    const matchesSearch = !searchTerm ||
      property.name.includes(searchTerm) ||
      property.address.includes(searchTerm) ||
      property.city.includes(searchTerm);

    // Portfolio filter
    const matchesPortfolio = !portfolioId || property.portfolio === portfolioId;

    // Occupancy filter
    const matchesOccupancy = filterByOccupancy(property.occupancy, occupancyRange);

    return matchesSearch && matchesPortfolio && matchesOccupancy;
  });

  updateDisplayedProperties();
  updateResultsCount();
}

/**
 * Filter properties by occupancy range
 */
function filterByOccupancy(occupancy, range) {
  if (!range) return true;

  switch(range) {
    case 'full':
      return occupancy === 100;
    case 'high':
      return occupancy >= 75 && occupancy < 100;
    case 'medium':
      return occupancy >= 50 && occupancy < 75;
    case 'low':
      return occupancy > 0 && occupancy < 50;
    case 'vacant':
      return occupancy === 0;
    default:
      return true;
  }
}

/**
 * Update which properties are displayed
 */
function updateDisplayedProperties() {
  allProperties.forEach(property => {
    const isVisible = filteredProperties.includes(property);
    property.element.style.display = isVisible ? '' : 'none';

    // Animate visibility changes
    if (isVisible) {
      property.element.style.animation = 'fadeIn 0.3s ease-in';
    }
  });

  // Show/hide empty state
  const emptyState = document.getElementById('emptyState');
  const propertyGrid = document.getElementById('propertyGrid');

  if (emptyState && propertyGrid) {
    if (filteredProperties.length === 0) {
      propertyGrid.style.display = 'none';
      emptyState.style.display = 'block';
      updateEmptyStateMessage();
    } else {
      propertyGrid.style.display = 'grid';
      emptyState.style.display = 'none';
    }
  }
}

/**
 * Update empty state message based on active filters
 */
function updateEmptyStateMessage() {
  const emptyState = document.getElementById('emptyState');
  if (!emptyState) return;

  const searchTerm = document.getElementById('propertySearch')?.value || '';
  const hasFilters = searchTerm ||
                    document.getElementById('portfolioFilter')?.value ||
                    document.getElementById('occupancyFilter')?.value;

  const title = emptyState.querySelector('h3');
  const description = emptyState.querySelector('p');

  if (hasFilters) {
    if (title) title.textContent = 'No Properties Found';
    if (description) description.textContent = 'Try adjusting your search or filter criteria.';
  } else {
    if (title) title.textContent = 'No Properties Yet';
    if (description) description.textContent = 'Get started by adding your first property to your portfolio.';
  }
}

/**
 * Update results count display
 */
function updateResultsCount() {
  const countElement = document.getElementById('resultsCount');
  if (!countElement) return;

  const count = filteredProperties.length;
  const total = allProperties.length;

  if (count === total) {
    countElement.innerHTML = `Showing <strong>${total}</strong> ${total === 1 ? 'property' : 'properties'}`;
  } else {
    countElement.innerHTML = `Showing <strong>${count}</strong> of <strong>${total}</strong> ${total === 1 ? 'property' : 'properties'}`;
  }
}

/**
 * Initialize dropdown menus for property cards
 */
function initializeDropdownMenus() {
  const menuButtons = document.querySelectorAll('.property-menu-btn');

  menuButtons.forEach(button => {
    button.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation(); // Prevent card link click

      const menu = this.closest('.property-card-menu');
      const isActive = menu.classList.contains('active');

      // Close all other dropdowns
      document.querySelectorAll('.property-card-menu.active').forEach(activeMenu => {
        if (activeMenu !== menu) {
          activeMenu.classList.remove('active');
        }
      });

      // Toggle this dropdown
      menu.classList.toggle('active');
      this.setAttribute('aria-expanded', !isActive);
    });
  });

  // Close dropdown when clicking outside
  document.addEventListener('click', function(e) {
    if (!e.target.closest('.property-card-menu')) {
      document.querySelectorAll('.property-card-menu.active').forEach(menu => {
        menu.classList.remove('active');
        const button = menu.querySelector('.property-menu-btn');
        if (button) button.setAttribute('aria-expanded', 'false');
      });
    }
  });

  // Prevent dropdown items from triggering card link
  document.querySelectorAll('.property-menu-dropdown .dropdown-item').forEach(item => {
    item.addEventListener('click', function(e) {
      e.stopPropagation();
    });
  });
}

/**
 * Initialize delete button handlers
 */
function initializeDeleteHandlers() {
  const deleteButtons = document.querySelectorAll('.delete-property-btn');

  deleteButtons.forEach(button => {
    button.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation(); // Prevent card link click
      const propertyId = this.dataset.propertyId;
      const propertyName = this.dataset.propertyName;
      showDeleteModal(propertyId, propertyName);
    });
  });
}

/**
 * Show delete confirmation modal
 */
function showDeleteModal(propertyId, propertyName) {
  const modal = document.getElementById('deletePropertyModal');
  if (!modal) {
    console.error('Delete modal not found');
    return;
  }

  // Update modal content
  const propertyNameElement = document.getElementById('deletePropertyName');
  if (propertyNameElement) {
    propertyNameElement.textContent = propertyName;
  }

  // Get confirm button and attach handler
  const confirmButton = document.getElementById('confirmDeleteBtn');
  if (confirmButton) {
    // Remove old listeners by cloning
    const newButton = confirmButton.cloneNode(true);
    confirmButton.parentNode.replaceChild(newButton, confirmButton);

    // Add new listener
    newButton.addEventListener('click', function() {
      deleteProperty(propertyId);
    });
  }

  // Show modal using Bootstrap
  const bsModal = new bootstrap.Modal(modal);
  bsModal.show();
}

/**
 * Delete property via AJAX
 */
async function deleteProperty(propertyId) {
  const modal = bootstrap.Modal.getInstance(document.getElementById('deletePropertyModal'));
  const confirmButton = document.getElementById('confirmDeleteBtn');
  const card = document.querySelector(`[data-property-id="${propertyId}"]`);

  if (!card) {
    console.error('Property card not found');
    return;
  }

  // Disable button and show loading state
  if (confirmButton) {
    confirmButton.disabled = true;
    confirmButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Deleting...';
  }

  try {
    const response = await fetch(`/property/${propertyId}/delete`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken()
      }
    });

    const data = await response.json();

    if (response.ok && data.success) {
      // Close modal
      if (modal) {
        modal.hide();
      }

      // Animate card removal
      card.classList.add('deleting');

      // Wait for animation then remove
      setTimeout(() => {
        // Remove from DOM
        card.remove();

        // Update arrays
        allProperties = allProperties.filter(p => p.id !== propertyId);
        filteredProperties = filteredProperties.filter(p => p.id !== propertyId);

        // Update display
        updateResultsCount();
        updateDisplayedProperties();

        // Show success toast
        if (typeof showToast === 'function') {
          showToast(data.message || 'Property deleted successfully', 'success');
        }
      }, 300);

    } else {
      throw new Error(data.message || 'Failed to delete property');
    }

  } catch (error) {
    console.error('Delete error:', error);

    // Show error toast
    if (typeof showToast === 'function') {
      showToast(error.message || 'Failed to delete property', 'error');
    }

    // Re-enable button
    if (confirmButton) {
      confirmButton.disabled = false;
      confirmButton.innerHTML = '<i class="fas fa-trash-alt me-2"></i>Delete Property';
    }
  }
}

/**
 * Get CSRF token from meta tag or cookie
 */
function getCsrfToken() {
  // Try meta tag first
  const metaTag = document.querySelector('meta[name="csrf-token"]');
  if (metaTag) {
    return metaTag.getAttribute('content');
  }

  // Fall back to cookie
  const cookies = document.cookie.split(';');
  for (let cookie of cookies) {
    const [name, value] = cookie.trim().split('=');
    if (name === 'csrf_token') {
      return decodeURIComponent(value);
    }
  }

  return '';
}

/**
 * Fade in animation for filtered results
 */
const fadeInKeyframes = `
  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
`;

// Add animation keyframes if not exists
if (!document.querySelector('#fadeInStyles')) {
  const style = document.createElement('style');
  style.id = 'fadeInStyles';
  style.textContent = fadeInKeyframes;
  document.head.appendChild(style);
}

// Export functions for external use
window.propertyList = {
  refresh: initializePropertyList,
  applyFilters: applyFilters,
  updateResultsCount: updateResultsCount
};
