let currentAnalysisId = null;
let analysisData = null;

$(document).ready(function() {
    setupEventListeners();
    setDefaultDates();
    loadRecentAnalyses(); // Load recent analyses on page load
});

function setupEventListeners() {
    $('#addBrandBtn').click(addBrandConfig);
    $('#startAnalysisBtn').click(startAnalysis);
    $('#applyFilterBtn').click(applyTimeFilter);
    $('#downloadBtn').click(downloadResults);
    $('#classifyImagesBtn').click(classifyByImages);
    $('#historyToggleBtn').click(toggleHistoryPanel);
    $('#closeHistoryBtn').click(closeHistoryPanel);
    $('#homeBtn').click(goToHome); // Add home button listener
    
    $(document).on('click', '.remove-brand', removeBrandConfig);
    $(document).on('click', '.load-analysis', loadPreviousAnalysis);
    $(document).on('click', '.delete-analysis', deleteAnalysis);
    $(document).on('click', '.reclassify-brand', reclassifyBrandPosts);
    $(document).on('click', '.post-thumbnail', openPostUrl);
}


function loadRecentAnalyses() {
    $.ajax({
        url: '/api/recent-analyses',
        method: 'GET',
        success: function(analyses) {
            const container = $('#historyList');
            container.empty();
            
            if (analyses.length === 0) {
                container.html('<p class="text-gray-500 text-sm p-4">No analyses found</p>');
                return;
            }
            
            analyses.forEach(analysis => {
                const statusColor = analysis.status === 'completed' ? 'text-green-600' : 
                                  analysis.status === 'error' ? 'text-red-600' : 'text-blue-600';
                
                const statusIcon = analysis.status === 'completed' ? 'fa-check-circle' : 
                                 analysis.status === 'error' ? 'fa-times-circle' : 'fa-spinner';
                
                const date = new Date(analysis.updated_at).toLocaleDateString();
                const time = new Date(analysis.updated_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                
                const analysisHtml = `
                    <div class="border-b border-gray-200 p-4 hover:bg-gray-50 transition-colors">
                        <div class="flex items-center justify-between mb-2">
                            <div class="flex items-center space-x-2">
                                <i class="fas ${statusIcon} ${statusColor}"></i>
                                <span class="font-medium text-sm text-gray-800">${analysis.analysis_id.substring(0, 8)}...</span>
                            </div>
                            <span class="text-xs text-gray-500">${date} ${time}</span>
                        </div>
                        <p class="text-xs text-gray-600 mb-3 line-clamp-2">${analysis.message || 'No message'}</p>
                        <div class="flex items-center justify-between">
                            <span class="text-xs ${statusColor} font-medium">${analysis.status} (${analysis.progress || 0}%)</span>
                            <div class="flex space-x-2">
                                ${analysis.status === 'completed' ? `
                                    <button class="load-analysis text-xs bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700 transition-colors" 
                                            data-analysis-id="${analysis.analysis_id}" 
                                            title="Load this analysis">
                                        <i class="fas fa-eye mr-1"></i>Load
                                    </button>
                                ` : ''}
                                <button class="delete-analysis text-xs bg-red-600 text-white px-3 py-1 rounded hover:bg-red-700 transition-colors" 
                                        data-analysis-id="${analysis.analysis_id}"
                                        title="Delete this analysis">
                                    <i class="fas fa-trash mr-1"></i>Delete
                                </button>
                            </div>
                        </div>
                    </div>
                `;
                container.append(analysisHtml);
            });
            
            console.log(`Loaded ${analyses.length} analyses in history`);
        },
        error: function(xhr, status, error) {
            console.error('Error loading recent analyses:', error);
            $('#historyList').html('<p class="text-red-500 text-sm p-4">Error loading analyses</p>');
        }
    });
}


// Add this debugging function
function debugAnalysisData(data) {
    console.log('=== Analysis Data Debug ===');
    console.log('Status:', data.status);
    console.log('Analysis ID:', data.analysis_id);
    console.log('Brands Data:', data.brands_data);
    
    if (data.brands_data) {
        Object.keys(data.brands_data).forEach(brandName => {
            console.log(`Brand: ${brandName}`);
            console.log('  Instagram posts:', data.brands_data[brandName].instagram?.posts?.length || 0);
            console.log('  Facebook posts:', data.brands_data[brandName].facebook?.posts?.length || 0);
            console.log('  Overall metrics:', data.brands_data[brandName].overall_metrics);
        });
    }
    console.log('=== End Debug ===');
}

function processLoadedAnalysisData(data) {
    /**
     * Process loaded analysis data to ensure compatibility with enhanced metrics structure
     * This handles cases where older analyses might have different data structures
     */
    
    if (!data.brands_data) {
        console.error('No brands_data found in loaded analysis');
        return;
    }
    
    Object.keys(data.brands_data).forEach(brandName => {
        const brandData = data.brands_data[brandName];
        
        // Process each platform
        ['instagram', 'facebook', 'overall'].forEach(platform => {
            if (brandData[platform === 'overall' ? 'overall_metrics' : platform]?.metrics) {
                const metrics = brandData[platform === 'overall' ? 'overall_metrics' : platform].metrics;
                
                // Ensure enhanced metrics structure exists
                if (!metrics.target_models) {
                    metrics.target_models = {};
                    metrics.alternative_models = {};
                    metrics.unclassified = { posts_count: 0, total_engagement: 0, posts: [] };
                    
                    // Get posts for this platform
                    let posts = [];
                    if (platform === 'overall') {
                        posts = [...(brandData.instagram?.posts || []), ...(brandData.facebook?.posts || [])];
                    } else {
                        posts = brandData[platform]?.posts || [];
                    }
                    
                    // Get original keywords from model_breakdown or derive from classified posts
                    const modelBreakdown = metrics.model_breakdown || {};
                    const originalKeywords = Object.keys(modelBreakdown).filter(k => k !== 'unclassified');
                    
                    // Categorize posts and create enhanced metrics
                    posts.forEach(post => {
                        const model = post.model || '';
                        const engagement = post.engagement || 0;
                        
                        if (!model || model.toLowerCase() === 'unclassified') {
                            metrics.unclassified.posts.push(post);
                            metrics.unclassified.posts_count++;
                            metrics.unclassified.total_engagement += engagement;
                        } else if (originalKeywords.some(k => k.toLowerCase() === model.toLowerCase())) {
                            // Target model
                            const targetKey = originalKeywords.find(k => k.toLowerCase() === model.toLowerCase());
                            if (!metrics.target_models[targetKey]) {
                                metrics.target_models[targetKey] = { posts: [], posts_count: 0, total_engagement: 0 };
                            }
                            metrics.target_models[targetKey].posts.push(post);
                            metrics.target_models[targetKey].posts_count++;
                            metrics.target_models[targetKey].total_engagement += engagement;
                        } else {
                            // Alternative model
                            if (!metrics.alternative_models[model]) {
                                metrics.alternative_models[model] = { posts: [], posts_count: 0, total_engagement: 0 };
                            }
                            metrics.alternative_models[model].posts.push(post);
                            metrics.alternative_models[model].posts_count++;
                            metrics.alternative_models[model].total_engagement += engagement;
                        }
                    });
                    
                    // Calculate averages and rates
                    const totalEngagement = metrics.total_engagement || 0;
                    
                    Object.keys(metrics.target_models).forEach(model => {
                        const modelData = metrics.target_models[model];
                        modelData.average_engagement = modelData.posts_count > 0 ? modelData.total_engagement / modelData.posts_count : 0;
                        modelData.engagement_rate = totalEngagement > 0 ? (modelData.total_engagement / totalEngagement * 100) : 0;
                    });
                    
                    Object.keys(metrics.alternative_models).forEach(model => {
                        const modelData = metrics.alternative_models[model];
                        modelData.average_engagement = modelData.posts_count > 0 ? modelData.total_engagement / modelData.posts_count : 0;
                        modelData.engagement_rate = totalEngagement > 0 ? (modelData.total_engagement / totalEngagement * 100) : 0;
                    });
                    
                    if (metrics.unclassified.posts_count > 0) {
                        metrics.unclassified.average_engagement = metrics.unclassified.total_engagement / metrics.unclassified.posts_count;
                        metrics.unclassified.engagement_rate = totalEngagement > 0 ? (metrics.unclassified.total_engagement / totalEngagement * 100) : 0;
                    }
                }
            }
        });
    });
}

function loadPreviousAnalysis() {
    const analysisId = $(this).data('analysis-id');
    
    if (!analysisId) {
        alert('No analysis ID found');
        return;
    }
    
    console.log('Loading analysis:', analysisId);
    showLoadingOverlay();
    

    
    $.ajax({
        url: `/api/analysis/${analysisId}`,
        method: 'GET',
        success: function(data) {
            debugAnalysisData(data); // Add this line
            console.log('Analysis data loaded:', data);
            hideLoadingOverlay();
                
            if (data.status === 'completed') {
                currentAnalysisId = analysisId;
                analysisData = data;
                
                // Close history panel
                closeHistoryPanel();
                
                // Hide config and show results
                $('#configSection').addClass('hidden');
                $('#resultsSection').removeClass('hidden');
                $('#downloadBtn').removeClass('hidden');
                $('#homeBtn').removeClass('hidden');
                
                // Process the loaded data to ensure it has the enhanced metrics structure
                processLoadedAnalysisData(data);
                
                // Render results
                renderBrandResults(data.brands_data);
                
                // Set date filters based on universal filter
                if (data.universal_filter) {
                    const startDate = new Date(data.universal_filter.start_date);
                    const endDate = new Date(data.universal_filter.end_date);
                    
                    $('#startDateFilter').val(startDate.toISOString().split('T')[0]);
                    $('#endDateFilter').val(endDate.toISOString().split('T')[0]);
                }
                
            } else if (data.status === 'error') {
                alert('This analysis failed: ' + data.message);
            } else {
                alert('Analysis is not completed yet (Status: ' + data.status + ')');
            }
        },
        error: function(xhr, status, error) {
            hideLoadingOverlay();
            console.error('Error loading analysis:', error, xhr.responseText);
            alert('Error loading analysis: ' + error);
        }
    });
}

function setDefaultDates() {
    const today = new Date();
    const threeMonthsAgo = new Date();
    threeMonthsAgo.setMonth(threeMonthsAgo.getMonth() - 3);
    
    $('#startDateFilter').val(threeMonthsAgo.toISOString().split('T')[0]);
    $('#endDateFilter').val(today.toISOString().split('T')[0]);
}




function toggleHistoryPanel() {
    const panel = $('#historyPanel');
    if (panel.hasClass('translate-x-full')) {
        panel.removeClass('translate-x-full');
        loadRecentAnalyses();
    } else {
        panel.addClass('translate-x-full');
    }
}

function closeHistoryPanel() {
    $('#historyPanel').addClass('translate-x-full');
}


function deleteAnalysis() {
    const analysisId = $(this).data('analysis-id');
    
    if (!confirm('Are you sure you want to delete this analysis? This action cannot be undone.')) {
        return;
    }
    
    $.ajax({
        url: `/api/analysis/${analysisId}`,
        method: 'DELETE',
        success: function(response) {
            alert('Analysis deleted successfully');
            loadRecentAnalyses(); // Refresh the list
        },
        error: function(xhr, status, error) {
            alert('Error deleting analysis: ' + (xhr.responseJSON?.detail || error));
        }
    });
}

function reclassifyBrandPosts() {
    const brandName = $(this).data('brand');
    
    if (!currentAnalysisId || !brandName) {
        alert('No analysis data available.');
        return;
    }

    showLoadingOverlay();

    $.ajax({
        url: `/api/reclassify-unclassified/${currentAnalysisId}?brand_name=${encodeURIComponent(brandName)}`,
        method: 'POST',
        success: function(response) {
            hideLoadingOverlay();
            
            let message = response.message;
            
            if (response.needs_image_classification > 0) {
                message += `\n\n${response.needs_image_classification} posts still need image classification. Please upload reference images for each model.`;
                
                // Show reference image section if there are posts needing image classification
                showReferenceImageSectionForBrand(brandName, response.posts_needing_images);
            }
            
            alert(message);
            
            // Update the brand data
            if (analysisData && analysisData.brands_data) {
                analysisData.brands_data[brandName] = response.updated_brand_data;
            }
            
            // Re-render the results
            renderBrandResults(analysisData.brands_data);
        },
        error: function(xhr, status, error) {
            hideLoadingOverlay();
            alert('Error reclassifying posts: ' + (xhr.responseJSON?.detail || error));
        }
    });
}

function openPostUrl() {
    const url = $(this).data('post-url');
    if (url) {
        window.open(url, '_blank');
    }
}

function downloadResults() {
    if (!currentAnalysisId) {
        alert('No analysis data available for download.');
        return;
    }

    const startDate = $('#startDateFilter').val();
    const endDate = $('#endDateFilter').val();
    
    let downloadUrl = `/api/download/${currentAnalysisId}`;
    
    if (startDate && endDate) {
        const timeFilter = {
            start_date: new Date(startDate).toISOString(),
            end_date: new Date(endDate + 'T23:59:59').toISOString()
        };
        downloadUrl += `?time_filter=${encodeURIComponent(JSON.stringify(timeFilter))}`;
    }

    // Show loading indication
    const originalText = $('#downloadBtn').text();
    $('#downloadBtn').text('Downloading...').prop('disabled', true);

    // Create a temporary anchor element for download
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.style.display = 'none';
    document.body.appendChild(link);
    
    // Trigger download
    link.click();
    
    // Cleanup
    document.body.removeChild(link);
    
    // Reset button after a delay
    setTimeout(() => {
        $('#downloadBtn').text(originalText).prop('disabled', false);
    }, 2000);
}




function addBrandConfig() {
    const brandCount = $('.brand-config').length + 1;
    const brandHtml = `
        <div class="brand-config bg-gray-50 p-4 rounded-lg mb-4">
            <div class="flex justify-between items-center mb-4">
                <h3 class="font-medium text-gray-700">Brand ${brandCount}</h3>
                <button class="remove-brand text-red-500 hover:text-red-700">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Brand Name</label>
                    <input type="text" class="brand-name w-full border rounded-lg px-3 py-2" placeholder="Enter brand name">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Instagram URL</label>
                    <input type="url" class="instagram-url w-full border rounded-lg px-3 py-2" placeholder="https://instagram.com/brand">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Facebook URL</label>
                    <input type="url" class="facebook-url w-full border rounded-lg px-3 py-2" placeholder="https://facebook.com/brand">
                </div>
            </div>
            <div class="mt-4">
                <label class="block text-sm font-medium text-gray-700 mb-1">Keywords/Models (comma separated)</label>
                <input type="text" class="keywords w-full border rounded-lg px-3 py-2" placeholder="model1, model2, model3">
                <p class="text-xs text-gray-500 mt-1">Enter vehicle models or keywords to track</p>
            </div>
        </div>
    `;
    $('#brandsContainer').append(brandHtml);
    updateReferenceImagesSection();
}

function updateReferenceImagesSection() {
    const container = $('#referenceImagesContainer');
    container.empty();
    
    $('.brand-config').each(function(index) {
        const brandName = $(this).find('.brand-name').val().trim() || `Brand ${index + 1}`;
        const keywords = $(this).find('.keywords').val().split(',').map(k => k.trim()).filter(k => k);
        
        if (keywords.length > 0) {
            let modelsHtml = '';
            keywords.forEach(model => {
                modelsHtml += createModelReferenceSection(brandName, model);
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

function createModelReferenceSection(brandName, modelName) {
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

function removeBrandConfig() {
    if ($('.brand-config').length > 1) {
        $(this).closest('.brand-config').remove();
    } else {
        alert('At least one brand configuration is required.');
    }
}


function startAnalysis() {
    // Collect brand configurations
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
        alert('Please fill in all required fields for each brand.');
        return;
    }

    // Show loading section immediately
    $('#configSection').addClass('hidden');
    $('#recentAnalysesSection').addClass('hidden');
    $('#loadingSection').removeClass('hidden');
    
    // Set initial loading state
    updateLoadingStatus({
        message: "Initializing analysis...",
        progress: 0,
        status: "starting"
    });

    // Start analysis
    $.ajax({
        url: '/api/analyze',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(brands),
        success: function(response) {
            currentAnalysisId = response.analysis_id;
            console.log('Analysis started with ID:', currentAnalysisId);
            
            // Start polling immediately with a short delay
            setTimeout(() => {
                pollAnalysisStatus();
            }, 500);
        },
        error: function(xhr, status, error) {
            console.error('Error starting analysis:', error);
            alert('Error starting analysis: ' + error);
            $('#configSection').removeClass('hidden');
            $('#recentAnalysesSection').removeClass('hidden');
            $('#loadingSection').addClass('hidden');
        }
    });
}

function showResults(data) {
    console.log('Showing results, hiding loading section');
    
    // Hide loading and show results
    $('#loadingSection').addClass('hidden');
    $('#resultsSection').removeClass('hidden');
    $('#downloadBtn').removeClass('hidden');
    
    // Show home button in header if not already visible
    $('#homeBtn').removeClass('hidden');
    
    renderBrandResults(data.brands_data);
}

function goToHome() {
    // Reset everything to initial state
    currentAnalysisId = null;
    analysisData = null;
    
    // Hide results and show config
    $('#resultsSection').addClass('hidden');
    $('#loadingSection').addClass('hidden');
    $('#referenceImageSection').addClass('hidden');
    $('#downloadBtn').addClass('hidden');
    $('#homeBtn').addClass('hidden');
    
    $('#configSection').removeClass('hidden');
    
    // Clear any existing brand configs except the first one
    $('.brand-config').not(':first').remove();
    
    // Clear the first brand config
    $('.brand-config:first input').val('');
}

function pollAnalysisStatus() {
    if (!currentAnalysisId) return;

    console.log(`Polling status for analysis: ${currentAnalysisId}`);

    $.ajax({
        url: `/api/analysis/${currentAnalysisId}`,
        method: 'GET',
        timeout: 10000,
        cache: false, // Prevent caching
        success: function(data) {
            console.log('Analysis status:', data.status, 'Progress:', data.progress, 'Message:', data.message);
            
            // Always update the UI with current data
            updateLoadingStatus(data);

            if (data.status === 'completed') {
                analysisData = data;
                showResults(data);
            } else if (data.status === 'error') {
                alert('Analysis failed: ' + data.message);
                $('#configSection').removeClass('hidden');
                $('#recentAnalysesSection').removeClass('hidden');
                $('#loadingSection').addClass('hidden');
            } else {
                // Continue polling with shorter intervals for active processing
                const pollInterval = (data.status === 'processing' || data.status === 'starting') ? 1000 : 2000;
                setTimeout(pollAnalysisStatus, pollInterval);
            }
        },
        error: function(xhr, status, error) {
            console.error('Polling error:', error, 'Status:', status);
            
            if (status === 'timeout') {
                console.log('Request timeout, retrying...');
                setTimeout(pollAnalysisStatus, 3000);
            } else {
                setTimeout(pollAnalysisStatus, 5000);
            }
        }
    });
}


function updateLoadingStatus(data) {
    const message = data.message || 'Processing...';
    const progress = Math.max(0, Math.min(100, data.progress || 0));
    
    console.log('Updating UI - Message:', message, 'Progress:', progress);
    
    $('#loadingMessage').text(message);
    
    // Smooth progress bar animation
    $('#progressBar').css({
        'width': progress + '%',
        'transition': 'width 0.5s ease-in-out'
    });
    
    $('#progressText').text(progress + '%');
    
    // Add visual feedback for different progress stages
    const progressBar = $('#progressBar');
    progressBar.removeClass('bg-blue-500 bg-yellow-500 bg-green-500');
    
    if (progress < 30) {
        progressBar.addClass('bg-blue-500');
    } else if (progress < 80) {
        progressBar.addClass('bg-yellow-500');
    } else {
        progressBar.addClass('bg-green-500');
    }
}

function showReferenceImageSection(data) {
    $('#referenceImageSection').removeClass('hidden');
    
    const container = $('#referenceImageContainer');
    container.empty();

    // Group posts by brand
    const postsByBrand = {};
    data.posts_without_text.forEach(post => {
        if (!postsByBrand[post.brand]) {
            postsByBrand[post.brand] = [];
        }
        postsByBrand[post.brand].push(post);
    });

    // Create upload sections for each brand
    Object.keys(data.brands_data).forEach(brandName => {
        if (postsByBrand[brandName]) {
            const brandSection = createReferenceImageSection(brandName, data.brands_data[brandName]);
            container.append(brandSection);
        }
    });
}

function createReferenceImageSection(brandName, brandData) {
    const keywords = Object.keys(brandData.overall_metrics?.model_breakdown || {});
    
    let keywordSections = '';
    keywords.forEach(keyword => {
        if (keyword !== 'unclassified') {
            keywordSections += `
                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 mb-2">${keyword} Reference Images</label>
                    <input type="file" class="reference-upload" data-brand="${brandName}" data-model="${keyword}" 
                           multiple accept="image/*" class="w-full border rounded-lg px-3 py-2">
                    <div class="uploaded-images mt-2 flex flex-wrap gap-2"></div>
                </div>
            `;
        }
    });

    return `
        <div class="brand-reference-section mb-6 p-4 border rounded-lg">
            <h4 class="font-semibold text-lg mb-4">${brandName}</h4>
            ${keywordSections}
        </div>
    `;
}

// Add error handling functions
function handleImageError(img, postUrl) {
    console.warn('Image failed to load:', img.src);
    img.onerror = null; // Prevent infinite loop
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'w-24 h-24 bg-red-50 border-2 border-red-200 rounded flex flex-col items-center justify-center text-xs text-red-600 p-2';
    errorDiv.innerHTML = `
        <i class="fas fa-image text-red-400 mb-1"></i>
        <span class="text-center">Image Error</span>
        ${postUrl ? '<span class="text-xs text-blue-600 underline cursor-pointer" onclick="window.open(\'' + postUrl + '\', \'_blank\')">View Post</span>' : ''}
    `;
    
    img.parentNode.replaceChild(errorDiv, img);
}

function handleGridImageError(img) {
    console.warn('Grid image failed to load:', img.src);
    img.onerror = null;
    img.className = 'w-full h-full bg-red-100 border border-red-300 flex items-center justify-center text-red-600 text-xs';
    img.style.display = 'flex';
    img.innerHTML = '✕';
    img.alt = 'Error';
}


function createImageDisplay(post) {
    const thumbnails = post.thumbnails || (post.thumbnail ? [post.thumbnail] : []);
    const postUrl = post.url || '';
    const mediaType = post.media_type || 'photo';
    
    if (thumbnails.length === 0) {
        return '<div class="w-24 h-24 bg-gray-200 rounded flex items-center justify-center text-xs text-gray-500">No Image</div>';
    }
    
    // Function to get proxied image URL
    function getProxiedImageUrl(originalUrl) {
        if (!originalUrl) return '';
        // Use image proxy for Instagram CDN URLs
        if (originalUrl.includes('cdninstagram.com') || originalUrl.includes('fbcdn.net')) {
            return `/api/image-proxy?url=${encodeURIComponent(originalUrl)}`;
        }
        return originalUrl;
    }
    
    const clickableClass = postUrl ? 'cursor-pointer hover:opacity-80 transition-opacity' : '';
    const clickHandler = postUrl ? `onclick="window.open('${postUrl}', '_blank')"` : '';
    const title = postUrl ? 'Click to view original post' : '';
    
    if (thumbnails.length === 1) {
        const proxiedUrl = getProxiedImageUrl(thumbnails[0]);
        const mediaIcon = mediaType === 'video' ? '<i class="fas fa-play absolute top-1 right-1 text-white bg-black bg-opacity-50 rounded-full p-1 text-xs"></i>' : '';
        
        return `
            <div class="relative ${clickableClass}" ${clickHandler} title="${title}">
                <img src="${proxiedUrl}" 
                     class="post-thumbnail rounded w-24 h-24 object-cover" 
                     alt="Post image" 
                     loading="lazy"
                     onerror="handleImageError(this, '${postUrl}')">
                ${mediaIcon}
            </div>
        `;
    }
    
    // Multiple images - show as grid
    let gridClass = 'image-grid w-24 h-24';
    const maxImages = Math.min(4, thumbnails.length);
    let imagesHtml = '';
    
    for (let i = 0; i < maxImages; i++) {
        const proxiedUrl = getProxiedImageUrl(thumbnails[i]);
        imagesHtml += `<img src="${proxiedUrl}" 
                           class="w-full h-full object-cover" 
                           alt="Post image ${i + 1}" 
                           loading="lazy"
                           onerror="handleGridImageError(this)">`;
    }
    
    if (thumbnails.length > 4) {
        imagesHtml += `<div class="bg-black bg-opacity-70 flex items-center justify-center text-white text-xs font-bold">+${thumbnails.length - 3}</div>`;
    }
    
    const mediaIcon = mediaType === 'video' ? '<i class="fas fa-play absolute top-1 right-1 text-white bg-black bg-opacity-50 rounded-full p-1 text-xs"></i>' : '';
    
    return `
        <div class="relative ${clickableClass}" ${clickHandler} title="${postUrl ? 'Click to view original post' : `${thumbnails.length} images`}">
            <div class="${gridClass} grid grid-cols-2 gap-0.5 rounded overflow-hidden">${imagesHtml}</div>
            ${mediaIcon}
        </div>
    `;
}

function renderBrandResults(brandsData) {
    const container = $('#brandResults');
    container.empty();

    Object.entries(brandsData).forEach(([brandName, brandData]) => {
        const brandCard = createEnhancedBrandCard(brandName, brandData);
        container.append(brandCard);
    });
    
    // Initialize tab functionality
    initializePlatformTabs();
}


function createEnhancedBrandCard(brandName, brandData) {
    const overallMetrics = brandData.overall_metrics || {};
    const instagramMetrics = brandData.instagram?.metrics || {};
    const facebookMetrics = brandData.facebook?.metrics || {};
    
    return `
        <div class="brand-card bg-white rounded-lg shadow-md mb-8" data-brand="${brandName}">
            <div class="p-6">
                <!-- Brand Header -->
                <div class="flex justify-between items-center mb-6">
                    <h3 class="text-2xl font-bold text-gray-800">${brandName}</h3>
                    <div class="flex items-center space-x-4">
                        <span class="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm">
                            ${overallMetrics.total_posts || 0} Posts
                        </span>
                        <span class="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm">
                            ${overallMetrics.total_engagement || 0} Total Engagement
                        </span>
                    </div>
                </div>

                <!-- Platform Overview -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                    <div class="bg-gradient-to-r from-purple-500 to-pink-500 text-white p-4 rounded-lg">
                        <h4 class="font-semibold mb-2">Instagram</h4>
                        <p>Followers: ${brandData.instagram?.profile?.followers || 0}</p>
                        <p>Posts: ${brandData.instagram?.posts?.length || 0}</p>
                        <p>Engagement: ${instagramMetrics.total_engagement || 0}</p>
                    </div>
                    <div class="bg-gradient-to-r from-blue-500 to-blue-600 text-white p-4 rounded-lg">
                        <h4 class="font-semibold mb-2">Facebook</h4>
                        <p>Followers: ${brandData.facebook?.profile?.followers || 0}</p>
                        <p>Posts: ${brandData.facebook?.posts?.length || 0}</p>
                        <p>Engagement: ${facebookMetrics.total_engagement || 0}</p>
                    </div>
                </div>

                <!-- Platform Tabs -->
                <div class="mb-6">
                    <div class="border-b border-gray-200">
                        <nav class="flex space-x-8">
                            <button class="platform-tab active py-2 px-1 border-b-2 border-blue-500 font-medium text-sm text-blue-600" 
                                    data-platform="overall" data-brand="${brandName}">
                                Overall
                            </button>
                            <button class="platform-tab py-2 px-1 border-b-2 border-transparent font-medium text-sm text-gray-500 hover:text-gray-700 hover:border-gray-300" 
                                    data-platform="instagram" data-brand="${brandName}">
                                Instagram
                            </button>
                            <button class="platform-tab py-2 px-1 border-b-2 border-transparent font-medium text-sm text-gray-500 hover:text-gray-700 hover:border-gray-300" 
                                    data-platform="facebook" data-brand="${brandName}">
                                Facebook
                            </button>
                        </nav>
                    </div>
                </div>

                <!-- Tab Content -->
                <div id="tabContent-${brandName}">
                    ${createPlatformTabContent(brandName, 'overall', overallMetrics, brandData)}
                    ${createPlatformTabContent(brandName, 'instagram', instagramMetrics, brandData)}
                    ${createPlatformTabContent(brandName, 'facebook', facebookMetrics, brandData)}
                </div>
            </div>
        </div>
    `;
}

function createGeneralSection(categoryData, title) {
    return `
        <div class="mb-8">
            <h4 class="text-lg font-semibold mb-4 text-gray-800">${title}</h4>
            <div class="bg-gray-50 p-4 rounded-lg border">
                <div class="grid grid-cols-2 gap-2 text-sm">
                    <p class="text-gray-600">Posts: <span class="font-medium">${categoryData.posts_count}</span></p>
                    <p class="text-gray-600">Engagement: <span class="font-medium">${categoryData.total_engagement}</span></p>
                    <p class="text-gray-600">Avg: <span class="font-medium">${Math.round(categoryData.average_engagement)}</span></p>
                    <p class="text-gray-600">Rate: <span class="font-medium">${categoryData.engagement_rate.toFixed(1)}%</span></p>
                </div>
            </div>
        </div>
    `;
}



function createPlatformTabContent(brandName, platform, metrics, brandData) {
    const isActive = platform === 'overall';
    const targetModels = metrics.target_models || {};
    const otherModels = metrics.other_models || {};
    const generalAutomotive = metrics.general_automotive || {};
    const nonAutomotive = metrics.non_automotive || {};
    const unclassified = metrics.unclassified || {};
    
    return `
        <div id="tab-${brandName}-${platform}" class="tab-content ${isActive ? '' : 'hidden'}">
            <!-- Target Model Performance Section -->
            ${Object.keys(targetModels).length > 0 ? createModelPerformanceSection(targetModels, 'Target Models') : ''}
            
            <!-- Other Models Found Section -->
            ${Object.keys(otherModels).length > 0 ? createModelPerformanceSection(otherModels, 'Other Vehicle Models Found') : ''}
            
            <!-- General Automotive Section -->
            ${generalAutomotive.posts_count > 0 ? createGeneralSection(generalAutomotive, 'General Automotive Content') : ''}
            
            <!-- Non-Automotive Section -->
            ${nonAutomotive.posts_count > 0 ? createGeneralSection(nonAutomotive, 'Non-Automotive Content') : ''}
            
            <!-- Target Model Posts -->
            ${Object.keys(targetModels).length > 0 ? createModelPostsSection(targetModels, 'Target Model Posts', brandName, platform) : ''}
            
            <!-- Other Model Posts -->
            ${Object.keys(otherModels).length > 0 ? createModelPostsSection(otherModels, 'Other Vehicle Model Posts', brandName, platform) : ''}
            
            <!-- General Automotive Posts -->
            ${generalAutomotive.posts_count > 0 ? createGeneralPostsSection(generalAutomotive, 'General Automotive Posts', brandName, platform) : ''}
            
            <!-- Unclassified Posts (Only posts with NO model content) -->
            ${unclassified.posts_count > 0 ? createUnclassifiedSection(unclassified, brandName, platform) : ''}
        </div>
    `;
}

function createGeneralPostsSection(categoryData, title, brandName, platform) {
    const posts = categoryData.posts || [];
    
    let postsHtml = '';
    posts.forEach(post => {
        const imageHtml = createImageDisplay(post);
        const reason = post.classification_reason || 'No reason provided';
        const confidence = post.classification_confidence || 0;
        
        postsHtml += `
            <div class="flex items-start space-x-3 p-3 bg-gray-50 rounded mb-3 border border-gray-200">
                <div class="flex-shrink-0">${imageHtml}</div>
                <div class="flex-1">
                    <div class="flex items-center justify-between mb-1">
                        <p class="text-sm font-medium text-gray-800">${post.platform}</p>
                        <span class="text-xs text-gray-500">${confidence}%</span>
                    </div>
                    <p class="text-xs text-gray-500 mb-2">Engagement: ${post.engagement}</p>
                    <p class="text-xs text-blue-600 mb-2">${reason}</p>
                    <p class="text-sm text-gray-700 mb-2 max-h-20 overflow-y-auto line-clamp-3">${(post.caption || post.text || 'No text content')}</p>
                    <p class="text-xs text-gray-400">${new Date(post.timestamp).toLocaleDateString()}</p>
                </div>
            </div>
        `;
    });
    
    return `
        <div class="mb-8">
            <h4 class="text-lg font-semibold mb-4 text-gray-800">${title}</h4>
            <div class="max-h-96 overflow-y-auto space-y-3">
                ${postsHtml || '<p class="text-gray-500 text-sm">No posts available</p>'}
            </div>
        </div>
    `;
}

function createUnclassifiedSection(unclassified, brandName, platform) {
    const posts = unclassified.posts || [];
    
    let postsHtml = '';
    posts.forEach(post => {
        const imageHtml = createImageDisplay(post);
        const reason = post.classification_reason || 'No classification reason';
        
        postsHtml += `
            <div class="flex items-start space-x-3 p-3 bg-yellow-50 rounded mb-3 border border-yellow-200">
                <div class="flex-shrink-0">${imageHtml}</div>
                <div class="flex-1">
                    <p class="text-sm font-medium text-yellow-800">No Model Content Found</p>
                    <p class="text-xs text-gray-600 mb-1">${post.platform}</p>
                    <p class="text-xs text-gray-500 mb-2">Engagement: ${post.engagement}</p>
                    <p class="text-xs text-yellow-600 mb-2">${reason}</p>
                    <p class="text-sm text-gray-700 mb-2 max-h-20 overflow-y-auto line-clamp-3">${(post.caption || post.text || 'No text content')}</p>
                    <p class="text-xs text-gray-400">${new Date(post.timestamp).toLocaleDateString()}</p>
                </div>
            </div>
        `;
    });
    
    return `
        <div class="mb-8">
            <h4 class="text-lg font-semibold mb-4 text-gray-800 flex items-center justify-between">
                <span><i class="fas fa-question-circle text-yellow-500 mr-2"></i>Unclassified Posts (${posts.length})</span>
                <button onclick="reclassifyBrandPosts()" data-brand="${brandName}" class="reclassify-brand text-xs bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700">
                    <i class="fas fa-redo mr-1"></i>Reclassify
                </button>
            </h4>
            <p class="text-sm text-gray-600 mb-4">These posts contain no identifiable vehicle model content.</p>
            <div class="max-h-96 overflow-y-auto space-y-3">
                ${postsHtml || '<p class="text-gray-500 text-sm">No unclassified posts</p>'}
            </div>
        </div>
    `;
}

function createUnclassifiedSection(unclassified, brandName, platform) {
    const posts = unclassified.posts || [];
    
    let postsHtml = '';
    posts.forEach(post => {
        const imageHtml = createImageDisplay(post);
        postsHtml += `
            <div class="flex items-start space-x-3 p-3 bg-yellow-50 rounded mb-3 border border-yellow-200">
                <div class="flex-shrink-0">${imageHtml}</div>
                <div class="flex-1">
                    <p class="text-sm font-medium text-yellow-800">Unclassified Post</p>
                    <p class="text-xs text-gray-600 mb-1">${post.platform}</p>
                    <p class="text-xs text-gray-500 mb-2">Engagement: ${post.engagement}</p>
                    <p class="text-sm text-gray-700 mb-2 max-h-20 overflow-y-auto line-clamp-3">${(post.caption || post.text || 'No text content')}</p>
                    <p class="text-xs text-gray-400">${new Date(post.timestamp).toLocaleDateString()}</p>
                </div>
            </div>
        `;
    });
    
    return `
        <div class="mb-8">
            <h4 class="text-lg font-semibold mb-4 text-gray-800 flex items-center justify-between">
                <span><i class="fas fa-question-circle text-yellow-500 mr-2"></i>Unclassified Posts (${posts.length})</span>
                <button onclick="reclassifyBrandPosts()" data-brand="${brandName}" class="reclassify-brand text-xs bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700">
                    <i class="fas fa-redo mr-1"></i>Reclassify
                </button>
            </h4>
            <div class="max-h-96 overflow-y-auto space-y-3">
                ${postsHtml || '<p class="text-gray-500 text-sm">No unclassified posts</p>'}
            </div>
        </div>
    `;
}

function initializePlatformTabs() {
    $(document).on('click', '.platform-tab', function() {
        const platform = $(this).data('platform');
        const brandName = $(this).data('brand');
        
        // Update tab styles
        $(this).closest('.brand-card').find('.platform-tab').removeClass('active border-blue-500 text-blue-600')
            .addClass('border-transparent text-gray-500');
        
        $(this).addClass('active border-blue-500 text-blue-600')
            .removeClass('border-transparent text-gray-500');
        
        // Show/hide content
        $(this).closest('.brand-card').find('.tab-content').addClass('hidden');
        $(`#tab-${brandName}-${platform}`).removeClass('hidden');
    });
}

function createModelPostsSection(models, title, brandName, platform) {
    if (Object.keys(models).length === 0) return '';
    
    let modelsContent = '';
    Object.entries(models).forEach(([model, stats]) => {
        const posts = stats.posts || [];
        
        let postsHtml = '';
        posts.forEach(post => {
            const imageHtml = createImageDisplay(post);
            const confidence = post.classification_confidence;
            const reason = post.classification_reason || 'No classification reason';
            
            // Color code by confidence
            let confidenceClass = 'text-gray-500';
            let confidenceIcon = 'fa-question';
            if (confidence >= 80) {
                confidenceClass = 'text-green-600';
                confidenceIcon = 'fa-check-circle';
            } else if (confidence >= 50) {
                confidenceClass = 'text-yellow-600'; 
                confidenceIcon = 'fa-exclamation-circle';
            } else {
                confidenceClass = 'text-red-600';
                confidenceIcon = 'fa-times-circle';
            }
            
            postsHtml += `
                <div class="flex items-start space-x-3 p-3 bg-blue-50 rounded mb-3 border border-blue-200">
                    <div class="flex-shrink-0">${imageHtml}</div>
                    <div class="flex-1">
                        <div class="flex items-center justify-between mb-1">
                            <p class="text-sm font-medium text-blue-800">${post.platform}</p>
                            <div class="flex items-center space-x-1 text-xs ${confidenceClass}">
                                <i class="fas ${confidenceIcon}"></i>
                                <span>${confidence}%</span>
                            </div>
                        </div>
                        <p class="text-xs text-gray-500 mb-1">Engagement: ${post.engagement}</p>
                        <p class="text-xs text-gray-400 mb-2" title="${reason}">${reason.substring(0, 80)}${reason.length > 80 ? '...' : ''}</p>
                        <p class="text-sm text-gray-700 mb-2 max-h-20 overflow-y-auto line-clamp-3">${(post.caption || post.text || 'No text content')}</p>
                        <p class="text-xs text-gray-400">${new Date(post.timestamp).toLocaleDateString()}</p>
                    </div>
                </div>
            `;
        });
        
        modelsContent += `
            <div class="mb-6">
                <h5 class="font-medium text-gray-800 mb-3 flex items-center">
                    <i class="fas fa-car mr-2 text-blue-500"></i>${model} 
                    <span class="ml-2 text-sm text-gray-500">(${posts.length} posts, ${stats.total_engagement} engagement)</span>
                </h5>
                <div class="max-h-96 overflow-y-auto space-y-3">
                    ${postsHtml || '<p class="text-gray-500 text-sm">No posts available</p>'}
                </div>
            </div>
        `;
    });
    
    return `
        <div class="mb-8">
            <h4 class="text-lg font-semibold mb-4 text-gray-800">${title}</h4>
            ${modelsContent}
        </div>
    `;
}


function createModelPerformanceSection(models, title) {
    if (Object.keys(models).length === 0) return '';
    
    let modelStats = '';
    Object.entries(models).forEach(([model, stats]) => {
        modelStats += `
            <div class="bg-gray-50 p-4 rounded-lg border">
                <h5 class="font-medium text-gray-800 mb-2">${model}</h5>
                <div class="grid grid-cols-2 gap-2 text-sm">
                    <p class="text-gray-600">Posts: <span class="font-medium">${stats.posts_count}</span></p>
                    <p class="text-gray-600">Engagement: <span class="font-medium">${stats.total_engagement}</span></p>
                    <p class="text-gray-600">Avg: <span class="font-medium">${Math.round(stats.average_engagement)}</span></p>
                    <p class="text-gray-600">Rate: <span class="font-medium">${stats.engagement_rate.toFixed(1)}%</span></p>
                </div>
            </div>
        `;
    });
    
    return `
        <div class="mb-8">
            <h4 class="text-lg font-semibold mb-4 text-gray-800">${title}</h4>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                ${modelStats}
            </div>
        </div>
    `;
}

function createEnhancedBrandResultCard(brandName, brandData) {
    const overallMetrics = brandData.overall_metrics || {};
    const modelBreakdown = overallMetrics.model_breakdown || {};
    
    // Get all posts
    const allPosts = [...(brandData.instagram?.posts || []), ...(brandData.facebook?.posts || [])];
    
    // Categorize posts
    const modelPosts = {};
    const unclassifiedPosts = [];
    const needsImageClassification = [];
    const alternativelyLabeled = [];
    
    allPosts.forEach(post => {
        const model = post.model || '';
        const reason = post.classification_reason || '';
        
        if (model === 'needs_image_classification') {
            needsImageClassification.push(post);
        } else if (['unclassified', ''].includes(model.toLowerCase())) {
            unclassifiedPosts.push(post);
        } else if (!brandData.keywords?.includes(model)) {
            // Posts labeled with alternative categories
            alternativelyLabeled.push(post);
        } else {
            // Posts classified with target models
            if (!modelPosts[model]) modelPosts[model] = [];
            modelPosts[model].push(post);
        }
    });
    
    // Create sections HTML
    let sectionsHtml = '';
    
    // Model breakdown section
    let modelStats = '';
    Object.entries(modelBreakdown).forEach(([model, stats]) => {
        modelStats += `
            <div class="bg-gray-50 p-3 rounded">
                <h5 class="font-medium text-gray-800">${model}</h5>
                <p class="text-sm text-gray-600">Posts: ${stats.posts_count}</p>
                <p class="text-sm text-gray-600">Engagement: ${stats.total_engagement}</p>
                <p class="text-sm text-gray-600">Avg: ${Math.round(stats.average_engagement)}</p>
            </div>
        `;
    });
    
    // Alternative labels section
    if (alternativelyLabeled.length > 0) {
        let alternativeHtml = '';
        alternativelyLabeled.forEach(post => {
            const imageHtml = createImageDisplay(post);
            alternativeHtml += `
                <div class="flex items-start space-x-3 p-3 bg-blue-50 rounded mb-3 border border-blue-200">
                    <div class="flex-shrink-0">${imageHtml}</div>
                    <div class="flex-1">
                        <p class="text-sm font-medium text-blue-800">${post.model}</p>
                        <p class="text-xs text-gray-600 mb-1">${post.platform}</p>
                        <p class="text-xs text-gray-500 mb-2">Engagement: ${post.engagement}</p>
                        <p class="text-xs text-gray-400 mb-1">${post.classification_reason}</p>
                        <p class="text-sm text-gray-700 mb-2 max-h-20 overflow-y-auto">${(post.caption || post.text || 'No text content')}</p>
                    </div>
                </div>
            `;
        });
        
        sectionsHtml += `
            <div class="mb-6">
                <h4 class="text-lg font-semibold mb-4 text-gray-800 flex items-center">
                    <i class="fas fa-tags text-blue-500 mr-2"></i>Alternative Categories (${alternativelyLabeled.length})
                </h4>
                <div class="space-y-3 max-h-64 overflow-y-auto">${alternativeHtml}</div>
            </div>
        `;
    }
    
    // Needs image classification section
    if (needsImageClassification.length > 0) {
        let imageNeededHtml = '';
        needsImageClassification.forEach(post => {
            const imageHtml = createImageDisplay(post);
            imageNeededHtml += `
                <div class="flex items-start space-x-3 p-3 bg-orange-50 rounded mb-3 border border-orange-200">
                    <div class="flex-shrink-0">${imageHtml}</div>
                    <div class="flex-1">
                        <p class="text-sm font-medium text-orange-800">Needs Image Analysis</p>
                        <p class="text-xs text-gray-600 mb-1">${post.platform}</p>
                        <p class="text-xs text-gray-500 mb-2">Engagement: ${post.engagement}</p>
                        <p class="text-xs text-orange-600 mb-2">${post.classification_reason}</p>
                    </div>
                </div>
            `;
        });
        
        sectionsHtml += `
            <div class="mb-6">
                <h4 class="text-lg font-semibold mb-4 text-gray-800 flex items-center justify-between">
                    <span><i class="fas fa-camera text-orange-500 mr-2"></i>Needs Image Classification (${needsImageClassification.length})</span>
                    <button onclick="showImageClassificationSection('${brandName}')" class="text-xs bg-orange-600 text-white px-3 py-1 rounded hover:bg-orange-700">
                        <i class="fas fa-upload mr-1"></i>Upload References
                    </button>
                </h4>
                <div class="space-y-3 max-h-64 overflow-y-auto">${imageNeededHtml}</div>
            </div>
        `;
    }
    
    // Return the complete brand card with all sections
    return `
        <div class="brand-card bg-white rounded-lg shadow-md p-6 mb-8">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-2xl font-bold text-gray-800">${brandName}</h3>
                <div class="flex items-center space-x-4">
                    <span class="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm">
                        ${overallMetrics.total_posts || 0} Posts
                    </span>
                    <span class="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm">
                        ${overallMetrics.total_engagement || 0} Total Engagement
                    </span>
                </div>
            </div>
            
            <!-- Platform Overview -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                <div class="bg-gradient-to-r from-purple-500 to-pink-500 text-white p-4 rounded-lg">
                    <h4 class="font-semibold mb-2">Instagram</h4>
                    <p>Followers: ${brandData.instagram?.profile?.followers || 0}</p>
                    <p>Posts: ${brandData.instagram?.posts?.length || 0}</p>
                    <p>Engagement: ${brandData.instagram?.metrics?.total_engagement || 0}</p>
                </div>
                <div class="bg-gradient-to-r from-blue-500 to-blue-600 text-white p-4 rounded-lg">
                    <h4 class="font-semibold mb-2">Facebook</h4>
                    <p>Followers: ${brandData.facebook?.profile?.followers || 0}</p>
                    <p>Posts: ${brandData.facebook?.posts?.length || 0}</p>
                    <p>Engagement: ${brandData.facebook?.metrics?.total_engagement || 0}</p>
                </div>
            </div>

            <!-- Model Breakdown -->
            <div class="mb-8">
                <h4 class="text-lg font-semibold mb-4 text-gray-800">Model Performance</h4>
                <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
                    ${modelStats}
                </div>
            </div>

            <!-- All classification sections -->
            ${sectionsHtml}
        </div>
    `;
}

function createBrandResultCard(brandName, brandData) {
    const overallMetrics = brandData.overall_metrics || {};
    const modelBreakdown = overallMetrics.model_breakdown || {};
    
    let modelStats = '';
    Object.entries(modelBreakdown).forEach(([model, stats]) => {
        modelStats += `
            <div class="bg-gray-50 p-3 rounded">
                <h5 class="font-medium text-gray-800">${model}</h5>
                <p class="text-sm text-gray-600">Posts: ${stats.posts_count}</p>
                <p class="text-sm text-gray-600">Engagement: ${stats.total_engagement}</p>
                <p class="text-sm text-gray-600">Avg: ${Math.round(stats.average_engagement)}</p>
            </div>
        `;
    });

    const topPosts = brandData.top_posts || [];
    const lowPosts = brandData.low_posts || [];

    let topPostsHtml = '';
    topPosts.forEach(post => {
        const imageHtml = createImageDisplay(post);
        topPostsHtml += `
            <div class="flex items-start space-x-3 p-3 bg-green-50 rounded">
                <div class="flex-shrink-0">
                    ${imageHtml}
                </div>
                <div class="flex-1">
                    <p class="text-sm font-medium">${post.model || 'Unclassified'}</p>
                    <p class="text-xs text-gray-600">${post.platform}</p>
                    <p class="text-xs text-gray-500">Engagement: ${post.engagement}</p>
                    <p class="text-xs text-gray-400 line-clamp-2">${(post.caption || post.text || '').substring(0, 100)}...</p>
                </div>
            </div>
        `;
    });

    let lowPostsHtml = '';
    lowPosts.forEach(post => {
        const imageHtml = createImageDisplay(post);
        lowPostsHtml += `
            <div class="flex items-start space-x-3 p-3 bg-red-50 rounded">
                <div class="flex-shrink-0">
                    ${imageHtml}
                </div>
                <div class="flex-1">
                    <p class="text-sm font-medium">${post.model || 'Unclassified'}</p>
                    <p class="text-xs text-gray-600">${post.platform}</p>
                    <p class="text-xs text-gray-500">Engagement: ${post.engagement}</p>
                    <p class="text-xs text-gray-400 line-clamp-2">${(post.caption || post.text || '').substring(0, 100)}...</p>
                </div>
            </div>
        `;
    });

    // Get unclassified posts - FIXED: Check for both undefined and 'unclassified' string
    const allPosts = [...(brandData.instagram?.posts || []), ...(brandData.facebook?.posts || [])];
    const unclassifiedPosts = allPosts.filter(post => {
        const model = post.model || '';
        return model === '' || model.toLowerCase() === 'unclassified' || !model;
    });
    
    console.log(`${brandName}: Found ${unclassifiedPosts.length} unclassified posts out of ${allPosts.length} total posts`);
    
    // Enhanced unclassified posts section
    let unclassifiedPostsHtml = '';
    unclassifiedPosts.forEach(post => {
        const imageHtml = createImageDisplay(post);
        const hasUrl = post.url && post.url !== '';
        
        unclassifiedPostsHtml += `
            <div class="flex items-start space-x-3 p-3 bg-yellow-50 rounded mb-3 border border-yellow-200">
                <div class="flex-shrink-0">
                    ${hasUrl ? `<div class="post-thumbnail cursor-pointer" data-post-url="${post.url}" title="Click to view original post">` : '<div>'}
                        ${imageHtml}
                    ${hasUrl ? '</div>' : '</div>'}
                </div>
                <div class="flex-1">
                    <p class="text-sm font-medium text-yellow-800">Unclassified Post</p>
                    <p class="text-xs text-gray-600 mb-1">${post.platform}</p>
                    <p class="text-xs text-gray-500 mb-2">Engagement: ${post.engagement}</p>
                    <p class="text-sm text-gray-700 mb-2 max-h-20 overflow-y-auto">${(post.caption || post.text || 'No text content')}</p>
                    ${hasUrl ? `<a href="${post.url}" target="_blank" class="text-xs text-blue-600 hover:underline">View Original Post</a>` : ''}
                </div>
            </div>
        `;
    });

    // Add reclassify button with brand data
    const reclassifyButtonHtml = `
        <button onclick="reclassifyBrandPosts()" data-brand="${brandName}" class="reclassify-brand text-xs bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700">
            <i class="fas fa-redo mr-1"></i>Reclassify
        </button>
    `;

    return `
        <div class="brand-card bg-white rounded-lg shadow-md p-6 mb-8">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-2xl font-bold text-gray-800">${brandName}</h3>
                <div class="flex items-center space-x-4">
                    <span class="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm">
                        ${overallMetrics.total_posts || 0} Posts
                    </span>
                    <span class="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm">
                        ${overallMetrics.total_engagement || 0} Total Engagement
                    </span>
                </div>
            </div>

            <!-- Platform Overview -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                <div class="bg-gradient-to-r from-purple-500 to-pink-500 text-white p-4 rounded-lg">
                    <h4 class="font-semibold mb-2">Instagram</h4>
                    <p>Followers: ${brandData.instagram?.profile?.followers || 0}</p>
                    <p>Posts: ${brandData.instagram?.posts?.length || 0}</p>
                    <p>Engagement: ${brandData.instagram?.metrics?.total_engagement || 0}</p>
                </div>
                <div class="bg-gradient-to-r from-blue-500 to-blue-600 text-white p-4 rounded-lg">
                    <h4 class="font-semibold mb-2">Facebook</h4>
                    <p>Followers: ${brandData.facebook?.profile?.followers || 0}</p>
                    <p>Posts: ${brandData.facebook?.posts?.length || 0}</p>
                    <p>Engagement: ${brandData.facebook?.metrics?.total_engagement || 0}</p>
                </div>
            </div>

            <!-- Model Breakdown -->
            <div class="mb-8">
                <h4 class="text-lg font-semibold mb-4 text-gray-800">Model Performance</h4>
                <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
                    ${modelStats}
                </div>
            </div>

            <!-- Top, Low, and Unclassified Posts -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div>
                    <h4 class="text-lg font-semibold mb-4 text-gray-800 flex items-center">
                        <i class="fas fa-trophy text-yellow-500 mr-2"></i>Top Performing Posts
                    </h4>
                    <div class="space-y-3">
                        ${topPostsHtml || '<p class="text-gray-500">No posts available</p>'}
                    </div>
                </div>
                <div>
                    <h4 class="text-lg font-semibold mb-4 text-gray-800 flex items-center">
                        <i class="fas fa-chart-line-down text-red-500 mr-2"></i>Low Performing Posts
                    </h4>
                    <div class="space-y-3">
                        ${lowPostsHtml || '<p class="text-gray-500">No posts available</p>'}
                    </div>
                </div>
                <div>
                    <h4 class="text-lg font-semibold mb-4 text-gray-800 flex items-center justify-between">
                        <span><i class="fas fa-question-circle text-yellow-500 mr-2"></i>Unclassified Posts</span>
                        <button onclick="reclassifyPosts('${brandName}')" class="text-xs bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700">
                            <i class="fas fa-redo mr-1"></i>Reclassify
                        </button>
                    </h4>
                    <div class="space-y-3 max-h-96 overflow-y-auto">
                        ${unclassifiedPostsHtml || '<p class="text-gray-500">No unclassified posts</p>'}
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Carousel functionality
function changeCarousel(carouselId, direction) {
    const container = document.getElementById(carouselId);
    const images = container.querySelectorAll('.carousel-image');
    const dots = container.querySelectorAll('.dot');
    
    let currentIndex = 0;
    images.forEach((img, index) => {
        if (img.classList.contains('active')) {
            currentIndex = index;
        }
    });
    
    images[currentIndex].classList.remove('active');
    dots[currentIndex].classList.remove('active');
    
    currentIndex += direction;
    if (currentIndex >= images.length) currentIndex = 0;
    if (currentIndex < 0) currentIndex = images.length - 1;
    
    images[currentIndex].classList.add('active');
    dots[currentIndex].classList.add('active');
}

function currentCarousel(carouselId, index) {
    const container = document.getElementById(carouselId);
    const images = container.querySelectorAll('.carousel-image');
    const dots = container.querySelectorAll('.dot');
    
    images.forEach(img => img.classList.remove('active'));
    dots.forEach(dot => dot.classList.remove('active'));
    
    images[index].classList.add('active');
    dots[index].classList.add('active');
}

function reclassifyPosts(brandName) {
    if (!currentAnalysisId) {
        alert('No analysis data available.');
        return;
    }

    showLoadingOverlay();

    $.ajax({
        url: `/api/reclassify-unclassified/${currentAnalysisId}?brand_name=${encodeURIComponent(brandName)}`,
        method: 'POST',
        success: function(response) {
            hideLoadingOverlay();
            alert(response.message);
            
            // Update the brand data in our local storage
            if (analysisData && analysisData.brands_data) {
                analysisData.brands_data[brandName] = response.updated_brand_data;
            }
            
            // Re-render the results
            renderBrandResults(analysisData.brands_data);
        },
        error: function(xhr, status, error) {
            hideLoadingOverlay();
            alert('Error reclassifying posts: ' + (xhr.responseJSON?.detail || error));
        }
    });
}


function applyTimeFilter() {
    const startDate = $('#startDateFilter').val();
    const endDate = $('#endDateFilter').val();

    if (!startDate || !endDate) {
        alert('Please select both start and end dates.');
        return;
    }

    if (new Date(startDate) > new Date(endDate)) {
        alert('Start date must be before end date.');
        return;
    }

    if (!currentAnalysisId) {
        alert('No analysis data available.');
        return;
    }

    showLoadingOverlay();

    const timeFilter = {
        start_date: new Date(startDate + 'T00:00:00').toISOString(),
        end_date: new Date(endDate + 'T23:59:59').toISOString()
    };

    $.ajax({
        url: `/api/filter-results/${currentAnalysisId}`,
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(timeFilter),
        success: function(response) {
            hideLoadingOverlay();
            console.log('Filter applied successfully:', response);
            
            // Update the displayed results with filtered data
            renderBrandResults(response.filtered_results);
            
            // Show success message
            showToast('Time filter applied successfully', 'success');
        },
        error: function(xhr, status, error) {
            hideLoadingOverlay();
            console.error('Error applying filter:', error);
            alert('Error applying filter: ' + (xhr.responseJSON?.detail || error));
        }
    });
}

// Add toast notification function
function showToast(message, type = 'info') {
    const toastColors = {
        'success': 'bg-green-500',
        'error': 'bg-red-500',
        'info': 'bg-blue-500',
        'warning': 'bg-yellow-500'
    };
    
    const toast = $(`
        <div class="toast ${toastColors[type]} text-white px-4 py-2 rounded-lg shadow-lg flex items-center space-x-2">
            <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'times' : 'info'}-circle"></i>
            <span>${message}</span>
        </div>
    `);
    
    $('#toastContainer').append(toast);
    
    setTimeout(() => {
        toast.addClass('toast-exit');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function downloadResults() {
    if (!currentAnalysisId) {
        alert('No analysis data available for download.');
        return;
    }

    const startDate = $('#startDateFilter').val();
    const endDate = $('#endDateFilter').val();
    
    let downloadUrl = `/api/download/${currentAnalysisId}`;
    
    if (startDate && endDate) {
        const timeFilter = {
            start_date: new Date(startDate).toISOString(),
            end_date: new Date(endDate + 'T23:59:59').toISOString()
        };
        downloadUrl += `?time_filter=${encodeURIComponent(JSON.stringify(timeFilter))}`;
    }

    // Create temporary download link
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = `social_media_analysis_${currentAnalysisId}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function classifyByImages() {
    if (!currentAnalysisId) {
        alert('No analysis data available.');
        return;
    }

    // Collect uploaded reference images
    const referenceImages = {};
    $('.reference-upload').each(function() {
        const brand = $(this).data('brand');
        const model = $(this).data('model');
        const files = this.files;

        if (files.length > 0) {
            if (!referenceImages[brand]) {
                referenceImages[brand] = {};
            }
            referenceImages[brand][model] = Array.from(files);
        }
    });

    if (Object.keys(referenceImages).length === 0) {
        alert('Please upload at least one reference image for each model.');
        return;
    }

    showLoadingOverlay();

    // Upload reference images first
    const uploadPromises = [];
    
    Object.entries(referenceImages).forEach(([brand, models]) => {
        Object.entries(models).forEach(([model, files]) => {
            const formData = new FormData();
            formData.append('brand', brand);
            formData.append('model', model);
            
            files.forEach(file => {
                formData.append('files', file);
            });

            const promise = $.ajax({
                url: `/api/upload-reference-images/${currentAnalysisId}`,
                method: 'POST',
                data: formData,
                processData: false,
                contentType: false
            });
            uploadPromises.push(promise);
        });
    });

    Promise.all(uploadPromises).then(() => {
        // Start image classification
        return $.ajax({
            url: `/api/classify-images/${currentAnalysisId}`,
            method: 'POST'
        });
    }).then((response) => {
        hideLoadingOverlay();
        $('#referenceImageSection').addClass('hidden');
        
        // Refresh analysis data
        return $.ajax({
            url: `/api/analysis/${currentAnalysisId}`,
            method: 'GET'
        });
    }).then((updatedData) => {
        analysisData = updatedData;
        renderBrandResults(updatedData.brands_data);
        alert('Image classification completed successfully!');
    }).catch((error) => {
        hideLoadingOverlay();
        alert('Error during image classification: ' + (error.responseText || error.message));
    });
}

function showLoadingOverlay() {
    $('#loadingOverlay').removeClass('hidden');
}

function hideLoadingOverlay() {
    $('#loadingOverlay').addClass('hidden');
}
// Update keywords input event listener
$(document).on('input', '.keywords', function() {
    updateReferenceImagesSection();
});

$(document).on('input', '.brand-name', function() {
    updateReferenceImagesSection();
});

// Handle reference image uploads
$(document).on('change', '.reference-image-input', function() {
    const files = Array.from(this.files);
    const brand = $(this).data('brand');
    const model = $(this).data('model');
    const previewContainer = $(`#preview-${this.id}`);
    
    // Limit to 3 images
    if (files.length > 3) {
        alert('Maximum 3 images allowed per model');
        this.value = '';
        return;
    }
    
    // Clear previous previews
    previewContainer.empty();
    
    // Create previews
    files.forEach((file, index) => {
        if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = function(e) {
                const preview = $(`
                    <div class="relative">
                        <img src="${e.target.result}" 
                             class="w-20 h-20 object-cover rounded border">
                        <button type="button" 
                                class="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs"
                                onclick="removeImagePreview(this)">×</button>
                    </div>
                `);
                previewContainer.append(preview);
            };
            reader.readAsDataURL(file);
        }
    });
});


function startAnalysisWithReferences() {
    // Collect brand configurations
    const brands = {};
    const referenceImages = {};
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

        // Collect reference images for this brand
        referenceImages[brandName] = {};
        keywords.forEach(model => {
            const inputElement = $(`.reference-image-input[data-brand="${brandName}"][data-model="${model}"]`)[0];
            if (inputElement && inputElement.files.length > 0) {
                referenceImages[brandName][model] = Array.from(inputElement.files);
            }
        });
    });

    if (hasError) {
        alert('Please fill in all required fields for each brand.');
        return;
    }

    // Show loading section
    $('#configSection').addClass('hidden');
    $('#referenceImagesSection').addClass('hidden');
    $('#loadingSection').removeClass('hidden');
    
    updateLoadingStatus({
        message: "Uploading reference images and initializing analysis...",
        progress: 0,
        status: "starting"
    });

    // Upload reference images and start analysis
    uploadReferenceImagesAndAnalyze(brands, referenceImages);
}


async function uploadReferenceImagesAndAnalyze(brands, referenceImages) {
    try {
        // Generate a proper temporary ID
        const tempId = 'ref-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
        const uploadedImagePaths = {};

        updateLoadingStatus({
            message: "Uploading reference images...",
            progress: 10,
            status: "uploading"
        });

        // Upload reference images first
        let uploadProgress = 10;
        const totalBrands = Object.keys(referenceImages).length;
        let processedBrands = 0;

        for (const [brandName, models] of Object.entries(referenceImages)) {
            uploadedImagePaths[brandName] = {};
            
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
                        const response = await $.ajax({
                            url: '/api/upload-reference-images',
                            method: 'POST',
                            data: formData,
                            processData: false,
                            contentType: false
                        });
                        
                        uploadedImagePaths[brandName][modelName] = response.paths;
                        console.log(`Uploaded images for ${brandName} - ${modelName}:`, response.paths);
                    } catch (error) {
                        console.error(`Error uploading images for ${brandName} - ${modelName}:`, error);
                        alert(`Failed to upload images for ${brandName} - ${modelName}: ${error.message}`);
                    }
                }
            }
            
            processedBrands++;
            uploadProgress = 10 + (processedBrands / totalBrands) * 20;
            updateLoadingStatus({
                message: `Uploaded images for ${brandName}...`,
                progress: uploadProgress,
                status: "uploading"
            });
        }

        updateLoadingStatus({
            message: "Starting analysis with vision AI...",
            progress: 30,
            status: "starting"
        });

        // Start analysis with reference images
        const analysisResponse = await $.ajax({
            url: '/api/analyze-with-references',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                brands_config: brands,
                reference_images: uploadedImagePaths
            })
        });

        currentAnalysisId = analysisResponse.analysis_id;
        console.log('Analysis with references started:', currentAnalysisId);
        
        // Start polling
        setTimeout(() => {
            pollAnalysisStatus();
        }, 1000);

    } catch (error) {
        console.error('Error starting analysis with references:', error);
        let errorMessage = 'Error starting analysis: ';
        if (error.responseJSON && error.responseJSON.detail) {
            errorMessage += error.responseJSON.detail;
        } else {
            errorMessage += error.message || 'Unknown error';
        }
        
        alert(errorMessage);
        $('#configSection').removeClass('hidden');
        $('#referenceImagesSection').removeClass('hidden');
        $('#loadingSection').addClass('hidden');
    }
}

function generateTempAnalysisId() {
    return 'temp-' + Math.random().toString(36).substr(2, 9);
}

// Update the start analysis button to use the new function
$('#startAnalysisBtn').off('click').on('click', startAnalysisWithReferences);


function removeImagePreview(button) {
    $(button).closest('.relative').remove();
}

// Handle file upload previews
$(document).on('change', '.reference-upload', function() {
    const container = $(this).siblings('.uploaded-images');
    container.empty();
    
    Array.from(this.files).forEach(file => {
        if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = function(e) {
                container.append(`
                    <img src="${e.target.result}" class="w-16 h-16 object-cover rounded border">
                `);
            };
            reader.readAsDataURL(file);
        }
    });
});