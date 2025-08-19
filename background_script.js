// LinkedIn Job Insights Extension - Background Script

chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    console.log('LinkedIn Job Insights extension installed');
    
    // Open welcome page or show notification
    chrome.notifications?.create({
      type: 'basic',
      iconUrl: 'icons/icon48.png',
      title: 'LinkedIn Job Insights Installed!',
      message: 'Visit LinkedIn Jobs page and click on any job to see insights.'
    });
  } else if (details.reason === 'update') {
    console.log('LinkedIn Job Insights extension updated');
  }
});

// Handle extension icon click
chrome.action.onClicked.addListener((tab) => {
  if (tab.url.includes('linkedin.com')) {
    // Inject content script if not already present
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ['content.js']
    });
  } else {
    // Open LinkedIn Jobs page
    chrome.tabs.create({ url: 'https://www.linkedin.com/jobs/' });
  }
});

// Listen for tab updates to ensure content script is loaded on LinkedIn pages
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url && tab.url.includes('linkedin.com/jobs')) {
    // Ensure content script is injected
    chrome.scripting.executeScript({
      target: { tabId: tabId },
      files: ['content.js']
    }).catch(err => {
      // Script might already be injected
      console.log('Content script injection skipped:', err.message);
    });
  }
});

// Handle messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'storeJobData') {
    // Store job data in chrome.storage for persistence
    chrome.storage.local.set({ jobData: request.data }, () => {
      sendResponse({ success: true });
    });
    return true; // Keep message channel open for async response
  }
  
  if (request.action === 'getJobData') {
    // Retrieve stored job data
    chrome.storage.local.get(['jobData'], (result) => {
      sendResponse({ data: result.jobData || {} });
    });
    return true;
  }
});