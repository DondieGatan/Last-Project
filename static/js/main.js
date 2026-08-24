// =============================================
// Smart Resume Analyser - Main JavaScript
// =============================================

document.addEventListener('DOMContentLoaded', function () {

    // ---------- File Upload Drag & Drop ----------
    var uploadArea = document.getElementById('upload-area');
    var fileInput = document.getElementById('resume-input');
    var fileName = document.getElementById('file-name');
    var uploadForm = document.getElementById('upload-form');
    var spinner = document.querySelector('.spinner');
    var loadingText = document.querySelector('.loading-text');

    if (uploadArea && fileInput) {
        uploadArea.addEventListener('click', function () {
            fileInput.click();
        });

        fileInput.addEventListener('change', function () {
            if (fileInput.files.length > 0) {
                var name = fileInput.files[0].name;
                if (fileName) {
                    fileName.textContent = name;
                    fileName.style.display = 'block';
                }
            }
        });

        // Drag and drop
        uploadArea.addEventListener('dragover', function (e) {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', function () {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', function (e) {
            e.preventDefault();
            uploadArea.classList.remove('dragover');

            var allowedTypes = [
                'application/pdf',
                'image/png', 'image/jpeg', 'image/bmp',
                'image/tiff', 'image/webp'
            ];
            var files = e.dataTransfer.files;
            if (files.length > 0) {
                var file = files[0];
                if (allowedTypes.indexOf(file.type) !== -1) {
                    fileInput.files = files;
                    if (fileName) {
                        fileName.textContent = file.name;
                        fileName.style.display = 'block';
                    }
                } else {
                    alert('Please upload a PDF or image file (PNG, JPG, BMP, TIFF, WebP).');
                }
            }
        });
    }

    // ---------- Form Submit with Loading ----------
    if (uploadForm) {
        uploadForm.addEventListener('submit', function (e) {
            if (!fileInput || fileInput.files.length === 0) {
                e.preventDefault();
                alert('Please select a PDF file to upload.');
                return;
            }

            if (spinner) spinner.style.display = 'block';
            if (loadingText) loadingText.style.display = 'block';

            var submitBtn = uploadForm.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Analysing...';
            }
        });
    }

    // ---------- Auth Form Submit Feedback ----------
    // Register/login/reset forms are plain POSTs with a full page reload, so
    // without this the button gives no sign anything happened until the new
    // page arrives, which reads as a stuck/slow request.
    var authForm = document.querySelector('.auth-form');
    if (authForm) {
        authForm.addEventListener('submit', function (e) {
            if (!authForm.checkValidity()) return;

            var submitBtn = authForm.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                submitBtn.disabled = true;
                submitBtn.dataset.originalText = submitBtn.textContent;
                submitBtn.textContent = 'Please wait...';
            }
        });
    }

    // ---------- Generic Animated Bar Observer ----------
    // Handles score bars, dashboard bars, field recommendation bars, and ATS bars
    function createBarObserver(selector) {
        var bars = document.querySelectorAll(selector);
        if (bars.length === 0) return;

        var observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    var bar = entry.target;
                    var width = bar.getAttribute('data-width');
                    if (width) {
                        bar.style.width = width + '%';
                    }
                    observer.unobserve(bar);
                }
            });
        }, { threshold: 0.2 });

        bars.forEach(function (bar) {
            bar.style.width = '0%';
            observer.observe(bar);
        });
    }

    // Animate all bar types
    createBarObserver('.score-bar .fill');
    createBarObserver('.bar-fill');
    createBarObserver('.field-rec-fill');

    // ---------- Flash Message Auto-dismiss ----------
    var flashMessages = document.querySelectorAll('.flash');
    flashMessages.forEach(function (msg) {
        setTimeout(function () {
            msg.style.transition = 'opacity 0.5s';
            msg.style.opacity = '0';
            setTimeout(function () {
                msg.remove();
            }, 500);
        }, 5000);
    });

    // ---------- Active Navigation Link ----------
    var currentPath = window.location.pathname;
    var navLinks = document.querySelectorAll('.navbar nav a');
    navLinks.forEach(function (link) {
        var href = link.getAttribute('href');
        if (href === currentPath || (currentPath.indexOf(href) === 0 && href !== '/')) {
            link.classList.add('active');
        }
    });

    // ---------- Smooth Scroll for Anchors ----------
    document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
        anchor.addEventListener('click', function (e) {
            var target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
});
