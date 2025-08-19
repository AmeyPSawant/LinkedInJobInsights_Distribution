#!/usr/bin/env python3
"""
LinkedIn Job Insights Extension - Standalone EXE Installer
Creates and installs the Chrome/Edge extension with a GUI installer.
"""

import os
import sys
import json
import zipfile
import shutil
import tempfile
import subprocess
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import threading
import time

class LinkedInJobInsightsInstaller:
    def __init__(self):
        self.extension_name = "LinkedInJobInsights"
        self.version = "1.0.0"
        self.root = None
        self.progress_var = None
        self.status_var = None
        self.installation_path = None
        
    def create_gui(self):
        """Create the installer GUI"""
        self.root = tk.Tk()
        self.root.title(f"LinkedIn Job Insights Extension Installer v{self.version}")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Icon and title
        title_label = ttk.Label(header_frame, text="📊 LinkedIn Job Insights", 
                               font=('Arial', 18, 'bold'))
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        subtitle_label = ttk.Label(header_frame, text="Chrome/Edge Extension Installer", 
                                  font=('Arial', 10))
        subtitle_label.grid(row=1, column=0, sticky=tk.W)
        
        # Description
        desc_frame = ttk.LabelFrame(main_frame, text="What This Extension Does", padding="10")
        desc_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        description = """• Displays job posting metrics when you click on LinkedIn jobs
• Shows: Listed Date, Expiry Date, View Count, Application Count  
• Works automatically - no configuration needed
• Privacy-first: all data stays in your browser
• Clean, non-intrusive tooltip interface"""
        
        desc_label = ttk.Label(desc_frame, text=description, justify=tk.LEFT)
        desc_label.grid(row=0, column=0, sticky=tk.W)
        
        # Installation options
        options_frame = ttk.LabelFrame(main_frame, text="Installation Options", padding="10")
        options_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # Installation path
        path_frame = ttk.Frame(options_frame)
        path_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(path_frame, text="Installation Location:").grid(row=0, column=0, sticky=tk.W)
        
        self.path_var = tk.StringVar(value=str(Path.home() / "Desktop" / "LinkedInJobInsights"))
        path_entry = ttk.Entry(path_frame, textvariable=self.path_var, width=50)
        path_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        browse_btn = ttk.Button(path_frame, text="Browse", command=self.browse_path)
        browse_btn.grid(row=1, column=1)
        
        path_frame.columnconfigure(0, weight=1)
        
        # Browser selection
        browser_frame = ttk.Frame(options_frame)
        browser_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(browser_frame, text="Target Browser:").grid(row=0, column=0, sticky=tk.W)
        
        self.browser_var = tk.StringVar(value="chrome")
        chrome_radio = ttk.Radiobutton(browser_frame, text="Chrome", 
                                      variable=self.browser_var, value="chrome")
        chrome_radio.grid(row=1, column=0, sticky=tk.W)
        
        edge_radio = ttk.Radiobutton(browser_frame, text="Edge", 
                                    variable=self.browser_var, value="edge")
        edge_radio.grid(row=1, column=1, sticky=tk.W, padx=(20, 0))
        
        both_radio = ttk.Radiobutton(browser_frame, text="Both", 
                                    variable=self.browser_var, value="both")
        both_radio.grid(row=1, column=2, sticky=tk.W, padx=(20, 0))
        
        # Progress section
        progress_frame = ttk.LabelFrame(main_frame, text="Installation Progress", padding="10")
        progress_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        self.status_var = tk.StringVar(value="Ready to install...")
        status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        status_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        self.progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                     maximum=100, length=400)
        progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        progress_frame.columnconfigure(0, weight=1)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(15, 0))
        
        self.install_btn = ttk.Button(button_frame, text="Install Extension", 
                                     command=self.start_installation, style='Accent.TButton')
        self.install_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.open_extensions_btn = ttk.Button(button_frame, text="Open Extensions Page", 
                                            command=self.open_extensions_page, state='disabled')
        self.open_extensions_btn.grid(row=0, column=1, padx=(0, 10))
        
        exit_btn = ttk.Button(button_frame, text="Exit", command=self.root.quit)
        exit_btn.grid(row=0, column=2)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
    def browse_path(self):
        """Browse for installation directory"""
        path = filedialog.askdirectory(initialdir=self.path_var.get())
        if path:
            self.path_var.set(path)
    
    def update_progress(self, value, status):
        """Update progress bar and status"""
        self.progress_var.set(value)
        self.status_var.set(status)
        self.root.update()
    
    def get_extension_files(self):
        """Return all extension files as a dictionary"""
        return {
            'manifest.json': '''{
  "manifest_version": 3,
  "name": "LinkedIn Job Insights",
  "version": "1.0.0",
  "description": "Displays job posting metrics when clicking on LinkedIn jobs",
  "permissions": ["activeTab", "storage"],
  "host_permissions": ["*://*.linkedin.com/*"],
  "content_scripts": [{
    "matches": ["*://*.linkedin.com/jobs/*"],
    "js": ["content.js"],
    "css": ["styles.css"],
    "run_at": "document_idle"
  }],
  "background": {"service_worker": "background.js"},
  "action": {
    "default_popup": "popup.html",
    "default_title": "LinkedIn Job Insights"
  },
  "icons": {
    "16": "icons/icon16.png",
    "48": "icons/icon48.png", 
    "128": "icons/icon128.png"
  }
}''',
            
            'content.js': '''// LinkedIn Job Insights Extension
class LinkedInJobInsights {
  constructor() {
    this.jobData = new Map();
    this.isInitialized = false;
    this.currentTooltip = null;
  }

  init() {
    if (this.isInitialized) return;
    console.log('LinkedIn Job Insights: Initializing...');
    this.interceptNetworkRequests();
    this.setupJobClickHandlers();
    this.isInitialized = true;
  }

  convertTimestamp(timestamp) {
    if (!timestamp) return 'N/A';
    const date = new Date(parseInt(timestamp));
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
  }

  extractJobId(url) {
    const patterns = [/\\/jobs\\/view\\/(\\d+)/, /currentJobId=(\\d+)/, /jobPostingId[=:](\\d+)/];
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
        return originalFetch.apply(this, args).then(response => {
          if (response.ok) {
            const clonedResponse = response.clone();
            clonedResponse.json().then(data => self.processJobData(data)).catch(console.log);
          }
          return response;
        });
      }
      return originalFetch.apply(this, args);
    };
  }

  processJobData(data) {
    try {
      let jobs = data.elements || (data.data && data.data.elements) || (Array.isArray(data) ? data : [data]);
      
      jobs.forEach(job => {
        const jobId = job.jobPostingId || this.extractJobId(job.entityUrn || '');
        if (jobId) {
          this.jobData.set(jobId, {
            id: jobId,
            listedAt: this.convertTimestamp(job.listedAt),
            expireAt: this.convertTimestamp(job.expireAt),
            views: job.views || 'N/A',
            applies: job.applies || 'N/A'
          });
        }
      });
    } catch (error) {
      console.error('Error processing job data:', error);
    }
  }

  setupJobClickHandlers() {
    const self = this;
    document.addEventListener('click', function(e) {
      const jobCard = e.target.closest('[data-job-id], .jobs-search-results__list-item, a[href*="/jobs/view/"]');
      if (jobCard) {
        setTimeout(() => self.showJobInsights(jobCard), 500);
      }
    });
  }

  showJobInsights(jobCard) {
    const jobId = jobCard.getAttribute('data-job-id') || 
                  this.extractJobId(jobCard.href || location.href);
    
    if (!jobId) return;
    
    const jobInfo = this.jobData.get(jobId);
    if (!jobInfo) return;

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

    setTimeout(() => this.removeExistingTooltip(), 10000);
  }

  removeExistingTooltip() {
    if (this.currentTooltip) {
      this.currentTooltip.remove();
      this.currentTooltip = null;
    }
  }
}

const jobInsights = new LinkedInJobInsights();
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => jobInsights.init());
} else {
  jobInsights.init();
}''',

            'styles.css': '''.linkedin-job-insights-tooltip {
  position: fixed;
  top: 20px;
  right: 20px;
  background: #ffffff;
  border: 2px solid #0a66c2;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  z-index: 10000;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  min-width: 280px;
  animation: slideIn 0.3s ease-out;
}

.job-insights-header {
  background: linear-gradient(135deg, #0a66c2, #004182);
  color: white;
  padding: 12px 16px;
  font-weight: 600;
  border-radius: 10px 10px 0 0;
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
  padding: 8px 0;
  border-bottom: 1px solid #e1e5e9;
}

.insight-row:last-child {
  border-bottom: none;
}

.insight-row .label {
  font-weight: 500;
  color: #5e6670;
}

.insight-row .value {
  font-weight: 600;
  color: #0a66c2;
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
}

@keyframes slideIn {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}''',

            'background.js': '''chrome.runtime.onInstalled.addListener(() => {
  console.log('LinkedIn Job Insights extension installed');
});''',

            'popup.html': '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { width: 250px; padding: 15px; font-family: Arial, sans-serif; }
        .header { color: #0a66c2; font-weight: bold; margin-bottom: 10px; }
        .status { padding: 8px; border-radius: 4px; margin: 10px 0; text-align: center; }
        .active { background: #d4edda; color: #155724; }
        .inactive { background: #f8d7da; color: #721c24; }
        button { width: 100%; padding: 8px; background: #0a66c2; color: white; border: none; border-radius: 4px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="header">📊 LinkedIn Job Insights</div>
    <div id="status" class="status inactive">Checking status...</div>
    <button onclick="chrome.tabs.create({url: 'https://linkedin.com/jobs'})">Open LinkedIn Jobs</button>
    <script>
        chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
            const tab = tabs[0];
            const isActive = tab.url && tab.url.includes('linkedin.com/jobs');
            document.getElementById('status').textContent = isActive ? '✅ Active' : '❌ Not on LinkedIn Jobs';
            document.getElementById('status').className = 'status ' + (isActive ? 'active' : 'inactive');
        });
    </script>
</body>
</html>''',

            'popup.js': '''// Popup functionality handled in HTML'''
        }
    
    def create_extension_files(self, base_path):
        """Create all extension files"""
        extension_path = Path(base_path) / self.extension_name
        extension_path.mkdir(parents=True, exist_ok=True)
        
        # Create icons directory
        icons_path = extension_path / 'icons'
        icons_path.mkdir(exist_ok=True)
        
        # Write extension files
        files = self.get_extension_files()
        for filename, content in files.items():
            (extension_path / filename).write_text(content, encoding='utf-8')
        
        # Create simple icon files (1x1 PNG placeholders)
        icon_data = b'\\x89PNG\\r\\n\\x1a\\n\\x00\\x00\\x00\\rIHDR\\x00\\x00\\x00\\x01\\x00\\x00\\x00\\x01\\x08\\x02\\x00\\x00\\x00\\x90wS\\xde\\x00\\x00\\x00\\x0cIDATx\\x9cc```\\x00\\x02\\x00\\x00\\x05\\x00\\x01\\r\\n-\\xdb\\x00\\x00\\x00\\x00IEND\\xaeB`\\x82'
        for size in [16, 48, 128]:
            (icons_path / f'icon{size}.png').write_bytes(icon_data)
        
        return extension_path
    
    def create_instructions(self, base_path):
        """Create installation instructions"""
        instructions = f'''# LinkedIn Job Insights Extension - Installation Complete!

## 🎉 Extension files created successfully!

### 📂 Location: {base_path / self.extension_name}

## 🚀 Next Steps:

### For Chrome:
1. Open Chrome and go to: chrome://extensions/
2. Enable "Developer mode" (toggle in top-right)
3. Click "Load unpacked"
4. Select the folder: {self.extension_name}

### For Edge:
1. Open Edge and go to: edge://extensions/
2. Enable "Developer mode" (toggle in left sidebar)
3. Click "Load unpacked"
4. Select the folder: {self.extension_name}

## ✨ How to Use:
1. Go to LinkedIn Jobs (linkedin.com/jobs)
2. Search and browse job listings
3. Click on any job posting
4. See the insights tooltip appear automatically!

## 📊 What You'll See:
- 📅 Job Listed Date
- ⏰ Job Expiry Date  
- 👀 View Count
- 📝 Application Count

The extension is now ready to use! Happy job hunting! 🚀
'''
        
        instructions_path = base_path / "INSTALLATION_COMPLETE.txt"
        instructions_path.write_text(instructions, encoding='utf-8')
        return instructions_path
    
    def open_extensions_page(self):
        """Open browser extensions page"""
        browser = self.browser_var.get()
        
        if browser == "chrome" or browser == "both":
            webbrowser.open("chrome://extensions/")
        
        if browser == "edge" or browser == "both":
            webbrowser.open("edge://extensions/")
    
    def install_extension(self):
        """Main installation process"""
        try:
            install_path = Path(self.path_var.get())
            install_path.mkdir(parents=True, exist_ok=True)
            
            self.update_progress(20, "Creating extension files...")
            time.sleep(0.5)
            
            # Create extension files
            extension_path = self.create_extension_files(install_path)
            self.installation_path = extension_path
            
            self.update_progress(60, "Writing configuration files...")
            time.sleep(0.5)
            
            # Create instructions
            instructions_path = self.create_instructions(install_path)
            
            self.update_progress(80, "Finalizing installation...")
            time.sleep(0.5)
            
            self.update_progress(100, "✅ Installation completed successfully!")
            
            # Enable buttons
            self.install_btn.config(state='disabled')
            self.open_extensions_btn.config(state='normal')
            
            # Show completion message
            result = messagebox.askyesno(
                "Installation Complete!", 
                f"Extension installed to: {extension_path}\\n\\n"
                "Would you like to open the browser extensions page now?\\n\\n"
                "You'll need to:\\n"
                "1. Enable 'Developer mode'\\n"
                "2. Click 'Load unpacked'\\n" 
                "3. Select the extension folder"
            )
            
            if result:
                self.open_extensions_page()
                
            # Open installation folder
            if sys.platform == "win32":
                os.startfile(install_path)
            
        except Exception as e:
            self.update_progress(0, f"❌ Error: {str(e)}")
            messagebox.showerror("Installation Error", f"Failed to install extension:\\n{str(e)}")
    
    def start_installation(self):
        """Start installation in separate thread"""
        self.install_btn.config(state='disabled')
        thread = threading.Thread(target=self.install_extension)
        thread.daemon = True
        thread.start()
    
    def run(self):
        """Run the installer GUI"""
        self.create_gui()
        self.root.mainloop()

if __name__ == "__main__":
    installer = LinkedInJobInsightsInstaller()
    installer.run()
