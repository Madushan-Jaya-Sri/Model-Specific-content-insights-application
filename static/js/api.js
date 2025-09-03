// API Helper Class
class API {
    static async request(url, options = {}) {
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            if (!response.ok) {
                let errorMessage = `HTTP ${response.status}`;
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorMessage;
                } catch (e) {
                    errorMessage = response.statusText || errorMessage;
                }
                throw new Error(errorMessage);
            }
            
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return response;
            }
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }
    
    static async getRecentAnalyses() {
        return await this.request('/api/recent-analyses');
    }
    
    static async startAnalysis(data) {
        return await this.request('/api/analyze', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
    
    static async getAnalysisStatus(analysisId) {
        return await this.request(`/api/analysis/${analysisId}`);
    }
    
    static async uploadReferenceImages(formData) {
        return await this.request('/api/upload-reference-images', {
            method: 'POST',
            headers: {}, // Remove Content-Type to let browser set it for FormData
            body: formData
        });
    }
    
    static async filterResults(analysisId, timeFilter) {
        return await this.request(`/api/filter-results/${analysisId}`, {
            method: 'POST',
            body: JSON.stringify(timeFilter)
        });
    }
    
    static async downloadResults(analysisId, startDate, endDate) {
        let downloadUrl = `/api/download/${analysisId}`;
        
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
        link.download = `social_media_analysis_${analysisId.substring(0, 8)}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    
    static async deleteAnalysis(analysisId) {
        return await this.request(`/api/analysis/${analysisId}`, {
            method: 'DELETE'
        });
    }
}