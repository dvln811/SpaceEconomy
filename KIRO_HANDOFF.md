# Kiro Handoff - SpaceEconomy

## What This Is

A browser-based space economy simulation game. Currently single-player with plans for a free MMORPG. The core appeal is a living, agent-driven commodity market spread across a network of star systems. You are one actor (a hauler/trader/miner) in a functioning economy, not the god of it. The economy runs 24/7 on a fly.io server.

**Owner:** Devlyn Napoli
**Repo:** https://github.com/dvln811/SpaceEconomy
**Live:** https://spaceeconomy.fly.dev
**Debug:** https://spaceeconomy.fly.dev/debug

---

## WORKFLOW RULES

1. **Commit and push automatically after completing each task/change.** Use `GIT_TERMINAL_PROMPT=0 git push` to avoid interactive prompt hangs.
2. Read this file at the start of every session.
3. Check `git log --oneline -5` and `git status` before starting.
4. Ask the user what they want to work on.
5. **NO M-DASHES in replies.** Use commas, periods, or rewrite the sentence instead.
6. **No local server start needed.** Work against the remote fly.io deployment.
7. GitHub Actions auto-deploys on push to master.
8. Use the **Nuke** button on /debug to reset simulation state after breaking schema changes.

---

## Current State (Phase 1 COMPLETE + Intra-System Navigation)

### Architecture
- **Backend:** Python (Flask), always-on server on fly.io (shared-cpu-2x, 1GB)
- **Frontend:** Vanilla JS + Three.js (3D star map) + HTML/CSS panels + Canvas (intra-system map)
- **Economy Engine:** Real-time agent-based tick simulation (1 tick/sec, background thread)
- **Database:** SQLite on persistent fly.io volume (`/app/data/game.db`), saves every 10 ticks
- **Deployment:** fly.io, auto-deploy via GitHub Actions on push to master
- **Local dev:** `restart_server.ps1` runs Flask with debug=True on port 8000

### What Exists

**Server (`server/`)**
- `server/main.py` - Flask app, tick loop thread, API endpoints (including `/api/system/<id>`)
- `server/simulation.py` - Economy engine: production/consumption, NPC AI, pathfinding, mining, intra-system travel
- `server/models.py` - Dataclasses: Commodity (20 types), Station, System, SystemObject, NPCShip, AsteroidField
- `server/universe.py` - 24-system universe seed data (3 clusters, connections, asteroid fields, intra-system objects)
- `server/persistence.py` - SQLite save/load state, nuke/reset

**Frontend**
- `game.html` - Main game UI with live 3D star map + inline system view window
  - 24 star systems with CSS2D labels, billboarded ship sprites
  - Ships visible on star map during inter-system travel
  - Inline draggable/resizable system view window (ISM) opened via "View System Map" button
  - ISM shows: radar-style schematic, orbital lines, planets with moons, gates, stations, belts
  - ISM ships: deterministic linear interpolation, visible only when traveling or mining (not docked)
  - Left panel: tabbed (Systems list / Ships list)
  - Right panel: tabbed (System Info / Market)
  - Bottom panel: ship schematic, activity feed, routes

- `debug.html` - Debug monitor at /debug
  - Simulation state, recent events, NPC ships table, price monitor
  - Inline system map window (dropdown to select system, opens floating canvas)
  - Nuke/Reset button

- `system_view.html` - Standalone system view (accessible via /system_view?id=<id>&debug=1)
- `design.html` - Game design document
- `universe.html` - Universe design document
- `economy.html` - Economy design document (production chain tiers, commodities, recipes)
- `docs.html` - Documentation hub linking to all design docs

**Infrastructure**
- `Dockerfile` - Python 3.12-slim, gunicorn
- `fly.toml` - spaceeconomy app, iad, shared-cpu-2x/1GB, always-on, se_data volume
- `.github/workflows/deploy.yml` - Auto-deploy on push to master
- `restart_server.ps1` - Local dev server launcher (port 8000)

### Two-Layer Navigation Model
- **Inter-system:** Ships travel between star systems (visible on 3D star map, ~50s transit at speed 1.0)
- **Intra-system:** Ships travel between objects within a system (visible in ISM, ~35-40s transit at 0.2 AU/tick)
- **Jump gates:** Located at outer ring of each system, one per connection. Ship must intra-travel to gate, then inter-system travel begins.
- **Flow:** idle at station -> load -> intra-travel to gate -> inter-system travel -> arrive at gate -> intra-travel to destination station -> unload

### Ship Movement (Deterministic)
- **All ships:** speed=1.0 (inter-system LY/tick), intra_speed=0.2 (intra-system AU/tick)
- **Server:** progress += speed_constant / distance per tick
- **Client:** Same math per frame (speed / dist / 60), pure linear interpolation along known path
- **API sends:** intra_from (polar), intra_to (polar), intra_dist, intra_speed for traveling ships
- **No velocity estimation, no lerp, no zig-zag**

### Simulation Details
- **40 NPC ships:** 30 traders (5 hull classes), 10 miners (3 hull classes)
- **Ship states:** idle, loading (3t), unloading (2t), traveling, intra_traveling, mining (5t)
- **BFS pathfinding:** Ships route through multi-hop paths along system connections
- **Trade AI:** NPCs scan 2-hop radius for profitable buy/sell opportunities
- **Mining:** NPCs find asteroid fields, mine ore over time, sell when cargo 80% full
- **Price engine:** `price = base * (demand/supply)^elasticity` per commodity per station
- **Production/consumption:** Each station produces and consumes goods every tick
- **20 commodities:** raw (ore, ice, helium3, etc), basic (food), essential (meds, fuel), advanced (electronics, alloys), illegal (narcotics)

### System Objects (per system)
- Star (center), 2-4 planets (with 0-2 moons each), stations (mid ring 3-7 AU), asteroid belts (4-9 AU), jump gates (outer ring 10-13 AU)
- All positioned with polar coordinates (distance from star in AU + angle in radians)

### API Endpoints
- `GET /` - Game UI
- `GET /design` - Design document
- `GET /universe` - Universe design document
- `GET /economy` - Economy design document
- `GET /docs` - Documentation hub
- `GET /system_view` - Standalone system view
- `GET /debug` - Debug monitor
- `GET /health` - Health check (tick count)
- `GET /api/state` - Full universe state (systems, stations, prices, inventories, objects)
- `GET /api/ships` - All NPC ship positions, states, intra-system path data
- `GET /api/system/<id>` - Detailed system view (objects + ships with intra coords)
- `GET /api/debug` - Debug summary (stats, events, prices, ship details)
- `POST /api/nuke` - Reset simulation to initial state

---

## Known Issues

- **Trade clustering:** NPC traders still gravitate heavily to Cygnus/Kepler corridor due to large price differentials. Production chain implementation should fix this by making trade directional.
- **Economy is flat:** Currently 20 commodities with no production chain. The economy.html design doc outlines a 5-tier chain (raw -> refined -> industrial -> components -> complex) that needs implementation.

---

## Build Phases

### Phase 1: Living Economy - COMPLETE
- System/station data model
- Commodity inventories with production/consumption per tick
- Price engine (supply/demand/elasticity)
- NPC hauler agents with trade AI
- NPC miners working asteroid fields
- BFS pathfinding for multi-hop routes
- SQLite persistence
- Frontend connected to live API
- Intra-system navigation (gates, objects, two-layer travel)
- Deterministic client-side ship movement

### Phase 2: Player Can Trade (NEXT)
- Player can buy/sell commodities at current station
- Player can set destination, travel takes real time
- Fuel consumption during travel
- Balance and cargo tracking
- Ship upgrades (cargo capacity, fuel efficiency, speed)
- Player mining (use mining laser hardpoint on asteroid fields)

### Phase 3: Production Chain Economy
- Implement 5-tier commodity chain (raw -> refined -> industrial -> components -> complex)
- Stations transform inputs to outputs (recipes)
- Mining ships as primary source of T1 materials
- Directional trade flow (ore flows toward factories, products flow outward)
- Tech levels (quality multiplier on T3-T5)

### Phase 4: Information and Risk
- Price data staleness (only see prices from last visit)
- Security zones with piracy risk (random cargo loss in low-sec)
- Basic events (supply disruptions, price spikes, faction skirmishes)
- Contracts and reputation

### Phase 5: Factions and Depth
- Faction territories, diplomacy, warfare
- Shifting borders that reshape trade routes
- Smuggling mechanics in embargoed systems
- Fleet ownership and infrastructure (late-game)
- Multiplayer (shared persistent world)

---

## Universe Structure

**3 Clusters, 24 Systems:**
- **Core (High-Sec, 8 systems):** Cygnus, Kepler, Tau Ceti, Procyon, Sirius, Deneb, Polaris, Fomalhaut
- **Rim (Low-Sec, 11 systems):** Vega, Arcturus, Barnard's, Altair, Antares, Capella, Betelgeuse, Castor, Achernar, Aldebaran, Regulus
- **Frontier (Null-Sec, 5 systems):** Wolf 359, Rigel, Pollux, Canopus, Spica

Connected by jump nexus chokepoints (Procyon, Castor, Spica).

---

## Key Design Decisions

- **Real-time, always-on.** Economy ticks 24/7, world persists whether player is online or not.
- **Mining as safety net.** You can always mine. Slow money but guaranteed. No going broke.
- **Progression as access, not power.** You gain access to more of the system, not raw strength.
- **NOT a combat game.** Conflict is an economic hazard, not a gameplay mechanic.
- **Two-layer navigation:** Inter-system (star map) + intra-system (system map). Space is big.
- **Universe will be regenerated** before "real" launch so owner has no pre-conceived knowledge.

---

## Tech Notes

- Git credentials stored via `credential.helper=store` in `~/.git-credentials`
- fly.io deploy token stored as GitHub Actions secret `FLY_API_TOKEN`
- SQLite DB on fly.io volume `se_data` mounted at `/app/data`
- `DATA_DIR` env var controls DB location (defaults to local `data/` dir)
- Schema changes require a nuke (saved state won't have new fields)
- Ship sprites use CanvasTexture on THREE.Sprite for billboarding
- System view uses Canvas 2D with polar-to-cartesian coordinate mapping

---

## Contact

- Owner: Devlyn Napoli (devlynnapoli@protonmail.com)
