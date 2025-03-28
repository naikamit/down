// app/static/js/dashboard.js
document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const eventsList = document.getElementById('events-list');
    const totalEventsEl = document.getElementById('total-events');
    const incomingEventsEl = document.getElementById('incoming-events');
    const outgoingEventsEl = document.getElementById('outgoing-events');
    const errorEventsEl = document.getElementById('error-events');
    const filterButtons = document.querySelectorAll('.filter-btn');
    
    // Variables
    let events = [];
    let currentFilter = 'all';
    let pollingInterval = 5000; // 5 seconds
    
    // Initial load
    fetchEvents();
    
    // Set up polling
    setInterval(fetchEvents, pollingInterval);
    
    // Filter button events
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Update active button
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Apply filter
            currentFilter = this.dataset.filter;
            renderEvents();
        });
    });
    
    // Fetch events from the API
    function fetchEvents() {
        fetch('/api/events')
            .then(response => response.json())
            .then(data => {
                events = data;
                updateStats();
                renderEvents();
            })
            .catch(error => {
                console.error('Error fetching events:', error);
                eventsList.innerHTML = `<div class="loading">Error loading events: ${error.message}</div>`;
            });
    }
    
    // Update stats counters
    function updateStats() {
        totalEventsEl.textContent = events.length;
        incomingEventsEl.textContent = events.filter(e => e.direction === 'incoming').length;
        outgoingEventsEl.textContent = events.filter(e => e.direction === 'outgoing').length;
        errorEventsEl.textContent = events.filter(e => e.direction === 'error').length;
    }
    
    // Render events based on current filter
    function renderEvents() {
        let filteredEvents = events;
        
        // Apply filter
        if (currentFilter !== 'all') {
            filteredEvents = events.filter(e => e.direction === currentFilter);
        }
        
        // Render events
        if (filteredEvents.length === 0) {
            eventsList.innerHTML = '<div class="loading">No events to display</div>';
            return;
        }
        
        eventsList.innerHTML = filteredEvents.map((event, index) => {
            return `
                <div class="event-item" data-direction="${event.direction}">
                    <div class="event-header" onclick="toggleEventBody(${index})">
                        <div class="event-type">
                            <span class="event-direction ${event.direction}">${event.direction}</span>
                            <span>${event.type}</span>
                        </div>
                        <div class="event-timestamp">${event.timestamp}</div>
                    </div>
                    <div class="event-body" id="event-body-${index}">
                        <pre>${JSON.stringify(event.data, null, 2)}</pre>
                    </div>
                </div>
            `;
        }).join('');
    }
});

// Global function to toggle event body visibility
function toggleEventBody(index) {
    const eventBody = document.getElementById(`event-body-${index}`);
    eventBody.classList.toggle('active');
}
