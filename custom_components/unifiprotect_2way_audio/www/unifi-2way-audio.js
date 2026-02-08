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
    this._isTalkbackActive = false;
    this._isMuted = false;
    this._lastCameraId = null;
    this._stream = null;
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
    this.updateCameraFeed();
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
          background: var(--accent-color);
          transform: scale(1.1);
        }
        .control-button:active {
          transform: scale(0.95);
        }
        .control-button.active {
          background: var(--accent-color, #03a9f4);
          color: white;
        }
        .control-button.recording {
          background: var(--accent-color, #03a9f4);
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
          <div id="camera-stream"></div>
          <div class="controls-overlay">
            <button class="control-button" id="mute-button" title="Toggle Mute">
              <svg class="icon" viewBox="0 0 24 24">
                <path id="mute-icon-path" d="M14,3.23V5.29C16.89,6.15 19,8.83 19,12C19,15.17 16.89,17.85 14,18.71V20.77C18,19.86 21,16.28 21,12C21,7.72 18,4.14 14,3.23M16.5,12C16.5,10.23 15.5,8.71 14,7.97V16C15.5,15.29 16.5,13.76 16.5,12M3,9V15H7L12,20V4L7,9H3Z"/>
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
    this._cameraStream = this.shadowRoot.getElementById('camera-stream');
    this._statusText = this.shadowRoot.getElementById('status-text');
    this._statusDot = this.shadowRoot.getElementById('status-dot');
    this._statusLabel = this.shadowRoot.getElementById('status-label');
    this._muteIconPath = this.shadowRoot.getElementById('mute-icon-path');

    this._muteButton.addEventListener('click', () => this.toggleMute());
    this._talkbackButton.addEventListener('click', () => this.toggleTalkback());

    this.updateState();
    this.updateCameraFeed();
  }

  updateCameraFeed() {
    console.dir({
      updateCameraFeed: {
        lastCameraId: this._lastCameraId,
        stream: this._stream,  
      }
    });
    if (!this._hass || !this._config) return;  
    const container = this.shadowRoot.getElementById("camera-stream");
    if (!container) return;

    container.innerHTML = "";

    const cameraEntityId = this.getCameraEntityId();
    if (!cameraEntityId) return;

    const stateObj = this._hass.states[cameraEntityId];
    if (!stateObj) return;

    if (cameraEntityId === this._lastCameraId && this._stream !== null) {
      return;
    }
    this._stream = document.createElement("ha-camera-stream");
    this._stream.hass = this._hass;
    this._stream.stateObj = stateObj;
    this._stream.controls = false;

    container.appendChild(this._stream);
    this._lastCameraId = cameraEntityId;
  }

  getCameraEntity() {
    return this._hass.states[this.getCameraEntityId()];
  }

  getCameraEntityId() {
    // Get the camera entity from the switch entity's target_camera attribute
    if (!this._config.entity || !this._hass) {
      return null;
    }
    
    const switchEntity = this._hass.states[this._config.entity];
    if (!switchEntity || !switchEntity.attributes || !switchEntity.attributes.target_camera) {
      return null;
    }
    
    return switchEntity.attributes.target_camera;
  }

  getSwitchEntityId() {
    // Return the configured switch entity
    if (!this._config.entity || !this._hass) {
      return null;
    }
    
    return this._config.entity;
  }

  getMediaPlayerEntityId() {
    // Get the media_player entity from the switch entity's target_media_player attribute
    if (!this._config.entity || !this._hass) {
      return null;
    }
    
    const switchEntity = this._hass.states[this._config.entity];
    if (!switchEntity || !switchEntity.attributes || !switchEntity.attributes.target_media_player) {
      return null;
    }
    
    return switchEntity.attributes.target_media_player;
  }

  updateState() {
    if (!this._hass || !this._config) return;

    // Get switch entity state for talkback
    const switchEntityId = this.getSwitchEntityId();
    const switchState = this._hass.states[switchEntityId];
    
    // Get media_player entity state for mute
    const mediaPlayerEntityId = this.getMediaPlayerEntityId();
    const mediaPlayerState = this._hass.states[mediaPlayerEntityId];
    
    // Determine if talkback is active from switch state
    const isTalkbackActive = switchState ? switchState.state === 'on' : false;
    
    // Determine if muted from media_player state
    const isMuted = mediaPlayerState ? mediaPlayerState.attributes.is_volume_muted === true : false;

    // Update talkback button state
    if (isTalkbackActive !== this._isTalkbackActive) {
      this._isTalkbackActive = isTalkbackActive;
      if (isTalkbackActive) {
        this._talkbackButton.classList.add('recording');
      } else {
        this._talkbackButton.classList.remove('recording');
      }
    }

    // Update mute button state
    if (isMuted !== this._isMuted) {
      this._isMuted = isMuted;
      if (isMuted) {
        this._muteButton.classList.add('muted');
        // Muted icon (speaker with X)
        this._muteIconPath.setAttribute('d', 'M12,4L9.91,6.09L12,8.18M4.27,3L3,4.27L7.73,9H3V15H7L12,20V13.27L16.25,17.52C15.58,18.04 14.83,18.46 14,18.7V20.77C15.38,20.45 16.63,19.82 17.68,18.96L19.73,21L21,19.73M19,12C19,12.94 18.8,13.82 18.46,14.64L19.97,16.15C20.62,14.91 21,13.5 21,12C21,7.72 18,4.14 14,3.23V5.29C16.89,6.15 19,8.83 19,12M16.5,12C16.5,10.23 15.5,8.71 14,7.97V10.18L16.45,12.63C16.5,12.43 16.5,12.21 16.5,12Z');
      } else {
        this._muteButton.classList.remove('muted');
        // Unmuted icon (speaker)
        this._muteIconPath.setAttribute('d', 'M14,3.23V5.29C16.89,6.15 19,8.83 19,12C19,15.17 16.89,17.85 14,18.71V20.77C18,19.86 21,16.28 21,12C21,7.72 18,4.14 14,3.23M16.5,12C16.5,10.23 15.5,8.71 14,7.97V16C15.5,15.29 16.5,13.76 16.5,12M3,9V15H7L12,20V4L7,9H3Z');
      }
    }

    // Update status
    if (isTalkbackActive) {
      this._statusText.textContent = 'Talkback Active';
      this._statusDot.className = 'status-dot recording';
      this._statusLabel.textContent = 'Active';
    } else if (isMuted) {
      this._statusText.textContent = 'Muted';
      this._statusDot.className = 'status-dot inactive';
      this._statusLabel.textContent = 'Muted';
    } else {
      this._statusText.textContent = 'Ready';
      this._statusDot.className = 'status-dot inactive';
      this._statusLabel.textContent = 'Idle';
    }

    this.updateCameraFeed();
  }

  async toggleMute() {
    if (!this._hass || !this._config) return;

    // Get media_player entity ID
    const mediaPlayerEntityId = this.getMediaPlayerEntityId();
    
    if (!mediaPlayerEntityId) {
      this._statusText.textContent = 'Camera speaker not available';
      console.warn('No media_player entity found for device');
      return;
    }
    
    try {
      // Toggle mute on the media_player entity
      await this._hass.callService('media_player', 'volume_mute', {
        entity_id: mediaPlayerEntityId,
        is_volume_muted: !this._isMuted,
      });
      this._statusText.textContent = !this._isMuted ? 'Unmuted' : 'Muted';
    } catch (error) {
      console.error('Error toggling mute:', error);
      this._statusText.textContent = 'Error toggling mute';
    }
  }

  async toggleTalkback() {
    if (!this._hass || !this._config) return;

    // Get switch entity ID
    const switchEntityId = this.getSwitchEntityId();
    
    try {
      // Toggle the switch entity
      await this._hass.callService('switch', 'toggle', {
        entity_id: switchEntityId,
      });
    } catch (error) {
      console.error('Error toggling talkback:', error);
      this._statusText.textContent = 'Error toggling talkback';
    }
  }

  static getConfigElement() {
    return document.createElement('unifiprotect-2way-audio-card-editor');
  }

  static getStubConfig() {
    return {
      entity: '',
      label: 'Talkback Control',
    };
  }

  static getConfigForm() {
    return {
      schema: [
        { 
          name: "label", 
          selector: { text: {} } 
        },
        { 
          name: "entity", 
          required: true, 
          selector: { 
            entity: {
              filter: [{domain: "switch", integration: "unifiprotect_2way_audio"}]
            } 
          } 
        },
      ],
      computeLabel: (schema) => {
        switch (schema.name) {
          case "label":
            return "Card Label";
          case "entity":
            return "Talkback Switch Entity";
        }
        return undefined;
      },
      computeHelper: (schema) => {
        switch (schema.name) {
          case "label":
            return "Optional label to display on the card";
          case "entity":
            return "Select the UniFi Protect 2-Way Audio talkback switch entity";
        }
        return undefined;
      },
      assertConfig: (config) => {
        if (!config.entity) {
          throw new Error("'entity' must be specified.");
        }
      },
    };
  }
}

// Register the custom card
customElements.define('unifi-2way-audio', Unifi2WayAudio);

const card = {
  type: 'unifi-2way-audio',
  name: 'UniFi Protect 2-Way Audio Card',
  description: 'A card for 2-way audio control of UniFi Protect cameras',
  preview: false,
  documentationURL: 'https://github.com/constructorfleet/hacs-unifiprotect-2way-audio',
};

// Apple iOS 12 doesn't support `||=`
if (window.customCards) window.customCards.push(card);
else window.customCards = [card];

console.info(
  '%c  UNIFIPROTECT-2WAY-AUDIO-CARD  %c  1.0.0  ',
  'color: white; font-weight: bold; background: #03a9f4',
  'color: white; font-weight: bold; background: dimgray',
);
