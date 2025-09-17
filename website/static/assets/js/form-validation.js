/**
 * RentFlow Form Validation System
 * Provides real-time form validation with user-friendly feedback
 */

class FormValidator {
    constructor(formSelector, options = {}) {
        this.form = document.querySelector(formSelector);
        this.options = {
            validateOnBlur: true,
            validateOnInput: true,
            showSuccessIcons: true,
            debounceDelay: 300,
            ...options
        };
        
        this.debounceTimers = new Map();
        this.validationRules = new Map();
        
        if (this.form) {
            this.init();
        }
    }

    init() {
        this.setupEventListeners();
        this.addBootstrapValidationClasses();
    }

    setupEventListeners() {
        // Form submission validation
        this.form.addEventListener('submit', (e) => {
            if (!this.validateForm()) {
                e.preventDefault();
                this.showFormErrors();
            }
        });

        // Real-time validation on input fields
        if (this.options.validateOnInput || this.options.validateOnBlur) {
            const inputs = this.form.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                if (this.options.validateOnInput) {
                    input.addEventListener('input', (e) => {
                        this.debounceValidation(e.target);
                    });
                }
                
                if (this.options.validateOnBlur) {
                    input.addEventListener('blur', (e) => {
                        this.validateField(e.target);
                    });
                }

                // Clear validation on focus
                input.addEventListener('focus', (e) => {
                    this.clearFieldValidation(e.target);
                });
            });
        }
    }

    debounceValidation(field) {
        const fieldName = field.name || field.id;
        
        // Clear existing timer
        if (this.debounceTimers.has(fieldName)) {
            clearTimeout(this.debounceTimers.get(fieldName));
        }
        
        // Set new timer
        const timer = setTimeout(() => {
            this.validateField(field);
        }, this.options.debounceDelay);
        
        this.debounceTimers.set(fieldName, timer);
    }

    validateField(field) {
        const validationResult = this.runFieldValidation(field);
        this.updateFieldUI(field, validationResult);
        return validationResult.isValid;
    }

    runFieldValidation(field) {
        const rules = this.getFieldRules(field);
        const value = field.value.trim();
        
        for (const rule of rules) {
            const result = rule.validator(value, field);
            if (!result.isValid) {
                return result;
            }
        }
        
        return { isValid: true, message: '' };
    }

    getFieldRules(field) {
        const rules = [];
        const fieldType = field.type;
        const fieldName = field.name || field.id;
        
        // Required field validation
        if (field.hasAttribute('required')) {
            rules.push({
                name: 'required',
                validator: (value) => ({
                    isValid: value.length > 0,
                    message: 'This field is required.'
                })
            });
        }

        // Email validation
        if (fieldType === 'email' || field.classList.contains('email-field')) {
            rules.push({
                name: 'email',
                validator: (value) => {
                    if (value.length === 0) return { isValid: true };
                    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                    return {
                        isValid: emailRegex.test(value),
                        message: 'Please enter a valid email address.'
                    };
                }
            });
        }

        // Number validation
        if (fieldType === 'number' || field.classList.contains('number-field')) {
            rules.push({
                name: 'number',
                validator: (value) => {
                    if (value.length === 0) return { isValid: true };
                    const min = field.getAttribute('min');
                    const max = field.getAttribute('max');
                    const numValue = parseFloat(value);
                    
                    if (isNaN(numValue)) {
                        return { isValid: false, message: 'Please enter a valid number.' };
                    }
                    
                    if (min && numValue < parseFloat(min)) {
                        return { isValid: false, message: `Value must be at least ${min}.` };
                    }
                    
                    if (max && numValue > parseFloat(max)) {
                        return { isValid: false, message: `Value must be no more than ${max}.` };
                    }
                    
                    return { isValid: true };
                }
            });
        }

        // Currency validation
        if (field.classList.contains('currency-field')) {
            rules.push({
                name: 'currency',
                validator: (value) => {
                    if (value.length === 0) return { isValid: true };
                    const currencyRegex = /^\d+(\.\d{1,2})?$/;
                    return {
                        isValid: currencyRegex.test(value),
                        message: 'Please enter a valid amount (e.g., 1234.56).'
                    };
                }
            });
        }

        // Phone validation
        if (fieldType === 'tel' || field.classList.contains('phone-field')) {
            rules.push({
                name: 'phone',
                validator: (value) => {
                    if (value.length === 0) return { isValid: true };
                    const phoneRegex = /^\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})$/;
                    return {
                        isValid: phoneRegex.test(value),
                        message: 'Please enter a valid phone number.'
                    };
                }
            });
        }

        // Password validation
        if (fieldType === 'password') {
            rules.push({
                name: 'password',
                validator: (value) => {
                    if (value.length === 0) return { isValid: true };
                    if (value.length < 6) {
                        return { isValid: false, message: 'Password must be at least 6 characters long.' };
                    }
                    return { isValid: true };
                }
            });
        }

        // Date validation
        if (fieldType === 'date') {
            rules.push({
                name: 'date',
                validator: (value) => {
                    if (value.length === 0) return { isValid: true };
                    const date = new Date(value);
                    return {
                        isValid: !isNaN(date.getTime()),
                        message: 'Please enter a valid date.'
                    };
                }
            });
        }

        // Custom validation rules
        const customRules = this.validationRules.get(fieldName) || [];
        rules.push(...customRules);

        return rules;
    }

    updateFieldUI(field, validationResult) {
        const fieldGroup = field.closest('.form-group') || field.closest('.mb-3') || field.closest('.col');
        const existingFeedback = fieldGroup?.querySelector('.invalid-feedback, .valid-feedback');
        
        // Remove existing validation classes
        field.classList.remove('is-valid', 'is-invalid');
        
        // Remove existing feedback
        if (existingFeedback) {
            existingFeedback.remove();
        }

        if (field.value.trim().length > 0) {
            if (validationResult.isValid) {
                field.classList.add('is-valid');
                if (this.options.showSuccessIcons && fieldGroup) {
                    const feedback = document.createElement('div');
                    feedback.className = 'valid-feedback';
                    feedback.textContent = 'Looks good!';
                    fieldGroup.appendChild(feedback);
                }
            } else {
                field.classList.add('is-invalid');
                if (fieldGroup) {
                    const feedback = document.createElement('div');
                    feedback.className = 'invalid-feedback';
                    feedback.textContent = validationResult.message;
                    fieldGroup.appendChild(feedback);
                }
            }
        }
    }

    clearFieldValidation(field) {
        const fieldGroup = field.closest('.form-group') || field.closest('.mb-3') || field.closest('.col');
        const existingFeedback = fieldGroup?.querySelector('.invalid-feedback, .valid-feedback');
        
        field.classList.remove('is-valid', 'is-invalid');
        if (existingFeedback) {
            existingFeedback.remove();
        }
    }

    validateForm() {
        const inputs = this.form.querySelectorAll('input, select, textarea');
        let isFormValid = true;
        
        inputs.forEach(input => {
            const isFieldValid = this.validateField(input);
            if (!isFieldValid) {
                isFormValid = false;
            }
        });
        
        return isFormValid;
    }

    showFormErrors() {
        const firstInvalidField = this.form.querySelector('.is-invalid');
        if (firstInvalidField) {
            firstInvalidField.focus();
            firstInvalidField.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    addCustomRule(fieldName, ruleName, validator) {
        if (!this.validationRules.has(fieldName)) {
            this.validationRules.set(fieldName, []);
        }
        
        this.validationRules.get(fieldName).push({
            name: ruleName,
            validator: validator
        });
    }

    addBootstrapValidationClasses() {
        // Add Bootstrap's validation classes to form
        this.form.classList.add('needs-validation');
        this.form.setAttribute('novalidate', '');
    }
}

// Auto-initialize form validation for common forms
document.addEventListener('DOMContentLoaded', function() {
    // Initialize validation for financial forms
    const financialForms = document.querySelectorAll('form[action*="financial"], form[action*="payment"], form[action*="expense"]');
    financialForms.forEach(form => {
        new FormValidator(`#${form.id}`, {
            validateOnBlur: true,
            validateOnInput: true,
            showSuccessIcons: true
        });
    });

    // Initialize validation for property/unit/tenant forms
    const managementForms = document.querySelectorAll('form[action*="property"], form[action*="unit"], form[action*="tenant"], form[action*="lease"]');
    managementForms.forEach(form => {
        new FormValidator(`#${form.id}`, {
            validateOnBlur: true,
            validateOnInput: false, // Less aggressive for longer forms
            showSuccessIcons: false
        });
    });

    // Initialize validation for auth forms
    const authForms = document.querySelectorAll('form[action*="login"], form[action*="register"], form[action*="auth"]');
    authForms.forEach(form => {
        new FormValidator(`#${form.id}`, {
            validateOnBlur: true,
            validateOnInput: true,
            showSuccessIcons: true
        });
    });
});

// Export for manual initialization
window.FormValidator = FormValidator;