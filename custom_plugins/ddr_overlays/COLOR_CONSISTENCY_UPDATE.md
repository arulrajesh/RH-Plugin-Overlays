# Color Consistency Update - Using activeColor Across All Overlays

## Problem

Previously, the overlays used inconsistent color sources:
- **Next Up / Last Heat**: Used `pilot.color` from `pilot_data` (always pilot-specific)
- **Node overlays**: Used `activeColor` from `current_heat` (respects RotorHazard's seat/pilot setting)

This meant that if RotorHazard was set to "color by seat", the node overlays would show seat colors but Next Up/Last Heat would still show pilot colors.

## Solution

All overlays now consistently use `activeColor` from the `current_heat` socket event, which **respects RotorHazard's color assignment setting** (color by pilot vs. color by seat).

## Changes Made

### 1. **ddr_overlays.js** - Updated `build_nextup()` function

**Added parameter**:
```javascript
function build_nextup(leaderboard, display_type, meta, ddr_pilot_data, ddr_frequency_data, show_position=false, ddr_heat_colors={})
```

**Updated color selection logic** (lines 199-237):
```javascript
// Priority 1: Use activeColor from current_heat (respects RotorHazard seat/pilot color setting)
if (ddr_heat_colors && ddr_heat_colors[current_pilot_id]) {
    pilot_color = colorvalToHex(ddr_heat_colors[current_pilot_id]);
    color_source = 'activeColor (heat data)';
}
// Priority 2: Fallback to pilot_data color (always pilot-specific)
else if (ddr_pilot_data && Array.isArray(ddr_pilot_data)) {
    let pilot = ddr_pilot_data.find(p => p.pilot_id === current_pilot_id);
    if (pilot && pilot.color) {
        pilot_color = pilot.color;
        color_source = 'pilot_data (pilot-specific)';
    }
}
```

**Added debug logging**:
```javascript
console.log('[DDR Overlays] ====== Color Source Debug ======');
console.log('[DDR Overlays] Pilot ID:', current_pilot_id);
console.log('[DDR Overlays] Primary color source:', color_source);
console.log('[DDR Overlays] Primary color value:', pilot_color);
console.log('[DDR Overlays] Available heat colors:', ...);
console.log('[DDR Overlays] Secondary colors from settings:', ...);
```

### 2. **next_up.html** - Capture and pass heat colors

**Added variable** (line 69):
```javascript
var ddr_heat_colors = {}; // Store activeColor from current_heat event
```

**Added `current_heat` handler** (lines 114-144):
```javascript
socket.on('current_heat', function (msg) {
    // Capture activeColor from heat data (respects RotorHazard's seat/pilot color setting)
    console.log('[DDR Overlays - Next Up] current_heat received, capturing activeColors');
    ddr_heat_colors = {}; // Reset

    if (msg.heatNodes) {
        for (var nodeIdx in msg.heatNodes) {
            var heatNode = msg.heatNodes[nodeIdx];
            if (heatNode && heatNode.pilot_id && heatNode.activeColor) {
                ddr_heat_colors[heatNode.pilot_id] = heatNode.activeColor;
                console.log('[DDR Overlays - Next Up] Captured activeColor for pilot', heatNode.pilot_id, ':', heatNode.activeColor);
            }
        }
    }

    // Rebuild display if we have leaderboard data
    if (ddr_last_leaderboard_data) {
        $('#nextup_pilot_box').empty();
        DDR_Settings.ready(function() {
            build_nextup(..., ddr_heat_colors); // Pass heat colors
        });
    }
});
```

**Updated all `build_nextup()` calls** to include `ddr_heat_colors` parameter:
- Line 140: In `current_heat` handler
- Line 168: In `frequency_data` handler
- Line 192: In `leaderboard` handler

### 3. **last_heat.html** - Same changes as next_up.html

**Added variable** (line 69):
```javascript
var ddr_heat_colors = {}; // Store activeColor from current_heat event
```

**Added `current_heat` handler** (lines 111-141) - identical to next_up.html

**Updated all `build_nextup()` calls** to include `ddr_heat_colors` parameter:
- Line 137: In `current_heat` handler
- Line 165: In `frequency_data` handler
- Line 240: In leaderboard handler

### 4. **node.html** - Already uses activeColor correctly

Node overlays already use `activeColor` directly from the `current_heat` event (line 174):
```javascript
if (hn.activeColor) {
    var color = colorvalToHex(hn.activeColor);
    updateNodeAnimation(color);
}
```

No changes needed for node overlays.

## How It Works

1. **Heat Load**: When RotorHazard sends a `current_heat` event:
   - The event contains `heatNodes` array with each pilot's `activeColor`
   - `activeColor` is set by RotorHazard based on its "color by pilot/seat" setting
   - Overlays capture this into `ddr_heat_colors` object keyed by `pilot_id`

2. **Leaderboard Display**: When building the overlay display:
   - First checks if `ddr_heat_colors[pilot_id]` exists → use activeColor (respects setting)
   - Falls back to `pilot_data.color` if heat colors aren't available yet
   - Uses default gray if neither source has a color

3. **Consistency**: All overlays now respect the same color source priority

## Color Source Priority

1. **activeColor from current_heat** (preferred) - Respects RotorHazard setting
2. **pilot.color from pilot_data** (fallback) - Always pilot-specific
3. **Default gray** (#b9b9b9) - When no color data available

## Debug Logs

When running overlays, check the browser console for:

```
[DDR Overlays - Next Up] current_heat received, capturing activeColors
[DDR Overlays - Next Up] Captured activeColor for pilot 1 : 16737536
[DDR Overlays] ====== Color Source Debug ======
[DDR Overlays] Pilot ID: 1
[DDR Overlays] Primary color source: activeColor (heat data)
[DDR Overlays] Primary color value: #ff6200
[DDR Overlays] Available heat colors: {"1":16737536,"2":65314}
```

## Testing

To verify the changes work correctly:

1. **Test with "Color by Pilot"** (RotorHazard default):
   - All overlays should show each pilot's assigned color
   - Colors should stay with pilots even when they move seats

2. **Test with "Color by Seat"**:
   - All overlays should show seat-based colors
   - Same seat should show same color regardless of pilot

3. **Check console logs** to verify color source:
   - Should see "activeColor (heat data)" when heat is loaded
   - May see "pilot_data (pilot-specific)" on initial load before heat data arrives

## Benefits

✅ **Consistent behavior** across all overlay types
✅ **Respects RotorHazard settings** for color assignment
✅ **Graceful fallback** when heat data isn't available yet
✅ **Detailed debug logging** for troubleshooting
✅ **No breaking changes** - works with existing setups
