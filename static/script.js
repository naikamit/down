// static/script.js - Dashboard JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const logsContainer = document.getElementById('logs');
    const totalRequestsEl = document.getElementById('total-requests');
    const successfulRequestsEl = document.getElementById('successful-requests');
    const failedRequestsEl = document.getElementById('failed-requests');
    
    // Filters
    const showRequestsCheckbox = document.getElementById('show-requests');
    const showResponsesCheckbox = document.getElementById('show-responses');
    const showErrorsCheckbox = document.getElementById('show-errors');
    
    // Stats
    let totalRequests = 0;
    let successfulRequests = 0;
    let failedRequests = 0;
    
    // Function to fetch logs
    async function fetchLogs() {
        try {
            const response = await fetch('/api/logs');
            if (!response.ok) {
                throw new Error('Failed to fetch logs');
            }
            
            const logs = await response.json();
            renderLogs(logs);
            
            // Update stats
            updateStats(logs);
            
            // Apply filters
            applyFilters();
        } catch (error) {
            console.error('Error fetching logs:', error);
        }
    }
    
    // Function to render logs
    function renderLogs(logs) {
        logsContainer.innerHTML = '';
        
        // Sort logs by ID in descending order (newest first)
        logs.sort((a, b) => b.id - a.id);
        
        logs.forEach(log => {
            const logEntry = document.createElement('div');
            logEntry.className = `log-entry ${log.type} ${log.status}`;
            logEntry.dataset.type = log.type;
            logEntry.dataset.status = log.status;
            
            // Create log header
            const logHeader = document.createElement('div');
            logHeader.className = 'log-header';
            
            // Create log ID and timestamp
            const idTimestamp = document.createElement('div');
            
            const logId = document.createElement('span');
            logId.className = 'log-id';
            logId.textContent = `#${log.id} `;
            idTimestamp.appendChild(logId);
            
            const timestamp = document.createElement('span');
            timestamp.className = 'log-timestamp';
            timestamp.textContent = log.timestamp;
            idTimestamp.appendChild(timestamp);
            
            logHeader.appendChild(idTimestamp);
            
            // Create log type/status badge
            const typeBadge = document.createElement('span');
            typeBadge.className = `log-type ${log.type === 'request' ? 'request' : log.status}`;
            typeBadge.textContent = log.type === 'request' ? 'Request' : 
                                   (log.status === 'error' ? 'Error' : 'Response');
            logHeader.appendChild(typeBadge);
            
            logEntry.appendChild(logHeader);
            
            // Create log summary
            const logSummary = document.createElement('div');
            logSummary.className = 'log-summary';
            
            if (log.type === 'request') {
                logSummary.textContent = `${log.method} ${log.endpoint}`;
                
                // If it's a webhook request, add the signal type
                if (log.endpoint === '/webhook' && log.data && log.data.signal) {
                    logSummary.textContent += ` - Signal: ${log.data.signal}`;
                }
            } else {
                logSummary.textContent = log.status === 'error' ? 'Error Response' : 'Success Response';
            }
            
            logEntry.appendChild(logSummary);
            
            // Create log details - always visible
            const logDetails = document.createElement('div');
            logDetails.className = 'log-details';
            // No longer hidden by default
            
            if (log.type === 'request') {
                // Method and Endpoint
                const methodEndpoint = document.createElement('div');
                methodEndpoint.className = 'log-detail';
                
                const methodEndpointLabel = document.createElement('div');
                methodEndpointLabel.className = 'log-detail-label';
                methodEndpointLabel.textContent = 'Method / Endpoint';
                methodEndpoint.appendChild(methodEndpointLabel);
                
                const methodEndpointContent = document.createElement('div');
                methodEndpointContent.className = 'log-content';
                methodEndpointContent.textContent = `${log.method} ${log.endpoint}`;
                methodEndpoint.appendChild(methodEndpointContent);
                
                logDetails.appendChild(methodEndpoint);
                
                // Data
                if (log.data) {
                    const data = document.createElement('div');
                    data.className = 'log-detail';
                    
                    const dataLabel = document.createElement('div');
                    dataLabel.className = 'log-detail-label';
                    dataLabel.textContent = 'Request Data';
                    data.appendChild(dataLabel);
                    
                    const dataContent = document.createElement('div');
                    dataContent.className = 'log-content';
                    dataContent.textContent = JSON.stringify(log.data, null, 2);
                    data.appendChild(dataContent);
                    
                    logDetails.appendChild(data);
                }
                
                // Params
                if (log.params) {
                    const params = document.createElement('div');
                    params.className = 'log-detail';
                    
                    const paramsLabel = document.createElement('div');
                    paramsLabel.className = 'log-detail-label';
                    paramsLabel.textContent = 'Request Parameters';
                    params.appendChild(paramsLabel);
                    
                    const paramsContent = document.createElement('div');
                    paramsContent.className = 'log-content';
                    paramsContent.textContent = JSON.stringify(log.params, null, 2);
                    params.appendChild(paramsContent);
                    
                    logDetails.appendChild(params);
                }
            } else {
                // Response
                const response = document.createElement('div');
                response.className = 'log-detail';
                
                const responseLabel = document.createElement('div');
                responseLabel.className = 'log-detail-label';
                responseLabel.textContent = 'Response Data';
                response.appendChild(responseLabel);
                
                const responseContent = document.createElement('div');
                responseContent.className = 'log-content';
                responseContent.textContent = JSON.stringify(log.response, null, 2);
                response.appendChild(responseContent);
                
                logDetails.appendChild(response);
            }
            
            logEntry.appendChild(logDetails);
            logsContainer.appendChild(logEntry);
        });
    }
    
    // Function to update stats
    function updateStats(logs) {
        const requestLogs = logs.filter(log => log.type === 'request');
        const successLogs = logs.filter(log => log.status === 'success');
        const errorLogs = logs.filter(log => log.status === 'error');
        
        totalRequests = requestLogs.length;
        successfulRequests = successLogs.length;
        failedRequests = errorLogs.length;
        
        totalRequestsEl.textContent = totalRequests;
        successfulRequestsEl.textContent = successfulRequests;
        failedRequestsEl.textContent = failedRequests;
    }
    
    // Function to apply filters
    function applyFilters() {
        const showRequests = showRequestsCheckbox.checked;
        const showResponses = showResponsesCheckbox.checked;
        const showErrors = showErrorsCheckbox.checked;
        
        // Get all log entries
        const logEntries = document.querySelectorAll('.log-entry');
        
        logEntries.forEach(entry => {
            const type = entry.dataset.type;
            const status = entry.dataset.status;
            
            if (type === 'request' && !showRequests) {
                entry.style.display = 'none';
            } else if (type === 'response' && status === 'error' && !showErrors) {
                entry.style.display = 'none';
            } else if (type === 'response' && status !== 'error' && !showResponses) {
                entry.style.display = 'none';
            } else {
                entry.style.display = 'block';
            }
        });
    }
    
    // Add event listeners for filters
    showRequestsCheckbox.addEventListener('change', applyFilters);
    showResponsesCheckbox.addEventListener('change', applyFilters);
    showErrorsCheckbox.addEventListener('change', applyFilters);
    
    // Initial fetch
    fetchLogs();
    
    // Set up polling to refresh logs every 5 seconds
    setInterval(fetchLogs, 5000);
});
