/**
 * RentFlow Loading States and Progress Indicators
 * Provides seamless loading feedback for forms and actions
 */

class LoadingManager {
    constructor() {
        this.loadingElements = new Map();
        this.init();
    }

    init() {
        this.createGlobalLoadingOverlay();
        this.setupFormLoadingStates();
        this.setupButtonLoadingStates();
        this.setupAjaxLoadingStates();
    }

    createGlobalLoadingOverlay() {
        // Create global loading overlay
        const overlay = document.createElement('div');
        overlay.id = 'globalLoadingOverlay';
        overlay.className = 'loading-overlay d-none';
        overlay.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <div class="loading-text mt-3">Processing...</div>
            </div>
        `;
        document.body.appendChild(overlay);

        // Add CSS for loading overlay
        this.addLoadingStyles();
    }

    addLoadingStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .loading-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(255, 255, 255, 0.9);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 9999;
                backdrop-filter: blur(2px);
            }

            .loading-spinner {
                text-align: center;
                background: white;
                padding: 2rem;
                border-radius: 0.5rem;
                box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
            }

            .loading-text {
                color: #6c757d;
                font-size: 0.9rem;
                font-weight: 500;
            }

            .btn-loading {
                position: relative;
                pointer-events: none;
            }

            .btn-loading .btn-text {
                opacity: 0;
            }

            .btn-loading::after {
                content: '';
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                width: 1rem;
                height: 1rem;
                border: 2px solid transparent;
                border-top: 2px solid currentColor;
                border-radius: 50%;
                animation: btn-spin 0.8s linear infinite;
            }

            @keyframes btn-spin {
                0% { transform: translate(-50%, -50%) rotate(0deg); }
                100% { transform: translate(-50%, -50%) rotate(360deg); }
            }

            .form-loading {
                position: relative;
                pointer-events: none;
            }

            .form-loading::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(255, 255, 255, 0.8);
                z-index: 10;
                border-radius: 0.375rem;
            }

            .progress-bar-animated {
                animation: progress-bar-stripes 1s linear infinite;
            }

            @keyframes progress-bar-stripes {
                0% { background-position-x: 1rem; }
                100% { background-position-x: 0; }
            }

            .skeleton {
                background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
                background-size: 200% 100%;
                animation: skeleton-loading 1.5s infinite;
            }

            @keyframes skeleton-loading {
                0% { background-position: 200% 0; }
                100% { background-position: -200% 0; }
            }

            .toast-container {
                position: fixed;
                top: 1rem;
                right: 1rem;
                z-index: 1055;
            }
        `;
        document.head.appendChild(style);
    }

    setupFormLoadingStates() {
        // Add loading states to all forms
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (form.tagName === 'FORM' && !form.classList.contains('no-loading')) {
                this.showFormLoading(form);
            }
        });
    }

    setupButtonLoadingStates() {
        // Add loading states to buttons with data-loading attribute
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('[data-loading]');
            if (btn) {
                const loadingText = btn.getAttribute('data-loading') || 'Loading...';
                this.showButtonLoading(btn, loadingText);
            }
        });
    }

    setupAjaxLoadingStates() {
        // Intercept fetch requests to show loading states
        const originalFetch = window.fetch;
        window.fetch = (...args) => {
            this.showGlobalLoading('Processing request...');
            return originalFetch(...args)
                .finally(() => {
                    this.hideGlobalLoading();
                });
        };
    }

    showGlobalLoading(text = 'Loading...') {
        const overlay = document.getElementById('globalLoadingOverlay');
        const textElement = overlay.querySelector('.loading-text');
        textElement.textContent = text;
        overlay.classList.remove('d-none');
    }

    hideGlobalLoading() {
        const overlay = document.getElementById('globalLoadingOverlay');
        overlay.classList.add('d-none');
    }

    showFormLoading(form) {
        form.classList.add('form-loading');
        
        // Disable all form elements
        const elements = form.querySelectorAll('input, select, textarea, button');
        elements.forEach(el => {
            el.disabled = true;
        });

        // Add loading spinner to submit button
        const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
        if (submitBtn) {
            this.showButtonLoading(submitBtn, 'Processing...');
        }
    }

    hideFormLoading(form) {
        form.classList.remove('form-loading');
        
        // Re-enable form elements
        const elements = form.querySelectorAll('input, select, textarea, button');
        elements.forEach(el => {
            el.disabled = false;
        });

        // Remove loading from buttons
        const buttons = form.querySelectorAll('.btn-loading');
        buttons.forEach(btn => this.hideButtonLoading(btn));
    }

    showButtonLoading(button, text) {
        if (button.classList.contains('btn-loading')) return;

        // Store original text
        const originalText = button.innerHTML;
        this.loadingElements.set(button, originalText);

        // Add loading class and text
        button.classList.add('btn-loading');
        button.innerHTML = `<span class="btn-text">${text}</span>`;
        button.disabled = true;
    }

    hideButtonLoading(button) {
        if (!button.classList.contains('btn-loading')) return;

        // Restore original text
        const originalText = this.loadingElements.get(button);
        if (originalText) {
            button.innerHTML = originalText;
            this.loadingElements.delete(button);
        }

        button.classList.remove('btn-loading');
        button.disabled = false;
    }

    showProgressBar(container, progress = 0) {
        const progressHtml = `
            <div class="progress mb-3" style="height: 4px;">
                <div class="progress-bar progress-bar-striped progress-bar-animated" 
                     role="progressbar" 
                     style="width: ${progress}%"
                     aria-valuenow="${progress}" 
                     aria-valuemin="0" 
                     aria-valuemax="100">
                </div>
            </div>
        `;
        container.insertAdjacentHTML('afterbegin', progressHtml);
    }

    updateProgress(container, progress) {
        const progressBar = container.querySelector('.progress-bar');
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
            progressBar.setAttribute('aria-valuenow', progress);
        }
    }

    showSkeletonLoader(container, type = 'card') {
        let skeletonHtml = '';
        
        switch (type) {
            case 'card':
                skeletonHtml = `
                    <div class="card">
                        <div class="card-body">
                            <div class="skeleton mb-2" style="height: 1.25rem; width: 60%;"></div>
                            <div class="skeleton mb-2" style="height: 1rem; width: 80%;"></div>
                            <div class="skeleton mb-2" style="height: 1rem; width: 70%;"></div>
                            <div class="skeleton" style="height: 1rem; width: 50%;"></div>
                        </div>
                    </div>
                `;
                break;
            case 'table':
                skeletonHtml = `
                    <div class="table-responsive">
                        <table class="table">
                            <tbody>
                                ${Array(5).fill().map(() => `
                                    <tr>
                                        <td><div class="skeleton" style="height: 1rem;"></div></td>
                                        <td><div class="skeleton" style="height: 1rem;"></div></td>
                                        <td><div class="skeleton" style="height: 1rem;"></div></td>
                                        <td><div class="skeleton" style="height: 1rem; width: 60%;"></div></td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                `;
                break;
            case 'list':
                skeletonHtml = `
                    ${Array(4).fill().map(() => `
                        <div class="d-flex align-items-center mb-3">
                            <div class="skeleton rounded-circle me-3" style="width: 40px; height: 40px;"></div>
                            <div class="flex-grow-1">
                                <div class="skeleton mb-1" style="height: 1rem; width: 70%;"></div>
                                <div class="skeleton" style="height: 0.875rem; width: 50%;"></div>
                            </div>
                        </div>
                    `).join('')}
                `;
                break;
        }
        
        container.innerHTML = skeletonHtml;
    }

    showToast(message, type = 'info', duration = 5000) {
        const toastContainer = this.getOrCreateToastContainer();
        const toastId = 'toast-' + Date.now();
        
        const toastHtml = `
            <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;
        
        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, { delay: duration });
        toast.show();
        
        // Remove from DOM after hiding
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
        
        return toast;
    }

    getOrCreateToastContainer() {
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        return container;
    }
}

// Initialize loading manager
const loadingManager = new LoadingManager();

// Export for manual use
window.LoadingManager = LoadingManager;
window.loadingManager = loadingManager;