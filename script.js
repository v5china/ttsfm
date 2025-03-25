const OPENAI_API_URL = 'https://ttsapi.site/v1/audio/speech';
const processingStatus = document.getElementById('processing-status');
const activeRequests = document.getElementById('queue-size');
const lastUpdate = document.getElementById('last-update');
const maxQueueSize = document.getElementById('max-queue-size');
const queueProgressBar = document.getElementById('queue-progress-bar');
const statusIndicator = document.getElementById('status-indicator');
const queueLoadText = document.getElementById('queue-load-text');

// Track active requests
let currentActiveRequests = 0;

function updateProcessingStatus(requestCount) {
    if (requestCount > 0) {
        processingStatus.textContent = 'Processing';
        processingStatus.className = 'processing';
    } else {
        processingStatus.textContent = 'Idle';
        processingStatus.className = 'idle';
    }
}

function updateLastUpdate() {
    const now = new Date();
    if (lastUpdate) {
        lastUpdate.textContent = now.toLocaleTimeString();
    }
}

// Function to update queue size with visual indicators
async function updateQueueSize() {
    try {
        const response = await fetch('https://ttsapi.site/api/queue-size');
        const data = await response.json();
        
        // Update text values
        document.getElementById('queue-size').textContent = data.queue_size;
        document.getElementById('max-queue-size').textContent = data.max_queue_size;
        
        // Calculate load percentage
        const loadPercentage = (data.queue_size / data.max_queue_size) * 100;
        
        // Update progress bar width
        queueProgressBar.style.width = `${loadPercentage}%`;
        
        // Update status indicators based on load
        updateLoadStatus(loadPercentage);
        
    } catch (error) {
        console.error('Error fetching queue size:', error);
    }
}

// Function to update load status indicators
function updateLoadStatus(loadPercentage) {
    // Remove all existing classes
    statusIndicator.classList.remove('indicator-low', 'indicator-medium', 'indicator-high');
    queueProgressBar.classList.remove('progress-low', 'progress-medium', 'progress-high');
    queueLoadText.classList.remove('low-load', 'medium-load', 'high-load');
    
    // Apply appropriate classes based on load percentage
    if (loadPercentage >= 75) {
        // High load (75-100%)
        statusIndicator.classList.add('indicator-high');
        queueProgressBar.classList.add('progress-high');
        queueLoadText.classList.add('high-load');
        queueLoadText.textContent = 'High Load';
    } else if (loadPercentage >= 40) {
        // Medium load (40-75%)
        statusIndicator.classList.add('indicator-medium');
        queueProgressBar.classList.add('progress-medium');
        queueLoadText.classList.add('medium-load');
        queueLoadText.textContent = 'Medium Load';
    } else {
        // Low load (0-40%)
        statusIndicator.classList.add('indicator-low');
        queueProgressBar.classList.add('progress-low');
        queueLoadText.classList.add('low-load');
        queueLoadText.textContent = loadPercentage > 0 ? 'Low Load' : 'No Load';
    }
}

// Update queue size every 2 seconds
setInterval(updateQueueSize, 2000);

// Initial update
updateQueueSize();

// Function to copy code blocks
function copyCode(button) {
    const codeBlock = button.closest('.code-block').querySelector('code');
    const text = codeBlock.textContent;
    
    navigator.clipboard.writeText(text).then(() => {
        // Visual feedback
        const originalIcon = button.innerHTML;
        button.innerHTML = '<i class="fas fa-check"></i>';
        button.style.color = '#4CAF50';
        
        // Reset after 2 seconds
        setTimeout(() => {
            button.innerHTML = originalIcon;
            button.style.color = '';
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy text:', err);
        // Visual feedback for error
        button.style.color = '#f44336';
        setTimeout(() => {
            button.style.color = '';
        }, 2000);
    });
}

// Playground functionality
document.addEventListener('DOMContentLoaded', function() {
    const submitButton = document.getElementById('playground-submit');
    const textInput = document.getElementById('playground-text');
    const voiceSelect = document.getElementById('playground-voice');
    const instructionsInput = document.getElementById('playground-instructions');
    const statusDiv = document.getElementById('playground-status');
    const audioDiv = document.getElementById('playground-audio');

    submitButton.addEventListener('click', async function() {
        const text = textInput.value.trim();
        const voice = voiceSelect.value;
        const instructions = instructionsInput.value.trim();

        if (!text) {
            showStatus('Please enter some text to convert', 'error');
            return;
        }

        // Disable the submit button and show loading state
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
        showStatus('Generating speech...', 'success');
        audioDiv.innerHTML = '';

        try {
            const response = await fetch(OPENAI_API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    input: text,
                    voice: voice,
                    instructions: instructions || undefined
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to generate speech');
            }

            const blob = await response.blob();
            const audioUrl = URL.createObjectURL(blob);
            
            // Create audio element
            const audio = document.createElement('audio');
            audio.controls = true;
            audio.src = audioUrl;
            
            // Clear previous audio and add new one
            audioDiv.innerHTML = '';
            audioDiv.appendChild(audio);
            
            showStatus('Speech generated successfully!', 'success');
        } catch (error) {
            showStatus(error.message || 'Failed to generate speech', 'error');
        } finally {
            // Re-enable the submit button and restore original text
            submitButton.disabled = false;
            submitButton.innerHTML = '<i class="fas fa-play"></i> Generate Speech';
        }
    });

    function showStatus(message, type) {
        statusDiv.textContent = message;
        statusDiv.className = `playground-status ${type}`;
    }
}); 