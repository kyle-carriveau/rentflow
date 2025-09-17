/**
 * RentFlow Confirmation Dialogs
 * Provides user-friendly confirmation dialogs for destructive actions
 */

class ConfirmationDialog {
    constructor() {
        this.init();
    }

    init() {
        this.createModalTemplate();
        this.setupEventListeners();
    }

    createModalTemplate() {
        const modalHtml = `
            <div class="modal fade" id="confirmationModal" tabindex="-1" aria-labelledby="confirmationModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header border-0 pb-0">
                            <div class="d-flex align-items-center">
                                <div class="modal-icon-wrapper me-3">
                                    <div class="modal-icon">
                                        <i class="fas fa-exclamation-triangle text-warning"></i>
                                    </div>
                                </div>
                                <div>
                                    <h5 class="modal-title" id="confirmationModalLabel">Confirm Action</h5>
                                    <p class="text-muted mb-0 fs--1">This action cannot be undone</p>
                                </div>
                            </div>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body pt-0">
                            <p class="modal-message">Are you sure you want to proceed with this action?</p>
                        </div>
                        <div class="modal-footer border-0 pt-0">
                            <button type="button" class="btn btn-falcon-default" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-danger confirm-action-btn" data-loading="Processing...">
                                <span class="fas fa-trash me-1"></span>Delete
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if present
        const existingModal = document.getElementById('confirmationModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        this.addModalStyles();
    }

    addModalStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .modal-icon-wrapper {
                width: 48px;
                height: 48px;
                background: rgba(255, 193, 7, 0.1);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
            }

            .modal-icon i {
                font-size: 1.5rem;
            }

            .modal-dialog-danger .modal-icon-wrapper {
                background: rgba(220, 53, 69, 0.1);
            }

            .modal-dialog-danger .modal-icon i {
                color: #dc3545 !important;
            }

            .modal-dialog-warning .modal-icon-wrapper {
                background: rgba(255, 193, 7, 0.1);
            }

            .modal-dialog-warning .modal-icon i {
                color: #ffc107 !important;
            }

            .modal-dialog-info .modal-icon-wrapper {
                background: rgba(13, 110, 253, 0.1);
            }

            .modal-dialog-info .modal-icon i {
                color: #0d6efd !important;
            }
        `;
        
        if (!document.getElementById('confirmation-dialog-styles')) {
            style.id = 'confirmation-dialog-styles';
            document.head.appendChild(style);
        }
    }

    setupEventListeners() {
        // Handle confirmation triggers
        document.addEventListener('click', (e) => {
            const trigger = e.target.closest('[data-confirm]');
            if (trigger) {
                e.preventDefault();
                this.showConfirmation(trigger);
            }
        });
    }

    showConfirmation(trigger) {
        const modal = document.getElementById('confirmationModal');
        const modalDialog = modal.querySelector('.modal-dialog');
        const titleElement = modal.querySelector('.modal-title');
        const messageElement = modal.querySelector('.modal-message');
        const confirmBtn = modal.querySelector('.confirm-action-btn');
        const iconElement = modal.querySelector('.modal-icon i');
        
        // Get configuration from trigger element
        const config = {
            title: trigger.getAttribute('data-confirm-title') || 'Confirm Action',
            message: trigger.getAttribute('data-confirm') || 'Are you sure you want to proceed?',
            confirmText: trigger.getAttribute('data-confirm-text') || 'Confirm',
            confirmClass: trigger.getAttribute('data-confirm-class') || 'btn-danger',
            type: trigger.getAttribute('data-confirm-type') || 'warning', // warning, danger, info
            icon: trigger.getAttribute('data-confirm-icon') || 'fas fa-exclamation-triangle'
        };

        // Update modal content
        titleElement.textContent = config.title;
        messageElement.textContent = config.message;
        confirmBtn.textContent = config.confirmText;
        confirmBtn.className = `btn ${config.confirmClass} confirm-action-btn`;
        iconElement.className = config.icon;
        
        // Update modal styling based on type
        modalDialog.className = `modal-dialog modal-dialog-centered modal-dialog-${config.type}`;
        
        // Store the original action for execution
        confirmBtn.onclick = () => {
            this.executeAction(trigger);
        };
        
        // Show modal
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();
    }

    executeAction(trigger) {
        const modal = document.getElementById('confirmationModal');
        const modalInstance = bootstrap.Modal.getInstance(modal);
        
        // Check if it's a form submission
        if (trigger.type === 'submit' || trigger.form) {
            const form = trigger.form || trigger.closest('form');
            if (form) {
                modalInstance.hide();
                // Add a flag to indicate confirmed submission
                const hiddenInput = document.createElement('input');
                hiddenInput.type = 'hidden';
                hiddenInput.name = 'confirmed';
                hiddenInput.value = '1';
                form.appendChild(hiddenInput);
                form.submit();
                return;
            }
        }
        
        // Check if it's a link
        if (trigger.href) {
            modalInstance.hide();
            window.location.href = trigger.href;
            return;
        }
        
        // Check if it has a custom action
        const customAction = trigger.getAttribute('data-confirm-action');
        if (customAction) {
            modalInstance.hide();
            // Execute custom JavaScript
            try {
                eval(customAction);
            } catch (error) {
                console.error('Error executing custom action:', error);
            }
            return;
        }
        
        // Default: trigger click event
        modalInstance.hide();
        trigger.click();
    }

    // Public methods for programmatic use
    confirm(options = {}) {
        return new Promise((resolve, reject) => {
            const modal = document.getElementById('confirmationModal');
            const modalDialog = modal.querySelector('.modal-dialog');
            const titleElement = modal.querySelector('.modal-title');
            const messageElement = modal.querySelector('.modal-message');
            const confirmBtn = modal.querySelector('.confirm-action-btn');
            const iconElement = modal.querySelector('.modal-icon i');
            
            const config = {
                title: options.title || 'Confirm Action',
                message: options.message || 'Are you sure you want to proceed?',
                confirmText: options.confirmText || 'Confirm',
                confirmClass: options.confirmClass || 'btn-danger',
                type: options.type || 'warning',
                icon: options.icon || 'fas fa-exclamation-triangle',
                ...options
            };

            // Update modal content
            titleElement.textContent = config.title;
            messageElement.textContent = config.message;
            confirmBtn.textContent = config.confirmText;
            confirmBtn.className = `btn ${config.confirmClass} confirm-action-btn`;
            iconElement.className = config.icon;
            modalDialog.className = `modal-dialog modal-dialog-centered modal-dialog-${config.type}`;
            
            // Set up event handlers
            confirmBtn.onclick = () => {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                modalInstance.hide();
                resolve(true);
            };
            
            modal.addEventListener('hidden.bs.modal', () => {
                resolve(false);
            }, { once: true });
            
            // Show modal
            const modalInstance = new bootstrap.Modal(modal);
            modalInstance.show();
        });
    }

    alert(message, type = 'info') {
        return this.confirm({
            title: type === 'error' ? 'Error' : type === 'warning' ? 'Warning' : 'Information',
            message: message,
            confirmText: 'OK',
            confirmClass: type === 'error' ? 'btn-danger' : type === 'warning' ? 'btn-warning' : 'btn-primary',
            type: type,
            icon: type === 'error' ? 'fas fa-times-circle' : type === 'warning' ? 'fas fa-exclamation-triangle' : 'fas fa-info-circle'
        });
    }
}

// Initialize confirmation dialogs
const confirmationDialog = new ConfirmationDialog();

// Export for use
window.ConfirmationDialog = ConfirmationDialog;
window.confirmationDialog = confirmationDialog;