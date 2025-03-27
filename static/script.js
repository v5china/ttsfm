// Use the current host for API requests
const OPENAI_API_URL = `${window.location.protocol}//${window.location.host}/v1/audio/speech`;
const processingStatus = document.getElementById('processing-status');
const activeRequests = document.getElementById('queue-size');
const lastUpdate = document.getElementById('last-update');
const maxQueueSize = document.getElementById('max-queue-size');
const queueProgressBar = document.getElementById('queue-progress-bar');
const statusIndicator = document.getElementById('status-indicator');
const queueLoadText = document.getElementById('queue-load-text');

// Track active requests
let currentActiveRequests = 0;

// Initialize current language
let currentLang = 'en';

// Language translations
const translations = {
    en: {
        title: "OpenAI TTS API Documentation",
        subtitle: "Text-to-Speech API with Multiple Voice Options",
        tryItOut: "Try It Out",
        textToConvert: "Text to Convert",
        voice: "Voice",
        instructions: "Instructions (Optional)",
        generateSpeech: "Generate Speech",
        quickStart: "Quick Start",
        availableVoices: "Available Voices",
        apiReference: "API Reference",
        queueStatus: "Queue Status",
        activeRequests: "Active Requests",
        maxCapacity: "Maximum Capacity",
        noLoad: "No Load",
        lowLoad: "Low Load",
        mediumLoad: "Medium Load",
        highLoad: "High Load"
    },
    zh: {
        title: "OpenAI TTS API 文档",
        subtitle: "支持多种语音的文本转语音 API",
        tryItOut: "立即体验",
        textToConvert: "要转换的文本",
        voice: "语音",
        instructions: "指令（可选）",
        generateSpeech: "生成语音",
        quickStart: "快速开始",
        availableVoices: "可用语音",
        apiReference: "API 参考",
        queueStatus: "队列状态",
        activeRequests: "活动请求",
        maxCapacity: "最大容量",
        noLoad: "无负载",
        lowLoad: "低负载",
        mediumLoad: "中负载",
        highLoad: "高负载"
    }
};

// Language switching functionality
document.addEventListener('DOMContentLoaded', function() {
    const langButtons = document.querySelectorAll('.lang-btn');
    
    // Set initial language based on current page
    const isChinesePage = window.location.pathname.includes('_zh.html');
    currentLang = isChinesePage ? 'zh' : 'en';
    
    // Update active state of language buttons
    langButtons.forEach(btn => {
        if (btn.getAttribute('data-lang') === currentLang) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    
    // Initial queue size update
    updateQueueSize();
});

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
        const response = await fetch('/api/queue-size');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        
        // Update text values
        document.getElementById('queue-size').textContent = data.queue_size;
        document.getElementById('max-queue-size').textContent = data.max_queue_size;
        
        // Calculate load percentage
        const loadPercentage = (data.queue_size / data.max_queue_size) * 100;
        
        // Update progress bar width
        queueProgressBar.style.width = `${Math.min(loadPercentage, 100)}%`;
        
        // Update status indicators based on load
        updateLoadStatus(loadPercentage);
        
    } catch (error) {
        console.error('Error fetching queue size:', error);
        // Show error state in UI
        document.getElementById('queue-size').textContent = '?';
        document.getElementById('max-queue-size').textContent = '?';
        queueProgressBar.style.width = '0%';
        statusIndicator.classList.remove('indicator-low', 'indicator-medium', 'indicator-high');
        statusIndicator.classList.add('indicator-error');
        queueProgressBar.classList.remove('progress-low', 'progress-medium', 'progress-high');
        queueLoadText.classList.remove('low-load', 'medium-load', 'high-load');
        queueLoadText.textContent = 'Error';
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
        queueLoadText.textContent = translations[currentLang].highLoad;
    } else if (loadPercentage >= 40) {
        // Medium load (40-75%)
        statusIndicator.classList.add('indicator-medium');
        queueProgressBar.classList.add('progress-medium');
        queueLoadText.classList.add('medium-load');
        queueLoadText.textContent = translations[currentLang].mediumLoad;
    } else {
        // Low load (0-40%)
        statusIndicator.classList.add('indicator-low');
        queueProgressBar.classList.add('progress-low');
        queueLoadText.classList.add('low-load');
        queueLoadText.textContent = loadPercentage > 0 ? translations[currentLang].lowLoad : translations[currentLang].noLoad;
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