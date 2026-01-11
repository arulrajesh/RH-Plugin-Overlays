/**
 * DDR Overlays Settings Manager
 * Handles server-side settings storage for consistency across all browsers (Chrome and OBS)
 */

var DDR_Settings = (function() {
    var settings = {};
    var isLoaded = false;
    var callbacks = [];

    /**
     * Load settings from server
     */
    function loadFromServer(callback) {
        fetch('/ddr_overlays/api/settings')
            .then(response => response.json())
            .then(data => {
                settings = data;
                isLoaded = true;
                console.log('[DDR Settings] Loaded from server:', settings);

                // Execute callback
                if (callback) callback(settings);

                // Execute any queued callbacks
                callbacks.forEach(cb => cb(settings));
                callbacks = [];
            })
            .catch(error => {
                console.error('[DDR Settings] Failed to load from server:', error);
                // Fallback to localStorage
                loadFromLocalStorage();
                if (callback) callback(settings);
            });
    }

    /**
     * Fallback: Load from localStorage
     */
    function loadFromLocalStorage() {
        settings = {
            show_channel: localStorage.getItem('ddr_show_channel') === 'true',
            border_thickness: localStorage.getItem('ddr_border_thickness') || '4',
            glow_intensity: localStorage.getItem('ddr_glow_intensity') || '15',
            animation_speed: localStorage.getItem('ddr_animation_speed') || '2',
            pilot_secondary_colors: JSON.parse(localStorage.getItem('ddr_pilot_secondary_colors') || '{}')
        };
        isLoaded = true;
        console.log('[DDR Settings] Loaded from localStorage (fallback):', settings);
    }

    /**
     * Save settings to server
     */
    function saveToServer(newSettings, callback) {
        fetch('/ddr_overlays/api/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(newSettings)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                settings = data.settings;
                console.log('[DDR Settings] Saved to server:', settings);
                if (callback) callback(true, settings);
            } else {
                console.error('[DDR Settings] Server returned error:', data.error);
                if (callback) callback(false, data.error);
            }
        })
        .catch(error => {
            console.error('[DDR Settings] Failed to save to server:', error);
            // Fallback: save to localStorage
            saveToLocalStorage(newSettings);
            if (callback) callback(false, error);
        });
    }

    /**
     * Fallback: Save to localStorage
     */
    function saveToLocalStorage(newSettings) {
        if (newSettings.show_channel !== undefined) {
            localStorage.setItem('ddr_show_channel', newSettings.show_channel);
        }
        if (newSettings.border_thickness !== undefined) {
            localStorage.setItem('ddr_border_thickness', newSettings.border_thickness);
        }
        if (newSettings.glow_intensity !== undefined) {
            localStorage.setItem('ddr_glow_intensity', newSettings.glow_intensity);
        }
        if (newSettings.animation_speed !== undefined) {
            localStorage.setItem('ddr_animation_speed', newSettings.animation_speed);
        }
        if (newSettings.pilot_secondary_colors !== undefined) {
            localStorage.setItem('ddr_pilot_secondary_colors', JSON.stringify(newSettings.pilot_secondary_colors));
        }
        console.log('[DDR Settings] Saved to localStorage (fallback)');
    }

    /**
     * Get a setting value
     */
    function get(key, defaultValue) {
        if (!isLoaded) {
            console.warn('[DDR Settings] Accessed before loaded, using default');
            return defaultValue;
        }
        return settings[key] !== undefined ? settings[key] : defaultValue;
    }

    /**
     * Set a setting value (and save to server)
     */
    function set(key, value, callback) {
        var update = {};
        update[key] = value;
        saveToServer(update, callback);
    }

    /**
     * Wait for settings to load, then execute callback
     */
    function ready(callback) {
        if (isLoaded) {
            callback(settings);
        } else {
            callbacks.push(callback);
        }
    }

    // Public API
    return {
        load: loadFromServer,
        get: get,
        set: set,
        ready: ready,
        getAll: function() { return settings; }
    };
})();
