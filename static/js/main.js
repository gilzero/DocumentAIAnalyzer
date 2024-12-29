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

    // File type icons mapping
    const fileTypeIcons = {
        'application/pdf': 'file-text',
        'application/msword': 'file-word',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'file-word'
    };

    // Enhanced file compatibility status with encoding support
    const fileCompatibility = {
        'application/pdf': { 
            status: 'Full support', 
            icon: 'check-circle', 
            class: 'text-success',
            encoding: 'UTF-8/Binary'
        },
        'application/msword': { 
            status: 'Legacy format', 
            icon: 'alert-triangle', 
            class: 'text-warning',
            encoding: 'Binary'
        },
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': { 
            status: 'Full support', 
            icon: 'check-circle', 
            class: 'text-success',
            encoding: 'UTF-8/Binary'
        }
    };

    // Drag and drop functionality with visual feedback
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

    function createFilenamePreview(filename) {
        const container = document.createElement('div');
        container.className = 'filename-preview mt-2';

        // Count characters by type
        const stats = {
            total: filename.length,
            ascii: 0,
            chinese: 0,
            other: 0
        };

        [...filename].forEach(char => {
            if (/[\u4e00-\u9fa5]/.test(char)) {
                stats.chinese++;
            } else if (/[\x00-\x7F]/.test(char)) {
                stats.ascii++;
            } else {
                stats.other++;
            }
        });

        container.innerHTML = `
            <div class="filename-stats">
                <div class="filename-display" title="${filename}">
                    <i data-feather="file" class="me-2"></i>
                    <span class="filename-text">${filename}</span>
                </div>
                <div class="char-count-tooltip">
                    <span class="total">Total: ${stats.total} characters</span>
                    ${stats.chinese ? `<span class="chinese">Chinese: ${stats.chinese}</span>` : ''}
                    ${stats.ascii ? `<span class="ascii">ASCII: ${stats.ascii}</span>` : ''}
                    ${stats.other ? `<span class="other">Other: ${stats.other}</span>` : ''}
                </div>
            </div>
        `;

        feather.replace();
        return container;
    }

    function showEncodingInfo(fileType) {
        const compatibility = fileCompatibility[fileType] || { 
            status: 'Unknown format', 
            icon: 'help-circle',
            class: 'text-muted',
            encoding: 'Unknown'
        };

        const infoHtml = `
            <div class="file-compatibility-info ${compatibility.class} mb-3">
                <div class="d-flex align-items-center">
                    <i data-feather="${compatibility.icon}" class="me-2"></i>
                    <span>${compatibility.status}</span>
                </div>
                <div class="encoding-info mt-1">
                    <small class="text-muted">
                        <i data-feather="code" class="me-1"></i>
                        Encoding: ${compatibility.encoding}
                    </small>
                </div>
            </div>
        `;

        const infoContainer = document.createElement('div');
        infoContainer.innerHTML = infoHtml;
        uploadArea.appendChild(infoContainer);
        feather.replace();
    }


    function showFileTypeInfo(fileType) {
        //This function is not used anymore, it's replaced by showEncodingInfo
    }

    function showToast({ message, type = 'info', details = null }) {
        const icon = type === 'error' ? 'alert-circle' : 'check-circle';
        const toast = Toastify({
            text: `
                <div class="d-flex flex-column">
                    <div class="d-flex align-items-center">
                        <i data-feather="${icon}" class="me-2"></i>
                        <span>${message}</span>
                    </div>
                    ${details ? `
                        <small class="text-muted mt-1">
                            ${details}
                        </small>
                    ` : ''}
                </div>
            `,
            duration: 4000,
            gravity: "top",
            position: "right",
            className: type,
            stopOnFocus: true,
            escapeMarkup: false,
            style: {
                minWidth: '300px'
            }
        }).showToast();

        feather.replace();
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
                                    <i data-feather="${fileTypeIcons[file.type] || 'file'}" class="preview-icon"></i>
                                </div>
                            `;
                            feather.replace();
                        });
                    });
                });
            } else {
                // For Word documents, show a generic icon with filename
                previewContainer.innerHTML = `
                    <div class="document-preview-placeholder">
                        <i data-feather="${fileTypeIcons[file.type] || 'file'}" class="preview-icon"></i>
                        <p class="mt-2">${decodeURIComponent(file.name)}</p>
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

    function createMetadataPanel(file, metadata = {}) {
        const panel = document.createElement('div');
        panel.className = 'metadata-panel collapsed';

        const formatFileSize = (bytes) => {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        };

        const formatDate = (date) => {
            return new Date(date).toLocaleString();
        };

        panel.innerHTML = `
            <div class="metadata-header">
                <div class="d-flex align-items-center">
                    <i data-feather="file-text" class="me-2"></i>
                    <span>Document Metadata</span>
                </div>
                <i data-feather="chevron-down" class="toggle-icon"></i>
            </div>
            <div class="metadata-content hidden">
                <div class="metadata-item">
                    <span class="metadata-label">Filename:</span>
                    <span class="metadata-value">${decodeURIComponent(file.name)}</span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">File Size:</span>
                    <span class="metadata-value">${formatFileSize(file.size)}</span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">File Type:</span>
                    <span class="metadata-value">${file.type || 'Unknown'}</span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">Last Modified:</span>
                    <span class="metadata-value">${formatDate(file.lastModified)}</span>
                </div>
                ${Object.entries(metadata).map(([key, value]) => `
                    <div class="metadata-item">
                        <span class="metadata-label">${key}:</span>
                        <span class="metadata-value">${value}</span>
                    </div>
                `).join('')}
            </div>
        `;

        // Add toggle functionality
        const header = panel.querySelector('.metadata-header');
        const content = panel.querySelector('.metadata-content');
        const toggleIcon = panel.querySelector('.toggle-icon');

        header.addEventListener('click', () => {
            panel.classList.toggle('collapsed');
            panel.classList.toggle('expanded');
            content.classList.toggle('hidden');
            toggleIcon.style.transform = panel.classList.contains('expanded') ? 
                'rotate(180deg)' : 'rotate(0deg)';
        });

        // Initialize Feather icons
        feather.replace();

        return panel;
    }

    function handleFileUpload(file) {
        if (!file) return;

        // Clear previous previews
        const prevPreviews = uploadArea.querySelectorAll('.filename-preview, .file-compatibility-info');
        prevPreviews.forEach(el => el.remove());

        // Add filename preview with stats
        const filenamePreview = createFilenamePreview(file.name);
        uploadArea.appendChild(filenamePreview);

        // Show file type and encoding compatibility
        showEncodingInfo(file.type);

        // Validate file type
        const validTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
        if (!validTypes.includes(file.type)) {
            showToast({
                message: 'Please upload a PDF or Word document',
                type: 'error',
                details: 'Supported formats: PDF (.pdf), Word (.doc, .docx)'
            });
            return;
        }

        // Validate filename characters
        const invalidChars = /[<>:"/\\|?*\x00-\x1F]/g;
        if (invalidChars.test(file.name)) {
            showToast({
                message: 'Invalid characters in filename',
                type: 'error',
                details: 'Filename contains invalid characters. Please rename the file and try again.'
            });
            return;
        }

        const maxSize = 16 * 1024 * 1024; // 16MB in bytes
        if (file.size > maxSize) {
            showToast({
                message: `File size (${(file.size / 1024 / 1024).toFixed(1)}MB) exceeds maximum allowed size (16MB)`,
                type: 'error',
                details: 'Please select a smaller file.'
            });
            return;
        }

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

        // Create and show document preview
        const preview = createDocumentPreview(file);
        document.getElementById('document-viewer').appendChild(preview);

        // Create and append metadata panel
        const metadataPanel = createMetadataPanel(file);
        document.getElementById('document-viewer').appendChild(metadataPanel);

        // Start progress animation
        const progressInterval = animateProgress();

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(async response => {
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                throw new Error(`Server error: Unexpected response type (${response.status})`);
            }
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }
            return data;
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

                    // Update metadata panel with additional info
                    const metadataPanel = document.querySelector('.metadata-panel');
                    if (metadataPanel && data.metadata) {
                        metadataPanel.remove(); // Remove old panel
                        const updatedPanel = createMetadataPanel(file, data.metadata);
                        document.getElementById('document-viewer').appendChild(updatedPanel);
                    }

                    showToast({message: 'Document analyzed successfully!', type: 'success'});
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

                // Enhanced error message handling
                let errorMessage = 'An error occurred while processing the document.';
                if (error.message.includes('Server error')) {
                    errorMessage = 'The server encountered an error. Please try again later.';
                } else if (error.message.includes('Failed to fetch')) {
                    errorMessage = 'Network error. Please check your connection and try again.';
                } else if (error.message.includes('HTTP error')) {
                    errorMessage = 'Server communication error. Please try again.';
                } else {
                    errorMessage = error.message;
                }

                showToast({message: errorMessage, type: 'error'});
                console.error('Error details:', error);
            }, 300);
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