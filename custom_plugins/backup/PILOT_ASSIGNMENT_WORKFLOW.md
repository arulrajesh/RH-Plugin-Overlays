# Pilot Assignment Workflow for OBS

## The Challenge

Secondary colors are currently tied to **pilot IDs**, not node/channel numbers. This means:
- When you reassign pilots to different nodes, the secondary colors stay with the pilots
- OBS URLs need to be updated when heat assignments change

## Recommended Workflows

### Option 1: Set Colors Once Per Event (Easiest)

**Best for:** Events where pilots stay in the same channels throughout

1. Assign pilots to their channels/nodes for the event
2. Configure secondary colors in the settings page
3. Generate OBS URLs and set them up in OBS
4. Don't change pilot assignments for the rest of the event

✅ **Advantage:** Set up once, works all day
❌ **Limitation:** Pilots must stay in same channels

---

### Option 2: Update URLs When Heats Change

**Best for:** Events where pilots rotate channels between heats

1. Before each heat, check pilot assignments in RotorHazard
2. Open settings page and verify "Current Pilot → Secondary Color Mapping"
3. If assignments changed, click "🔄 Refresh URLs"
4. Copy updated URLs and paste into OBS (right-click source → Properties)

✅ **Advantage:** Works with any heat assignment
❌ **Limitation:** Requires manual URL updates

**Time required:** ~30 seconds per heat change

---

### Option 3: Don't Use Secondary Colors in OBS

**Best for:** Events with frequent pilot reassignments

Just use single-color glow effects:
- Pilots get their primary color from RotorHazard
- Single-color pulsating glow works automatically
- No secondary colors = no URL updates needed

URL Example:
```
http://localhost:5000/ddr_overlays/pages/stream/next_up?show_channel=true
```

✅ **Advantage:** Zero maintenance, works with any assignments
❌ **Limitation:** No dual-color blink effect

---

### Option 4: Use Settings Page in OBS (Not Recommended)

Open the settings page itself as an OBS browser source and configure there. This stores settings in OBS's localStorage directly.

❌ **Problem:** Still uses pilot IDs, same issue as Option 2

---

## Why Node-Based Colors Would Be Better

If secondary colors were assigned to **node numbers** instead of pilot IDs:
- Node 1 always has Color A
- Node 2 always has Color B
- Doesn't matter which pilot is in that node

**Future Enhancement Idea:** Add a "Node-Based Mode" toggle that switches between:
- **Pilot Mode** (current): Colors follow the pilot
- **Node Mode** (new): Colors assigned to physical channels

Example:
```
Node 1 (R1): Always blinks red
Node 2 (R2): Always blinks blue
Node 3 (R3): Always blinks green
...regardless of which pilot is flying
```

This would be perfect for OBS since node numbers don't change!

---

## Best Practice Recommendation

**For most events:** Use **Option 1** or **Option 3**

- If pilots stay in same channels: Use dual-color (Option 1)
- If pilots rotate frequently: Skip dual-color (Option 3)

**For special broadcasts:** Use **Option 2**
- When you want dual-color effects despite pilot changes
- Requires discipline to update URLs between heats

---

## Technical Note

The URLs include all settings as parameters:
```
?show_channel=true&secondary_colors={"1":"#ff0000","2":"#00ff00"}
```

Where `"1"` and `"2"` are pilot IDs, not node numbers.

When pilots are reassigned, these IDs change, requiring new URLs.
