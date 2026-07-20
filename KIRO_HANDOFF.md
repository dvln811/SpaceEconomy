# Space Economy - Session Handoff (July 20, 2026)

## BRANCH & STATE

- **Working branch**: `feature/polish-and-fixes` (branched from master)
- **Master**: Merged and deployed to Fly.io (app: `spaceeconomy`)
- **Live status**: Running. Regenerate endpoint hit after deploy.

## WHAT WORKS

### Core Flight
- **Intra-system warp**: Full flow - departure (LSG objects recede), SSG travel (interpolated _playerSS), approach (LSG slides toward player from 10,000km), arrival (remainingKm < 100)
- **Impulse flight**: Double-click to fly, ship aligns and accelerates. Max speed from server (Pinto Runner: 1000 m/s in DB, sent as 10 units/s)
- **Camera**: Orbit camera follows ship, smooth lerp
- **Ship model**: Pinto Runner inline geometry, proper heading quaternion

### Warp Specifics
- **Snap bug FIXED**: SSG `distAU > 0.0000000001` threshold (was 0.00001 = 1500km causing direction collapse)
- **_playerSS**: Client-authoritative during flight/warp, interpolated linearly from _warpFromSS to _warpToSS
- **SSE isolation**: After first state, SSE only updates NPC ships. Never replaces localState.objects or _playerSS
- **Warp audio**: Uses `Flying_a_spaceship_5.WAV`, pitch 0.6-1.2, volume 0.1-0.5 based on speed fraction

### Rendering
- **HDR Skybox**: 4 PNG textures (pre-decoded from HDR, stored in `static/skyboxes/cached/`). Loaded via THREE.TextureLoader. Custom blend shader with stars + noise * alpha mask
- **Per-system skybox**: System ID hashed to pick one of 9 variants (11,13,14,16,17,18,20,Cube1,Cube2). Presets in `skybox_presets.json`
- **Planet textures**: Web Worker (`planet_texture_worker.js`) generates 2048x1024 noise-based textures with color ramps per planet_type. Returns color + normal map + roughness map
- **Normal maps**: Sobel-filtered from heightmap, applied async via 500ms interval checker
- **Roughness maps**: Water areas (below sea level) get roughness 0.15, land 0.85. Specular oceans.
- **Planet material**: MeshStandardMaterial with map, normalMap, roughnessMap
- **Sun**: Positioned by _playerSS direction to (0,0,0), includes Y axis. DirectionalLight + PointLight + lens flares
- **Clouds**: DISABLED (shader works in viewer but not in game due to unknown rendering issue - see below)

### Docking/Undocking
- **Dock button**: Shows within 30 units of a visible station model (uses `getWorldPosition`)
- **Jump button**: Shows within 20 units of a visible gate model (uses `getWorldPosition`)
- **Dock action**: POST /api/player/dock, SSE delivers state='docked', triggers setDockedScene
- **Undock**: POST /api/player/undock, directly calls setFlightScene(), 2s grace period before showing buttons
- **Hangar**: Octagonal room (walls BackSide, floor, ceiling, ring, wall lights), skybox hidden when docked

### System Jumps
- **Gate jump**: POST /api/player/jump, sets _systemJustChanged, clears all models, waits 1.5s, reloads everything
- **Fade**: Overlay fades to black, fades back in within 3s max (doesn't wait for texture generation)
- **Skybox swap**: loadSkyboxForSystem() called on system change, loads new variant's noise+alpha PNGs

### Infrastructure
- **Server**: Flask, gunicorn on Fly.io, SQLite DB on volume mount at /app/data
- **Regenerate endpoint**: POST /api/admin/regenerate - rebuilds system_objects, reinits local_space. Button on dashboard.
- **Save skybox presets**: POST /api/admin/save_skybox_preset - writes to skybox_presets.json
- **Static file caching**: `Cache-Control: public, max-age=604800, immutable` on .hdr/.wav/.png
- **GitHub Actions**: Auto-deploys to Fly on push to master

## KNOWN ISSUES / INCOMPLETE

### Clouds (DISABLED)
- Shader works perfectly in planet_viewer tool (`/planet_viewer`)
- In the game: renders as inverse fresnel (visible at edges only, not over planet face)
- Red MeshBasicMaterial test sphere DOES render correctly at same position/scale
- Root cause likely: ShaderMaterial transparent rendering interacting with MeshStandardMaterial planet in unexpected way
- Cloud settings finalized: opacity=1, scale=8, threshLow=0.21, threshHigh=0.56, speed=0, height=1.03
- Code is all there, just `addCloudLayer` is never called (disabled in normalMap checker)

### Impulse Sound
- Task created but not implemented yet. Should use same WAV at lower pitch/volume for impulse flight.

### Asteroid Fields
- Task: add common asteroid field to Rigel. Not done yet.

### Warp Deceleration
- No visible slowdown on arrival currently. Ship just stops at remainingKm < 100.

### Pinto Runner Speed
- DB has 1000 m/s (for testing convenience). Original was 111 m/s. Reset before going live with real gameplay.

## KEY FILES

| File | Purpose |
|------|---------|
| `ship.html` | Main game client (3D flight, warp, docking, everything) |
| `server/main.py` | Flask server, all API routes |
| `server/local_space.py` | SSE state, ship simulation, SS coordinate computation |
| `server/generate_system_objects.py` | System object generator (planets, moons, gates, stations, belts) |
| `static/planet_textures.js` | Planet texture module (worker manager, cache, async delivery) |
| `static/planet_texture_worker.js` | Web Worker: noise heightmap -> color + normal + roughness pixels |
| `skybox_presets.json` | Per-variant skybox blend settings |
| `tools/skybox_viewer.html` | Skybox editor with all variants |
| `tools/planet_viewer.html` | Planet + cloud shader editor |
| `tools/prebuild_skybox.py` | Converts HDR -> PNG cached files |
| `data/game_data.db` | SQLite database (16MB, on Fly volume) |
| `warp_game_work.html` | Standalone warp test (reference implementation) |

## COORDINATE SYSTEMS

### World Space (playerPos, camera, meshes)
- Origin: wherever the player starts (or 0,0,0 after undock)
- Units: 1 unit = 100 meters (so playerMaxSpeed 10 = 1000 m/s displayed)
- Player moves through this space with impulse drive

### SS Space (_playerSS, obj.ss_x/ss_y/ss_z)
- AU-based solar system coordinates
- Star at (0,0,0)
- Used for: warp destination calc, SSG planet positioning, sun direction, nav distances
- _playerSS interpolated during warp, set from anchor on first connect

### LSG Space (lsgGroup, obj.x/obj.y/obj.z)
- Local positions from server (relative to anchor object)
- lsgGroup positioned in world space during warp approach
- Station/gate models placed inside lsgGroup at obj.x positions
- After warp: lsgGroup stays where approach left it (~100 units from player)

### SSG Space (ssgPlanetGroup, ssgPlanetMeshes)
- Separate group for planet/moon meshes
- Positioned based on direction from _playerSS to obj.ss_x/ss_y/ss_z
- renderDist = distKm / WARP_SCALE_FACTOR(4)
- scale = radiusKm / WARP_SCALE_FACTOR(4)

## IMPORTANT RULES (from user)
- NEVER revert without explicit approval
- Discuss first, confirm approach, THEN code
- Write diagnostic logs to `/api/debug_log` endpoint (writes to `debug_output.txt`), NOT console
- The server should NOT dictate client-side SSG rendering
- `playerPos` should not be "snapped" - no visible discontinuity ever
- No m-dashes in replies
- Server restart: `Start-Process python -ArgumentList "-m","server.main" -WorkingDirectory "C:\TrinityRepos\request_simulator\SpaceEconomy"`

## TASK LIST (from last session)

Remaining from integration tasks:
- [ ] Add impulse engine low rumble sound
- [ ] Add common asteroid field to Rigel system  
- [ ] Fix deceleration/slowdown on warp arrival
- [ ] Check gate jumping works fully (jump works but needs more testing)

## RECENT FIXES
- Agent lifecycle ID collision: `_spawn_replacement` now retries with larger random range if ID exists
- Dock/Jump buttons: Use actual model world positions (`getWorldPosition`) for distance checks
- starField null guard in setFlightScene
- Removed console.log spam from updateFromState
- Jump fade timeout: 3s max instead of waiting for all texture generation
