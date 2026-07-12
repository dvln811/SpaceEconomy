# LSG Warp System - Session Handoff (July 4, 2026)

## CURRENT STATE

Branch: `cm-scale-rework` at commit `6a190ad` (stashed WIP on top)
Stash: "WIP: continuous warp flow attempt - departure broken, still popping"

## WHAT WORKS (at commit 6a190ad)

1. **Departure**: Objects move backward along -warpHeading when warp starts. Looks good.
2. **Labels/SSG**: Labels project correctly using SS coordinates, distances update during warp.
3. **Positioning**: Models end up at correct locations (10km from player at stations/gates).
4. **Speed display**: Ramps up, peaks, comes back down (no more jumps to billions).
5. **Gate/station/asteroid/planet models**: Load and display correctly when at their location.
6. **Test page** (`warp_test.html`): Proves the lsgGroup approach works perfectly in isolation.

## WHAT'S BROKEN

### The Pop-In Problem
Models "pop" visible at the end of warp instead of smoothly approaching. 

**Root cause identified**: In the game, there are TWO copies of models being created:
1. One inside `lsgGroup` (correct, created during warp fetch at 20%)
2. One added directly to `scene` by some other code path (SSE reconnect, visibility block, or nav refresh calling loaders again)

The one you SEE is #2 (added to scene at origin, pops in when conditions are met). The one in the group (#1) is invisible because the group is far away during approach.

**Evidence**: Scaling the gate 100x in the loader didn't change what the user sees - confirming the visible model is NOT the one in the group.

### Departure Snap
On departure, the `lsgGroup.position.set(0, 0, 0)` resets the group before moving it backward. If the group was at a non-zero position from a previous arrival (e.g., `warpHeading * arrDist`), it snaps to origin first then moves. Should just start moving from wherever it is.

## THE ARCHITECTURE

### Centimeter Scale (cm-scale-rework)
- 1 unit = 1 centimeter (effectively). Everything /100 from original.
- Display: multiply by 100 for meters. `111 m/s` displayed = 1.11 units/s internal.
- Station ~100 units wide (10km displayed). Gate ~10 units. Planet 5000-30000 units.
- Camera far plane: 5,000,000 units. Starfield: 4,500,000 units.

### LSG (Local Space Grid)
- Anchor object (station/gate/asteroid field) at (0,0,0) inside `lsgGroup`
- Planets placed at large offsets (50,000-200,000 units from anchor)
- Player is at `(-warpHeading * arrDist)` from origin (100 units = 10km from anchor)

### SSG (Solar System Grid)
- AU-based positions for all objects (`ss_x`, `ss_z` on each object)
- Used ONLY for: label projection, warp direction calculation, distance display
- Never rendered directly

### Warp Flow (intended)
1. **Click warp** → set warpHeading from SS coords, enter aligning state
2. **Aligning** → ship turns, accelerates to 75% speed, enters warping at 0.9995 dot
3. **Warping** (one state, continuous):
   - 0-10%: departure (move lsgGroup backward along -heading)
   - 10%: hide departure objects (once)
   - 20%: fetch `/api/lsg_data/<target>`, build models into NEW lsgGroup (hidden)
   - 70%: if ready, show group at 5000 units ahead, start approach
   - 70-100%: interpolate group from 5000 to arrDist (100 units)
   - 100%: finalize (place player, set warpState='none', connectStream)
4. **No separate arriving state**

### The Duplicate Model Problem
Something creates models OUTSIDE the lsgGroup:
- Possible culprits:
  - SSE `firstState` trigger re-calling loaders
  - `connectStream()` at end of warp triggering fresh SSE which triggers loaders
  - The visibility block (`warpState !== 'warping'`) calling something
  - The nav refresh calling loaders
- The `(lsgGroup||scene).add(model)` in loaders SHOULD add to group, but if `lsgGroup` is null/stale at async completion time, it falls back to scene

### The warp_test.html Proof
A standalone test page with the EXACT same logic (group, departure, approach, interpolation) works PERFECTLY. No SSE, no server calls, no visibility checks. This proves:
- The Three.js group approach works
- The interpolation math is correct
- The departure/arrival visual flow is correct

The problem is exclusively something in the game's additional systems interfering.

## KEY FILES

- `ship.html` - Main game ship page (client)
- `server/local_space.py` - Server-side local space worker
- `server/main.py` - Flask app, `/api/lsg_data/<id>` endpoint
- `warp_test.html` - Standalone test (NO SERVER NEEDED, uses CDN Three.js)

## SERVER ENDPOINTS INVOLVED

- `/api/lsg_data/<target_id>` - Returns objects, ships, arrival_dist for destination
- `/api/player/local_space/stream` - SSE stream (1/sec), delivers object positions
- `/api/player/position` - Client reports final position after arrival
- `/api/gate_model/<sys>/<id>` - Fetches gate 3D model JSON
- `/api/station_model/<id>` - Fetches station 3D model JSON
- `/api/asteroid_model/<field_id>` - Fetches asteroid field data

## NEXT STEPS

1. Fix `warp_test.html` (ship orientation, warp-to-gate button) - minor
2. Figure out what in the game creates the duplicate model outside the group
3. Options to fix:
   a. Kill ALL other code paths that call loaders during/after warp
   b. Make loaders refuse to run if `warpState !== 'none'` (except the one in the fetch)
   c. Remove `connectStream()` from warp end, reconnect later
   d. Add a flag like `_warpLoadLock = true` that prevents any loader from running except the warp fetch one

## RULES (from handoff)

- **NEVER revert without explicit approval**
- **NEVER start coding just because the visionary asks a question**
- Discuss first, confirm approach, THEN code
- Ask before coding when user asks a question vs requests a change


## IMPORTANT RULES
- NEVER ask the user if they want to keep going or stop. Just keep working.



## SSG/LSG WARP DESIGN (DEFINITIVE)

### Core Concept
- **SSG travel is virtual**: We update a coordinate (`_playerSS`) to represent where we are in the solar system. Used for projecting labels, calculating distances, and rendering planets. Nothing physically moves in the scene during SSG travel.
- **LSG is a local box of space**: Self-contained 3D area. Anchor body at (0,0,0). Ships, structures, asteroids positioned relative to anchor. NO relationship to SSG coordinates.

### Warp Sequence
1. **WARP PHASE**: Ship 'travels' through SSG by updating `_playerSS`. Labels project, distances calculate, planets render/grow. Ship does NOT physically move.
2. SSG travel continues until `_playerSS` REACHES the target body's SSG coordinate.
3. Once reached: **SSG COORDINATES STOP UPDATING. They are DONE.** Planets stop moving. Labels stop changing. SSG phase is OVER.
4. **APPROACH PHASE begins**: LSG spawns at far edge ahead of ship. LSG slides toward the ship following decel curve. ONLY the LSG group moves during approach — nothing else.
5. LSG STOPS when it reaches target local position (e.g., 80 units from ship).
6. Once stopped: player is IN the LSG, moves locally with flight controls.

### Key Rules
- Ship NEVER moves during warp OR approach — LSG moves to the ship during approach
- SSG and Approach are TWO SEPARATE PHASES — SSG ends BEFORE approach begins
- Once approach starts, SSG coords DO NOT change — they are frozen
- NO mapping between SSG coords and LSG coords — they are separate systems
- LSG spawns far, slides in, stops. That's it.
- After stop, player flies locally within the LSG
- Orbit LSGs have no model at (0,0,0) unless it's a structure (station/gate/field)
- Planet/moon LSGs are just empty space (the planet is rendered by SSG and stops at approach point)
- `_playerSS` is only for SSG calculations (labels, distances, planet rendering) — FROZEN during approach
- `playerPos` is for LSG local movement (after approach ends)

### Speed Label Behavior
- Speed is ONE CONTINUOUS CURVE from departure through warp to approach. No jumps.
- The display adapts: m/s → km/s → AU/s → km/s → m/s as speed ramps up and back down.
- What MOVES changes based on speed, but the speed value itself is continuous:
  - At low speed (start/end): LSG moves (departure/approach)
  - At high speed (middle): SSG coords update (warp travel)
- The transition between LSG movement and SSG movement happens naturally at some speed threshold.
- LSG must be large enough to accommodate the speed at transition points.

### LSG Dimensions
- LSG is a 100,000 km cube (100k km per axis)
- In scene units (1 unit = 100m): 1,000,000 units per axis
- Anchor body at center (0,0,0)
- Approach entry point: 500,000 units from anchor (50,000 km)
- Approach stop point: ~100 units from anchor (~10 km)
- Approach slide distance: ~499,900 units (49,990 km)
- Departure is the reverse: from 100 units, slide out to 500,000 units


### Label Distance Transition
- Label always projects from the anchor body (0,0,0 of LSG)
- During SSG warp: distance computed from `_playerSS` to target SS coords (AU → M km → k km)
- At transition (approach begins): distance switches to LSG-based (player position to 0,0,0)
- This is smooth because: SSG distance at transition ≈ 50,000 km, LSG entry distance = 50,000 km. Same value, no jump.
- During approach: distance shrinks as LSG slides in (50,000 km → 10 km)
- After stop: distance = player's LSG position to (0,0,0) ≈ 10 km
- Format adapts throughout: AU → M km → k km → km → m
