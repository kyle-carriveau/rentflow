/**
 * Form Auto-Save System
 * Automatically saves form data to localStorage and restores it when the page is revisited
 */
class FormAutoSave {
    constructor(formSelector, options = {}) {
        this.form = document.querySelector(formSelector);
        if (!this.form) return;

        this.options = {
            saveInterval: 30000, // Save every 30 seconds
            storagePrefix: 'autosave_',
            excludeFields: ['password', 'confirm_password', 'csrf_token'],
            showIndicators: true,
            clearOnSubmit: true,
            restoreOnLoad: true,
            ...options
        };

        this.storageKey = this.options.storagePrefix + this.getFormIdentifier();
        this.saveTimer = null;
        this.lastSaved = null;
        this.indicator = null;

        this.init();
    }

    init() {
        this.createSaveIndicator();
        this.bindEvents();
        
        if (this.options.restoreOnLoad) {
            this.restoreFormData();
        }

        // Start auto-save timer
        this.startAutoSave();
    }

    getFormIdentifier() {
        // Create unique identifier based on form ID, action, or current path
        return this.form.id || 
               this.form.action.split('/').pop() || 
               window.location.pathname.replace(/[^a-zA-Z0-9]/g, '_');
    }

    createSaveIndicator() {
        if (!this.options.showIndicators) return;

        const indicator = document.createElement('div');
        indicator.id = 'autosave-indicator';
        indicator.className = 'autosave-indicator';
        indicator.innerHTML = `
            <div class="autosave-status">
                <i class="fas fa-save me-1"></i>
                <span class="status-text">Auto-save enabled</span>
                <small class="last-saved"></small>
            </div>
        `;

        // Add CSS styles
        const style = document.createElement('style');
        style.textContent = `
            .autosave-indicator {
                position: fixed;
                top: 80px;
                right: 20px;
                background: #fff;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 12px 16px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                z-index: 1050;
                font-size: 13px;
                color: #6c757d;
                opacity: 0;
                transform: translateX(100%);
                transition: all 0.3s ease;
            }
            
            .autosave-indicator.show {
                opacity: 1;
                transform: translateX(0);
            }
            
            .autosave-indicator.saving {
                border-color: #ffc107;
                background: #fff9e6;
                color: #856404;
            }
            
            .autosave-indicator.saved {
                border-color: #28a745;
                background: #f0f9f0;
                color: #155724;
            }
            
            .autosave-indicator.error {
                border-color: #dc3545;
                background: #f8f0f0;
                color: #721c24;
            }
            
            .autosave-status {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .last-saved {
                opacity: 0.7;
            }
            
            @media (max-width: 768px) {
                .autosave-indicator {
                    position: relative;
                    top: auto;
                    right: auto;
                    margin-bottom: 16px;
                    transform: none;
                    opacity: 1;
                }
            }
        `;
        
        document.head.appendChild(style);
        document.body.appendChild(indicator);
        this.indicator = indicator;

        // Show indicator briefly on load
        setTimeout(() => {
            indicator.classList.add('show');
            setTimeout(() => {
                indicator.classList.remove('show');
            }, 3000);
        }, 1000);
    }

    bindEvents() {
        // Save on form input changes
        this.form.addEventListener('input', this.debounce(() => {
            this.saveFormData();
        }, 2000));

        // Save on form submit and clear saved data
        this.form.addEventListener('submit', () => {
            if (this.options.clearOnSubmit) {
                this.clearSavedData();
            }
        });

        // Save before page unload
        window.addEventListener('beforeunload', () => {
            this.saveFormData();
        });

        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'hidden') {
                this.saveFormData();
            }
        });
    }

    startAutoSave() {
        if (this.saveTimer) {
            clearInterval(this.saveTimer);
        }

        this.saveTimer = setInterval(() => {
            this.saveFormData();
        }, this.options.saveInterval);
    }

    stopAutoSave() {
        if (this.saveTimer) {
            clearInterval(this.saveTimer);
            this.saveTimer = null;
        }
    }

    getFormData() {
        const formData = new FormData(this.form);
        const data = {};

        for (let [key, value] of formData.entries()) {
            // Skip excluded fields
            if (this.options.excludeFields.includes(key)) {
                continue;
            }

            // Handle multiple values (checkboxes, multi-select)
            if (data[key]) {
                if (Array.isArray(data[key])) {
                    data[key].push(value);
                } else {
                    data[key] = [data[key], value];
                }
            } else {
                data[key] = value;
            }
        }

        return data;
    }

    saveFormData() {
        try {
            const data = this.getFormData();
            const hasData = Object.keys(data).some(key => {
                const value = data[key];
                return value && value.toString().trim() !== '';
            });

            if (!hasData) return; // Don't save empty forms

            const saveData = {
                data: data,
                timestamp: Date.now(),
                url: window.location.href
            };

            localStorage.setItem(this.storageKey, JSON.stringify(saveData));
            this.lastSaved = new Date();
            this.updateSaveIndicator('saved');

        } catch (error) {
            console.error('Auto-save failed:', error);
            this.updateSaveIndicator('error');
        }
    }

    restoreFormData() {
        try {
            const savedData = localStorage.getItem(this.storageKey);
            if (!savedData) return;

            const { data, timestamp, url } = JSON.parse(savedData);
            
            // Check if data is recent (within 24 hours) and from same URL
            const maxAge = 24 * 60 * 60 * 1000; // 24 hours
            if (Date.now() - timestamp > maxAge || url !== window.location.href) {
                this.clearSavedData();
                return;
            }

            // Check if form is already filled (don't overwrite user input)
            const currentData = this.getFormData();
            const hasCurrentData = Object.keys(currentData).some(key => {
                const value = currentData[key];
                return value && value.toString().trim() !== '';
            });

            if (hasCurrentData) return; // Don't restore if form already has data

            // Restore form data
            let restoredCount = 0;
            Object.entries(data).forEach(([key, value]) => {
                const field = this.form.querySelector(`[name="${key}"]`);
                if (field) {
                    if (field.type === 'checkbox' || field.type === 'radio') {
                        if (Array.isArray(value)) {
                            field.checked = value.includes(field.value);
                        } else {
                            field.checked = field.value === value;
                        }
                    } else {
                        field.value = Array.isArray(value) ? value[0] : value;
                    }
                    restoredCount++;
                    
                    // Trigger input event to update any validation or formatting
                    field.dispatchEvent(new Event('input', { bubbles: true }));
                }
            });

            if (restoredCount > 0) {
                this.showRestoreNotification(new Date(timestamp));
            }

        } catch (error) {
            console.error('Failed to restore form data:', error);
            this.clearSavedData();
        }
    }

    showRestoreNotification(savedTime) {
        // Create temporary notification
        const notification = document.createElement('div');
        notification.className = 'alert alert-info alert-dismissible fade show';
        notification.style.cssText = 'position: fixed; top: 20px; left: 50%; transform: translateX(-50%); z-index: 1051; max-width: 500px;';
        notification.innerHTML = `
            <i class="fas fa-info-circle me-2"></i>
            <strong>Form data restored!</strong> 
            We've restored your progress from ${this.formatTime(savedTime)}.
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(notification);

        // Auto-remove notification after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    updateSaveIndicator(status) {
        if (!this.indicator) return;

        const statusText = this.indicator.querySelector('.status-text');
        const lastSavedText = this.indicator.querySelector('.last-saved');

        this.indicator.className = 'autosave-indicator show ' + status;

        switch (status) {
            case 'saving':
                statusText.textContent = 'Saving...';
                break;
            case 'saved':
                statusText.textContent = 'Draft saved';
                lastSavedText.textContent = this.lastSaved ? 
                    `Last saved: ${this.formatTime(this.lastSaved)}` : '';
                break;
            case 'error':
                statusText.textContent = 'Save failed';
                lastSavedText.textContent = 'Please check your connection';
                break;
        }

        // Hide indicator after delay (except for errors)
        if (status !== 'error') {
            setTimeout(() => {
                this.indicator.classList.remove('show');
            }, 2000);
        }
    }

    clearSavedData() {
        try {
            localStorage.removeItem(this.storageKey);
        } catch (error) {
            console.error('Failed to clear saved data:', error);
        }
    }

    formatTime(date) {
        const now = new Date();
        const diff = now - date;
        
        if (diff < 60000) { // Less than 1 minute
            return 'just now';
        } else if (diff < 3600000) { // Less than 1 hour
            const minutes = Math.floor(diff / 60000);
            return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
        } else if (diff < 86400000) { // Less than 1 day
            const hours = Math.floor(diff / 3600000);
            return `${hours} hour${hours > 1 ? 's' : ''} ago`;
        } else {
            return date.toLocaleDateString();
        }
    }

    debounce(func, wait) {
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

    // Public API
    destroy() {
        this.stopAutoSave();
        
        if (this.indicator) {
            this.indicator.remove();
        }

        // Remove event listeners
        this.form.removeEventListener('input', this.saveFormData);
        this.form.removeEventListener('submit', this.clearSavedData);
        window.removeEventListener('beforeunload', this.saveFormData);
        document.removeEventListener('visibilitychange', this.saveFormData);
    }

    manual save() {
        this.updateSaveIndicator('saving');
        this.saveFormData();
    }

    clearDraft() {
        this.clearSavedData();
        this.updateSaveIndicator('cleared');
    }
}

// Auto-initialize for common forms
document.addEventListener('DOMContentLoaded', function() {
    // Initialize auto-save for forms with data-autosave attribute
    const autoSaveForms = document.querySelectorAll('[data-autosave]');
    
    autoSaveForms.forEach(form => {
        const options = {};
        
        // Parse options from data attributes
        if (form.dataset.autosaveInterval) {
            options.saveInterval = parseInt(form.dataset.autosaveInterval) * 1000;
        }
        
        if (form.dataset.autosaveExclude) {
            options.excludeFields = form.dataset.autosaveExclude.split(',').map(s => s.trim());
        }

        new FormAutoSave(`#${form.id}`, options);
    });

    // Initialize for specific forms by default
    const defaultForms = [
        '#createTenantForm',
        '#editTenantForm', 
        '#createPropertyForm',
        '#editPropertyForm',
        '#createLeaseForm',
        '#editLeaseForm'
    ];

    defaultForms.forEach(selector => {
        if (document.querySelector(selector)) {
            new FormAutoSave(selector);
        }
    });
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FormAutoSave;
}