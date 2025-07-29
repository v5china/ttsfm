/**
 * WebSocket TTS Streaming Client
 * 
 * Because apparently HTTP requests are so 2023.
 * Now we need real-time streaming for everything.
 */

class WebSocketTTSClient {
    constructor(options = {}) {
        this.socketUrl = options.socketUrl || window.location.origin;
        this.socket = null;
        this.activeRequests = new Map();
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 5;
        this.reconnectDelay = options.reconnectDelay || 1000;
        this.debug = options.debug || false;
        
        // Audio context for seamless playback
        this.audioContext = null;
        this.audioQueue = new Map(); // request_id -> audio chunks
        
        // Event handlers
        this.onConnect = options.onConnect || (() => {});
        this.onDisconnect = options.onDisconnect || (() => {});
        this.onError = options.onError || ((error) => console.error('WebSocket error:', error));
        
        // Initialize
        this.connect();
    }
    
    connect() {
        if (this.socket && this.socket.connected) {
            this.log('Already connected');
            return;
        }
        
        this.log('Connecting to WebSocket server...');
        
        // Initialize Socket.IO connection
        this.socket = io(this.socketUrl, {
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionAttempts: this.maxReconnectAttempts,
            reconnectionDelay: this.reconnectDelay
        });
        
        // Set up event handlers
        this.setupEventHandlers();
    }
    
    setupEventHandlers() {
        // Connection events
        this.socket.on('connect', () => {
            this.log('Connected to WebSocket server');
            this.reconnectAttempts = 0;
            this.onConnect();
        });
        
        this.socket.on('disconnect', (reason) => {
            this.log('Disconnected from WebSocket server:', reason);
            this.onDisconnect(reason);
        });
        
        this.socket.on('connect_error', (error) => {
            this.log('Connection error:', error);
            this.reconnectAttempts++;
            this.onError({
                type: 'connection_error',
                message: error.message,
                attempts: this.reconnectAttempts
            });
        });
        
        // TTS streaming events
        this.socket.on('connected', (data) => {
            this.log('Session established:', data.session_id);
        });
        
        this.socket.on('stream_started', (data) => {
            this.log('Stream started:', data.request_id);
            const request = this.activeRequests.get(data.request_id);
            if (request && request.onStart) {
                request.onStart(data);
            }
        });
        
        this.socket.on('audio_chunk', (data) => {
            this.handleAudioChunk(data);
        });
        
        this.socket.on('stream_progress', (data) => {
            this.handleProgress(data);
        });
        
        this.socket.on('stream_complete', (data) => {
            this.handleStreamComplete(data);
        });
        
        this.socket.on('stream_error', (data) => {
            this.handleStreamError(data);
        });
    }
    
    /**
     * Generate speech with real-time streaming
     */
    generateSpeech(text, options = {}) {
        return new Promise((resolve, reject) => {
            if (!this.socket || !this.socket.connected) {
                reject(new Error('WebSocket not connected'));
                return;
            }
            
            const requestId = this.generateRequestId();
            const audioChunks = [];
            
            // Store request info
            this.activeRequests.set(requestId, {
                resolve,
                reject,
                audioChunks,
                options,
                startTime: Date.now(),
                onStart: options.onStart,
                onProgress: options.onProgress,
                onChunk: options.onChunk,
                onComplete: options.onComplete,
                onError: options.onError
            });
            
            // Initialize audio queue for this request
            this.audioQueue.set(requestId, []);
            
            // Emit generation request
            this.socket.emit('generate_stream', {
                request_id: requestId,
                text: text,
                voice: options.voice || 'alloy',
                format: options.format || 'mp3',
                chunk_size: options.chunkSize || 1024
            });
            
            this.log('Requested speech generation:', requestId);
        });
    }
    
    handleAudioChunk(data) {
        const request = this.activeRequests.get(data.request_id);
        if (!request) {
            this.log('Received chunk for unknown request:', data.request_id);
            return;
        }
        
        // Convert hex string back to binary
        const audioData = this.hexToArrayBuffer(data.audio_data);
        
        // Store chunk
        request.audioChunks.push({
            index: data.chunk_index,
            data: audioData,
            duration: data.duration,
            format: data.format
        });
        
        // Add to audio queue for streaming playback
        const queue = this.audioQueue.get(data.request_id);
        if (queue) {
            queue.push(audioData);
        }
        
        // Call chunk handler if provided
        if (request.onChunk) {
            request.onChunk({
                chunkIndex: data.chunk_index,
                totalChunks: data.total_chunks,
                audioData: audioData,
                duration: data.duration,
                text: data.chunk_text
            });
        }
        
        this.log(`Received chunk ${data.chunk_index + 1}/${data.total_chunks} for request ${data.request_id}`);
    }
    
    handleProgress(data) {
        const request = this.activeRequests.get(data.request_id);
        if (request && request.onProgress) {
            request.onProgress({
                progress: data.progress,
                chunksCompleted: data.chunks_completed,
                totalChunks: data.total_chunks,
                status: data.status
            });
        }
    }
    
    handleStreamComplete(data) {
        const request = this.activeRequests.get(data.request_id);
        if (!request) {
            this.log('Completion for unknown request:', data.request_id);
            return;
        }
        
        // Sort chunks by index
        request.audioChunks.sort((a, b) => a.index - b.index);
        
        // Combine all audio chunks
        const combinedAudio = this.combineAudioChunks(request.audioChunks);
        
        const result = {
            requestId: data.request_id,
            audioData: combinedAudio,
            chunks: request.audioChunks,
            duration: request.audioChunks.reduce((sum, chunk) => sum + chunk.duration, 0),
            generationTime: Date.now() - request.startTime,
            format: request.audioChunks[0]?.format || 'mp3'
        };
        
        // Call complete handler
        if (request.onComplete) {
            request.onComplete(result);
        }
        
        // Resolve promise
        request.resolve(result);
        
        // Cleanup
        this.activeRequests.delete(data.request_id);
        this.audioQueue.delete(data.request_id);
        
        this.log('Stream completed:', data.request_id);
    }
    
    handleStreamError(data) {
        const request = this.activeRequests.get(data.request_id);
        if (!request) {
            this.log('Error for unknown request:', data.request_id);
            return;
        }
        
        const error = new Error(data.error);
        error.requestId = data.request_id;
        error.timestamp = data.timestamp;
        
        // Call error handler
        if (request.onError) {
            request.onError(error);
        }
        
        // Reject promise
        request.reject(error);
        
        // Cleanup
        this.activeRequests.delete(data.request_id);
        this.audioQueue.delete(data.request_id);
        
        this.log('Stream error:', data.request_id, data.error);
    }
    
    /**
     * Cancel an active stream
     */
    cancelStream(requestId) {
        if (!this.socket || !this.socket.connected) {
            throw new Error('WebSocket not connected');
        }
        
        this.socket.emit('cancel_stream', { request_id: requestId });
        
        // Clean up local state
        const request = this.activeRequests.get(requestId);
        if (request) {
            request.reject(new Error('Stream cancelled by user'));
            this.activeRequests.delete(requestId);
            this.audioQueue.delete(requestId);
        }
    }
    
    /**
     * Combine audio chunks into a single buffer
     */
    combineAudioChunks(chunks) {
        if (chunks.length === 0) return new ArrayBuffer(0);
        
        // Calculate total size
        const totalSize = chunks.reduce((sum, chunk) => sum + chunk.data.byteLength, 0);
        
        // Create combined buffer
        const combined = new ArrayBuffer(totalSize);
        const view = new Uint8Array(combined);
        
        let offset = 0;
        for (const chunk of chunks) {
            view.set(new Uint8Array(chunk.data), offset);
            offset += chunk.data.byteLength;
        }
        
        return combined;
    }
    
    /**
     * Play audio directly (experimental streaming playback)
     */
    async playAudioStream(requestId) {
        if (!this.audioContext) {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }
        
        const queue = this.audioQueue.get(requestId);
        if (!queue) {
            throw new Error('No audio queue found for request');
        }
        
        // This is a simplified version - real implementation would need
        // proper audio decoding and buffering for seamless playback
        this.log('Streaming audio playback not fully implemented yet');
    }
    
    /**
     * Utility functions
     */
    hexToArrayBuffer(hex) {
        const bytes = new Uint8Array(hex.length / 2);
        for (let i = 0; i < hex.length; i += 2) {
            bytes[i / 2] = parseInt(hex.substr(i, 2), 16);
        }
        return bytes.buffer;
    }
    
    generateRequestId() {
        return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    
    log(...args) {
        if (this.debug) {
            console.log('[WebSocketTTS]', ...args);
        }
    }
    
    /**
     * Get connection status
     */
    isConnected() {
        return this.socket && this.socket.connected;
    }
    
    /**
     * Disconnect from server
     */
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }
        
        // Clear all active requests
        for (const [requestId, request] of this.activeRequests) {
            request.reject(new Error('Client disconnected'));
        }
        this.activeRequests.clear();
        this.audioQueue.clear();
    }
}

// Export for use
window.WebSocketTTSClient = WebSocketTTSClient;