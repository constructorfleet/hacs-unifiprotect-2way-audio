/**
 * UniFi Protect 2-Way Audio Card
 * 
 * A custom Lovelace card for Home Assistant that provides 2-way audio controls
 * for UniFi Protect cameras with microphone and speaker capabilities.
 */

class Unifi2WayAudio extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._hass = null;
    this._config = null;
    this._isRecording = false;
    this._isMuted = false;
    this._mediaRecorder = null;
    this._audioChunks = [];
    this._mediaStream = null;
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error('You need to define an entity');
    }
    this._config = config;
    this.render();
  }

  set hass(hass) {
    this._hass = hass;
    this.updateState();
  }

  getCardSize() {
    return 3;
  }

  render() {
    if (!this._config) {
      return;
    }
    
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
        }
        ha-card {
          overflow: hidden;
          position: relative;
        }
        .camera-container {
          position: relative;
          width: 100%;
          aspect-ratio: 16 / 9;
          background: #000;
        }
        .camera-image {
          width: 100%;
          height: 100%;
          object-fit: contain;
        }
        .controls-overlay {
          position: absolute;
          bottom: 0;
          left: 0;
          right: 0;
          background: linear-gradient(to top, rgba(0,0,0,0.7), transparent);
          padding: 16px;
          display: flex;
          justify-content: center;
          gap: 12px;
          align-items: flex-end;
        }
        .control-button {
          background: rgba(255, 255, 255, 0.9);
          border: none;
          border-radius: 50%;
          width: 56px;
          height: 56px;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.3s ease;
          box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }
        .control-button:hover {
          background: rgba(255, 255, 255, 1);
          transform: scale(1.1);
        }
        .control-button:active {
          transform: scale(0.95);
        }
        .control-button.active {
          background: var(--primary-color, #03a9f4);
          color: white;
        }
        .control-button.recording {
          background: #f44336;
          color: white;
          animation: pulse 1.5s ease-in-out infinite;
        }
        .control-button.muted {
          background: #ff9800;
          color: white;
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.7; }
        }
        .icon {
          width: 24px;
          height: 24px;
          fill: currentColor;
        }
        .status-bar {
          padding: 8px 16px;
          background: var(--card-background-color, #fff);
          display: flex;
          justify-content: space-between;
          align-items: center;
          font-size: 14px;
        }
        .status-text {
          color: var(--primary-text-color);
        }
        .status-indicator {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .status-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #4caf50;
        }
        .status-dot.inactive {
          background: #9e9e9e;
        }
        .status-dot.recording {
          background: #f44336;
          animation: pulse 1.5s ease-in-out infinite;
        }
      </style>
      <ha-card>
        <div class="camera-container">
          <img class="camera-image" id="camera-image" src="" alt="Camera feed">
          <div class="controls-overlay">
            <button class="control-button" id="mute-button" title="Toggle Mute">
              <svg class="icon" viewBox="0 0 24 24">
                <path id="mute-icon-path" d="M12,2A3,3 0 0,1 15,5V11A3,3 0 0,1 12,14A3,3 0 0,1 9,11V5A3,3 0 0,1 12,2M19,11C19,14.53 16.39,17.44 13,17.93V21H11V17.93C7.61,17.44 5,14.53 5,11H7A5,5 0 0,0 12,16A5,5 0 0,0 17,11H19Z"/>
              </svg>
            </button>
            <button class="control-button" id="talkback-button" title="Push to Talk">
              <svg class="icon" viewBox="0 0 24 24">
                <path d="M9,5A4,4 0 0,1 13,9A4,4 0 0,1 9,13A4,4 0 0,1 5,9A4,4 0 0,1 9,5M9,15C11.67,15 17,16.34 17,19V21H1V19C1,16.34 6.33,15 9,15M16.76,5.36C18.78,7.56 18.78,10.61 16.76,12.63L15.08,10.94C15.92,9.76 15.92,8.23 15.08,7.05L16.76,5.36M20.07,2C24,6.05 23.97,12.11 20.07,16L18.44,14.37C21.21,11.19 21.21,6.65 18.44,3.63L20.07,2Z"/>
              </svg>
            </button>
          </div>
        </div>
        <div class="status-bar">
          <div class="status-text" id="status-text">Ready</div>
          <div class="status-indicator">
            <div class="status-dot inactive" id="status-dot"></div>
            <span id="status-label">Idle</span>
          </div>
        </div>
      </ha-card>
    `;

    this._muteButton = this.shadowRoot.getElementById('mute-button');
    this._talkbackButton = this.shadowRoot.getElementById('talkback-button');
    this._cameraImage = this.shadowRoot.getElementById('camera-image');
    this._statusText = this.shadowRoot.getElementById('status-text');
    this._statusDot = this.shadowRoot.getElementById('status-dot');
    this._statusLabel = this.shadowRoot.getElementById('status-label');
    this._muteIconPath = this.shadowRoot.getElementById('mute-icon-path');

    this._muteButton.addEventListener('click', () => this.toggleMute());
    this._talkbackButton.addEventListener('mousedown', () => this.startTalkback());
    this._talkbackButton.addEventListener('mouseup', () => this.stopTalkback());
    this._talkbackButton.addEventListener('mouseleave', () => this.stopTalkback());
    this._talkbackButton.addEventListener('touchstart', (e) => {
      e.preventDefault();
      this.startTalkback();
    });
    this._talkbackButton.addEventListener('touchend', (e) => {
      e.preventDefault();
      this.stopTalkback();
    });

    this.updateCameraFeed();
    this.updateState();
  }

  updateCameraFeed() {
    if (!this._hass || !this._config) return;

    const cameraEntity = this._config.camera_entity || this._config.entity.replace('media_player.', 'camera.');
    const cameraState = this._hass.states[cameraEntity];
    
    if (cameraState && cameraState.attributes.entity_picture) {
      this._cameraImage.src = cameraState.attributes.entity_picture;
    }
  }

  updateState() {
    if (!this._hass || !this._config) return;

    const state = this._hass.states[this._config.entity];
    if (!state) return;

    const isTalkbackActive = state.attributes.talkback_active || false;
    const isMuted = state.attributes.muted || false;

    // Update mute button
    if (isMuted !== this._isMuted) {
      this._isMuted = isMuted;
      if (isMuted) {
        this._muteButton.classList.add('muted');
        this._muteIconPath.setAttribute('d', 'M19,11C19,14.53 16.39,17.44 13,17.93V21H11V17.93C7.61,17.44 5,14.53 5,11H7A5,5 0 0,0 12,16A5,5 0 0,0 17,11H19M12,2A3,3 0 0,1 15,5V11A3,3 0 0,1 12,14A3,3 0 0,1 9,11V5A3,3 0 0,1 12,2M21,4.27L19.73,3L3,19.73L4.27,21L8.46,16.81C9.69,17.62 11.13,18.09 12.7,18.09C13.17,18.09 13.63,18.05 14.08,17.97L21,4.27Z');
      } else {
        this._muteButton.classList.remove('muted');
        this._muteIconPath.setAttribute('d', 'M12,2A3,3 0 0,1 15,5V11A3,3 0 0,1 12,14A3,3 0 0,1 9,11V5A3,3 0 0,1 12,2M19,11C19,14.53 16.39,17.44 13,17.93V21H11V17.93C7.61,17.44 5,14.53 5,11H7A5,5 0 0,0 12,16A5,5 0 0,0 17,11H19Z');
      }
    }

    // Update status
    if (isTalkbackActive) {
      this._statusText.textContent = 'Talkback Active';
      this._statusDot.className = 'status-dot recording';
      this._statusLabel.textContent = 'Active';
    } else {
      this._statusText.textContent = 'Ready';
      this._statusDot.className = 'status-dot inactive';
      this._statusLabel.textContent = 'Idle';
    }

    this.updateCameraFeed();
  }

  async toggleMute() {
    if (!this._hass || !this._config) return;

    try {
      await this._hass.callService('unifiprotect_2way_audio', 'toggle_mute', {
        entity_id: this._config.entity,
      });
      this._statusText.textContent = this._isMuted ? 'Unmuted' : 'Muted';
    } catch (error) {
      console.error('Error toggling mute:', error);
      this._statusText.textContent = 'Error toggling mute';
    }
  }

  async startTalkback() {
    if (this._isRecording || !this._hass || !this._config) return;

    this._isRecording = true;
    this._talkbackButton.classList.add('recording');
    this._statusText.textContent = 'Recording...';
    this._statusDot.className = 'status-dot recording';
    this._statusLabel.textContent = 'Recording';

    try {
      // Request microphone access
      this._mediaStream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        } 
      });

      this._audioChunks = [];
      this._mediaRecorder = new MediaRecorder(this._mediaStream, {
        mimeType: 'audio/webm;codecs=opus'
      });

      this._mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this._audioChunks.push(event.data);
        }
      };

      this._mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(this._audioChunks, { type: 'audio/webm;codecs=opus' });
        const reader = new FileReader();
        
        reader.onloadend = async () => {
          const base64Audio = reader.result.split(',')[1];
          
          try {
            await this._hass.callService('unifiprotect_2way_audio', 'start_talkback', {
              entity_id: this._config.entity,
              audio_data: base64Audio,
              sample_rate: 16000,
              channels: 1,
            });
          } catch (error) {
            console.error('Error sending audio:', error);
            this._statusText.textContent = 'Error sending audio';
          }
        };
        
        reader.readAsDataURL(audioBlob);
      };

      this._mediaRecorder.start();

      // Also call the start service immediately
      await this._hass.callService('unifiprotect_2way_audio', 'start_talkback', {
        entity_id: this._config.entity,
      });

    } catch (error) {
      console.error('Error accessing microphone:', error);
      this._statusText.textContent = 'Microphone access denied';
      this._isRecording = false;
      this._talkbackButton.classList.remove('recording');
      this._statusDot.className = 'status-dot inactive';
      this._statusLabel.textContent = 'Idle';
    }
  }

  async stopTalkback() {
    if (!this._isRecording || !this._hass || !this._config) return;

    this._isRecording = false;
    this._talkbackButton.classList.remove('recording');

    if (this._mediaRecorder && this._mediaRecorder.state !== 'inactive') {
      this._mediaRecorder.stop();
    }

    if (this._mediaStream) {
      this._mediaStream.getTracks().forEach(track => track.stop());
      this._mediaStream = null;
    }

    try {
      await this._hass.callService('unifiprotect_2way_audio', 'stop_talkback', {
        entity_id: this._config.entity,
      });
      this._statusText.textContent = 'Stopped';
      this._statusDot.className = 'status-dot inactive';
      this._statusLabel.textContent = 'Idle';
    } catch (error) {
      console.error('Error stopping talkback:', error);
    }
  }

  static getConfigElement() {
    return document.createElement('unifiprotect-2way-audio-card-editor');
  }

  static getStubConfig() {
    return {
      entity: 'media_player.camera_2way_audio',
      camera_entity: 'camera.camera',
    };
  }
}

// Register the custom card
customElements.define('unifi-2way-audio', Unifi2WayAudio);

// Register card for card picker
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'unifi-2way-audio',
  name: 'UniFi Protect 2-Way Audio Card',
  description: 'A card for 2-way audio control of UniFi Protect cameras',
  preview: false,
  documentationURL: 'https://github.com/constructorfleet/hacs-unifiprotect-2way-audio',
});

console.info(
  '%c  UNIFIPROTECT-2WAY-AUDIO-CARD  %c  1.0.0  ',
  'color: white; font-weight: bold; background: #03a9f4',
  'color: white; font-weight: bold; background: dimgray',
);
