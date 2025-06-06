// TTSFM Playground JavaScript

// Global variables
let currentAudioBlob = null;
let currentFormat = 'mp3';
let batchResults = [];

// Initialize playground
document.addEventListener('DOMContentLoaded', function() {
    initializePlayground();
});

function initializePlayground() {
    loadVoices();
    loadFormats();
    updateCharCount();
    setupEventListeners();
    
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

function setupEventListeners() {
    // Form and input events
    document.getElementById('text-input').addEventListener('input', updateCharCount);
    document.getElementById('tts-form').addEventListener('submit', generateSpeech);
    document.getElementById('max-length-input').addEventListener('input', updateCharCount);
    document.getElementById('auto-split-check').addEventListener('change', updateGenerateButton);

    // Enhanced button events
    document.getElementById('validate-text-btn').addEventListener('click', validateText);
    document.getElementById('random-text-btn').addEventListener('click', loadRandomText);
    document.getElementById('download-btn').addEventListener('click', downloadAudio);
    document.getElementById('download-all-btn').addEventListener('click', downloadAllAudio);

    // New button events
    const clearTextBtn = document.getElementById('clear-text-btn');
    if (clearTextBtn) {
        clearTextBtn.addEventListener('click', clearText);
    }



    const resetFormBtn = document.getElementById('reset-form-btn');
    if (resetFormBtn) {
        resetFormBtn.addEventListener('click', resetForm);
    }

    const replayBtn = document.getElementById('replay-btn');
    if (replayBtn) {
        replayBtn.addEventListener('click', replayAudio);
    }

    const shareBtn = document.getElementById('share-btn');
    if (shareBtn) {
        shareBtn.addEventListener('click', shareAudio);
    }

    // Voice and format selection events
    document.getElementById('voice-select').addEventListener('change', updateVoiceInfo);
    document.getElementById('format-select').addEventListener('change', updateFormatInfo);

    // Example text buttons
    document.querySelectorAll('.use-example').forEach(button => {
        button.addEventListener('click', function() {
            document.getElementById('text-input').value = this.dataset.text;
            updateCharCount();
            // Add visual feedback
            this.classList.add('btn-success');
            setTimeout(() => {
                this.classList.remove('btn-success');
                this.classList.add('btn-outline-primary');
            }, 1000);
        });
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + Enter to generate speech
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            document.getElementById('generate-btn').click();
        }
        
        // Escape to clear results
        if (e.key === 'Escape') {
            clearResults();
        }
    });
}

async function loadVoices() {
    try {
        const response = await fetch('/api/voices');
        const data = await response.json();
        
        const select = document.getElementById('voice-select');
        select.innerHTML = '';
        
        data.voices.forEach(voice => {
            const option = document.createElement('option');
            option.value = voice.id;
            option.textContent = `${voice.name} - ${voice.description}`;
            select.appendChild(option);
        });
        
        // Select default voice
        select.value = 'alloy';
        
    } catch (error) {
        console.error('Failed to load voices:', error);
        console.log('Failed to load voices. Please refresh the page.');
    }
}

async function loadFormats() {
    try {
        const response = await fetch('/api/formats');
        const data = await response.json();
        
        const select = document.getElementById('format-select');
        select.innerHTML = '';
        
        data.formats.forEach(format => {
            const option = document.createElement('option');
            option.value = format.id;
            option.textContent = `${format.name} (${format.mime_type})`;
            select.appendChild(option);
        });
        
        // Select default format
        select.value = 'mp3';
        
    } catch (error) {
        console.error('Failed to load formats:', error);
        console.log('Failed to load formats. Please refresh the page.');
    }
}

function updateCharCount() {
    const text = document.getElementById('text-input').value;
    const maxLength = parseInt(document.getElementById('max-length-input').value) || 4096;
    const charCount = text.length;
    
    document.getElementById('char-count').textContent = charCount.toLocaleString();
    
    // Update length status with better visual feedback
    const statusElement = document.getElementById('length-status');
    const percentage = (charCount / maxLength) * 100;
    
    if (charCount > maxLength) {
        statusElement.innerHTML = '<span class="badge bg-danger"><i class="fas fa-exclamation-triangle me-1"></i>Exceeds limit</span>';
    } else if (percentage > 80) {
        statusElement.innerHTML = '<span class="badge bg-warning"><i class="fas fa-exclamation me-1"></i>Near limit</span>';
    } else if (percentage > 50) {
        statusElement.innerHTML = '<span class="badge bg-info"><i class="fas fa-info me-1"></i>Good</span>';
    } else {
        statusElement.innerHTML = '<span class="badge bg-success"><i class="fas fa-check me-1"></i>OK</span>';
    }
    
    updateGenerateButton();
}

function updateGenerateButton() {
    const text = document.getElementById('text-input').value;
    const maxLength = parseInt(document.getElementById('max-length-input').value) || 4096;
    const autoSplit = document.getElementById('auto-split-check').checked;
    const generateBtn = document.getElementById('generate-btn');
    const btnText = generateBtn.querySelector('.btn-text');
    
    if (text.length > maxLength && autoSplit) {
        btnText.innerHTML = '<i class="fas fa-layer-group me-2"></i>Generate Speech (Batch Mode)';
        generateBtn.classList.add('btn-warning');
        generateBtn.classList.remove('btn-primary');
    } else {
        btnText.innerHTML = '<i class="fas fa-magic me-2"></i>Generate Speech';
        generateBtn.classList.add('btn-primary');
        generateBtn.classList.remove('btn-warning');
    }
}

async function validateText() {
    const text = document.getElementById('text-input').value.trim();
    const maxLength = parseInt(document.getElementById('max-length-input').value) || 4096;
    
    if (!text) {
        console.log('Please enter some text to validate');
        return;
    }
    
    const validateBtn = document.getElementById('validate-text-btn');
    setLoading(validateBtn, true);
    
    try {
        const response = await fetch('/api/validate-text', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, max_length: maxLength })
        });
        
        const data = await response.json();
        const resultDiv = document.getElementById('validation-result');
        
        if (data.is_valid) {
            resultDiv.innerHTML = `
                <div class="alert alert-success fade-in">
                    <i class="fas fa-check-circle me-2"></i>
                    <strong>Text is valid!</strong> (${data.text_length.toLocaleString()} characters)
                    <div class="progress progress-custom mt-2">
                        <div class="progress-bar-custom" style="width: ${(data.text_length / data.max_length) * 100}%"></div>
                    </div>
                </div>
            `;
        } else {
            resultDiv.innerHTML = `
                <div class="alert alert-warning fade-in">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>Text exceeds limit!</strong> (${data.text_length.toLocaleString()}/${data.max_length.toLocaleString()} characters)
                    <br><small class="mt-2 d-block">Suggested chunks: ${data.suggested_chunks}</small>
                    <div class="mt-3">
                        <strong>Preview of chunks:</strong>
                        <div class="mt-2">
                            ${data.chunk_preview.map((chunk, i) => `
                                <div class="border rounded p-2 mb-2 bg-light">
                                    <small class="text-muted">Chunk ${i+1}:</small>
                                    <div class="small">${chunk}</div>
                                </div>
                            `).join('')}
                        </div>
                        <button class="btn btn-sm btn-outline-primary mt-2" onclick="enableAutoSplit()">
                            <i class="fas fa-magic me-1"></i>Enable Auto-Split
                        </button>
                    </div>
                </div>
            `;
        }
        
        resultDiv.classList.remove('d-none');
        resultDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
    } catch (error) {
        console.error('Validation failed:', error);
        console.log('Failed to validate text. Please try again.');
    } finally {
        setLoading(validateBtn, false);
    }
}

function enableAutoSplit() {
    document.getElementById('auto-split-check').checked = true;
    updateGenerateButton();
    console.log('Auto-split enabled! Click Generate Speech to process in batch mode.');
}

async function generateSpeech(event) {
    event.preventDefault();
    
    const button = document.getElementById('generate-btn');
    const audioResult = document.getElementById('audio-result');
    const batchResult = document.getElementById('batch-result');
    
    // Get form data
    const formData = getFormData();
    
    if (!validateFormData(formData)) {
        return;
    }
    
    // Check if we need batch processing
    const needsBatch = formData.text.length > formData.maxLength && formData.autoSplit;
    
    // Show loading state
    setLoading(button, true);
    clearResults();
    
    try {
        if (needsBatch) {
            await generateBatchSpeech(formData);
        } else {
            await generateSingleSpeech(formData);
        }
    } catch (error) {
        console.error('Generation failed:', error);
        console.log(`Failed to generate speech: ${error.message}`);
    } finally {
        setLoading(button, false);
    }
}

function getFormData() {
    return {
        text: document.getElementById('text-input').value.trim(),
        voice: document.getElementById('voice-select').value,
        format: document.getElementById('format-select').value,
        instructions: document.getElementById('instructions-input').value.trim(),
        maxLength: parseInt(document.getElementById('max-length-input').value) || 4096,
        validateLength: document.getElementById('validate-length-check').checked,
        autoSplit: document.getElementById('auto-split-check').checked
    };
}

function validateFormData(formData) {
    if (!formData.text || !formData.voice || !formData.format) {
        console.log('Please fill in all required fields');
        return false;
    }

    if (formData.text.length > formData.maxLength && formData.validateLength && !formData.autoSplit) {
        console.log(`Text is too long (${formData.text.length} characters). Enable auto-split or reduce text length.`);
        return false;
    }

    return true;
}

function clearResults() {
    document.getElementById('audio-result').classList.add('d-none');
    document.getElementById('batch-result').classList.add('d-none');
    document.getElementById('validation-result').classList.add('d-none');
}

// Utility functions
function setLoading(button, loading) {
    if (loading) {
        button.classList.add('loading');
        button.disabled = true;
    } else {
        button.classList.remove('loading');
        button.disabled = false;
    }
}



async function generateSingleSpeech(formData) {
    const audioResult = document.getElementById('audio-result');

    const response = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            text: formData.text,
            voice: formData.voice,
            format: formData.format,
            instructions: formData.instructions || undefined,
            max_length: formData.maxLength,
            validate_length: formData.validateLength
        })
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP ${response.status}`);
    }

    // Get audio data
    const audioBlob = await response.blob();
    currentAudioBlob = audioBlob;
    currentFormat = formData.format;

    // Create audio URL and setup player
    const audioUrl = URL.createObjectURL(audioBlob);
    const audioPlayer = document.getElementById('audio-player');
    audioPlayer.src = audioUrl;

    // Use enhanced display function
    displayAudioResult(audioBlob, formData.format, formData.voice, formData.text);

    console.log('Speech generated successfully! Click play to listen.');

    // Auto-play if user prefers
    if (localStorage.getItem('autoPlay') === 'true') {
        audioPlayer.play().catch(() => {
            // Auto-play blocked, that's fine
        });
    }
}

async function generateBatchSpeech(formData) {
    const batchResult = document.getElementById('batch-result');

    const response = await fetch('/api/generate-batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            text: formData.text,
            voice: formData.voice,
            format: formData.format,
            instructions: formData.instructions || undefined,
            max_length: formData.maxLength,
            preserve_words: true
        })
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP ${response.status}`);
    }

    const data = await response.json();
    batchResults = data.results;

    // Update batch summary
    const summaryDiv = document.getElementById('batch-summary');
    summaryDiv.innerHTML = `
        <i class="fas fa-layer-group me-2"></i>
        <strong>Batch Processing Complete!</strong>
        Generated ${data.successful_chunks} of ${data.total_chunks} audio chunks successfully.
        ${data.successful_chunks < data.total_chunks ?
            `<br><small class="text-warning">⚠️ ${data.total_chunks - data.successful_chunks} chunks failed to generate.</small>` :
            '<br><small class="text-success">✅ All chunks generated successfully!</small>'
        }
    `;

    // Display chunks
    displayBatchChunks(data.results, formData.format);

    // Show batch result with animation
    batchResult.classList.remove('d-none');
    batchResult.classList.add('fade-in');

    console.log(`Batch processing completed! Generated ${data.successful_chunks} audio files.`);
}

function displayBatchChunks(results, format) {
    const chunksDiv = document.getElementById('batch-chunks');
    chunksDiv.innerHTML = '';

    results.forEach((result, index) => {
        const chunkDiv = document.createElement('div');
        chunkDiv.className = 'col-md-6 col-lg-4 mb-3';

        if (result.audio_data) {
            // Convert base64 to blob
            const audioBlob = base64ToBlob(result.audio_data, result.content_type);
            const audioUrl = URL.createObjectURL(audioBlob);

            chunkDiv.innerHTML = `
                <div class="card batch-chunk-card h-100">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h6 class="card-title mb-0">
                                <i class="fas fa-music me-1"></i>Chunk ${result.chunk_index}
                            </h6>
                            <span class="badge bg-success">
                                <i class="fas fa-check me-1"></i>Success
                            </span>
                        </div>
                        <p class="card-text small text-muted mb-3">${result.chunk_text}</p>
                        <audio controls class="w-100 mb-3" preload="metadata">
                            <source src="${audioUrl}" type="${result.content_type}">
                            Your browser does not support audio playback.
                        </audio>
                        <div class="d-flex justify-content-between align-items-center">
                            <small class="text-muted">
                                <i class="fas fa-file-audio me-1"></i>
                                ${(result.size / 1024).toFixed(1)} KB
                            </small>
                            <button class="btn btn-sm btn-outline-primary download-chunk"
                                    data-url="${audioUrl}"
                                    data-filename="chunk_${result.chunk_index}.${result.format}"
                                    title="Download this chunk">
                                <i class="fas fa-download"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        } else {
            chunkDiv.innerHTML = `
                <div class="card border-danger h-100">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h6 class="card-title mb-0 text-danger">
                                <i class="fas fa-exclamation-triangle me-1"></i>Chunk ${result.chunk_index}
                            </h6>
                            <span class="badge bg-danger">
                                <i class="fas fa-times me-1"></i>Failed
                            </span>
                        </div>
                        <p class="card-text small text-muted mb-3">${result.chunk_text}</p>
                        <div class="alert alert-danger small mb-0">
                            <i class="fas fa-exclamation-circle me-1"></i>
                            ${result.error}
                        </div>
                    </div>
                </div>
            `;
        }

        chunksDiv.appendChild(chunkDiv);
    });

    // Add download event listeners
    document.querySelectorAll('.download-chunk').forEach(btn => {
        btn.addEventListener('click', function() {
            const url = this.dataset.url;
            const filename = this.dataset.filename;
            downloadFromUrl(url, filename);

            // Visual feedback
            const icon = this.querySelector('i');
            icon.className = 'fas fa-check';
            setTimeout(() => {
                icon.className = 'fas fa-download';
            }, 1000);
        });
    });
}

function downloadAudio() {
    if (!currentAudioBlob) {
        console.log('No audio to download');
        return;
    }

    const url = URL.createObjectURL(currentAudioBlob);
    const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
    downloadFromUrl(url, `ttsfm-speech-${timestamp}.${currentFormat}`);
    URL.revokeObjectURL(url);
}

function downloadAllAudio() {
    const downloadButtons = document.querySelectorAll('.download-chunk');
    if (downloadButtons.length === 0) {
        console.log('No batch audio files to download');
        return;
    }

    console.log(`Starting download of ${downloadButtons.length} files...`);

    downloadButtons.forEach((btn, index) => {
        setTimeout(() => {
            btn.click();
        }, index * 500); // Stagger downloads to avoid browser limits
    });
}

function base64ToBlob(base64, contentType) {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: contentType });
}

function downloadFromUrl(url, filename) {
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.style.display = 'none';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

// New enhanced functions
function clearText() {
    document.getElementById('text-input').value = '';
    updateCharCount();
    clearResults();
    console.log('Text cleared successfully');
}

function loadRandomText() {
    const randomTexts = [
        // News & Information
        "Breaking news: Scientists have discovered a revolutionary new method for generating incredibly natural synthetic speech using advanced neural networks and machine learning algorithms.",
        "Weather update: Today will be partly cloudy with temperatures reaching 75 degrees Fahrenheit. Light winds from the southwest at 5 to 10 miles per hour.",
        "Technology report: The latest advancements in artificial intelligence are revolutionizing how we interact with digital devices and services.",

        // Educational & Informative
        "The human brain contains approximately 86 billion neurons, each connected to thousands of others, creating a complex network that enables consciousness, memory, and thought.",
        "Photosynthesis is the process by which plants convert sunlight, carbon dioxide, and water into glucose and oxygen, forming the foundation of most life on Earth.",
        "The speed of light in a vacuum is exactly 299,792,458 meters per second, making it one of the fundamental constants of physics.",

        // Creative & Storytelling
        "Once upon a time, in a land far away, there lived a wise old wizard who could speak to the stars and understand their ancient secrets.",
        "The mysterious lighthouse stood alone on the rocky cliff, its beacon cutting through the fog like a sword of light, guiding lost ships safely home.",
        "In the depths of the enchanted forest, where sunbeams danced through emerald leaves, a young adventurer discovered a hidden path to destiny.",

        // Business & Professional
        "Our quarterly results demonstrate strong growth across all market segments, with revenue increasing by 23% compared to the same period last year.",
        "The new product launch exceeded expectations, capturing 15% market share within the first six months and establishing our brand as an industry leader.",
        "We are committed to sustainable business practices that benefit our customers, employees, and the environment for generations to come.",

        // Technical & Programming
        "The TTSFM package provides a comprehensive API for text-to-speech generation with support for multiple voices and audio formats.",
        "Machine learning algorithms process vast amounts of data to identify patterns and make predictions with remarkable accuracy.",
        "Cloud computing has transformed how businesses store, process, and access their data, enabling scalability and flexibility like never before.",

        // Conversational & Casual
        "Welcome to TTSFM! Experience the future of text-to-speech technology with our premium AI voices.",
        "Good morning! Today is a beautiful day to learn something new and explore the possibilities of text-to-speech technology.",
        "Have you ever wondered what it would be like if your computer could speak with perfect human-like intonation and emotion?"
    ];

    const randomText = randomTexts[Math.floor(Math.random() * randomTexts.length)];
    document.getElementById('text-input').value = randomText;
    updateCharCount();
    console.log('Random text loaded successfully');
}



function resetForm() {
    // Reset form to default values
    document.getElementById('text-input').value = 'Welcome to TTSFM! Experience the future of text-to-speech technology with our premium AI voices. Generate natural, expressive speech for any application.';
    document.getElementById('voice-select').value = 'alloy';
    document.getElementById('format-select').value = 'mp3';
    document.getElementById('instructions-input').value = '';
    document.getElementById('max-length-input').value = '4096';
    document.getElementById('validate-length-check').checked = true;
    document.getElementById('auto-split-check').checked = false;

    updateCharCount();
    updateGenerateButton();
    clearResults();
    console.log('Form reset to default values');
}

function replayAudio() {
    const audioPlayer = document.getElementById('audio-player');
    if (audioPlayer && audioPlayer.src) {
        audioPlayer.currentTime = 0;
        audioPlayer.play().catch(() => {
            console.log('Unable to replay audio. Please check your browser settings.');
        });
    }
}

function shareAudio() {
    if (navigator.share && currentAudioBlob) {
        const file = new File([currentAudioBlob], `ttsfm-speech.${currentFormat}`, {
            type: `audio/${currentFormat}`
        });

        navigator.share({
            title: 'TTSFM Generated Speech',
            text: 'Check out this speech generated with TTSFM!',
            files: [file]
        }).catch(() => {
            // Fallback to copying link
            copyAudioLink();
        });
    } else {
        copyAudioLink();
    }
}

function copyAudioLink() {
    const audioPlayer = document.getElementById('audio-player');
    if (audioPlayer && audioPlayer.src) {
        navigator.clipboard.writeText(audioPlayer.src).then(() => {
            console.log('Audio link copied to clipboard!');
        }).catch(() => {
            console.log('Unable to copy link. Please try downloading the audio instead.');
        });
    }
}

function updateVoiceInfo() {
    const voiceSelect = document.getElementById('voice-select');
    const previewBtn = document.getElementById('preview-voice-btn');

    if (voiceSelect.value) {
        previewBtn.disabled = false;
        previewBtn.onclick = () => previewVoice(voiceSelect.value);
    } else {
        previewBtn.disabled = true;
    }
}

function updateFormatInfo() {
    const formatSelect = document.getElementById('format-select');
    const formatInfo = document.getElementById('format-info');

    const formatDescriptions = {
        'mp3': 'MP3 - Best for web and general use',
        'wav': 'WAV - Uncompressed, highest quality',
        'opus': 'OPUS - Efficient compression',
        'aac': 'AAC - Good quality, small size',
        'flac': 'FLAC - Lossless compression',
        'pcm': 'PCM - Raw audio data'
    };

    if (formatInfo && formatSelect.value) {
        formatInfo.textContent = formatDescriptions[formatSelect.value] || 'High-quality audio format';
    }
}

function previewVoice(voiceId) {
    // This would typically play a short preview of the voice
    console.log(`Voice preview for ${voiceId} - Feature coming soon!`);
}

// Enhanced audio result display
function displayAudioResult(audioBlob, format, voice, text) {
    const audioResult = document.getElementById('audio-result');
    const audioPlayer = document.getElementById('audio-player');
    const audioInfo = document.getElementById('audio-info');

    // Create audio URL and setup player
    const audioUrl = URL.createObjectURL(audioBlob);
    audioPlayer.src = audioUrl;

    // Update audio stats
    const sizeKB = (audioBlob.size / 1024).toFixed(1);
    document.getElementById('audio-size').textContent = `${sizeKB} KB`;
    document.getElementById('audio-format').textContent = format.toUpperCase();
    document.getElementById('audio-voice').textContent = voice.charAt(0).toUpperCase() + voice.slice(1);

    // Update audio info
    audioInfo.innerHTML = `
        <i class="fas fa-check-circle text-success me-1"></i>
        Generated successfully • ${sizeKB} KB • ${format.toUpperCase()}
    `;

    // Show result with animation
    audioResult.classList.remove('d-none');
    audioResult.classList.add('fade-in');

    // Update duration when metadata loads
    audioPlayer.addEventListener('loadedmetadata', function() {
        const duration = Math.round(audioPlayer.duration);
        document.getElementById('audio-duration').textContent = `${duration}s`;
    }, { once: true });

    // Scroll to result
    audioResult.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Export functions for use in HTML
window.enableAutoSplit = enableAutoSplit;
window.clearText = clearText;
window.loadRandomText = loadRandomText;
window.resetForm = resetForm;
