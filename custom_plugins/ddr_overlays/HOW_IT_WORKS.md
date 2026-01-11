# How Secondary Colors Work

## The Smart Way: Colors Follow Pilots

Secondary colors are assigned to **pilots**, not nodes. This is actually perfect because:

### How It Works:

1. You configure: "Pilot John → Red secondary color"
2. John is assigned to Node 1 for Heat 1
3. Overlay shows John with red blink on Node 1 ✅
4. John is reassigned to Node 3 for Heat 2
5. Overlay **automatically** shows John with red blink on Node 3 ✅

**The colors follow the pilot!**

### Why This Is Better:

✅ **Set URLs once** - Never need to update OBS browser source URLs
✅ **Works with any heat assignment** - Pilots can move between nodes
✅ **Consistent branding** - Each pilot always has their signature colors
✅ **Zero maintenance** - Configure colors once at start of event

### Example Scenario:

**Event Setup:**
- Pilot "SpeedyFPV" → Secondary Color: Red (#ff0000)
- Pilot "SmoothOperator" → Secondary Color: Blue (#0000ff)

**Heat 1:**
- Node 1: SpeedyFPV (shows orange→red blink)
- Node 2: SmoothOperator (shows green→blue blink)

**Heat 2:**
- Node 1: SmoothOperator (shows green→blue blink) ← Automatically!
- Node 2: SpeedyFPV (shows orange→red blink) ← Automatically!

The OBS URL never changed! The overlay dynamically looks up who's flying and applies their colors.

### Technical Details:

When a heat starts, the overlay:
1. Receives leaderboard data with pilot assignments
2. For each pilot, looks up their pilot_id
3. Checks localStorage for that pilot's secondary color
4. Applies the color if found
5. Updates automatically when heat changes

### What Gets Stored:

**In Chrome/Browser localStorage:**
```json
{
  "1": "#ff0000",  // Pilot ID 1 → Red
  "2": "#0000ff",  // Pilot ID 2 → Blue
  "3": "#00ff00"   // Pilot ID 3 → Green
}
```

**In OBS URL:**
```
?secondary_colors=%7B%221%22%3A%22%23ff0000%22%2C%222%22%3A%22%2300ff00%22%7D
```
(Same data, URL-encoded)

### URL Parameters Are Static:

The URL parameters define which pilots have secondary colors, but the overlay dynamically determines where to show them based on current heat assignments.

**This means:**
- Configure pilots' colors once
- Set OBS URL once
- Works for all heats automatically

### When To Update URLs:

You only need to regenerate URLs if:
- ✅ You add new pilots to the event
- ✅ You change a pilot's secondary color
- ✅ You adjust other settings (glow intensity, animation speed, etc.)

You do NOT need to update URLs when:
- ❌ Pilots are reassigned to different nodes
- ❌ Heat changes
- ❌ Race format changes

### Best Practice:

1. **Day of Event Setup:**
   - Configure all pilots' secondary colors in settings page
   - Generate OBS URLs
   - Set them in OBS browser sources
   - Done!

2. **During Event:**
   - Change heats as needed in RotorHazard
   - Colors automatically follow pilots
   - No OBS updates needed

3. **If You Add New Pilots:**
   - Add their secondary colors in settings page
   - Click "🔄 Refresh URLs"
   - Update OBS browser sources with new URLs
   - Continue racing

### Comparison: Pilot-Based vs Node-Based

| Aspect | Pilot-Based (Current) | Node-Based (Alternative) |
|--------|----------------------|--------------------------|
| URL Updates | Only when adding pilots | Only when changing node colors |
| Pilot Consistency | ✅ Same colors everywhere | ❌ Colors change with node |
| Branding | ✅ Pilot keeps their colors | ❌ Node has fixed colors |
| Flexibility | ✅ Pilots can move nodes | ⚠️ Locked to nodes |
| Best For | **Most events** | Fixed node assignments |

**Conclusion:** Pilot-based is the right choice for most use cases!
