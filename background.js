// Background script for LinkedIn Job Stats Extension

chrome.runtime.onInstalled.addListener(() => {
  console.log('LinkedIn Job Stats Extension installed');
});

// Handle any background tasks if needed in the future
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'GET_JOB_STATS') {
    // Future: Could implement additional API calls or data processing here
    sendResponse({ success: true });
  }
});

// Optional: Add context menu for debugging
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'refresh-job-stats',
    title: 'Refresh Job Stats',
    contexts: ['page'],
    documentUrlPatterns: ['https://www.linkedin.com/jobs/*']
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'refresh-job-stats') {
    chrome.tabs.sendMessage(tab.id, { type: 'REFRESH_STATS' });
  }
});