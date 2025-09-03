// UI Helper Class
class UI {
    static showLoadingOverlay() {
        $('#loadingOverlay').removeClass('hidden');
    }
    
    static hideLoadingOverlay() {
        $('#loadingOverlay').addClass('hidden');
    }
    
    static updateLoadingStatus(data) {
        const message = data.message || 'Processing...';
        const progress = Math.max(0, Math.min(100, data.progress || 0));
        
        console.log('Updating UI - Message:', message, 'Progress:', progress);
        
        $('#loadingMessage').text(message);
        
        $('#progressBar').css({
            'width': progress + '%',
            'transition': 'width 0.5s ease-in-out'
        });
        
        $('#progressText').text(progress + '%');
        
        // Color coding for progress
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
    
    static showToast(message, type = 'info') {
        const toastColors = {
            'success': 'bg-green-500',
            'error': 'bg-red-500',
            'info': 'bg-blue-500',
            'warning': 'bg-yellow-500'
        };
        
        const iconTypes = {
            'success': 'fa-check-circle',
            'error': 'fa-times-circle',
            'info': 'fa-info-circle',
            'warning': 'fa-exclamation-triangle'
        };
        
        const toast = $(`
            <div class="toast ${toastColors[type]} text-white px-4 py-3 rounded-lg shadow-lg flex items-center space-x-3 min-w-72">
                <i class="fas ${iconTypes[type]} text-lg"></i>
                <span class="flex-1">${message}</span>
                <button class="text-white hover:text-gray-200 ml-2" onclick="$(this).parent().addClass('toast-exit')">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `);
        
        $('#toastContainer').append(toast);
        
        setTimeout(() => {
            toast.addClass('toast-exit');
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    }
    
    static displayAnalysesHistory(analyses) {
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
    }
    
    static renderBrandResults(brandsData) {
        console.log('Rendering brand results:', brandsData);
        const container = $('#brandResults');
        container.empty(); // Always clear and rebuild for consistency
        
        if (!brandsData || Object.keys(brandsData).length === 0) {
            container.html('<div class="text-center py-8 text-gray-500">No brand data available</div>');
            return;
        }

        Object.entries(brandsData).forEach(([brandName, brandData]) => {
            console.log(`Creating card for brand: ${brandName}`, brandData);
            const brandCard = this.createBrandCard(brandName, brandData);
            container.append(brandCard);
        });
        
        // Add fade-in animation
        $('.brand-card').addClass('fade-in');
    }
    
    // Remove the complex updateBrandMetrics function as it was causing issues
    // The simple rebuild approach is more reliable
    
    static createBrandCard(brandName, brandData) {
        const overallMetrics = brandData.overall_metrics || {};
        const modelBreakdown = overallMetrics.model_breakdown || {};
        
        // Create model breakdown stats
        let modelStats = '';
        Object.entries(modelBreakdown).forEach(([model, stats]) => {
            const confidenceClass = stats.posts_count > 5 ? 'confidence-high' : 
                                   stats.posts_count > 2 ? 'confidence-medium' : 'confidence-low';
            
            modelStats += `
                <div class="bg-gray-50 p-4 rounded-lg border hover:shadow-md transition-shadow">
                    <h5 class="font-medium text-gray-800 mb-2 flex items-center">
                        <i class="fas fa-car mr-2 text-blue-500"></i>${model}
                    </h5>
                    <div class="space-y-1 text-sm">
                        <p class="text-gray-600">Posts: <span class="font-medium text-gray-800">${stats.posts_count}</span></p>
                        <p class="text-gray-600">Engagement: <span class="font-medium text-gray-800">${stats.total_engagement.toLocaleString()}</span></p>
                        <p class="text-gray-600">Avg: <span class="font-medium text-gray-800">${Math.round(stats.average_engagement).toLocaleString()}</span></p>
                        <div class="flex items-center justify-between">
                            <span class="text-xs text-gray-500">Rate:</span>
                            <span class="text-xs font-medium px-2 py-1 rounded ${confidenceClass}">
                                ${stats.engagement_rate.toFixed(1)}%
                            </span>
                        </div>
                    </div>
                </div>
            `;
        });

        // Create top and low performing posts
        const topPosts = this.createPostsList(brandData.top_posts || [], 'Top Performing Posts', 'fa-trophy text-yellow-500');
        const lowPosts = this.createPostsList(brandData.low_posts || [], 'Low Performing Posts', 'fa-chart-line-down text-red-500');
        
        // Create all posts breakdown by model
        const allPosts = [...(brandData.instagram?.posts || []), ...(brandData.facebook?.posts || [])];
        const postsByModel = this.createPostsByModel(allPosts, Object.keys(modelBreakdown));

        return `
            <div class="brand-card bg-white rounded-lg shadow-md p-6 mb-8 fade-in">
                <!-- Brand Header -->
                <div class="flex justify-between items-center mb-6">
                    <h3 class="text-2xl font-bold text-gray-800">${brandName}</h3>
                    <div class="flex items-center space-x-4">
                        <span class="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
                            ${overallMetrics.total_posts || 0} Posts
                        </span>
                        <span class="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-medium">
                            ${(overallMetrics.total_engagement || 0).toLocaleString()} Engagement
                        </span>
                    </div>
                </div>

                <!-- Platform Overview -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                    <div class="metric-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                        <h4>Instagram</h4>
                        <div class="metric-value">${(brandData.instagram?.profile?.followers || 0).toLocaleString()}</div>
                        <div class="metric-change">
                            ${brandData.instagram?.posts?.length || 0} posts • 
                            ${(brandData.instagram?.metrics?.total_engagement || 0).toLocaleString()} engagement
                        </div>
                    </div>
                    <div class="metric-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                        <h4>Facebook</h4>
                        <div class="metric-value">${(brandData.facebook?.profile?.followers || 0).toLocaleString()}</div>
                        <div class="metric-change">
                            ${brandData.facebook?.posts?.length || 0} posts • 
                            ${(brandData.facebook?.metrics?.total_engagement || 0).toLocaleString()} engagement
                        </div>
                    </div>
                </div>

                <!-- Model Performance -->
                <div class="mb-8">
                    <h4 class="text-lg font-semibold mb-4 text-gray-800 flex items-center">
                        <i class="fas fa-chart-bar mr-2 text-blue-600"></i>Model Performance
                    </h4>
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        ${modelStats || '<p class="text-gray-500 col-span-full text-center py-4">No model data available</p>'}
                    </div>
                </div>

                <!-- Posts Analysis -->
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
                    ${topPosts}
                    ${lowPosts}
                </div>

                <!-- Posts by Model -->
                ${postsByModel}
            </div>
        `;
    }
    
    static createPostsList(posts, title, iconClass) {
        if (!posts || posts.length === 0) {
            return `
                <div>
                    <h4 class="text-lg font-semibold mb-4 text-gray-800 flex items-center">
                        <i class="fas ${iconClass} mr-2"></i>${title}
                    </h4>
                    <p class="text-gray-500 text-center py-8">No posts available</p>
                </div>
            `;
        }

        let postsHtml = '';
        posts.forEach(post => {
            const imageHtml = this.createImageDisplay(post);
            const platformBadge = `<span class="platform-badge platform-${post.platform}">${post.platform}</span>`;
            const modelBadge = post.model ? `<span class="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded">${post.model}</span>` : '';
            
            postsHtml += `
                <div class="bg-gray-50 rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div class="flex items-start space-x-3">
                        <div class="flex-shrink-0">
                            ${imageHtml}
                        </div>
                        <div class="flex-1 min-w-0">
                            <div class="flex items-center justify-between mb-2">
                                ${platformBadge}
                                <span class="text-sm font-semibold text-green-600">${post.engagement.toLocaleString()}</span>
                            </div>
                            ${modelBadge}
                            <p class="text-sm text-gray-700 mt-2 line-clamp-3">${(post.caption || post.text || 'No text content').substring(0, 120)}...</p>
                            <div class="flex items-center justify-between mt-3 text-xs text-gray-500">
                                <span>${new Date(post.timestamp).toLocaleDateString()}</span>
                                <div class="flex items-center space-x-3">
                                    <span><i class="fas fa-heart mr-1"></i>${post.likes || 0}</span>
                                    <span><i class="fas fa-comment mr-1"></i>${post.comments || 0}</span>
                                    ${post.shares ? `<span><i class="fas fa-share mr-1"></i>${post.shares}</span>` : ''}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });

        return `
            <div>
                <h4 class="text-lg font-semibold mb-4 text-gray-800 flex items-center">
                    <i class="fas ${iconClass} mr-2"></i>${title}
                </h4>
                <div class="space-y-4 max-h-96 overflow-y-auto">
                    ${postsHtml}
                </div>
            </div>
        `;
    }
    
    static createPostsByModel(allPosts, models) {
        if (!allPosts || allPosts.length === 0) {
            return '<div class="text-center py-8 text-gray-500">No posts data available</div>';
        }
        
        let modelSections = '';
        
        // Create sections for each model
        models.forEach(model => {
            const modelPosts = allPosts.filter(post => post.model === model);
            if (modelPosts.length > 0) {
                modelSections += this.createModelSection(model, modelPosts);
            }
        });
        
        // Unclassified posts section
        const unclassifiedPosts = allPosts.filter(post => !post.model || post.model === 'unclassified' || post.model === '');
        if (unclassifiedPosts.length > 0) {
            modelSections += this.createModelSection('Unclassified', unclassifiedPosts, true);
        }
        
        return `
            <div class="mt-8">
                <h4 class="text-lg font-semibold mb-6 text-gray-800 flex items-center">
                    <i class="fas fa-layer-group mr-2 text-purple-600"></i>Posts by Model Classification
                </h4>
                <div class="space-y-6">
                    ${modelSections}
                </div>
            </div>
        `;
    }
    
    static createModelSection(modelName, posts, isUnclassified = false) {
        const headerColor = isUnclassified ? 'text-yellow-600' : 'text-blue-600';
        const headerIcon = isUnclassified ? 'fa-question-circle' : 'fa-tag';
        
        let postsHtml = '';
        posts.slice(0, 6).forEach(post => { // Limit to 6 posts per model
            const imageHtml = this.createImageDisplay(post);
            const confidence = post.classification_confidence || 0;
            const confidenceClass = confidence >= 80 ? 'confidence-high' : 
                                   confidence >= 50 ? 'confidence-medium' : 'confidence-low';
            
            postsHtml += `
                <div class="flex items-start space-x-3 p-3 bg-white rounded border hover:shadow-sm transition-shadow">
                    <div class="flex-shrink-0">
                        ${imageHtml}
                    </div>
                    <div class="flex-1 min-w-0">
                        <div class="flex items-center justify-between mb-1">
                            <span class="platform-badge platform-${post.platform}">${post.platform}</span>
                            <div class="flex items-center space-x-2">
                                ${confidence > 0 ? `<span class="text-xs px-2 py-1 rounded ${confidenceClass}">${confidence}%</span>` : ''}
                                <span class="text-sm font-medium text-gray-800">${post.engagement.toLocaleString()}</span>
                            </div>
                        </div>
                        <p class="text-sm text-gray-700 line-clamp-2 mb-2">${(post.caption || post.text || 'No text content').substring(0, 100)}...</p>
                        <div class="flex items-center justify-between text-xs text-gray-500">
                            <span>${new Date(post.timestamp).toLocaleDateString()}</span>
                            <div class="flex items-center space-x-2">
                                <span>${post.likes || 0} likes</span>
                                <span>${post.comments || 0} comments</span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        const showingText = posts.length > 6 ? `Showing 6 of ${posts.length} posts` : `${posts.length} posts`;
        
        return `
            <div class="bg-gray-50 rounded-lg p-4">
                <div class="flex items-center justify-between mb-4">
                    <h5 class="font-medium ${headerColor} flex items-center">
                        <i class="fas ${headerIcon} mr-2"></i>${modelName}
                    </h5>
                    <span class="text-sm text-gray-500">${showingText}</span>
                </div>
                <div class="space-y-3 max-h-64 overflow-y-auto">
                    ${postsHtml}
                </div>
            </div>
        `;
    }
    
    static createImageDisplay(post) {
        const thumbnails = post.thumbnails || (post.thumbnail ? [post.thumbnail] : []);
        const postUrl = post.url || '';
        
        if (thumbnails.length === 0) {
            return '<div class="w-16 h-16 bg-gray-200 rounded flex items-center justify-center text-xs text-gray-500">No Image</div>';
        }
        
        const getProxiedImageUrl = (originalUrl) => {
            if (!originalUrl) return '';
            if (originalUrl.includes('cdninstagram.com') || originalUrl.includes('fbcdn.net')) {
                return `/api/image-proxy?url=${encodeURIComponent(originalUrl)}`;
            }
            return originalUrl;
        };
        
        const clickableClass = postUrl ? 'cursor-pointer hover:opacity-80 transition-opacity' : '';
        const clickHandler = postUrl ? `data-post-url="${postUrl}"` : '';
        const title = postUrl ? 'Click to view original post' : '';
        
        if (thumbnails.length === 1) {
            const proxiedUrl = getProxiedImageUrl(thumbnails[0]);
            return `
                <div class="post-thumbnail ${clickableClass}" ${clickHandler} title="${title}">
                    <img src="${proxiedUrl}" 
                         class="w-16 h-16 object-cover rounded border" 
                         alt="Post image" 
                         loading="lazy"
                         onerror="this.parentNode.innerHTML='<div class=\\'w-16 h-16 bg-gray-200 rounded flex items-center justify-center text-xs text-gray-500\\'>Error</div>'">
                </div>
            `;
        }
        
        // Multiple images - show as grid
        const maxImages = Math.min(4, thumbnails.length);
        let imagesHtml = '';
        
        for (let i = 0; i < maxImages; i++) {
            const proxiedUrl = getProxiedImageUrl(thumbnails[i]);
            imagesHtml += `<img src="${proxiedUrl}" 
                               class="w-full h-full object-cover" 
                               alt="Post image ${i + 1}" 
                               loading="lazy"
                               onerror="this.style.display='none'">`;
        }
        
        if (thumbnails.length > 4) {
            imagesHtml += `<div class="bg-black bg-opacity-70 flex items-center justify-center text-white text-xs font-bold">+${thumbnails.length - 3}</div>`;
        }
        
        return `
            <div class="post-thumbnail ${clickableClass}" ${clickHandler} title="${title}">
                <div class="image-grid grid-cols-2 w-16 h-16 grid gap-0.5 rounded overflow-hidden border">${imagesHtml}</div>
            </div>
        `;
    }
}