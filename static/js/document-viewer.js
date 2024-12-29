class DocumentViewer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.pdfjs = window.pdfjsLib;
        this.currentPage = 1;
        this.totalPages = 0;
        this.pdf = null;
        this.isLoading = false;
    }

    showLoading() {
        this.isLoading = true;
        this.container.innerHTML = `
            <div class="document-loading">
                <div class="document-loading-animation">
                    <div class="page-flip"></div>
                </div>
                <p class="loading-text">Loading document preview...</p>
            </div>
        `;
    }

    hideLoading() {
        this.isLoading = false;
        const loadingEl = this.container.querySelector('.document-loading');
        if (loadingEl) {
            loadingEl.classList.add('fade-out');
            setTimeout(() => {
                if (loadingEl.parentNode === this.container) {
                    this.container.removeChild(loadingEl);
                }
            }, 300);
        }
    }

    async loadPDF(url) {
        try {
            this.showLoading();
            this.pdf = await this.pdfjs.getDocument(url).promise;
            this.totalPages = this.pdf.numPages;
            await this.renderPage(1);
            this.setupNavigation();
            this.hideLoading();
        } catch (error) {
            console.error('Error loading PDF:', error);
            this.showError('Failed to load PDF document.');
            this.hideLoading();
        }
    }

    async renderPage(pageNumber) {
        try {
            const page = await this.pdf.getPage(pageNumber);
            const viewport = page.getViewport({ scale: 1.5 });

            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');
            canvas.height = viewport.height;
            canvas.width = viewport.width;

            const renderContext = {
                canvasContext: context,
                viewport: viewport
            };

            await page.render(renderContext).promise;

            // Add fade-in animation to new page
            canvas.classList.add('page-transition');
            this.container.innerHTML = '';
            this.container.appendChild(canvas);

            // Trigger fade-in
            setTimeout(() => {
                canvas.classList.add('visible');
            }, 50);

            this.currentPage = pageNumber;
            this.updateNavigationStatus();
        } catch (error) {
            console.error('Error rendering page:', error);
            this.showError('Failed to render page.');
        }
    }

    setupNavigation() {
        const navigation = document.createElement('div');
        navigation.className = 'pdf-navigation mt-3 text-center';
        navigation.innerHTML = `
            <button class="btn btn-secondary" id="prev-page" ${this.currentPage <= 1 ? 'disabled' : ''}>
                <i data-feather="chevron-left"></i> Previous
            </button>
            <span class="mx-3 page-indicator">Page ${this.currentPage} of ${this.totalPages}</span>
            <button class="btn btn-secondary" id="next-page" ${this.currentPage >= this.totalPages ? 'disabled' : ''}>
                Next <i data-feather="chevron-right"></i>
            </button>
        `;

        this.container.parentNode.appendChild(navigation);

        document.getElementById('prev-page').addEventListener('click', () => {
            if (this.currentPage > 1) {
                this.currentPage--;
                this.renderPage(this.currentPage);
            }
        });

        document.getElementById('next-page').addEventListener('click', () => {
            if (this.currentPage < this.totalPages) {
                this.currentPage++;
                this.renderPage(this.currentPage);
            }
        });

        // Initialize Feather icons
        feather.replace();
    }

    updateNavigationStatus() {
        const pageIndicator = document.querySelector('.page-indicator');
        const prevButton = document.getElementById('prev-page');
        const nextButton = document.getElementById('next-page');

        if (pageIndicator) {
            pageIndicator.textContent = `Page ${this.currentPage} of ${this.totalPages}`;
        }

        if (prevButton) {
            prevButton.disabled = this.currentPage <= 1;
        }

        if (nextButton) {
            nextButton.disabled = this.currentPage >= this.totalPages;
        }
    }

    showError(message) {
        this.container.innerHTML = `
            <div class="alert alert-danger fade-in" role="alert">
                <i data-feather="alert-circle" class="me-2"></i>
                ${message}
            </div>
        `;
        feather.replace();
    }
}