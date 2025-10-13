// Main Application Controller
class SocialMediaAnalytics {
    constructor() {
        this.currentAnalysisId = null;
        this.analysisData = null;
        this.referenceImages = {};
        this.pollRetryCount = 0; // Add this
        this.maxRetries = 50; // Add this (50 retries = ~10 minutes with exponential backoff)
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setDefaultDates();
        this.loadRecentAnalyses();
        this.updateReferenceImagesSection();
    }
    
    setupEventListeners() {
        // Main buttons
        $('#addBrandBtn').click(() => this.addBrandConfig());
        $('#startAnalysisBtn').click(() => this.startAnalysis());
        $('#applyFilterBtn').click(() => this.applyTimeFilter());
        $('#downloadBtn').click(() => this.downloadResults());
        $('#homeBtn').click(() => this.goToHome());
        
        // History panel
        $('#historyToggleBtn').click(() => this.toggleHistoryPanel());
        $('#closeHistoryBtn').click(() => this.closeHistoryPanel());
        
        // Dynamic event handlers
        $(document).on('click', '.remove-brand', (e) => this.removeBrandConfig(e));
        $(document).on('click', '.load-analysis', (e) => this.loadPreviousAnalysis(e));
        $(document).on('click', '.delete-analysis', (e) => this.deleteAnalysis(e));
        $(document).on('click', '.post-thumbnail', (e) => this.openPostUrl(e));
        $(document).on('input', '.brand-name, .keywords', () => this.updateReferenceImagesSection());
        $(document).on('change', '.reference-image-input', (e) => this.handleReferenceImageUpload(e));
    }
    
    setDefaultDates() {
        const today = new Date();
        const threeMonthsAgo = new Date();
        threeMonthsAgo.setMonth(threeMonthsAgo.getMonth() - 3);
        
        $('#startDateFilter').val(threeMonthsAgo.toISOString().split('T')[0]);
        $('#endDateFilter').val(today.toISOString().split('T')[0]);
    }
    
    addBrandConfig() {
        const brandCount = $('.brand-config').length + 1;
        const brandHtml = `
            <div class="brand-config bg-gray-50 p-4 rounded-lg mb-4 fade-in">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="font-medium text-gray-700">Brand ${brandCount}</h3>
                    <button class="remove-brand text-red-500 hover:text-red-700">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Brand Name</label>
                        <input type="text" class="brand-name w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder="Enter brand name">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Instagram URL</label>
                        <input type="url" class="instagram-url w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder="https://instagram.com/brand">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Facebook URL</label>
                        <input type="url" class="facebook-url w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder="https://facebook.com/brand">
                    </div>
                </div>
                <div class="mt-4">
                    <label class="block text-sm font-medium text-gray-700 mb-1">Keywords/Models (comma separated)</label>
                    <input type="text" class="keywords w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder="model1, model2, model3">
                    <p class="text-xs text-gray-500 mt-1">Enter vehicle models or keywords to track</p>
                </div>
            </div>
        `;
        $('#brandsContainer').append(brandHtml);
        this.updateReferenceImagesSection();
    }
    
    removeBrandConfig(e) {
        if ($('.brand-config').length > 1) {
            $(e.target).closest('.brand-config').remove();
            this.updateReferenceImagesSection();
        } else {
            UI.showToast('At least one brand configuration is required.', 'warning');
        }
    }
    
    updateReferenceImagesSection() {
        const container = $('#referenceImagesContainer');
        container.empty();
        
        $('.brand-config').each((index, element) => {
            const brandName = $(element).find('.brand-name').val().trim() || `Brand ${index + 1}`;
            const keywords = $(element).find('.keywords').val().split(',').map(k => k.trim()).filter(k => k);
            
            if (keywords.length > 0) {
                let modelsHtml = '';
                keywords.forEach(model => {
                    modelsHtml += this.createModelReferenceSection(brandName, model);
                });
                
                const brandSection = `
                    <div class="brand-reference-section mb-8 p-4 border rounded-lg bg-gray-50">
                        <h3 class="text-lg font-semibold mb-4 text-gray-800">${brandName}</h3>
                        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            ${modelsHtml}
                        </div>
                    </div>
                `;
                container.append(brandSection);
            }
        });
    }
    
    createModelReferenceSection(brandName, modelName) {
        const sanitizedBrand = brandName.replace(/[^a-zA-Z0-9]/g, '');
        const sanitizedModel = modelName.replace(/[^a-zA-Z0-9]/g, '');
        const inputId = `ref-${sanitizedBrand}-${sanitizedModel}`;
        
        return `
            <div class="model-reference-upload">
                <label class="block text-sm font-medium text-gray-700 mb-2">${modelName}</label>
                <input type="file" 
                       id="${inputId}"
                       class="reference-image-input w-full border rounded-lg px-3 py-2 mb-2" 
                       data-brand="${brandName}" 
                       data-model="${modelName}"
                       multiple 
                       accept="image/*"
                       max="3">
                <p class="text-xs text-gray-500 mb-2">Upload up to 3 reference images</p>
                <div class="reference-previews flex flex-wrap gap-2" id="preview-${inputId}">
                    <!-- Preview images will appear here -->
                </div>
            </div>
        `;
    }
    
    handleReferenceImageUpload(e) {
        const files = Array.from(e.target.files);
        const brand = $(e.target).data('brand');
        const model = $(e.target).data('model');
        const previewContainer = $(`#preview-${e.target.id}`);
        
        if (files.length > 3) {
            UI.showToast('Maximum 3 images allowed per model', 'warning');
            e.target.value = '';
            return;
        }
        
        // Store reference images
        if (!this.referenceImages[brand]) {
            this.referenceImages[brand] = {};
        }
        this.referenceImages[brand][model] = files;
        
        // Clear previous previews
        previewContainer.empty();
        
        // Create previews
        files.forEach((file, index) => {
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = (event) => {
                    const preview = $(`
                        <div class="reference-preview">
                            <img src="${event.target.result}" alt="Reference ${index + 1}">
                            <button type="button" class="remove-btn" onclick="app.removeImagePreview(this, '${brand}', '${model}', ${index})">×</button>
                        </div>
                    `);
                    previewContainer.append(preview);
                };
                reader.readAsDataURL(file);
            }
        });
    }
    
    removeImagePreview(button, brand, model, index) {
        // Remove from UI
        $(button).closest('.reference-preview').remove();
        
        // Update stored reference images
        if (this.referenceImages[brand] && this.referenceImages[brand][model]) {
            this.referenceImages[brand][model].splice(index, 1);
            if (this.referenceImages[brand][model].length === 0) {
                delete this.referenceImages[brand][model];
                if (Object.keys(this.referenceImages[brand]).length === 0) {
                    delete this.referenceImages[brand];
                }
            }
        }
    }
    
    async startAnalysis() {
        // Validate form
        const brands = this.collectBrandConfigurations();
        if (!brands) return;
        
        // Prepare reference images for upload
        const uploadPromises = await this.uploadReferenceImages();
        if (uploadPromises === null) return; // Upload failed
        
        // Show loading
        this.showLoadingSection();
        this.pollRetryCount = 0;
        
        try {
            // Start analysis with reference images
            const response = await API.startAnalysis({
                brands_config: brands,
                reference_images: uploadPromises
            });
            
            this.currentAnalysisId = response.analysis_id;
            console.log('Analysis started:', this.currentAnalysisId);
            
            // Start polling
            setTimeout(() => this.pollAnalysisStatus(), 1000);
            
        } catch (error) {
            console.error('Error starting analysis:', error);
            UI.showToast('Error starting analysis: ' + error.message, 'error');
            this.hideLoadingSection();
        }
        setTimeout(() => this.pollAnalysisStatus(), 1000);
    }
    
    collectBrandConfigurations() {
        const brands = {};
        let hasError = false;

        $('.brand-config').each(function() {
            const brandName = $(this).find('.brand-name').val().trim();
            const instagramUrl = $(this).find('.instagram-url').val().trim();
            const facebookUrl = $(this).find('.facebook-url').val().trim();
            const keywords = $(this).find('.keywords').val().split(',').map(k => k.trim()).filter(k => k);

            if (!brandName || !instagramUrl || !facebookUrl || keywords.length === 0) {
                hasError = true;
                return false;
            }

            brands[brandName] = {
                instagram_url: instagramUrl,
                facebook_url: facebookUrl,
                keywords: keywords
            };
        });

        if (hasError) {
            UI.showToast('Please fill in all required fields for each brand.', 'error');
            return null;
        }
        
        return brands;
    }
    
    async uploadReferenceImages() {
        const uploadedPaths = {};
        const tempId = 'temp-' + Date.now();
        
        try {
            UI.updateLoadingStatus({
                message: "Uploading reference images...",
                progress: 10
            });
            
            for (const [brandName, models] of Object.entries(this.referenceImages)) {
                uploadedPaths[brandName] = {};
                
                for (const [modelName, files] of Object.entries(models)) {
                    if (files.length > 0) {
                        const formData = new FormData();
                        formData.append('brand', brandName);
                        formData.append('model', modelName);
                        formData.append('analysis_id', tempId);
                        
                        files.forEach(file => {
                            formData.append('files', file);
                        });
                        
                        try {
                            const response = await API.uploadReferenceImages(formData);
                            uploadedPaths[brandName][modelName] = response.paths;
                        } catch (error) {
                            console.error(`Error uploading images for ${brandName} - ${modelName}:`, error);
                            UI.showToast(`Failed to upload images for ${brandName} - ${modelName}`, 'error');
                            return null;
                        }
                    }
                }
            }
            
            return uploadedPaths;
            
        } catch (error) {
            console.error('Error in reference image upload:', error);
            UI.showToast('Error uploading reference images: ' + error.message, 'error');
            return null;
        }
    }
    
    showLoadingSection() {
        $('#configSection').addClass('hidden');
        $('#referenceImagesSection').addClass('hidden');
        $('#loadingSection').removeClass('hidden');
    }
    
    hideLoadingSection() {
        $('#configSection').removeClass('hidden');
        $('#referenceImagesSection').removeClass('hidden');
        $('#loadingSection').addClass('hidden');
    }
        
    async pollAnalysisStatus() {
        if (!this.currentAnalysisId) return;
        
        if (this.pollRetryCount >= this.maxRetries) {
            UI.showToast('Analysis is taking too long. Please check back later.', 'warning');
            this.hideLoadingSection();
            return;
        }

        try {
            const data = await API.getAnalysisStatus(this.currentAnalysisId);
            
            // Reset retry count on successful request
            this.pollRetryCount = 0;
            
            UI.updateLoadingStatus({
                message: data.message,
                progress: data.progress
            });

            if (data.status === 'completed') {
                this.analysisData = data;
                this.showResults(data);
            } else if (data.status === 'error') {
                UI.showToast('Analysis failed: ' + data.message, 'error');
                this.hideLoadingSection();
            } else {
                const pollInterval = 5000;
                setTimeout(() => this.pollAnalysisStatus(), pollInterval);
            }
            
        } catch (error) {
            console.error('Polling error:', error);
            this.pollRetryCount++;
            
            // Exponential backoff: 5s, 10s, 15s, 20s, then 20s
            const backoffDelay = Math.min(5000 * this.pollRetryCount, 20000);
            
            console.log(`Retry ${this.pollRetryCount}/${this.maxRetries} in ${backoffDelay/1000}s...`);
            setTimeout(() => this.pollAnalysisStatus(), backoffDelay);
        }
    }
    showResults(data) {
        console.log('Showing results');
        
        $('#loadingSection').addClass('hidden');
        $('#resultsSection').removeClass('hidden');
        $('#downloadBtn').removeClass('hidden');
        $('#homeBtn').removeClass('hidden');
        
        UI.renderBrandResults(data.brands_data);
        
        if (data.universal_filter) {
            const startDate = new Date(data.universal_filter.start_date);
            const endDate = new Date(data.universal_filter.end_date);
            
            $('#startDateFilter').val(startDate.toISOString().split('T')[0]);
            $('#endDateFilter').val(endDate.toISOString().split('T')[0]);
        }
    }
    
    goToHome() {
        this.currentAnalysisId = null;
        this.analysisData = null;
        this.referenceImages = {};
        
        $('#resultsSection').addClass('hidden');
        $('#loadingSection').addClass('hidden');
        $('#downloadBtn').addClass('hidden');
        $('#homeBtn').addClass('hidden');
        
        $('#configSection').removeClass('hidden');
        $('#referenceImagesSection').removeClass('hidden');
        
        // Clear forms
        $('.brand-config').not(':first').remove();
        $('.brand-config:first input').val('');
        this.updateReferenceImagesSection();
    }
    
    async loadRecentAnalyses() {
        try {
            const analyses = await API.getRecentAnalyses();
            UI.displayAnalysesHistory(analyses);
        } catch (error) {
            console.error('Error loading recent analyses:', error);
            $('#historyList').html('<p class="text-red-500 text-sm p-4">Error loading analyses</p>');
        }
    }
    
    async loadPreviousAnalysis(e) {
        const analysisId = $(e.target).data('analysis-id');
        
        if (!analysisId) {
            UI.showToast('No analysis ID found', 'error');
            return;
        }
        
        UI.showLoadingOverlay();
        
        try {
            const data = await API.getAnalysisStatus(analysisId);
            
            if (data.status === 'completed') {
                this.currentAnalysisId = analysisId;
                this.analysisData = data;
                
                this.closeHistoryPanel();
                this.showResults(data);
            } else {
                UI.showToast(`Analysis is not completed yet (Status: ${data.status})`, 'warning');
            }
            
        } catch (error) {
            console.error('Error loading analysis:', error);
            UI.showToast('Error loading analysis: ' + error.message, 'error');
        } finally {
            UI.hideLoadingOverlay();
        }
    }
    
    async deleteAnalysis(e) {
        // Get analysis ID from the clicked element or its parent
        let analysisId = $(e.target).data('analysis-id');
        
        // If not found on the target, check parent elements
        if (!analysisId) {
            analysisId = $(e.target).closest('[data-analysis-id]').data('analysis-id');
        }
        
        // If still not found, check if the click was on an icon inside the button
        if (!analysisId) {
            analysisId = $(e.target).closest('.delete-analysis').data('analysis-id');
        }
        
        console.log('Delete analysis ID:', analysisId); // Debug log
        
        if (!analysisId) {
            UI.showToast('No analysis ID found', 'error');
            return;
        }
        
        if (!confirm('Are you sure you want to delete this analysis? This action cannot be undone.')) {
            return;
        }
        
        try {
            await API.deleteAnalysis(analysisId);
            UI.showToast('Analysis deleted successfully', 'success');
            this.loadRecentAnalyses();
        } catch (error) {
            console.error('Delete error:', error);
            UI.showToast('Error deleting analysis: ' + error.message, 'error');
        }
    }
    
    toggleHistoryPanel() {
        const panel = $('#historyPanel');
        if (panel.hasClass('translate-x-full')) {
            panel.removeClass('translate-x-full');
            this.loadRecentAnalyses();
        } else {
            panel.addClass('translate-x-full');
        }
    }
    
    closeHistoryPanel() {
        $('#historyPanel').addClass('translate-x-full');
    }
    
    async applyTimeFilter() {
        const startDate = $('#startDateFilter').val();
        const endDate = $('#endDateFilter').val();

        if (!startDate || !endDate) {
            UI.showToast('Please select both start and end dates.', 'warning');
            return;
        }

        if (new Date(startDate) > new Date(endDate)) {
            UI.showToast('Start date must be before end date.', 'error');
            return;
        }

        if (!this.currentAnalysisId) {
            UI.showToast('No analysis data available.', 'error');
            return;
        }

        console.log('Applying time filter:', { startDate, endDate, analysisId: this.currentAnalysisId });

        // Show filtering feedback
        const filterButton = $('#applyFilterBtn');
        const originalText = filterButton.html();
        filterButton.html('<i class="fas fa-spinner fa-spin mr-2"></i>Filtering...').prop('disabled', true);

        try {
            const timeFilter = {
                start_date: new Date(startDate + 'T00:00:00').toISOString(),
                end_date: new Date(endDate + 'T23:59:59').toISOString()
            };

            console.log('Sending filter request with:', timeFilter);
            
            const response = await API.filterResults(this.currentAnalysisId, timeFilter);
            console.log('Filter response received:', response);
            
            if (response.filtered_results) {
                // Clear and rebuild the results with filtered data
                $('#brandResults').empty();
                UI.renderBrandResults(response.filtered_results);
                UI.showToast('Time filter applied successfully', 'success');
            } else {
                console.error('No filtered_results in response:', response);
                UI.showToast('Invalid filter response received', 'error');
            }
            
        } catch (error) {
            console.error('Error applying filter:', error);
            UI.showToast('Error applying filter: ' + error.message, 'error');
        } finally {
            // Restore button state
            filterButton.html(originalText).prop('disabled', false);
        }
    }
    
    async downloadResults() {
        if (!this.currentAnalysisId) {
            UI.showToast('No analysis data available for download.', 'error');
            return;
        }

        const startDate = $('#startDateFilter').val();
        const endDate = $('#endDateFilter').val();
        
        try {
            await API.downloadResults(this.currentAnalysisId, startDate, endDate);
            UI.showToast('Download started', 'success');
        } catch (error) {
            UI.showToast('Download failed: ' + error.message, 'error');
        }
    }
    
    async downloadResults() {
        if (!this.currentAnalysisId) {
            UI.showToast('No analysis data available for download.', 'error');
            return;
        }

        const startDate = $('#startDateFilter').val();
        const endDate = $('#endDateFilter').val();
        
        // Show loading state on button
        const downloadBtn = $('#downloadBtn');
        const originalHtml = downloadBtn.html();
        downloadBtn.html('<i class="fas fa-spinner fa-spin mr-2"></i>Downloading...').prop('disabled', true);
        
        try {
            const result = await API.downloadResults(this.currentAnalysisId, startDate, endDate);
            UI.showToast(`Downloaded: ${result.filename}`, 'success');
        } catch (error) {
            console.error('Download failed:', error);
            UI.showToast('Download failed: ' + error.message, 'error');
        } finally {
            // Restore button state
            setTimeout(() => {
                downloadBtn.html(originalHtml).prop('disabled', false);
            }, 1000);
        }
    }
    openPostUrl(e) {
        const url = $(e.target).data('post-url') || $(e.target).closest('.post-thumbnail').data('post-url');
        if (url) {
            window.open(url, '_blank');
        }
    }
}

// Initialize app when DOM is ready
$(document).ready(() => {
    window.app = new SocialMediaAnalytics();
});