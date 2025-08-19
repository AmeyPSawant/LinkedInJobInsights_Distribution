#!/usr/bin/env python3
"""
LinkedIn Job Insights Extension Installer
Creates a packaged Chrome/Edge extension and provides installation instructions.
"""

import os
import json
import zipfile
import shutil
import tempfile
from pathlib import Path
import base64
import sys

class ExtensionInstaller:
    def __init__(self):
        self.extension_name = "LinkedInJobInsights"
        self.extension_files = {
            'manifest.json': self.get_manifest(),
            'content.js': self.get_content_script(),
            'styles.css': self.get_styles(),
            'background.js': self.get_background_script(),
            'popup.html': self.get_popup_html(),
            'popup.js': self.get_popup_script(),
        }
        
    def get_manifest(self):
        return """{
  "manifest_version": 3,
  "name": "LinkedIn Job Insights",
  "version": "1.0.0",
  "description": "Displays job posting metrics (listed date, expiry, views, applies) when clicking on LinkedIn jobs",
  "permissions": [
    "activeTab",
    "storage"
  ],
  "host_permissions": [
    "*://*.linkedin.com/*"
  ],
  "content_scripts": [
    {
      "matches": ["*://*.linkedin.com/jobs/*"],
      "js": ["content.js"],
      "css": ["styles.css"],
      "run_at": "document_idle"
    }
  ],
  "background": {
    "service_worker": "background.js"
  },
  "action": {
    "default_popup": "popup.html",
    "default_title": "LinkedIn Job Insights"
  },
  "icons": {
    "16": "icons/icon16.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  }
}"""

    def get_content_script(self):
        # Return the full content script (truncated for brevity)
        return """// LinkedIn Job Insights Extension - Content Script
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

  convertTimestamp(timestamp) {
    if (!timestamp) return 'N/A';
    const date = new Date(parseInt(timestamp));
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
  }

  extractJobId(url) {
    const patterns = [
      /\\/jobs\\/view\\/(\\d+)/,
      /currentJobId=(\\d+)/,
      /jobPostingId[=:](\\d+)/,
      /"jobPostingId":"(\\d+)"/
    ];
    
    for (const pattern of patterns) {
      const match = url.match(pattern);
      if (match) return match[1];
    }
    return null;
  }

  interceptNetworkRequests() {
    const originalFetch = window.fetch;
    const self = this;

    window.fetch = function(...args) {
      const url = args[0];
      
      if (typeof url === 'string' && url.includes('voyager/api/jobs/jobPostings')) {
        return originalFetch.apply(this, args)
          .then(response => {
            if (response.ok) {
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
  }

  processJobData(data, url) {
    try {
      let jobs = [];
      
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

  setupJobClickHandlers() {
    const self = this;
    
    document.addEventListener('click', function(e) {
      const jobCard = e.target.closest('[data-job-id], .jobs-search-results__list-item, .job-card-container, a[href*="/jobs/view/"]');
      
      if (jobCard) {
        setTimeout(() => self.showJobInsights(jobCard), 500);
      }
    });

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

  showJobInsights(jobCard) {
    let jobId = null;
    
    jobId = jobCard.getAttribute('data-job-id') || 
            jobCard.getAttribute('data-occludable-job-id') ||
            this.extractJobId(jobCard.href || '') ||
            this.extractJobId(location.href);

    if (!jobId) {
      const link = jobCard.querySelector('a[href*="/jobs/view/"]');
      if (link) {
        jobId = this.extractJobId(link.href);
      }
    }

    if (jobId) {
      this.showJobInsightsForId(jobId);
    }
  }

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

    const rect = document.querySelector('.jobs-details, .job-view-layout, .jobs-search__job-details').getBoundingClientRect();
    tooltip.style.left = Math.min(rect.right - tooltip.offsetWidth - 20, window.innerWidth - tooltip.offsetWidth - 20) + 'px';
    tooltip.style.top = Math.max(rect.top + 20, 20) + 'px';

    setTimeout(() => {
      if (this.currentTooltip === tooltip) {
        this.removeExistingTooltip();
      }
    }, 10000);
  }

  removeExistingTooltip() {
    if (this.currentTooltip) {
      this.currentTooltip.remove();
      this.currentTooltip = null;
    }
    
    document.querySelectorAll('.linkedin-job-insights-tooltip').forEach(el => el.remove());
  }

  observePageChanges() {
    this.observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
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

  destroy() {
    if (this.observer) {
      this.observer.disconnect();
    }
    this.removeExistingTooltip();
    this.jobData.clear();
    this.isInitialized = false;
  }
}

const jobInsights = new LinkedInJobInsights();

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => jobInsights.init());
} else {
  jobInsights.init();
}

window.addEventListener('beforeunload', () => jobInsights.destroy());"""

    def get_styles(self):
        return """.linkedin-job-insights-tooltip {
  position: fixed;
  top: 20px;
  right: 20px;
  background: #ffffff;
  border: 2px solid #0a66c2;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  z-index: 10000;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-size: 13px;
  line-height: 1.4;
  min-width: 280px;
  max-width: 350px;
  animation: slideIn 0.3s ease-out;
}

.job-insights-header {
  background: linear-gradient(135deg, #0a66c2, #004182);
  color: white;
  padding: 12px 16px;
  font-weight: 600;
  font-size: 14px;
  border-radius: 10px 10px 0 0;
  display: flex;
  align-items: center;
  position: relative;
}

.job-insights-content {
  padding: 16px;
  background: #fafafa;
  border-radius: 0 0 10px 10px;
}

.insight-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #e1e5e9;
}

.insight-row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.insight-row .label {
  font-weight: 500;
  color: #5e6670;
  font-size: 12px;
}

.insight-row .value {
  font-weight: 600;
  color: #0a66c2;
  text-align: right;
  max-width: 180px;
  word-break: break-word;
}

.close-tooltip {
  position: absolute;
  top: 8px;
  right: 12px;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  cursor: pointer;
  font-size: 16px;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.close-tooltip:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.1);
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@media (prefers-color-scheme: dark) {
  .linkedin-job-insights-tooltip {
    background: #1d2226;
    border-color: #0a66c2;
  }
  
  .job-insights-content {
    background: #2f3336;
  }
  
  .insight-row .label {
    color: #b0b7c3;
  }
  
  .insight-row .value {
    color: #70b5f9;
  }
  
  .insight-row {
    border-bottom-color: #404649;
  }
}

@media (max-width: 768px) {
  .linkedin-job-insights-tooltip {
    position: fixed;
    top: auto;
    bottom: 20px;
    left: 20px;
    right: 20px;
    max-width: none;
    min-width: auto;
  }
}"""

    def get_background_script(self):
        return """chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    console.log('LinkedIn Job Insights extension installed');
    
    chrome.notifications?.create({
      type: 'basic',
      iconUrl: 'icons/icon48.png',
      title: 'LinkedIn Job Insights Installed!',
      message: 'Visit LinkedIn Jobs page and click on any job to see insights.'
    });
  }
});

chrome.action.onClicked.addListener((tab) => {
  if (tab.url.includes('linkedin.com')) {
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ['content.js']
    });
  } else {
    chrome.tabs.create({ url: 'https://www.linkedin.com/jobs/' });
  }
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url && tab.url.includes('linkedin.com/jobs')) {
    chrome.scripting.executeScript({
      target: { tabId: tabId },
      files: ['content.js']
    }).catch(err => {
      console.log('Content script injection skipped:', err.message);
    });
  }
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'storeJobData') {
    chrome.storage.local.set({ jobData: request.data }, () => {
      sendResponse({ success: true });
    });
    return true;
  }
  
  if (request.action === 'getJobData') {
    chrome.storage.local.get(['jobData'], (result) => {
      sendResponse({ data: result.jobData || {} });
    });
    return true;
  }
});"""

    def get_popup_html(self):
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {
            width: 300px;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 14px;
            line-height: 1.4;
        }
        
        .header {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #0a66c2;
        }
        
        .icon {
            font-size: 24px;
            margin-right: 10px;
        }
        
        .title {
            font-size: 18px;
            font-weight: 600;
            color: #0a66c2;
        }
        
        .status {
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 15px;
            text-align: center;
            font-weight: 500;
        }
        
        .status.active {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .status.inactive {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .instructions {
            background: #e7f3ff;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #0a66c2;
            margin-bottom: 15px;
        }
        
        .instructions h3 {
            margin: 0 0 8px 0;
            font-size: 14px;
            color: #0a66c2;
        }
        
        .instructions ol {
            margin: 8px 0 0 0;
            padding-left: 20px;
        }
        
        .instructions li {
            margin-bottom: 4px;
            font-size: 12px;
        }
        
        .button {
            background: #0a66c2;
            color: white;
            border: none;
            padding: 10px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            width: 100%;
            margin-bottom: 10px;
            transition: background 0.2s;
        }
        
        .button:hover {
            background: #004182;
        }
    </style>
</head>
<body>
    <div class="header">
        <span class="icon">📊</span>
        <span class="title">LinkedIn Job Insights</span>
    </div>
    
    <div id="status" class="status inactive">
        Checking status...
    </div>
    
    <div class="instructions">
        <h3>How to Use:</h3>
        <ol>
            <li>Navigate to LinkedIn Jobs page</li>
            <li>Search for jobs or browse listings</li>
            <li>Click on any job posting</li>
            <li>View insights tooltip with metrics</li>
        </ol>
    </div>
    
    <button class="button" id="openLinkedIn">Open LinkedIn Jobs</button>

    <script src="popup.js"></script>
</body>
</html>"""

    def get_popup_script(self):
        return """document.addEventListener('DOMContentLoaded', function() {
    const statusElement = document.getElementById('status');
    const openLinkedInButton = document.getElementById('openLinkedIn');

    chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
        const currentTab = tabs[0];
        const isOnLinkedIn = currentTab.url && currentTab.url.includes('linkedin.com');
        const isOnJobsPage = currentTab.url && currentTab.url.includes('linkedin.com/jobs');

        if (isOnJobsPage) {
            statusElement.textContent = '✅ Active on LinkedIn Jobs';
            statusElement.className = 'status active';
        } else if (isOnLinkedIn) {
            statusElement.textContent = '⚠️ On LinkedIn (navigate to Jobs)';
            statusElement.className = 'status inactive';
        } else {
            statusElement.textContent = '❌ Not on LinkedIn';
            statusElement.className = 'status inactive';
        }
    });

    openLinkedInButton.addEventListener('click', function() {
        chrome.tabs.create({ url: 'https://www.linkedin.com/jobs/' });
        window.close();
    });
});"""

    def create_icons(self, icons_dir):
        """Create simple icon files (base64 encoded simple icons)"""
        # Simple base64 encoded PNG icons (placeholder - you'd want real icons)
        icon_data = {
            16: "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAdgAAAHYBTnsmCAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAFYSURBVDiNpZM9SwNBEIafgwiChYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYW