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
        processingNow: "Processing Now",
        waitingInQueue: "Waiting in Queue",
        totalReported: "Total Reported",
        maxCapacity: "Maximum Capacity",
        noLoad: "No Load",
        lowLoad: "Low Load",
        mediumLoad: "Medium Load",
        highLoad: "High Load",
        error: "Error",
        queueError: "Queue status unavailable"
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
        processingNow: "正在处理",
        waitingInQueue: "队列等待",
        totalReported: "报告总数",
        maxCapacity: "最大容量",
        noLoad: "无负载",
        lowLoad: "低负载",
        mediumLoad: "中负载",
        highLoad: "高负载",
        error: "错误",
        queueError: "队列状态不可用"
    }
};

// Function to fetch and update version
async function updateVersion() {
    const versionElement = document.getElementById('version');
    if (!versionElement) return;

    // Set loading text based on language
    const isChinesePage = window.location.pathname.includes('_zh.html');
    versionElement.textContent = isChinesePage ? '加载中...' : 'Loading...';

    try {
        const response = await fetch('/api/version');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        versionElement.textContent = data.version;
    } catch (error) {
        console.error('Error fetching version:', error);
        versionElement.textContent = isChinesePage ? '未知' : 'Unknown';
    }
}

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
    
    // Initial version update
    updateVersion();
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
    const processingTasksElement = document.getElementById('processing-tasks');
    const waitingTasksElement = document.getElementById('waiting-tasks');
    const totalTasksElement = document.getElementById('total-tasks');
    const maxQueueSizeElement = document.getElementById('max-queue-size');
    const queueProgressBar = document.getElementById('queue-progress-bar');
    const statusIndicator = document.getElementById('status-indicator');
    const queueLoadText = document.getElementById('queue-load-text');
    const queueErrorTextElement = document.getElementById('queue-error-text');

    try {
        const response = await fetch('/api/queue-size');
        // Don't throw immediately for non-200, as 500 might contain error info
        const data = await response.json(); 

        if (!response.ok || data.error) {
            // Handle error reported by the API (e.g., inspection failure)
             console.error('Error fetching queue size:', data.error || `HTTP error! status: ${response.status}`);
             showQueueErrorState(data.error || `HTTP ${response.status}`);
             return; // Stop processing if there's an error
        }
        
        // Clear any previous error message
        if (queueErrorTextElement) {
            queueErrorTextElement.textContent = '';
            queueErrorTextElement.style.display = 'none';
        }
        
        // Calculate waiting tasks
        const waitingTasks = data.reserved_tasks + data.scheduled_tasks;
        
        // Update text content
        if (processingTasksElement) processingTasksElement.textContent = data.active_tasks;
        if (waitingTasksElement) waitingTasksElement.textContent = waitingTasks;
        if (totalTasksElement) totalTasksElement.textContent = data.total_reported_by_workers;
        if (maxQueueSizeElement) maxQueueSizeElement.textContent = data.max_queue_size_limit;
        
        // Calculate load percentage based on total reported tasks
        // Avoid division by zero if max_queue_size_limit is 0 or undefined
        const maxLimit = data.max_queue_size_limit || 1; // Use 1 to prevent division by zero
        const loadPercentage = (data.total_reported_by_workers / maxLimit) * 100;
        
        // Update progress bar
        if (queueProgressBar) {
            queueProgressBar.style.width = `${Math.min(loadPercentage, 100)}%`;
        }
        
        // Update status indicators
        if (statusIndicator && queueProgressBar && queueLoadText) {
            updateLoadStatus(loadPercentage);
        }
        
    } catch (error) {
        // Handle network errors or JSON parsing errors
        console.error('Failed to fetch or parse queue size:', error);
        showQueueErrorState(translations[currentLang].queueError || 'Queue status unavailable');
    }
}

// Function to display error state in the queue status UI
function showQueueErrorState(errorMessage) {
    const processingTasksElement = document.getElementById('processing-tasks');
    const waitingTasksElement = document.getElementById('waiting-tasks');
    const totalTasksElement = document.getElementById('total-tasks');
    const maxQueueSizeElement = document.getElementById('max-queue-size');
    const queueProgressBar = document.getElementById('queue-progress-bar');
    const statusIndicator = document.getElementById('status-indicator');
    const queueLoadText = document.getElementById('queue-load-text');
    const queueErrorTextElement = document.getElementById('queue-error-text');
    
    if (processingTasksElement) processingTasksElement.textContent = '?';
    if (waitingTasksElement) waitingTasksElement.textContent = '?';
    if (totalTasksElement) totalTasksElement.textContent = '?';
    if (maxQueueSizeElement) maxQueueSizeElement.textContent = '?';
    
    if (queueProgressBar) {
        queueProgressBar.style.width = '0%';
        queueProgressBar.classList.remove('progress-low', 'progress-medium', 'progress-high');
    }
    if (statusIndicator) {
        statusIndicator.classList.remove('indicator-low', 'indicator-medium', 'indicator-high');
        statusIndicator.classList.add('indicator-error');
    }
    if (queueLoadText) {
        queueLoadText.classList.remove('low-load', 'medium-load', 'high-load');
        queueLoadText.textContent = translations[currentLang].error || 'Error';
    }
    if (queueErrorTextElement) {
        queueErrorTextElement.textContent = errorMessage;
        queueErrorTextElement.style.display = 'block';
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
    const formatSelect = document.getElementById('playground-format');
    const statusDiv = document.getElementById('playground-status');
    const audioDiv = document.getElementById('playground-audio');

    submitButton.addEventListener('click', async function() {
        const text = textInput.value.trim();
        const voice = voiceSelect.value;
        const instructions = instructionsInput.value.trim();
        const format = formatSelect.value;

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
                    instructions: instructions || undefined,
                    response_format: format
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

// Voice sample functionality
let currentSampleAudio = null;

// Function to load and play voice sample
async function loadVoiceSample(voice) {
    const previewAudioDiv = document.getElementById('preview-audio');
    
    try {
        // Create new audio element
        const response = await fetch(`/api/voice-sample/${voice}`);
        if (!response.ok) {
            throw new Error(`Failed to load voice sample: ${response.statusText}`);
        }
        
        const blob = await response.blob();
        const audioUrl = URL.createObjectURL(blob);
        
        // Create and configure audio element
        currentSampleAudio = document.createElement('audio');
        currentSampleAudio.controls = true;
        currentSampleAudio.src = audioUrl;
        
        // Clear previous audio and add new one
        previewAudioDiv.innerHTML = '';
        previewAudioDiv.appendChild(currentSampleAudio);
        
    } catch (error) {
        console.error('Error loading voice sample:', error);
        // Show error in status
        const statusDiv = document.getElementById('playground-status');
        statusDiv.innerHTML = `<div class="error-message">Error loading voice sample: ${error.message}</div>`;
    }
}

// Add voice selection change handler
document.getElementById('playground-voice').addEventListener('change', function() {
    loadVoiceSample(this.value);
});

// Load initial voice sample when page loads
document.addEventListener('DOMContentLoaded', function() {
    const voiceSelect = document.getElementById('playground-voice');
    if (voiceSelect) {
        loadVoiceSample(voiceSelect.value);
    }
});

// Update the example code blocks
document.addEventListener('DOMContentLoaded', function() {
    // Update Python example
    const pythonExample = document.querySelector('.language-python');
    if (pythonExample) {
        pythonExample.textContent = `import requests

url = "https://ttsapi.site/v1/audio/speech"
headers = {
    "Content-Type": "application/json"
}
data = {
    "input": "Hello, this is a test.",
    "voice": "alloy",
    "instructions": "Speak in a cheerful and upbeat tone.",  # Optional
    "response_format": "mp3"  # Optional, supported formats: mp3, opus, aac, flac, wav, pcm
}

response = requests.post(url, json=data, headers=headers)
if response.status_code == 200:
    # Get the appropriate file extension based on format
    format = data.get("response_format", "mp3")
    filename = f"output.{format}"
    
    # Save the audio file
    with open(filename, "wb") as f:
        f.write(response.content)
    print(f"Audio saved as {filename}")
else:
    print(f"Error: {response.status_code}, {response.json()}")`;
    }

    // Update JavaScript example
    const javascriptExample = document.querySelector('.language-javascript');
    if (javascriptExample) {
        javascriptExample.textContent = `async function generateSpeech() {
    const response = await fetch('https://ttsapi.site/v1/audio/speech', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            input: 'Hello, this is a test.',
            voice: 'alloy',
            instructions: 'Speak in a cheerful and upbeat tone.',  // Optional
            response_format: 'mp3'  // Optional, supported formats: mp3, opus, aac, flac, wav, pcm
        })
    });

    if (response.ok) {
        const blob = await response.blob();
        const audio = new Audio(URL.createObjectURL(blob));
        audio.play();
    } else {
        const error = await response.json();
        console.error('Error:', error);
    }
}`;
    }
}); 