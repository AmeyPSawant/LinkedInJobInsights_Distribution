// Content script for LinkedIn Job Stats Extension
class LinkedInJobStatsExtension {
  constructor() {
    this.jobData = new Map();
    this.processedJobs = new Set();
    this.init();
  }

  init() {
    // Inject script to intercept network requests
    this.injectNetworkInterceptor();
    
    // Start observing for job cards
    this.observeJobCards();
    
    // Listen for messages from injected script
    window.addEventListener('message', (event) => {
      if (event.source !== window || event.data.type !== 'JOB_DATA_INTERCEPTED') return;
      
      this.handleJobData(event.data.payload);
    });
  }

  injectNetworkInterceptor() {
    const script = document.createElement('script');
    script.src = chrome.runtime.getURL('injected.js');
    script.onload = () => script.remove();
    (document.head || document.documentElement).appendChild(script);
  }

  handleJobData(data) {
    if (data.url && data.url.includes('voyager/api/jobs/jobPostings') && data.response) {
      this.parseJobPostings(data.response);
    }
  }

  parseJobPostings(response) {
    try {
      const data = JSON.parse(response);
      
      // Handle different response structures
      const jobs = data.elements || data.data || [data];
      
      jobs.forEach(job => {
        if (job.jobPostingId || job.entityUrn) {
          const jobId = job.jobPostingId || this.extractJobIdFromUrn(job.entityUrn);
          
          if (jobId) {
            this.jobData.set(jobId, {
              listedAt: this.convertTimestamp(job.listedAt),
              expireAt: this.convertTimestamp(job.expireAt),
              originalListedAt: this.convertTimestamp(job.originalListedAt),
              views: job.views || 'N/A',
              applies: job.applies || 'N/A'
            });
            
            // Update any existing job cards
            this.updateJobCard(jobId);
          }
        }
      });
    } catch (error) {
      console.log('Error parsing job data:', error);
    }
  }

  extractJobIdFromUrn(urn) {
    if (!urn) return null;
    const match = urn.match(/jobPosting:(\d+)/);
    return match ? match[1] : null;
  }

  convertTimestamp(timestamp) {
    if (!timestamp) return 'N/A';
    
    // Handle LinkedIn timestamp format (usually milliseconds)
    const date = new Date(timestamp);
    if (isNaN(date.getTime())) return 'N/A';
    
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  }

  observeJobCards() {
    const observer = new MutationObserver((mutations) => {
      mutations.forEach(mutation => {
        mutation.addedNodes.forEach(node => {
          if (node.nodeType === Node.ELEMENT_NODE) {
            this.processJobCards(node);
          }
        });
      });
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    // Process existing job cards
    this.processJobCards(document.body);
  }

  processJobCards(container) {
    // LinkedIn job card selectors (may need adjustment based on current LinkedIn UI)
    const jobCardSelectors = [
      '[data-job-id]',
      '.job-card-container',
      '.jobs-search-results__list-item',
      '.scaffold-layout__list-item'
    ];

    jobCardSelectors.forEach(selector => {
      const jobCards = container.querySelectorAll(selector);
      jobCards.forEach(card => this.processJobCard(card));
    });
  }

  processJobCard(jobCard) {
    const jobId = this.extractJobIdFromCard(jobCard);
    if (!jobId || this.processedJobs.has(jobId)) return;

    this.processedJobs.add(jobId);
    
    // Add placeholder for stats
    this.addStatsPlaceholder(jobCard, jobId);
    
    // Update if data is already available
    if (this.jobData.has(jobId)) {
      this.updateJobCard(jobId);
    }
  }

  extractJobIdFromCard(jobCard) {
    // Try different methods to extract job ID
    const dataJobId = jobCard.getAttribute('data-job-id');
    if (dataJobId) return dataJobId;

    // Look for job ID in links
    const links = jobCard.querySelectorAll('a[href*="/jobs/view/"]');
    for (let link of links) {
      const match = link.href.match(/\/jobs\/view\/(\d+)/);
      if (match) return match[1];
    }

    return null;
  }

  addStatsPlaceholder(jobCard, jobId) {
    if (jobCard.querySelector('.job-stats-overlay')) return;

    const statsContainer = document.createElement('div');
    statsContainer.className = 'job-stats-overlay';
    statsContainer.setAttribute('data-job-id', jobId);
    
    statsContainer.innerHTML = `
      <div class="job-stats-content">
        <div class="job-stats-loading">Loading stats...</div>
      </div>
    `;

    // Find the best place to insert stats
    const titleElement = jobCard.querySelector('h3, .job-card-list__title, [data-control-name="job_card_title"]');
    if (titleElement) {
      titleElement.parentNode.insertBefore(statsContainer, titleElement.nextSibling);
    } else {
      jobCard.appendChild(statsContainer);
    }
  }

  updateJobCard(jobId) {
    const statsElement = document.querySelector(`[data-job-id="${jobId}"] .job-stats-overlay`);
    if (!statsElement) return;

    const data = this.jobData.get(jobId);
    if (!data) return;

    const content = statsElement.querySelector('.job-stats-content');
    if (content) {
      content.innerHTML = `
        <div class="job-stats-row">
          <span class="job-stat-item">L@: ${data.listedAt}</span>
          <span class="job-stat-divider">|</span>
          <span class="job-stat-item">E@: ${data.expireAt}</span>
          <span class="job-stat-divider">|</span>
          <span class="job-stat-item">OL@: ${data.originalListedAt}</span>
        </div>
        <div class="job-stats-row">
          <span class="job-stat-item">Views: ${data.views}</span>
          <span class="job-stat-divider">|</span>
          <span class="job-stat-item">Applies: ${data.applies}</span>
        </div>
      `;
    }
  }
}

// Initialize the extension
new LinkedInJobStatsExtension();