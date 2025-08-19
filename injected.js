// Injected script to intercept network requests
(function() {
  'use strict';

  // Store original fetch and XMLHttpRequest
  const originalFetch = window.fetch;
  const originalXHROpen = XMLHttpRequest.prototype.open;
  const originalXHRSend = XMLHttpRequest.prototype.send;

  // Intercept fetch requests
  window.fetch = function(...args) {
    return originalFetch.apply(this, args)
      .then(response => {
        if (response.url && response.url.includes('voyager/api/jobs/jobPostings')) {
          // Clone the response to avoid consuming the original
          const responseClone = response.clone();
          
          responseClone.text().then(responseText => {
            window.postMessage({
              type: 'JOB_DATA_INTERCEPTED',
              payload: {
                url: response.url,
                response: responseText,
                method: 'fetch'
              }
            }, '*');
          }).catch(err => {
            console.log('Error reading fetch response:', err);
          });
        }
        return response;
      });
  };

  // Intercept XMLHttpRequest
  XMLHttpRequest.prototype.open = function(method, url, async, user, password) {
    this._method = method;
    this._url = url;
    return originalXHROpen.apply(this, arguments);
  };

  XMLHttpRequest.prototype.send = function(data) {
    const xhr = this;
    
    if (xhr._url && xhr._url.includes('voyager/api/jobs/jobPostings')) {
      const originalOnReadyStateChange = xhr.onreadystatechange;
      
      xhr.onreadystatechange = function() {
        if (xhr.readyState === 4 && xhr.status === 200) {
          try {
            window.postMessage({
              type: 'JOB_DATA_INTERCEPTED',
              payload: {
                url: xhr._url,
                response: xhr.responseText,
                method: 'xhr'
              }
            }, '*');
          } catch (error) {
            console.log('Error intercepting XHR response:', error);
          }
        }
        
        if (originalOnReadyStateChange) {
          originalOnReadyStateChange.apply(xhr, arguments);
        }
      };
    }
    
    return originalXHRSend.apply(this, arguments);
  };

  console.log('LinkedIn Job Stats Extension: Network interceptor injected');
})();