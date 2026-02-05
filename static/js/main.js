/**
 * Campus Event Management System - Main JavaScript
 */

// Auto-hide alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
});

// Form validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;
    
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.style.borderColor = 'var(--danger-color)';
            isValid = false;
        } else {
            input.style.borderColor = 'var(--border-color)';
        }
    });
    
    return isValid;
}

// Confirm before delete/reject actions
function confirmAction(message) {
    // Backwards-compatible helper. If called as confirmAction(formElement, message)
    // it will show a customConfirm (if available) and submit the form asynchronously.
    if (message && typeof message === 'string' && message.trim() === '') message = undefined;
    if (arguments.length > 1 && typeof arguments[0] === 'object' && arguments[0].tagName) {
        var form = arguments[0];
        var msg = arguments[1] || 'Are you sure you want to perform this action?';
        if (window.customConfirm) {
            window.customConfirm(msg).then(function(yes) {
                if (yes) form.submit();
            });
            return false; // prevent default submit; we'll submit if confirmed
        }
        return confirm(msg);
    }

    // Fallback: if customConfirm not available, use native confirm synchronously
    return confirm(message || 'Are you sure you want to perform this action?');
}

// Date validation - ensure event date is not in the past
function validateEventDate() {
    const dateInput = document.querySelector('input[name="date"][type="date"]');
    if (dateInput) {
        dateInput.addEventListener('change', function() {
            const selectedDate = new Date(this.value);
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            
            if (selectedDate < today) {
                if (window.customAlert) { window.customAlert('Event date cannot be in the past'); } else { alert('Event date cannot be in the past'); }
                this.value = '';
            }
        });
    }
}

// Time validation - ensure end time is after start time
function validateEventTime() {
    const startTime = document.querySelector('input[name="start_time"]');
    const endTime = document.querySelector('input[name="end_time"]');
    
    if (startTime && endTime) {
        endTime.addEventListener('change', function() {
            if (startTime.value && endTime.value) {
                if (endTime.value <= startTime.value) {
                    if (window.customAlert) { window.customAlert('End time must be after start time'); } else { alert('End time must be after start time'); }
                    this.value = '';
                }
            }
        });
    }
}

// Initialize validations
document.addEventListener('DOMContentLoaded', function() {
    validateEventDate();
    validateEventTime();
});

// Smooth scroll to top
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// Print certificate
function printCertificate() {
    window.print();
}

// Copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        if (window.customAlert) { window.customAlert('Copied to clipboard!'); } else { alert('Copied to clipboard!'); }
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
}

// Toggle mobile menu
function toggleMobileMenu() {
    const navMenu = document.querySelector('.nav-menu');
    if (navMenu) {
        navMenu.classList.toggle('active');
    }
}

// Search/filter table
function filterTable(inputId, tableId) {
    const input = document.getElementById(inputId);
    const table = document.getElementById(tableId);
    
    if (!input || !table) return;
    
    input.addEventListener('keyup', function() {
        const filter = this.value.toLowerCase();
        const rows = table.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(filter) ? '' : 'none';
        });
    });
}

// Export table to CSV
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    rows.forEach(row => {
        const cols = row.querySelectorAll('td, th');
        const rowData = Array.from(cols).map(col => col.textContent.trim());
        csv.push(rowData.join(','));
    });
    
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || 'export.csv';
    a.click();
}

// Loading spinner
function showLoading() {
    const spinner = document.createElement('div');
    spinner.id = 'loading-spinner';
    spinner.innerHTML = '<div class="spinner"></div>';
    document.body.appendChild(spinner);
}

function hideLoading() {
    const spinner = document.getElementById('loading-spinner');
    if (spinner) spinner.remove();
}

// Debounce function for search inputs
function debounce(func, wait) {
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

// Initialize tooltips (if needed)
function initTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(element => {
        element.addEventListener('mouseenter', function() {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = this.dataset.tooltip;
            document.body.appendChild(tooltip);
            
            const rect = this.getBoundingClientRect();
            tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
            tooltip.style.left = rect.left + (rect.width - tooltip.offsetWidth) / 2 + 'px';
        });
        
        element.addEventListener('mouseleave', function() {
            const tooltip = document.querySelector('.tooltip');
            if (tooltip) tooltip.remove();
        });
    });
}

// Password strength indicator
function checkPasswordStrength(password) {
    let strength = 0;
    if (password.length >= 8) strength++;
    if (password.match(/[a-z]+/)) strength++;
    if (password.match(/[A-Z]+/)) strength++;
    if (password.match(/[0-9]+/)) strength++;
    if (password.match(/[$@#&!]+/)) strength++;
    
    return strength;
}

// Display password strength
function displayPasswordStrength() {
    const passwordInput = document.querySelector('input[type="password"]');
    if (!passwordInput) return;
    
    const strengthMeter = document.createElement('div');
    strengthMeter.className = 'password-strength';
    passwordInput.parentNode.appendChild(strengthMeter);
    
    passwordInput.addEventListener('input', function() {
        const strength = checkPasswordStrength(this.value);
        const labels = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong'];
        const colors = ['#ef4444', '#f59e0b', '#eab308', '#10b981', '#059669'];
        
        strengthMeter.textContent = labels[strength - 1] || '';
        strengthMeter.style.color = colors[strength - 1] || '';
    });
}

// Initialize all features
document.addEventListener('DOMContentLoaded', function() {
    initTooltips();
});

// Read more / Read less toggle for long descriptions
document.addEventListener('click', function (e) {
    const target = e.target;
    if (target && target.classList.contains('read-more')) {
        e.preventDefault();
        const container = target.closest('.event-description');
        if (!container) return;
        const shortEl = container.querySelector('.desc-short');
        const fullEl = container.querySelector('.desc-full');
        if (!shortEl || !fullEl) return;

        const fullDisplay = window.getComputedStyle(fullEl).display;
        if (fullDisplay === 'none') {
            // expand
            shortEl.style.display = 'none';
            fullEl.style.display = '';
            target.textContent = 'Read less';
        } else {
            // collapse
            shortEl.style.display = '';
            fullEl.style.display = 'none';
            target.textContent = 'Read more';
        }
    }
});

// Toggle venue / meeting URL fields when creating events
document.addEventListener('DOMContentLoaded', function() {
    const modeSelect = document.getElementById('event-mode');
    const venueSelect = document.getElementById('venue-select');
    const meetingUrl = document.getElementById('meeting-url');

    function updateMode() {
        const val = (modeSelect && modeSelect.value) ? modeSelect.value.toLowerCase() : 'offline';
        if (val === 'online') {
            if (venueSelect) venueSelect.style.display = 'none';
            if (meetingUrl) meetingUrl.style.display = '';
        } else {
            if (venueSelect) venueSelect.style.display = '';
            if (meetingUrl) meetingUrl.style.display = 'none';
        }
    }

    if (modeSelect) {
        modeSelect.addEventListener('change', updateMode);
        updateMode();
    }
});

// Filter venue options by selected department (show common venues as well)
function updateVenueOptions() {
    const deptSelect = document.getElementById('dept-select');
    const venueSelectInput = document.getElementById('venue-select-input');
    if (!deptSelect || !venueSelectInput) return;

    const selectedDept = deptSelect.value;
    let anyVisible = false;

    Array.from(venueSelectInput.options).forEach(opt => {
        // keep the placeholder option
        if (!opt.dataset || typeof opt.dataset.dept === 'undefined') return;
        const optDept = opt.dataset.dept;
        // show if common or matches selected dept
        if (optDept === 'common' || (selectedDept && optDept === selectedDept)) {
            opt.style.display = '';
            anyVisible = true;
        } else {
            opt.style.display = 'none';
            // if currently selected option is hidden, clear selection
            if (venueSelectInput.value === opt.value) venueSelectInput.value = '';
        }
    });

    // If no dept selected, show all venues
    if (!selectedDept) {
        Array.from(venueSelectInput.options).forEach(opt => opt.style.display = '');
        anyVisible = true;
    }

    // Set required flag depending on visibility and mode
    const modeSelect = document.getElementById('event-mode');
    const mode = modeSelect ? modeSelect.value.toLowerCase() : 'offline';
    if (mode === 'offline' && anyVisible) {
        venueSelectInput.setAttribute('required', 'required');
    } else {
        venueSelectInput.removeAttribute('required');
    }
}

// Hook dept select change to update venues
document.addEventListener('DOMContentLoaded', function() {
    const deptSelect = document.getElementById('dept-select');
    if (deptSelect) {
        deptSelect.addEventListener('change', updateVenueOptions);
        // initial filter
        updateVenueOptions();
    }
    // also ensure venue filtering runs when mode changes
    const modeSelect2 = document.getElementById('event-mode');
    if (modeSelect2) modeSelect2.addEventListener('change', updateVenueOptions);
});

// Utility: Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// Utility: Format time
function formatTime(timeString) {
    const [hours, minutes] = timeString.split(':');
    const hour = parseInt(hours);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour % 12 || 12;
    return `${displayHour}:${minutes} ${ampm}`;
}

console.log('Campus Event Management System - Loaded');
