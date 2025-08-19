// LinkedIn Job Insights Extension - Content Script
class LinkedInJobInsights {
  constructor() {
    this.jobData = new Map();
    this.isInitialized = false;
    this.observer = null;
    this.currentTooltip = null;
  }

  init() {
    if (this.isInitialized) return;
    
    console.log('LinkedIn Job Insights: Initializing...');
    this.interceptNetworkRequests();
    this.setupJobClickHandlers();
    this.observePageChanges();
    this.isInitialized = true;
  }

  // Convert LinkedIn timestamp to readable date
  convertTimestamp(timestamp) {
    if (!timestamp) return 'N/A';
    // LinkedIn timestamps are usually in milliseconds
    const date = new Date(parseInt(timestamp));
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
  }

  // Extract job ID from various LinkedIn URL formats
  extractJobId(url) {
    const patterns = [
      /\/jobs\/view\/(\d+)/,
      /currentJobId=(\d+)/,
      /jobPostingId[=:](\d+)/,
      /"jobPostingId":"(\d+)"/
    ];
    
    for (const pattern of patterns) {
      const match = url.match(pattern);
      if (match) return match[1];
    }
    return null;
  }

  // Intercept network requests to capture job data
  interceptNetworkRequests() {
    const originalFetch = window.fetch;
    const self = this;

    window.fetch = function(...args) {
      const url = args[0];
      
      if (typeof url === 'string' && url.includes('voyager/api/jobs/jobPostings')) {
        return originalFetch.apply(this, args)
          .then(response => {
            if (response.ok) {
              // Clone the response to read it without consuming the original
              const clonedResponse = response.clone();
              clonedResponse.json().then(data => {
                self.processJobData(data, url);
              }).catch(err => console.log('Error processing job data:', err));
            }
            return response;
          });
      }
      
      return originalFetch.apply(this, args);
    };

    // Also intercept XMLHttpRequest for older implementations
    const originalXHR = window.XMLHttpRequest.prototype.open;
    window.XMLHttpRequest.prototype.open = function(method, url, ...args) {
      if (url.includes('voyager/api/jobs/jobPostings')) {
        this.addEventListener('load', function() {
          if (this.status === 200) {
            try {
              const data = JSON.parse(this.responseText);
              self.processJobData(data, url);
            } catch (e) {
              console.log('Error parsing XHR job data:', e);
            }
          }
        });
      }
      return originalXHR.apply(this, [method, url, ...args]);
    };
  }

  // Process and store job data from API responses
  processJobData(data, url) {
    try {
      let jobs = [];
      
      // Handle different response structures
      if (data.elements) {
        jobs = data.elements;
      } else if (data.data && data.data.elements) {
        jobs = data.data.elements;
      } else if (Array.isArray(data)) {
        jobs = data;
      } else if (data.jobPostingId) {
        jobs = [data];
      }

      jobs.forEach(job => {
        if (job.jobPostingId || job.entityUrn) {
          const jobId = job.jobPostingId || this.extractJobId(job.entityUrn);
          
          if (jobId) {
            this.jobData.set(jobId, {
              id: jobId,
              listedAt: this.convertTimestamp(job.listedAt),
              expireAt: this.convertTimestamp(job.expireAt),
              originalListedAt: this.convertTimestamp(job.originalListedAt),
              views: job.views || 'N/A',
              applies: job.applies || 'N/A',
              title: job.title || 'Unknown',
              company: job.companyDetails?.companyResolutionResult?.name || 'Unknown'
            });
          }
        }
      });

      console.log(`LinkedIn Job Insights: Processed ${jobs.length} jobs. Total stored: ${this.jobData.size}`);
    } catch (error) {
      console.error('LinkedIn Job Insights: Error processing job data:', error);
    }
  }

  // Setup click handlers for job listings
  setupJobClickHandlers() {
    const self = this;
    
    // Handle clicks on job cards
    document.addEventListener('click', function(e) {
      const jobCard = e.target.closest('[data-job-id], .jobs-search-results__list-item, .job-card-container, a[href*="/jobs/view/"]');
      
      if (jobCard) {
        setTimeout(() => self.showJobInsights(jobCard), 500); // Small delay to ensure data is loaded
      }
    });

    // Handle URL changes (for single-page app navigation)
    let lastUrl = location.href;
    new MutationObserver(() => {
      const url = location.href;
      if (url !== lastUrl) {
        lastUrl = url;
        setTimeout(() => {
          const jobId = self.extractJobId(url);
          if (jobId) {
            self.showJobInsightsForId(jobId);
          }
        }, 1000);
      }
    }).observe(document, { subtree: true, childList: true });
  }

  // Show insights for a specific job card
  showJobInsights(jobCard) {
    let jobId = null;
    
    // Try to extract job ID from various attributes
    jobId = jobCard.getAttribute('data-job-id') || 
            jobCard.getAttribute('data-occludable-job-id') ||
            this.extractJobId(jobCard.href || '') ||
            this.extractJobId(location.href);

    if (!jobId) {
      // Try to find job ID in nested links
      const link = jobCard.querySelector('a[href*="/jobs/view/"]');
      if (link) {
        jobId = this.extractJobId(link.href);
      }
    }

    if (jobId) {
      this.showJobInsightsForId(jobId);
    }
  }

  // Display job insights tooltip
  showJobInsightsForId(jobId) {
    const jobInfo = this.jobData.get(jobId);
    
    if (!jobInfo) {
      console.log(`LinkedIn Job Insights: No data found for job ${jobId}`);
      return;
    }

    this.removeExistingTooltip();

    const tooltip = document.createElement('div');
    tooltip.className = 'linkedin-job-insights-tooltip';
    tooltip.innerHTML = `
      <div class="job-insights-header">📊 Job Insights</div>
      <div class="job-insights-content">
        <div class="insight-row">
          <span class="label">📅 Listed:</span>
          <span class="value">${jobInfo.listedAt}</span>
        </div>
        <div class="insight-row">
          <span class="label">⏰ Expires:</span>
          <span class="value">${jobInfo.expireAt}</span>
        </div>
        <div class="insight-row">
          <span class="label">👀 Views:</span>
          <span class="value">${jobInfo.views}</span>
        </div>
        <div class="insight-row">
          <span class="label">📝 Applies:</span>
          <span class="value">${jobInfo.applies}</span>
        </div>
      </div>
      <button class="close-tooltip" onclick="this.parentElement.remove()">×</button>
    `;

    document.body.appendChild(tooltip);
    this.currentTooltip = tooltip;

    // Position tooltip
    const rect = document.querySelector('.jobs-details, .job-view-layout, .jobs-search__job-details').getBoundingClientRect();
    tooltip.style.left = Math.min(rect.right - tooltip.offsetWidth - 20, window.innerWidth - tooltip.offsetWidth - 20) + 'px';
    tooltip.style.top = Math.max(rect.top + 20, 20) + 'px';

    // Auto-remove after 10 seconds
    setTimeout(() => {
      if (this.currentTooltip === tooltip) {
        this.removeExistingTooltip();
      }
    }, 10000);
  }

  // Remove existing tooltip
  removeExistingTooltip() {
    if (this.currentTooltip) {
      this.currentTooltip.remove();
      this.currentTooltip = null;
    }
    
    // Also remove any orphaned tooltips
    document.querySelectorAll('.linkedin-job-insights-tooltip').forEach(el => el.remove());
  }

  // Observe page changes for dynamic content loading
  observePageChanges() {
    this.observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
          // Check if new job listings were added
          const hasJobListings = Array.from(mutation.addedNodes).some(node => 
            node.nodeType === 1 && (
              node.querySelector && (
                node.querySelector('.jobs-search-results__list-item') ||
                node.querySelector('[data-job-id]') ||
                node.classList?.contains('jobs-search-results__list-item')
              )
            )
          );
          
          if (hasJobListings) {
            console.log('LinkedIn Job Insights: New job listings detected');
          }
        }
      });
    });

    this.observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }

  // Cleanup
  destroy() {
    if (this.observer) {
      this.observer.disconnect();
    }
    this.removeExistingTooltip();
    this.jobData.clear();
    this.isInitialized = false;
  }
}

// Initialize the extension
const jobInsights = new LinkedInJobInsights();

// Wait for page to load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => jobInsights.init());
} else {
  jobInsights.init();
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => jobInsights.destroy());