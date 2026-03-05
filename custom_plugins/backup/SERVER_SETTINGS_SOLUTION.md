# Server-Side Settings Solution

## The Problem (Solved!)

**Before:** Settings were stored in browser localStorage
- Chrome has its own localStorage
- OBS has its own localStorage
- URLs needed parameters to sync settings
- Hundreds of OBS sources would need URL updates

**This was NOT scalable!**

## The Solution: Server-Side Storage

Settings are now stored on the **RotorHazard server** itself!

### How It Works:

```
Settings Page (any browser)
    ↓
Saves to Server
    ↓
plugins/ddr_overlays/data/settings.json
    ↑
All Overlays Read From Server
    ↑
Works in Chrome AND OBS automatically!
```

### Benefits:

✅ **One source of truth** - Server stores all settings
✅ **No URL parameters needed** - Clean URLs forever
✅ **Works everywhere** - Chrome, OBS, any browser
✅ **Zero OBS updates** - Set URL once, never touch again
✅ **Automatic sync** - Change settings once, applies everywhere

## Implementation

### 1. Server API Endpoints

**GET `/ddr_overlays/api/settings`**
- Returns all settings as JSON
- Example response:
```json
{
  "show_channel": true,
  "border_thickness": "5",
  "glow_intensity": "20",
  "animation_speed": "2.5",
  "pilot_secondary_colors": {
    "1": "#ff0000",
    "2": "#00ff00"
  }
}
```

**POST `/ddr_overlays/api/settings`**
- Updates settings on server
- Accepts partial updates
- Example request:
```json
{
  "show_channel": true,
  "pilot_secondary_colors": {
    "1": "#ff0000"
  }
}
```

### 2. Client-Side Library

**ddr_settings.js** - Manages settings access

```javascript
// Load settings from server
DDR_Settings.load(function(settings) {
    console.log('Settings loaded:', settings);
});

// Get a setting
var showChannel = DDR_Settings.get('show_channel', false);

// Set a setting (saves to server automatically)
DDR_Settings.set('show_channel', true, function(success) {
    console.log('Saved:', success);
});
```

### 3. Fallback Support

If server API fails:
- Falls back to localStorage
- Ensures overlays still work
- Logs warning to console

## User Workflow

### Setup (One Time):

1. Open settings page: `http://localhost:5000/ddr_overlays`
2. Configure all settings (channel display, colors, etc.)
3. Settings automatically save to server
4. Add overlays to OBS with clean URLs:
   - `http://localhost:5000/ddr_overlays/pages/stream/next_up`
   - `http://localhost:5000/ddr_overlays/pages/stream/last_heat`
   - `http://localhost:5000/ddr_overlays/pages/stream/node/1`

### During Event:

1. Change settings anytime in settings page
2. Settings save to server instantly
3. **All overlays update automatically!**
4. Works in Chrome preview AND OBS simultaneously
5. No URL updates ever needed

### Adding New Pilots:

1. Configure their secondary colors in settings page
2. Save (automatic)
3. Done! Their colors work in all overlays immediately

## Technical Details

### Storage Location:

```
plugins/
  ddr_overlays/
    data/
      settings.json  ← All settings stored here
```

### Settings Schema:

```json
{
  "show_channel": boolean,
  "border_thickness": string (number),
  "glow_intensity": string (number),
  "animation_speed": string (number),
  "pilot_secondary_colors": {
    "<pilot_id>": "<hex_color>",
    ...
  }
}
```

### API Routes:

- **GET** `/ddr_overlays/api/settings` - Fetch settings
- **POST** `/ddr_overlays/api/settings` - Update settings

### Files Modified:

1. `__init__.py` - Added API endpoints and JSON storage ✅
2. `ddr_settings.js` - New client library for settings management ✅
3. `ddr_overlays.js` - Updated to use DDR_Settings instead of localStorage ✅
4. `next_up.html` - Loads settings from server ✅
5. `ddr_overlay_index.html` - Settings page uses server API ✅
6. `last_heat.html` - Loads settings from server ✅
7. `node.html` - Loads settings from server ✅

**All files updated! Server-side settings implementation is complete.**

## Migration Path

### For Existing Users:

1. **Automatic:** Settings library falls back to localStorage
2. First time opening settings page after update:
   - Reads current localStorage values
   - Saves them to server
   - Future reads come from server

### Clean URLs in OBS:

**Old way** (complicated):
```
http://localhost:5000/ddr_overlays/pages/stream/next_up?show_channel=true&border_thickness=5&glow_intensity=20&animation_speed=2.5&secondary_colors=%7B%221%22%3A%22%23ff0000%22%7D
```

**New way** (clean):
```
http://localhost:5000/ddr_overlays/pages/stream/next_up
```

That's it! All settings come from the server automatically.

## Advantages Over URL Parameters:

| Aspect | URL Parameters | Server Storage |
|--------|----------------|----------------|
| URL Length | Long, messy | Clean, short |
| Updates Needed | Every time settings change | Never |
| Works in OBS | Yes, but cumbersome | Yes, automatically |
| Works in Chrome | Yes | Yes |
| Sync Between Browsers | No | Yes |
| Number of Sources to Update | Hundreds | Zero |
| Settings Management | Encoded in URL | Centralized on server |

## Future Enhancements:

- Web UI to import/export settings
- Per-event settings profiles
- Reset to defaults button
- Settings backup/restore

## Conclusion:

**Server-side storage is the right solution!**

- ✅ Clean URLs forever
- ✅ Zero OBS maintenance
- ✅ Works everywhere automatically
- ✅ Single source of truth
- ✅ Easy to manage

Users configure settings once, and they work everywhere, forever. No URL updates needed!
