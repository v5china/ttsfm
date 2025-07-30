// TTSFM Enhanced Playground with WebSocket Streaming Support - Fixed Version

// Global variables
let currentAudioBlob = null;
let currentFormat = 'mp3';
let batchResults = [];
let wsClient = null;
let streamingMode = false;
let currentStreamRequest = null;

// Initialize playground
document.addEventListener('DOMContentLoaded', function() {
    initializePlayground();
    initializeWebSocket();
});

// Initialize WebSocket client
function initializeWebSocket() {
    // Check if Socket.IO is available
    if (typeof io === 'undefined') {
        console.warn('Socket.IO not loaded. WebSocket streaming will be disabled.');
        return;
    }
    
    // Initialize WebSocket client
    wsClient = new WebSocketTTSClient({
        socketUrl: window.location.origin,
        debug: true,
        onConnect: () => {
            console.log('WebSocket connected');
            updateStreamingStatus('connected');
        },
        onDisconnect: () => {
            console.log('WebSocket disconnected');
            updateStreamingStatus('disconnected');
        },
        onError: (error) => {
            console.error('WebSocket error:', error);
            updateStreamingStatus('error');
        }
    });
}

// Update streaming status indicator
function updateStreamingStatus(status) {
    const indicator = document.getElementById('streaming-indicator');
    if (!indicator) return;
    
    indicator.className = 'streaming-status';
    switch(status) {
        case 'connected':
            indicator.classList.add('connected');
            indicator.innerHTML = '<i class="fas fa-bolt"></i> Streaming Ready';
            enableStreamingMode(true);
            break;
        case 'disconnected':
            indicator.classList.add('disconnected');
            indicator.innerHTML = '<i class="fas fa-plug"></i> Streaming Offline';
            enableStreamingMode(false);
            break;
        case 'error':
            indicator.classList.add('error');
            indicator.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Connection Error';
            enableStreamingMode(false);
            break;
        case 'streaming':
            indicator.classList.add('streaming');
            indicator.innerHTML = '<i class="fas fa-stream"></i> Streaming...';
            break;
    }
}

// Enable/disable streaming mode
function enableStreamingMode(enabled) {
    const streamToggle = document.getElementById('stream-mode-toggle');
    if (streamToggle) {
        streamToggle.disabled = !enabled;
        if (!enabled && streamingMode) {
            streamingMode = false;
            streamToggle.checked = false;
        }
    }
}

// Check authentication status
async function checkAuthStatus() {
    try {
        const response = await fetch('/api/auth-status');
        const data = await response.json();

        const apiKeySection = document.getElementById('api-key-section');
        if (apiKeySection) {
            if (data.api_key_required) {
                apiKeySection.style.display = 'block';
                const apiKeyInput = document.getElementById('api-key-input');
                if (apiKeyInput) {
                    apiKeyInput.required = true;
                }
            } else {
                apiKeySection.style.display = 'none';
            }
        }
    } catch (error) {
        console.warn('Could not check auth status:', error);
    }
}

function initializePlayground() {
    console.log('Initializing enhanced playground...');
    checkAuthStatus();
    loadVoices();
    loadFormats();
    updateCharCount();
    setupEventListeners();
    setupStreamingControls();
    console.log('Enhanced playground initialization complete');
}

function setupStreamingControls() {
    // Add streaming mode toggle
    const generateButton = document.getElementById('generate-btn');
    if (generateButton && generateButton.parentElement) {
        const streamingControls = document.createElement('div');
        streamingControls.className = 'streaming-controls mt-3';
        streamingControls.innerHTML = `
            <div class="form-check form-switch">
                <input class="form-check-input" type="checkbox" id="stream-mode-toggle" disabled>
                <label class="form-check-label" for="stream-mode-toggle">
                    <i class="fas fa-bolt me-1"></i>
                    Enable WebSocket Streaming
                    <small class="text-muted">(Real-time audio chunks)</small>
                </label>
            </div>
            <div id="streaming-indicator" class="streaming-status mt-2"></div>
        `;
        generateButton.parentElement.appendChild(streamingControls);
        
        // Add toggle event listener
        const toggle = document.getElementById('stream-mode-toggle');
        if (toggle) {
            toggle.addEventListener('change', (e) => {
                streamingMode = e.target.checked;
                console.log('Streaming mode:', streamingMode ? 'ON' : 'OFF');
                
                // Update button text
                const btnText = generateButton.querySelector('.btn-text');
                if (btnText) {
                    if (streamingMode) {
                        btnText.innerHTML = '<i class="fas fa-bolt me-2"></i>Stream Speech';
                    } else {
                        btnText.innerHTML = '<i class="fas fa-magic me-2"></i>' + 
                            (window.currentLocale === 'zh' ? '生成语音' : 'Generate Speech');
                    }
                }
            });
        }
    }
    
    // Add streaming progress section and error message div
    const audioResult = document.getElementById('audio-result');
    if (audioResult && audioResult.parentElement) {
        // Add error message div
        const errorDiv = document.createElement('div');
        errorDiv.id = 'error-message';
        errorDiv.className = 'alert alert-danger';
        errorDiv.style.display = 'none';
        audioResult.parentElement.insertBefore(errorDiv, audioResult);
        
        // Add loading section
        const loadingDiv = document.createElement('div');
        loadingDiv.id = 'loading-section';
        loadingDiv.className = 'text-center';
        loadingDiv.style.display = 'none';
        loadingDiv.innerHTML = `
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Generating speech...</p>
        `;
        audioResult.parentElement.insertBefore(loadingDiv, audioResult);
        
        // Add progress section
        const progressSection = document.createElement('div');
        progressSection.id = 'streaming-progress';
        progressSection.className = 'streaming-progress-section';
        progressSection.style.display = 'none';
        progressSection.innerHTML = `
            <div class="card border-primary">
                <div class="card-body">
                    <h5 class="card-title">
                        <i class="fas fa-stream me-2"></i>Streaming Progress
                    </h5>
                    <div class="progress mb-3" style="height: 25px;">
                        <div class="progress-bar progress-bar-striped progress-bar-animated" 
                             id="stream-progress-bar" 
                             role="progressbar" 
                             style="width: 0%">
                            <span id="stream-progress-text">0%</span>
                        </div>
                    </div>
                    <div class="row text-center">
                        <div class="col-md-4">
                            <h6>Chunks</h6>
                            <p class="h5"><span id="chunks-count">0</span> / <span id="total-chunks">0</span></p>
                        </div>
                        <div class="col-md-4">
                            <h6>Data</h6>
                            <p class="h5" id="data-transferred">0 KB</p>
                        </div>
                        <div class="col-md-4">
                            <h6>Time</h6>
                            <p class="h5" id="stream-time">0.0s</p>
                        </div>
                    </div>
                    <div id="chunks-visualization" class="chunks-visual mt-3"></div>
                </div>
            </div>
        `;
        audioResult.parentElement.insertBefore(progressSection, audioResult);
    }
}

function setupEventListeners() {
    console.log('Setting up event listeners...');

    // Form and input events
    const textInput = document.getElementById('text-input');
    if (textInput) {
        textInput.addEventListener('input', updateCharCount);
    }

    // Form submit
    const form = document.getElementById('tts-form');
    if (form) {
        form.addEventListener('submit', function(event) {
            event.preventDefault();
            event.stopPropagation();
            
            if (streamingMode && wsClient && wsClient.isConnected()) {
                generateSpeechStreaming(event);
            } else {
                generateSpeech(event);
            }
            
            return false;
        });
    }

    // Download button
    const downloadBtn = document.getElementById('download-btn');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', downloadAudio);
    }
}

// Generate speech using WebSocket streaming
async function generateSpeechStreaming(event) {
    event.preventDefault();
    
    const text = document.getElementById('text-input').value.trim();
    const voice = document.getElementById('voice-select').value;
    const format = document.getElementById('format-select').value;
    
    if (!text) {
        showError('Please enter some text to convert');
        return;
    }
    
    // Reset UI
    hideError();
    hideResults();
    disableForm();
    
    // Show streaming progress
    const progressSection = document.getElementById('streaming-progress');
    if (progressSection) progressSection.style.display = 'block';
    
    // Reset progress
    updateStreamingProgress(0, 0, 0);
    const chunksViz = document.getElementById('chunks-visualization');
    if (chunksViz) chunksViz.innerHTML = '';
    
    // Update status
    updateStreamingStatus('streaming');
    
    const startTime = Date.now();
    let audioChunks = [];
    
    try {
        const result = await wsClient.generateSpeech(text, {
            voice: voice,
            format: format,
            chunkSize: 512,
            onStart: (data) => {
                currentStreamRequest = data.request_id;
                console.log('Streaming started:', data);
            },
            onProgress: (progress) => {
                updateStreamingProgress(
                    progress.progress,
                    progress.chunksCompleted,
                    progress.totalChunks
                );
                
                const elapsed = (Date.now() - startTime) / 1000;
                const timeEl = document.getElementById('stream-time');
                if (timeEl) timeEl.textContent = `${elapsed.toFixed(1)}s`;
            },
            onChunk: (chunk) => {
                // Visualize chunk
                const chunksViz = document.getElementById('chunks-visualization');
                if (chunksViz) {
                    const chunkViz = document.createElement('div');
                    chunkViz.className = 'chunk-indicator';
                    chunkViz.title = `Chunk ${chunk.chunkIndex + 1} - ${(chunk.audioData.byteLength / 1024).toFixed(1)}KB`;
                    chunkViz.innerHTML = `<i class="fas fa-music"></i>`;
                    chunksViz.appendChild(chunkViz);
                }
                
                // Update data transferred
                const dataEl = document.getElementById('data-transferred');
                if (dataEl) {
                    const currentData = parseFloat(dataEl.textContent) || 0;
                    const newData = currentData + (chunk.audioData.byteLength / 1024);
                    dataEl.textContent = `${newData.toFixed(1)} KB`;
                }
                
                audioChunks.push(chunk);
            },
            onComplete: (result) => {
                console.log('Streaming complete:', result);
                
                // Create blob from audio data
                currentAudioBlob = new Blob([result.audioData], { type: `audio/${result.format}` });
                currentFormat = result.format;
                
                // Show results
                showResults(currentAudioBlob, result.format);
                
                // Update final stats
                const totalTime = (Date.now() - startTime) / 1000;
                showStreamingStats({
                    chunks: result.chunks.length,
                    totalSize: (result.audioData.byteLength / 1024).toFixed(1),
                    totalTime: totalTime.toFixed(2),
                    format: result.format
                });
            },
            onError: (error) => {
                showError(`Streaming error: ${error.message}`);
                enableForm();
                if (progressSection) progressSection.style.display = 'none';
            }
        });
        
    } catch (error) {
        showError(`Failed to stream speech: ${error.message}`);
        enableForm();
        if (progressSection) progressSection.style.display = 'none';
    } finally {
        updateStreamingStatus('connected');
        currentStreamRequest = null;
    }
}

function updateStreamingProgress(progress, chunks, totalChunks) {
    const progressBar = document.getElementById('stream-progress-bar');
    const progressText = document.getElementById('stream-progress-text');
    const chunksCount = document.getElementById('chunks-count');
    const totalChunksEl = document.getElementById('total-chunks');
    
    if (progressBar) {
        progressBar.style.width = `${progress}%`;
        if (progressText) progressText.textContent = `${progress}%`;
    }
    if (chunksCount) chunksCount.textContent = chunks;
    if (totalChunksEl) totalChunksEl.textContent = totalChunks;
}

function showStreamingStats(stats) {
    const progressSection = document.getElementById('streaming-progress');
    if (!progressSection) return;
    
    const statsHtml = `
        <div class="alert alert-success mt-3">
            <h6><i class="fas fa-check-circle me-2"></i>Streaming Complete!</h6>
            <div class="row mt-2">
                <div class="col-md-3">
                    <strong>Chunks:</strong> ${stats.chunks}
                </div>
                <div class="col-md-3">
                    <strong>Total Size:</strong> ${stats.totalSize} KB
                </div>
                <div class="col-md-3">
                    <strong>Time:</strong> ${stats.totalTime}s
                </div>
                <div class="col-md-3">
                    <strong>Format:</strong> ${stats.format.toUpperCase()}
                </div>
            </div>
        </div>
    `;
    
    const statsDiv = document.createElement('div');
    statsDiv.innerHTML = statsHtml;
    progressSection.appendChild(statsDiv);
}

// Load available voices
async function loadVoices() {
    try {
        const response = await fetch('/api/voices');
        const data = await response.json();
        
        const voiceSelect = document.getElementById('voice-select');
        if (voiceSelect) {
            voiceSelect.innerHTML = '';
            
            data.voices.forEach(voice => {
                const option = document.createElement('option');
                option.value = voice.id;
                option.textContent = voice.name;
                if (voice.id === 'alloy') {
                    option.selected = true;
                }
                voiceSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Failed to load voices:', error);
    }
}

// Load available formats
async function loadFormats() {
    try {
        const response = await fetch('/api/formats');
        const data = await response.json();
        
        const formatSelect = document.getElementById('format-select');
        if (formatSelect) {
            formatSelect.innerHTML = '';
            
            data.formats.forEach(format => {
                const option = document.createElement('option');
                option.value = format.id;
                option.textContent = `${format.name} - ${format.quality}`;
                if (format.id === 'mp3') {
                    option.selected = true;
                }
                formatSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Failed to load formats:', error);
    }
}

// Update character count
function updateCharCount() {
    const textInput = document.getElementById('text-input');
    const charCount = document.getElementById('char-count');
    const maxLengthInput = document.getElementById('max-length-input');
    
    if (textInput && charCount) {
        const currentLength = textInput.value.length;
        const maxLength = maxLengthInput ? parseInt(maxLengthInput.value) : 4096;
        
        charCount.textContent = currentLength;
        
        if (currentLength > maxLength) {
            charCount.className = 'text-danger fw-bold';
        } else if (currentLength > maxLength * 0.8) {
            charCount.className = 'text-warning fw-bold';
        } else {
            charCount.className = '';
        }
    }
}

// Generate speech (original HTTP method)
async function generateSpeech(event) {
    event.preventDefault();
    
    const text = document.getElementById('text-input').value.trim();
    const voice = document.getElementById('voice-select').value;
    const format = document.getElementById('format-select').value;
    const instructions = document.getElementById('instructions-input')?.value.trim() || '';
    const apiKey = document.getElementById('api-key-input')?.value.trim() || '';
    
    if (!text) {
        showError('Please enter some text to convert');
        return;
    }
    
    hideError();
    hideResults();
    showLoading();
    disableForm();
    
    try {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (apiKey) {
            headers['Authorization'] = `Bearer ${apiKey}`;
        }
        
        const requestBody = {
            text: text,
            voice: voice,
            format: format
        };
        
        if (instructions) {
            requestBody.instructions = instructions;
        }
        
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            let errorMessage = `Error: ${response.status} ${response.statusText}`;
            try {
                const errorData = await response.json();
                if (errorData.error?.message) {
                    errorMessage = errorData.error.message;
                }
            } catch (e) {
                // Use default error message
            }
            throw new Error(errorMessage);
        }
        
        const blob = await response.blob();
        currentAudioBlob = blob;
        currentFormat = format;
        
        showResults(blob, format);
        
    } catch (error) {
        showError(error.message);
    } finally {
        hideLoading();
        enableForm();
    }
}

// Show/hide functions
function showLoading() {
    const loading = document.getElementById('loading-section');
    if (loading) loading.style.display = 'block';
}

function hideLoading() {
    const loading = document.getElementById('loading-section');
    if (loading) loading.style.display = 'none';
}

function showResults(blob, format) {
    const audioUrl = URL.createObjectURL(blob);
    const audioPlayer = document.getElementById('audio-player');
    if (audioPlayer) {
        audioPlayer.src = audioUrl;
    }
    
    const audioResult = document.getElementById('audio-result');
    if (audioResult) {
        audioResult.classList.remove('d-none');
    }
    
    const downloadBtn = document.getElementById('download-btn');
    if (downloadBtn) {
        downloadBtn.disabled = false;
    }
    
    enableForm();
}

function hideResults() {
    const audioResult = document.getElementById('audio-result');
    if (audioResult) {
        audioResult.classList.add('d-none');
    }
}

function showError(message) {
    const errorDiv = document.getElementById('error-message');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }
}

function hideError() {
    const errorDiv = document.getElementById('error-message');
    if (errorDiv) {
        errorDiv.style.display = 'none';
    }
}

function disableForm() {
    const elements = ['generate-btn', 'text-input', 'voice-select', 'format-select'];
    elements.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.disabled = true;
    });
}

function enableForm() {
    const elements = ['generate-btn', 'text-input', 'voice-select', 'format-select'];
    elements.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.disabled = false;
    });
}

// Download audio
function downloadAudio() {
    if (!currentAudioBlob) return;
    
    const url = URL.createObjectURL(currentAudioBlob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `tts_${Date.now()}.${currentFormat}`;
    a.click();
    URL.revokeObjectURL(url);
}

// Add CSS for streaming visualization
const style = document.createElement('style');
style.textContent = `
.streaming-controls {
    padding: 15px;
    background-color: #f8f9fa;
    border-radius: 8px;
}

.streaming-status {
    display: inline-block;
    padding: 5px 10px;
    border-radius: 20px;
    font-size: 0.875rem;
    font-weight: 500;
}

.streaming-status.connected {
    background-color: #d4edda;
    color: #155724;
}

.streaming-status.disconnected {
    background-color: #f8d7da;
    color: #721c24;
}

.streaming-status.error {
    background-color: #fff3cd;
    color: #856404;
}

.streaming-status.streaming {
    background-color: #cce5ff;
    color: #004085;
    animation: pulse 1.5s infinite;
}

@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.7; }
    100% { opacity: 1; }
}

.streaming-progress-section {
    margin-bottom: 20px;
}

.chunks-visual {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
}

.chunk-indicator {
    width: 30px;
    height: 30px;
    background-color: #007bff;
    color: white;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    animation: chunkAppear 0.3s ease-out;
}

@keyframes chunkAppear {
    from {
        transform: scale(0);
        opacity: 0;
    }
    to {
        transform: scale(1);
        opacity: 1;
    }
}
`;
document.head.appendChild(style);