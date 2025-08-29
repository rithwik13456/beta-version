// Story in Short - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // URL validation
    const urlInput = document.getElementById('url');
    const analyzeForm = document.getElementById('analyzeForm');
    
    if (urlInput && analyzeForm) {
        // Add protocol if missing when user types
        urlInput.addEventListener('blur', function() {
            let url = this.value.trim();
            if (url && !url.match(/^https?:\/\//)) {
                this.value = 'https://' + url;
            }
        });
        
        // Form validation
        analyzeForm.addEventListener('submit', function(e) {
            const url = urlInput.value.trim();
            
            if (!url) {
                e.preventDefault();
                showAlert('Please enter a URL to analyze.', 'danger');
                return;
            }
            
            if (!isValidUrl(url)) {
                e.preventDefault();
                showAlert('Please enter a valid URL.', 'danger');
                return;
            }
            
            // Show loading state
            showLoading();
        });
    }
    
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Fade in animations
    const fadeElements = document.querySelectorAll('.fade-in');
    fadeElements.forEach((el, index) => {
        setTimeout(() => {
            el.style.opacity = '1';
            el.style.transform = 'translateY(0)';
        }, index * 100);
    });
    
    // Copy URL functionality
    const copyButtons = document.querySelectorAll('.copy-url');
    copyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const url = this.dataset.url;
            navigator.clipboard.writeText(url).then(() => {
                showAlert('URL copied to clipboard!', 'success');
            });
        });
    });
});

function isValidUrl(string) {
    try {
        const url = new URL(string);
        return url.protocol === 'http:' || url.protocol === 'https:';
    } catch (_) {
        return false;
    }
}

function showAlert(message, type = 'info') {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.alert');
    existingAlerts.forEach(alert => alert.remove());
    
    // Create new alert
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert at top of main content
    const mainContent = document.querySelector('main') || document.body;
    mainContent.insertBefore(alertDiv, mainContent.firstChild);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

function showLoading() {
    const form = document.getElementById('analyzeForm');
    const button = form.querySelector('button[type="submit"]');
    
    if (button) {
        button.disabled = true;
        button.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2"></span>
            Processing...
        `;
    }
    
    // Show loading message
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'loading mt-4';
    loadingDiv.innerHTML = `
        <div class="spinner mb-3"></div>
        <h5>Analyzing Content...</h5>
        <p class="text-muted">This may take a few moments depending on the website size.</p>
    `;
    
    form.parentNode.appendChild(loadingDiv);
}

// Chart interaction enhancements
function enhanceCharts() {
    const charts = document.querySelectorAll('.chart-container img');
    charts.forEach(chart => {
        chart.addEventListener('click', function() {
            // Create modal for larger view
            const modal = document.createElement('div');
            modal.className = 'modal fade';
            modal.innerHTML = `
                <div class="modal-dialog modal-lg">
                    <div class="modal-content bg-dark">
                        <div class="modal-header">
                            <h5 class="modal-title">Chart View</h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body text-center">
                            <img src="${this.src}" class="img-fluid" alt="Chart">
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            const modalInstance = new bootstrap.Modal(modal);
            modalInstance.show();
            
            // Remove modal after hiding
            modal.addEventListener('hidden.bs.modal', () => {
                modal.remove();
            });
        });
    });
}

// Initialize chart enhancements after page load
window.addEventListener('load', enhanceCharts);

// Progressive enhancement for word tags
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('word-tag')) {
        const word = e.target.textContent;
        showAlert(`Selected word: "${word}"`, 'info');
    }
});

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Back to top functionality
function addBackToTop() {
    const backToTop = document.createElement('button');
    backToTop.innerHTML = '↑';
    backToTop.className = 'btn btn-primary position-fixed bottom-0 end-0 m-3';
    backToTop.style.display = 'none';
    backToTop.style.zIndex = '1000';
    
    backToTop.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    
    document.body.appendChild(backToTop);
    
    window.addEventListener('scroll', () => {
        if (window.pageYOffset > 300) {
            backToTop.style.display = 'block';
        } else {
            backToTop.style.display = 'none';
        }
    });
}

// Initialize back to top button
addBackToTop();
