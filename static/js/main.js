document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const uploadArea = document.querySelector('.upload-area');
    const loadingSpinner = document.querySelector('.loading-spinner');
    const resultsContainer = document.getElementById('results-container');

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

    function handleFileUpload(file) {
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        loadingSpinner.style.display = 'block';
        resultsContainer.innerHTML = '';

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            loadingSpinner.style.display = 'none';
            displayResults(data);
        })
        .catch(error => {
            loadingSpinner.style.display = 'none';
            showError('An error occurred while processing the document.');
            console.error('Error:', error);
        });
    }

    function displayResults(data) {
        const resultsHtml = `
            <div class="paper-container">
                <h3>Document Analysis</h3>
                <div class="card mb-3">
                    <div class="card-body">
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

    function showError(message) {
        resultsContainer.innerHTML = `
            <div class="alert alert-danger" role="alert">
                ${message}
            </div>
        `;
    }
});
