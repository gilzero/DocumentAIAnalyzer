document.addEventListener('DOMContentLoaded', function() {
    // Configure PDF.js worker
    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js';

    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const uploadArea = document.querySelector('.upload-area');
    const loadingSpinner = document.querySelector('.loading-spinner');
    const resultsContainer = document.getElementById('results-container');
    const progressContainer = document.querySelector('.progress-container');
    const progressBar = document.querySelector('.progress-bar');

    // Drag and drop functionality
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.classList.add('highlight');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.classList.remove('highlight');
        });
    });

    uploadArea.addEventListener('drop', handleDrop);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        fileInput.files = files;
        handleFileUpload(files[0]);
    }

    fileInput.addEventListener('change', (e) => {
        handleFileUpload(e.target.files[0]);
    });

    function showToast(message, type = 'info') {
        Toastify({
            text: message,
            duration: 3000,
            gravity: "top",
            position: "right",
            className: type,
            stopOnFocus: true
        }).showToast();
    }

    function animateProgress() {
        let progress = 0;
        progressContainer.classList.add('active');

        const interval = setInterval(() => {
            if (progress < 90) {
                // Smooth, non-linear progress animation
                const increment = Math.max(0.5, (90 - progress) / 10);
                progress += increment;
                updateProgress(Math.min(90, progress));
            }
        }, 100);

        return interval;
    }

    function updateProgress(percent) {
        progressContainer.style.display = 'block';
        progressBar.style.width = `${percent}%`;
        progressBar.setAttribute('aria-valuenow', percent);

        // Update status message with animation
        const statusText = progressContainer.querySelector('.progress-status');
        let message = 'Preparing upload...';
        let emphasize = false;

        if (percent >= 90) {
            message = 'Finalizing...';
            emphasize = true;
        } else if (percent >= 70) {
            message = 'Generating insights...';
            emphasize = true;
        } else if (percent >= 40) {
            message = 'Processing document...';
        } else if (percent >= 20) {
            message = 'Analyzing structure...';
        }

        if (statusText.textContent !== message) {
            statusText.style.opacity = '0';
            setTimeout(() => {
                statusText.textContent = message;
                statusText.style.opacity = '1';
                statusText.classList.toggle('emphasize', emphasize);
            }, 200);
        }
    }

    function createDocumentPreview(file) {
        const reader = new FileReader();
        const previewContainer = document.createElement('div');
        previewContainer.className = 'document-preview';

        reader.onload = function(e) {
            if (file.type === 'application/pdf') {
                // For PDFs, use PDF.js to generate thumbnail
                const pdfData = new Uint8Array(e.target.result);
                pdfjsLib.getDocument({data: pdfData}).promise.then(function(pdf) {
                    pdf.getPage(1).then(function(page) {
                        const canvas = document.createElement('canvas');
                        const viewport = page.getViewport({scale: 0.5});
                        canvas.width = viewport.width;
                        canvas.height = viewport.height;
                        page.render({
                            canvasContext: canvas.getContext('2d'),
                            viewport: viewport
                        }).promise.then(() => {
                            previewContainer.innerHTML = `
                                <img src="${canvas.toDataURL()}" alt="PDF Preview">
                                <div class="overlay">
                                    <i data-feather="file-text"></i>
                                </div>
                            `;
                            feather.replace();
                        });
                    });
                });
            } else {
                // For Word documents, show a generic icon
                previewContainer.innerHTML = `
                    <div class="document-preview-placeholder">
                        <i data-feather="file-text" style="width: 48px; height: 48px;"></i>
                        <p class="mt-2">${file.name}</p>
                    </div>
                `;
                feather.replace();
            }
        };

        if (file.type === 'application/pdf') {
            reader.readAsArrayBuffer(file);
        } else {
            reader.readAsText(file);
        }

        return previewContainer;
    }

    function handleFileUpload(file) {
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        // Reset and show progress container
        progressContainer.style.display = 'block';
        progressContainer.classList.remove('active');
        progressBar.style.width = '0%';

        // Add status message element if it doesn't exist
        if (!progressContainer.querySelector('.progress-status')) {
            const statusEl = document.createElement('div');
            statusEl.className = 'progress-status';
            progressContainer.appendChild(statusEl);
        }

        // Delay to allow CSS transition to work
        setTimeout(() => {
            progressContainer.classList.add('active');
            updateProgress(0);
        }, 50);

        loadingSpinner.style.display = 'block';
        loadingSpinner.classList.add('active');
        resultsContainer.innerHTML = '';

        // Start progress animation
        const progressInterval = animateProgress();

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            clearInterval(progressInterval);
            updateProgress(100);

            // Smooth transition to completion
            setTimeout(() => {
                progressContainer.classList.remove('active');
                loadingSpinner.classList.remove('active');

                setTimeout(() => {
                    progressContainer.style.display = 'none';
                    loadingSpinner.style.display = 'none';
                    displayResults(data);
                    showToast('Document analyzed successfully!', 'success');
                }, 300);
            }, 500);
        })
        .catch(error => {
            clearInterval(progressInterval);
            progressContainer.classList.remove('active');
            loadingSpinner.classList.remove('active');

            setTimeout(() => {
                progressContainer.style.display = 'none';
                loadingSpinner.style.display = 'none';
                showToast(error.message || 'An error occurred while processing the document.', 'error');
            }, 300);

            console.error('Error:', error);
        });
    }

    function displayResults(data) {
        const resultsHtml = `
            <div class="paper-container">
                <h3>Document Analysis</h3>
                <div class="card mb-3">
                    <div class="card-body">
                        <h5>Document Type</h5>
                        <p>${data.document_type || 'Not detected'}</p>
                        <h5>Summary</h5>
                        <p>${data.summary}</p>
                    </div>
                </div>
                <div class="insights-container">
                    <h5>Key Insights</h5>
                    ${data.insights.map(insight => `
                        <div class="insight-card">
                            <p>${insight}</p>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        resultsContainer.innerHTML = resultsHtml;
    }
});