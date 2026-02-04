/**
 * Campus Event System - Production-Ready QR Scanner
 * Uses html5-qrcode library for reliable camera-based QR code scanning
 * Supports: Android, iOS (Safari/Chrome), Desktop browsers
 */

class CampusQRScanner {
    constructor(options = {}) {
        // Configuration
        this.containerId = options.containerId || 'qr-reader';
        this.eventId = options.eventId;
        this.apiEndpoint = options.apiEndpoint || '/api/scan-qr';
        
        // UI Elements
        this.statusElement = options.statusElement || document.getElementById('camera-status');
        this.resultElement = options.resultElement || document.getElementById('scan-result');
        this.resultSection = options.resultSection || document.getElementById('result-section');
        this.startButton = options.startButton || document.getElementById('start-scan');
        this.stopButton = options.stopButton || document.getElementById('stop-scan');
        this.scanNextButton = options.scanNextButton || document.getElementById('scan-next');
        
        // Scanner state
        this.html5QrCode = null;
        this.isScanning = false;
        this.isProcessing = false;
        this.currentCameraId = null;
        this.availableCameras = [];
        
        // Callbacks
        this.onScanSuccess = options.onScanSuccess || null;
        this.onScanError = options.onScanError || null;
        
        // Initialize
        this.init();
    }
    
    init() {
        // Check for secure context
        if (!this.checkSecureContext()) {
            return;
        }
        
        // Check for camera support
        if (!this.checkCameraSupport()) {
            return;
        }
        
        // Bind event listeners
        this.bindEvents();
        
        // Update status
        this.setStatus('Click "Start Scanner" to begin', 'info');
    }
    
    checkSecureContext() {
        const isSecure = window.isSecureContext || 
                         location.hostname === 'localhost' || 
                         location.hostname === '127.0.0.1' ||
                         location.protocol === 'https:';
        
        if (!isSecure) {
            this.setStatus('Camera requires HTTPS. Please use a secure connection.', 'error');
            this.disableControls();
            return false;
        }
        return true;
    }
    
    checkCameraSupport() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            this.setStatus('Camera not supported in this browser. Please use a modern browser.', 'error');
            this.disableControls();
            return false;
        }
        return true;
    }
    
    bindEvents() {
        if (this.startButton) {
            this.startButton.addEventListener('click', () => this.startScanning());
        }
        if (this.stopButton) {
            this.stopButton.addEventListener('click', () => this.stopScanning());
        }
        if (this.scanNextButton) {
            this.scanNextButton.addEventListener('click', () => this.scanNext());
        }
    }
    
    disableControls() {
        if (this.startButton) this.startButton.disabled = true;
        if (this.stopButton) this.stopButton.disabled = true;
    }
    
    setStatus(message, type = 'info') {
        if (this.statusElement) {
            this.statusElement.textContent = message;
            this.statusElement.className = `scanner-status status-${type}`;
        }
    }
    
    showResult(html, type = 'success') {
        if (this.resultSection) {
            this.resultSection.style.display = 'block';
        }
        if (this.resultElement) {
            this.resultElement.innerHTML = html;
            this.resultElement.className = `scan-result-content result-${type}`;
        }
    }
    
    hideResult() {
        if (this.resultSection) {
            this.resultSection.style.display = 'none';
        }
    }
    
    async startScanning() {
        if (this.isScanning) return;
        
        this.setStatus('Requesting camera access...', 'info');
        
        // Update button states
        if (this.startButton) this.startButton.disabled = true;
        if (this.stopButton) this.stopButton.disabled = false;
        if (this.scanNextButton) this.scanNextButton.style.display = 'none';
        
        try {
            // First, request camera permission explicitly
            await this.requestCameraPermission();
            
            // Create scanner instance
            this.html5QrCode = new Html5Qrcode(this.containerId);
            
            // Get available cameras
            this.availableCameras = await Html5Qrcode.getCameras();
            
            if (!this.availableCameras || this.availableCameras.length === 0) {
                throw new Error('No cameras found on this device');
            }
            
            // Select back camera if available (preferred for mobile)
            const backCamera = this.findBackCamera();
            const cameraId = backCamera ? backCamera.id : this.availableCameras[0].id;
            this.currentCameraId = cameraId;
            
            // Calculate optimal QR box size
            const qrboxFunction = (viewfinderWidth, viewfinderHeight) => {
                const minEdge = Math.min(viewfinderWidth, viewfinderHeight);
                const size = Math.floor(minEdge * 0.7);
                return { width: Math.max(200, size), height: Math.max(200, size) };
            };
            
            // Start scanning
            await this.html5QrCode.start(
                cameraId,
                {
                    fps: 10,
                    qrbox: qrboxFunction,
                    aspectRatio: 1.0,
                    disableFlip: false
                },
                (decodedText, decodedResult) => this.handleScanSuccess(decodedText, decodedResult),
                (errorMessage) => this.handleScanError(errorMessage)
            );
            
            this.isScanning = true;
            this.setStatus('Scanner active - Point camera at QR code', 'success');
            
        } catch (error) {
            console.error('Failed to start scanner:', error);
            this.handleStartError(error);
        }
    }
    
    async requestCameraPermission() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ 
                video: { facingMode: 'environment' },
                audio: false 
            });
            // Stop the stream immediately - we just needed permission
            stream.getTracks().forEach(track => track.stop());
        } catch (error) {
            // Try with any camera
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    video: true,
                    audio: false 
                });
                stream.getTracks().forEach(track => track.stop());
            } catch (err) {
                throw err;
            }
        }
    }
    
    findBackCamera() {
        // Try to find back camera by various label patterns
        const backCameraPatterns = [
            /back/i,
            /rear/i,
            /environment/i,
            /trasera/i,  // Spanish
            /arrière/i   // French
        ];
        
        for (const camera of this.availableCameras) {
            const label = camera.label || '';
            for (const pattern of backCameraPatterns) {
                if (pattern.test(label)) {
                    return camera;
                }
            }
        }
        
        // If multiple cameras and no label match, assume last one is back camera
        if (this.availableCameras.length > 1) {
            return this.availableCameras[this.availableCameras.length - 1];
        }
        
        return null;
    }
    
    async handleScanSuccess(decodedText, decodedResult) {
        if (this.isProcessing) return;
        this.isProcessing = true;
        
        // Pause scanner
        try {
            await this.html5QrCode.pause(true);
        } catch (e) {
            console.warn('Could not pause scanner:', e);
        }
        
        this.setStatus('Processing QR code...', 'info');
        
        // Play success sound (optional)
        this.playBeep();
        
        // Send to server
        try {
            const response = await this.sendToServer(decodedText);
            
            if (response.status === 'success') {
                this.showSuccessResult(response);
                this.setStatus('✓ Attendance marked successfully!', 'success');
                
                // Show scan next button
                if (this.scanNextButton) {
                    this.scanNextButton.style.display = 'inline-block';
                }
                
                // Stop scanner after success
                await this.stopScanning();
                
            } else if (response.status === 'duplicate') {
                this.showDuplicateResult(response);
                this.setStatus('⚠ Already scanned', 'warning');
                
                // Resume scanning after delay
                setTimeout(() => this.resumeScanning(), 2000);
                
            } else {
                this.showErrorResult(response);
                this.setStatus('✗ ' + (response.message || 'Invalid QR code'), 'error');
                
                // Resume scanning after delay
                setTimeout(() => this.resumeScanning(), 2000);
            }
            
        } catch (error) {
            console.error('Server error:', error);
            this.showErrorResult({ message: 'Network error. Please check your connection.' });
            this.setStatus('✗ Network error', 'error');
            
            // Resume scanning after delay
            setTimeout(() => this.resumeScanning(), 2000);
        }
        
        this.isProcessing = false;
    }
    
    handleScanError(errorMessage) {
        // This is called frequently during scanning - don't log everything
        // Only log actual errors, not "QR code not found" type messages
        if (errorMessage && !errorMessage.includes('No QR code found')) {
            console.debug('Scan error:', errorMessage);
        }
    }
    
    handleStartError(error) {
        let message = 'Failed to start camera';
        
        if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
            message = 'Camera permission denied. Please allow camera access and try again.';
        } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
            message = 'No camera found. Please connect a camera and try again.';
        } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
            message = 'Camera is in use by another application. Please close other apps using the camera.';
        } else if (error.name === 'OverconstrainedError') {
            message = 'Camera does not meet requirements. Trying alternative settings...';
        } else if (error.message) {
            message = error.message;
        }
        
        this.setStatus(message, 'error');
        
        // Reset buttons
        if (this.startButton) this.startButton.disabled = false;
        if (this.stopButton) this.stopButton.disabled = true;
        
        this.isScanning = false;
    }
    
    async sendToServer(qrCode) {
        const response = await fetch(this.apiEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                qr_code: qrCode,
                event_id: this.eventId
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }
    
    showSuccessResult(data) {
        const html = `
            <div class="result-card result-success">
                <div class="result-icon">
                    <i class="ph ph-check-circle"></i>
                </div>
                <div class="result-content">
                    <h3>Attendance Marked!</h3>
                    <div class="result-details">
                        <p><strong>Student:</strong> ${this.escapeHtml(data.student_name || 'N/A')}</p>
                        <p><strong>Email:</strong> ${this.escapeHtml(data.student_email || 'N/A')}</p>
                        <p><strong>Event:</strong> ${this.escapeHtml(data.event_name || 'N/A')}</p>
                        <p><strong>Time:</strong> ${this.escapeHtml(data.timestamp || new Date().toLocaleString())}</p>
                    </div>
                </div>
            </div>
        `;
        this.showResult(html, 'success');
        
        if (this.onScanSuccess) {
            this.onScanSuccess(data);
        }
    }
    
    showDuplicateResult(data) {
        const html = `
            <div class="result-card result-warning">
                <div class="result-icon">
                    <i class="ph ph-warning-circle"></i>
                </div>
                <div class="result-content">
                    <h3>Already Scanned</h3>
                    <div class="result-details">
                        <p><strong>Student:</strong> ${this.escapeHtml(data.student_name || 'N/A')}</p>
                        <p><strong>Previous Scan:</strong> ${this.escapeHtml(data.scan_time || 'N/A')}</p>
                        <p class="result-note">This student's attendance was already recorded.</p>
                    </div>
                </div>
            </div>
        `;
        this.showResult(html, 'warning');
    }
    
    showErrorResult(data) {
        const html = `
            <div class="result-card result-error">
                <div class="result-icon">
                    <i class="ph ph-x-circle"></i>
                </div>
                <div class="result-content">
                    <h3>Scan Failed</h3>
                    <div class="result-details">
                        <p>${this.escapeHtml(data.message || 'Unknown error occurred')}</p>
                    </div>
                </div>
            </div>
        `;
        this.showResult(html, 'error');
        
        if (this.onScanError) {
            this.onScanError(data);
        }
    }
    
    async resumeScanning() {
        if (!this.isScanning || !this.html5QrCode) return;
        
        this.isProcessing = false;
        
        try {
            await this.html5QrCode.resume();
            this.setStatus('Scanner active - Point camera at QR code', 'success');
        } catch (error) {
            console.warn('Could not resume scanner:', error);
            // Try restarting
            await this.stopScanning();
            await this.startScanning();
        }
    }
    
    async stopScanning() {
        if (!this.html5QrCode) {
            this.isScanning = false;
            return;
        }
        
        try {
            await this.html5QrCode.stop();
        } catch (error) {
            console.warn('Error stopping scanner:', error);
        }
        
        try {
            this.html5QrCode.clear();
        } catch (error) {
            console.warn('Error clearing scanner:', error);
        }
        
        this.html5QrCode = null;
        this.isScanning = false;
        this.isProcessing = false;
        
        // Update buttons
        if (this.startButton) this.startButton.disabled = false;
        if (this.stopButton) this.stopButton.disabled = true;
        
        this.setStatus('Scanner stopped', 'info');
    }
    
    scanNext() {
        this.hideResult();
        if (this.scanNextButton) {
            this.scanNextButton.style.display = 'none';
        }
        this.startScanning();
    }
    
    playBeep() {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = 800;
            oscillator.type = 'sine';
            gainNode.gain.value = 0.1;
            
            oscillator.start();
            oscillator.stop(audioContext.currentTime + 0.1);
        } catch (e) {
            // Audio not available - ignore
        }
    }
    
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Method to switch cameras (front/back)
    async switchCamera() {
        if (!this.isScanning || this.availableCameras.length < 2) return;
        
        const currentIndex = this.availableCameras.findIndex(c => c.id === this.currentCameraId);
        const nextIndex = (currentIndex + 1) % this.availableCameras.length;
        const nextCamera = this.availableCameras[nextIndex];
        
        this.setStatus('Switching camera...', 'info');
        
        try {
            await this.stopScanning();
            this.currentCameraId = nextCamera.id;
            await this.startScanning();
        } catch (error) {
            console.error('Failed to switch camera:', error);
            this.setStatus('Failed to switch camera', 'error');
        }
    }
}

// Export for use in templates
window.CampusQRScanner = CampusQRScanner;
