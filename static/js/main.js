// =============================================
// Smart Resume Analyser - Main JavaScript
// =============================================

document.addEventListener('DOMContentLoaded', function () {

    // ---------- File Upload Drag & Drop ----------
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('resume-input');
    const fileName = document.getElementById('file-name');
    const uploadForm = document.getElementById('upload-form');
    const spinner = document.querySelector('.spinner');
    const loadingText = document.querySelector('.loading-text');

    if (uploadArea && fileInput) {
        uploadArea.addEventListener('click', function () {
            fileInput.click();
        });

        fileInput.addEventListener('change', function () {
            if (fileInput.files.length > 0) {
                const name = fileInput.files[0].name;
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

            const files = e.dataTransfer.files;
            if (files.length > 0) {
                const file = files[0];
                if (file.type === 'application/pdf') {
                    fileInput.files = files;
                    if (fileName) {
                        fileName.textContent = file.name;
                        fileName.style.display = 'block';
                    }
                } else {
                    alert('Please upload a PDF file only.');
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

            // Show loading state
            if (spinner) spinner.style.display = 'block';
            if (loadingText) loadingText.style.display = 'block';

            const submitBtn = uploadForm.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Analysing...';
            }
        });
    }

    // ---------- Animate Score Bars ----------
    const scoreBars = document.querySelectorAll('.score-bar .fill');
    if (scoreBars.length > 0) {
        const observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    const bar = entry.target;
                    const width = bar.getAttribute('data-width');
                    bar.style.width = width + '%';
                    observer.unobserve(bar);
                }
            });
        }, { threshold: 0.2 });

        scoreBars.forEach(function (bar) {
            bar.style.width = '0%';
            observer.observe(bar);
        });
    }

    // ---------- Animate Dashboard Bar Charts ----------
    const barFills = document.querySelectorAll('.bar-fill');
    if (barFills.length > 0) {
        const observer2 = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    const bar = entry.target;
                    const width = bar.getAttribute('data-width');
                    bar.style.width = width + '%';
                    observer2.unobserve(bar);
                }
            });
        }, { threshold: 0.2 });

        barFills.forEach(function (bar) {
            bar.style.width = '0%';
            observer2.observe(bar);
        });
    }

    // ---------- Flash Message Auto-dismiss ----------
    const flashMessages = document.querySelectorAll('.flash');
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
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar nav a');
    navLinks.forEach(function (link) {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
});
