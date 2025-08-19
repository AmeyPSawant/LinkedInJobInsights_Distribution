// LinkedIn Job Insights Extension - Popup Script

document.addEventListener('DOMContentLoaded', function() {
    const statusElement = document.getElementById('status');
    const jobCountElement = document.getElementById('jobCount');
    const sessionCountElement = document.getElementById('sessionCount');
    const openLinkedInButton = document.getElementById('openLinkedIn');
    const clearDataButton = document.getElementById('clearData');

    // Check if user is currently on LinkedIn
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

    // Load stored job data stats
    chrome.storage.local.get(['jobData', 'sessionCount'], function(result) {
        const jobData = result.jobData || {};
        const jobCount = Object.keys(jobData).length;
        const sessionCount = result.sessionCount || 0;

        jobCountElement.textContent = jobCount;
        sessionCountElement.textContent = sessionCount;
    });

    // Open LinkedIn Jobs button
    openLinkedInButton.addEventListener('click', function() {
        chrome.tabs.create({ url: 'https://www.linkedin.com/jobs/' });
        window.close();
    });

    // Clear stored data button
    clearDataButton.addEventListener('click', function() {
        if (confirm('Are you sure you want to clear all stored job data?')) {
            chrome.storage.local.clear(function() {
                jobCountElement.textContent = '0';
                sessionCountElement.textContent = '0';
                
                // Show confirmation
                const originalText = clearDataButton.textContent;
                clearDataButton.textContent = 'Cleared!';
                clearDataButton.style.background = '#28a745';
                
                setTimeout(() => {
                    clearDataButton.textContent = originalText;
                    clearDataButton.style.background = '#6c757d';
                }, 1500);
            });
        }
    });

    // Update stats every few seconds if popup remains open
    setInterval(function() {
        chrome.storage.local.get(['jobData', 'sessionCount'], function(result) {
            const jobData = result.jobData || {};
            const jobCount = Object.keys(jobData).length;
            const sessionCount = result.sessionCount || 0;

            jobCountElement.textContent = jobCount;
            sessionCountElement.textContent = sessionCount;
        });
    }, 3000);
});