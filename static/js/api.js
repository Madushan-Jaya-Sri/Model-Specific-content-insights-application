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
        // Note: Don't set Content-Type header for FormData - browser will set it automatically with boundary
        const response = await fetch('/api/upload-reference-images', {
            method: 'POST',
            body: formData
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
        
        return await response.json();
    }
    
    static async filterResults(analysisId, timeFilter) {
        return await this.request(`/api/filter-results/${analysisId}`, {
            method: 'POST',
            body: JSON.stringify(timeFilter)
        });
    }
    

    static async downloadResults(analysisId, startDate, endDate) {
        try {
            // Build download URL
            let downloadUrl = `/api/download/${analysisId}`;
            
            if (startDate && endDate) {
                const timeFilter = {
                    start_date: new Date(startDate + 'T00:00:00').toISOString(),
                    end_date: new Date(endDate + 'T23:59:59').toISOString()
                };
                downloadUrl += `?time_filter=${encodeURIComponent(JSON.stringify(timeFilter))}`;
            }

            console.log('Downloading from:', downloadUrl);

            // Fetch the file
            const response = await fetch(downloadUrl, {
                method: 'GET',
                credentials: 'same-origin'
            });

            if (!response.ok) {
                const contentType = response.headers.get('content-type');
                let errorMessage = `Download failed: HTTP ${response.status}`;
                
                if (contentType && contentType.includes('application/json')) {
                    try {
                        const errorData = await response.json();
                        errorMessage = errorData.detail || errorMessage;
                    } catch (e) {
                        console.error('Failed to parse error response:', e);
                    }
                }
                
                throw new Error(errorMessage);
            }

            // Get the blob from response
            const blob = await response.blob();
            
            // Verify blob is not empty
            if (blob.size === 0) {
                throw new Error('Downloaded file is empty');
            }
            
            console.log('Download successful, file size:', blob.size, 'bytes');
            
            // Get filename from Content-Disposition header or use default
            let filename = `social_media_analysis_${analysisId.substring(0, 8)}.csv`;
            const contentDisposition = response.headers.get('Content-Disposition');
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename[^;=\\n]*=((['"]).*?\\2|[^;\\n]*)/);
                if (filenameMatch && filenameMatch[1]) {
                    filename = filenameMatch[1].replace(/['"]/g, '');
                }
            }

            // Create download link and trigger download
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            link.style.display = 'none';
            
            document.body.appendChild(link);
            link.click();
            
            // Cleanup
            setTimeout(() => {
                document.body.removeChild(link);
                window.URL.revokeObjectURL(url);
            }, 100);

            return { success: true, filename, size: blob.size };
            
        } catch (error) {
            console.error('Download error:', error);
            throw error;
        }
    }

    
    
    static async deleteAnalysis(analysisId) {
        return await this.request(`/api/analysis/${analysisId}`, {
            method: 'DELETE'
        });
    }
}