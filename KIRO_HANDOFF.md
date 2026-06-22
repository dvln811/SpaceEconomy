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

## Architecture

### Data Architecture (IMPORTANT)
- **ALL game data is in SQLite:** `data/game_data.db` (tracked in git, deploys with code)
- **Python files contain ONLY dataclass definitions** (no hardcoded data)
- **Runtime state** (inventories, ship positions, prices): `data/game.db` (on fly.io volume, NOT in git)
- **CRUD API** at `/api/data/*` for editing game data
- **To update game data:** Edit `game_data.db` directly or via CRUD API, then push. No Python changes needed for data.

### Tech Stack
- **Backend:** Python (Flask), always-on server on fly.io (shared-cpu-2x, 1GB)
- **Frontend:** Vanilla JS + Three.js (3D star map + 3D system map) + HTML/CSS panels
- **Simulation:** Multi-threaded Supervisor + 6 Worker architecture (see docs/ARCHITECTURE_THREADS.md)
- **Databases:**
  - `data/game_data.db` - Static game data (items, ships, systems, factions). Source of truth. In git.
  - `data/game.db` - Runtime simulation state. On fly.io volume. Nuked on reset.
- **Deployment:** fly.io, auto-deploy via GitHub Actions on push to master
- **Local dev:** `restart_server.ps1` runs Flask with debug=True on port 8000

### Simulation Architecture
- **Supervisor thread** owns tick clock (1/sec), distributes state snapshots to workers, merges intents
- **Economy worker** - production, consumption, ore gen, price updates (every tick)
- **NPC Decision worker** - hauler/miner AI, batched 50 ships/tick, uses region inventory cache
- **Faction Strategy worker** - goals, expansion, diplomacy (every 200 ticks)
- **Battle Sim worker** - fleet combat, ship destruction/building (every 20 ticks)
- **Corsair/Spawn worker** - pirate AI, NPC spawning (every 50 ticks)
- **Dashboard worker** - cached JSON for API endpoints (every 5 ticks)
- Workers produce typed **intents** (dataclasses), Supervisor applies them atomically between ticks
- **Region inventory cache** rebuilt every 10 ticks for O(1) NPC trade lookups
- **20 regions** (~125 systems each) define NPC market search boundaries
- Performance: ~10-18ms per tick, 15-55 ticks/sec at 120x speed

---

## Database Schema (game_data.db)

| Table | Records | Description |
|-------|---------|-------------|
| commodities | 1540 | All items with 3-level hierarchy (category/subcategory/group_name) |
| recipes | 3391 | Production chain inputs per commodity |
| ships | 56 | Unified ship table (14 civilian hulls + 42 faction military) |
| systems | 2500 | Star systems with positions, security, faction, region |
| system_connections | ~7000 | Jump gate connections |
| stations | ~700 | Stations with types and production rates |
| station_produces | ~700 | What each station can manufacture |
| asteroid_fields | ~800 | Mining fields with density |
| field_yields | ~2400 | What ores each field produces |
| system_objects | ~15000 | Stars, planets, moons, gates, belts |
| factions | 6 | Major factions |
| corporations | 24 | Sub-factions (4 per faction) |
| fleet_targets | 42 | How many ships each faction maintains |
| station_consumption | 38 | End-use demand per station type |

---

## Items System (1540 items)

### Hierarchy: category > subcategory > group_name
- **Weapons** (192): Turrets (Autocannon, Artillery, Blaster, Railgun, Gauss, Flak), Energy Weapons (Pulse Laser, Beam Laser, Plasma Cannon), Launchers (Rocket, Missile, Torpedo)
- **Ammunition** (396): Projectile Ammo, Hybrid Charges, Energy Crystals, Missiles, Magnetic Ammo, Energy Cells
- **Ship Equipment** (748): Shields, Armor, Hull, Propulsion, Navigation, Electronic Warfare, Tackle, Energy Warfare, Remote Repair, Engineering, Electronics, Drones, Mining
- **Drones** (96): Combat (EM/Thermal/Kinetic/Explosive), Utility, Logistics, EWAR
- **Materials** (96): Raw Materials (Ore/Ice/Crystals/Gas/Organic/Exotic), Refined, Manufactured, Components
- **Trade Goods** (6)

### Sizes: Small (S), Medium (M), Large (L), Capital (C)
### Quality Tiers: Standard, Named (Compact), T2 (Advanced), Faction (Navy)

### Weapon Stats Model
- Weapons modify: optimal_range, rof_bonus, tracking
- Damage comes from ammo/crystal loaded into the weapon
- Slot type: weapon_mount

### Module Slot System
- **Weapon Mounts** - weapons, mining lasers, salvagers, tractor beams
- **Utility Bays** - shields, EWAR, propulsion, cap boosters, scanners
- **Core Slots** - armor, engineering, damage mods, cargo expanders

---

## Ships (56 total, unified `ships` table)

### Hull Classes
- **Frigate** (small combat), **Destroyer** (small combat)
- **Cruiser**, **Battlecruiser**, **Battleship** (medium/large combat)
- **Carrier**, **Dreadnought** (capital)
- **Industrial** (hauling), **Mining Barge** (mining)

### Design: Hull determines potential, fitting determines role
- All ships have minimum 2 Weapon Mounts
- No military vs civilian split on hulls. Faction ships are just variants.
- See docs/SHIP_HULL_CLASSES.md and docs/SHIP_BUILD_TIMES.md

### Build Times
- Fighter: 8m, Frigate: 22m, Destroyer: 3h, Cruiser: 12h
- Battlecruiser: 1.5d, Battleship: 8d, Carrier: 17d, Dreadnought: 28d
- Industrial T1: 5-10m, T3: 1-2d, Clydesdale: 6d

---

## Server Files

| File | Purpose |
|------|---------|
| `server/main.py` | Flask app, API endpoints, CRUD, supervisor startup |
| `server/supervisor.py` | Tick clock, snapshot distribution, intent merge, worker lifecycle |
| `server/intents.py` | Typed intent/event dataclasses for inter-thread communication |
| `server/simulation.py` | Simulation class (universe init, ship spawn, bootstrap) |
| `server/workers/economy.py` | Production, consumption, ore generation, price updates |
| `server/workers/npc_decisions.py` | Hauler/miner AI with region cache lookups (batched) |
| `server/workers/faction_strategy.py` | War declarations, expansion, diplomacy |
| `server/workers/battle_sim.py` | Fleet combat resolution, ship building |
| `server/workers/corsair_spawn.py` | Pirate AI, universe assessment, NPC spawning |
| `server/workers/dashboard.py` | Cached JSON state preparation for API endpoints |
| `server/persistence.py` | Save/load runtime state (game.db) |
| `server/game_data_db.py` | Schema definition for game_data.db |
| `server/data_access.py` | Load functions (commodities, universe, ships, factions from DB) |
| `server/models.py` | Dataclass definitions ONLY (no data) |
| `server/generate_items.py` | Item database generator (1540 items with recipes) |
| `server/categorize_items.py` | Assigns 3-level hierarchy to all items |
| `server/cleanup_pass.py` | Stats formatting, ammo descriptions, weapon model fixes |
| `server/merge_ships.py` | Merges ship_types + military_ships into unified ships table |
| `server/fix_military_ships.py` | Fixes military ship weapons/modules/recipes |
| `server/set_build_times.py` | Sets build times per docs/SHIP_BUILD_TIMES.md |
| `server/assign_regions_v2.py` | Assigns 20 balanced regions via priority-queue BFS |

---

## Frontend Pages

| URL | File | Purpose |
|-----|------|---------|
| `/` | `game.html` | Main game (3D star map, system view, market, activity feed) |
| `/debug` | `debug.html` | Dashboard (overview, stations, ships, combat, market, systems) |
| `/items` | `items.html` | Items DB (collapsible tree, size/quality filters, sortable columns) |
| `/ships_db` | `ships_db.html` | Ships DB (civilian + military, Weapons/Utility/Core columns) |
| `/chain` | `chain.html` | Production chain calculator (tree breakdown) |
| `/ships` | `ships.html` | Ship 3D model viewer |
| `/docs` | `docs.html` | Documentation hub |
| `/design` | `design.html` | Game design document |
| `/universe` | `universe.html` | Universe design |
| `/economy` | `economy.html` | Economy overview hub |
| `/resources` | `resources.html` | T1 harvesting guide |
| `/materials` | `materials.html` | T2-T3 refining/manufacturing |
| `/products` | `products.html` | T4-T5 components/products |
| `/fitting` | `fitting.html` | Ship fitting design (slots, CPU/PG) |
| `/factions` | `factions_doc.html` | Faction lore and corps |

---

## API Endpoints

### Game
- `GET /api/positions` - System positions/connections (fetched once)
- `GET /api/ships` - All NPC ship states (polled every 3s)
- `GET /api/market/<system_id>` - Market data for one system
- `GET /api/events` - Recent events
- `GET /api/system/<id>` - Intra-system detail
- `GET /api/ship_model/<class_id>` - 3D geometry for ship renderer
- `POST /api/nuke` - Reset simulation state
- `GET/POST /api/speed` - Get/set simulation speed multiplier

### CRUD (game data editing)
- `GET /api/data/commodities` - All items (with category, subcategory, group_name, stats, build_time)
- `GET/PUT /api/data/commodities/<id>` - Single item
- `GET /api/data/ships` - All ships (unified table)
- `GET /api/data/ship_types` - Non-faction ships only
- `GET /api/data/military_ships` - Faction ships only
- `GET /api/data/systems` - All systems
- `GET /api/data/factions` - All factions
- `POST /api/reload_data` - Hot-reload without restart

### Debug
- `GET /api/state` - Full universe state (heavy, avoid polling)
- `GET /api/debug` - Debug summary with production health + performance metrics

---

## Key Design Decisions

- **All data in SQLite.** No hardcoded Python dicts. DB is source of truth.
- **Real-time, always-on.** Economy ticks 24/7 at 1 tick/sec.
- **Multi-threaded.** Supervisor + 6 workers with intent queues. Scales to 100K+ ships.
- **Hull class system.** No military vs civilian. Hull determines potential, fitting determines role.
- **Eve-inspired items.** 4 sizes, 4 quality tiers, weapons modify delivery not damage.
- **Volume-based cargo.** Common ores 0.1m3 (bulk hauling easy), exotics 2.0m3 (scarce).
- **Contract haulers.** Assigned to stations, not free-roaming arbitrage.
- **Self-limiting production.** Stations throttle based on input availability.
- **Warfare drives demand.** Ships get destroyed, need rebuilding, pulls entire chain.
- **Recipes are logical.** Ship recipe = hull materials + fitted modules.
- **Security tiers matter.** Common ores in high-sec, exotics only in null-sec.
- **Regions bound market visibility.** Ships only see prices within their region.

---

## Documentation Files

| File | Content |
|------|---------|
| `docs/ARCHITECTURE_THREADS.md` | Multi-threaded simulation design |
| `docs/SHIP_HULL_CLASSES.md` | Hull class system, slot types, design principles |
| `docs/SHIP_BUILD_TIMES.md` | Build times by hull class, design intent |

---

## Current Status / Next Steps

### COMPLETED THIS SESSION
- [x] Multi-threaded simulation architecture (Supervisor + 6 workers)
- [x] Item expansion: 153 to 1540 items with proper hierarchy
- [x] Ship table merge: unified `ships` table with hull classes
- [x] Hardpoint/slot system (Weapon Mount / Utility Bay / Core Slot)
- [x] Weapon stats model (weapons modify range/RoF/tracking, ammo does damage)
- [x] All data pages cleaned up (no raw IDs, collapsible trees, sortable, filterable)
- [x] Performance metrics in debug dashboard
- [x] Build times documented and set

### NEXT (to be discussed)
- [ ] **Combat system design** - How ships fight, damage model, weapons + ammo interaction
- [ ] **Faction strategy AI** - What drives faction decisions, expansion, war goals, territory control
- [ ] **Economy seeding/rebalance** - Stations need to produce items from the expanded 1540-item catalog
- [ ] **Player integration** - Buy/sell, ship control, travel, fitting
- [ ] **Corsair/pirate AI** - Dynamic spawning, trade route interdiction

---

## Build/Deploy

- Push to master triggers GitHub Actions deploy to fly.io
- `data/game_data.db` deploys with code (in git)
- `data/game.db` persists on fly.io volume (runtime state)
- No manual fly.io steps needed for normal deploys
- Nuke via debug page resets runtime state only (game_data.db untouched)
- Deferred init: server responds to health checks immediately, sim loads in background (120s grace)
