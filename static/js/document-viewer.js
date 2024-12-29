class DocumentViewer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.pdfjs = window.pdfjsLib;
        this.currentPage = 1;
        this.totalPages = 0;
        this.pdf = null;
    }

    async loadPDF(url) {
        try {
            this.pdf = await this.pdfjs.getDocument(url).promise;
            this.totalPages = this.pdf.numPages;
            await this.renderPage(1);
            this.setupNavigation();
        } catch (error) {
            console.error('Error loading PDF:', error);
            this.showError('Failed to load PDF document.');
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
            
            this.container.innerHTML = '';
            this.container.appendChild(canvas);
        } catch (error) {
            console.error('Error rendering page:', error);
            this.showError('Failed to render page.');
        }
    }

    setupNavigation() {
        const navigation = document.createElement('div');
        navigation.className = 'pdf-navigation mt-3 text-center';
        navigation.innerHTML = `
            <button class="btn btn-secondary" id="prev-page">Previous</button>
            <span class="mx-3">Page ${this.currentPage} of ${this.totalPages}</span>
            <button class="btn btn-secondary" id="next-page">Next</button>
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
    }

    showError(message) {
        this.container.innerHTML = `
            <div class="alert alert-danger" role="alert">
                ${message}
            </div>
        `;
    }
}
