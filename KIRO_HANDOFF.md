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

### Simulation Architecture (NEW)
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

---

## Database Schema (game_data.db)

| Table | Records | Description |
|-------|---------|-------------|
| commodities | 152 | All items (ores, materials, weapons, ammo, etc) |
| recipes | ~300 | Production chain inputs per commodity |
| systems | 48 | Star systems with positions, security, faction |
| system_connections | ~140 | Jump gate connections |
| stations | 58 | Stations with types and production rates |
| station_produces | ~80 | What each station can manufacture |
| asteroid_fields | 34 | Mining fields with density |
| field_yields | ~100 | What ores each field produces |
| system_objects | 620+ | Stars, planets, moons, gates, belts |
| ship_types | 14 | Civilian ships (6 haulers, 5 miners, 3 military) |
| military_ships | 42 | Warships across 6 factions |
| factions | 6 | Major factions |
| corporations | 24 | Sub-factions (4 per faction) |
| fleet_targets | 42 | How many ships each faction maintains |
| station_consumption | 38 | End-use demand per station type |

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
| `server/warfare.py` | (Legacy) Faction battles, ship destruction/rebuilding |
| `server/persistence.py` | Save/load runtime state (game.db) |
| `server/game_data_db.py` | Schema definition for game_data.db |
| `server/data_access.py` | Load functions (commodities, universe, ships, factions from DB) |
| `server/models.py` | Dataclass definitions ONLY (no data) |
| `server/ship_types.py` | ShipType dataclass ONLY |
| `server/military.py` | MilitaryShipClass dataclass ONLY |
| `server/factions.py` | Faction/Corporation dataclass ONLY |
| `server/ship_geometry.py` | 3D ship model geometry data for renderer |
| `server/assign_regions_v2.py` | Assigns 20 balanced regions via priority-queue BFS |

---

## Frontend Pages

| URL | File | Purpose |
|-----|------|---------|
| `/` | `game.html` | Main game (3D star map, system view, market, activity feed) |
| `/debug` | `debug.html` | Dashboard (simulation stats, stations, ships, market, systems) |
| `/docs` | `docs.html` | Documentation hub |
| `/design` | `design.html` | Game design document |
| `/universe` | `universe.html` | Universe design |
| `/economy` | `economy.html` | Economy overview hub |
| `/resources` | `resources.html` | T1 harvesting guide |
| `/materials` | `materials.html` | T2-T3 refining/manufacturing |
| `/products` | `products.html` | T4-T5 components/products |
| `/fitting` | `fitting.html` | Ship fitting design (slots, CPU/PG) |
| `/factions` | `factions_doc.html` | Faction lore and corps |
| `/items` | `items.html` | Items database (table per category, stats) |
| `/ships_db` | `ships_db.html` | Ships database (civilian + military, build costs) |
| `/chain` | `chain.html` | Production chain calculator (tree breakdown) |
| `/ships` | `ships.html` | Ship 3D model viewer |

---

## Economy System

### 152 Commodities (in game_data.db)
- 29 T1 raw ores (common 0.1m3, exotic 2.0m3)
- 20 T2 refined materials
- 18 T3 manufactured materials
- 22 T4 components
- 29 T5 products (weapons S/M/L, shields, engines, drones, mining)
- 13 T5 ammunition (projectile, missiles, energy charges)
- 6 T0 trade goods

### Production Chain
- Mining colonies passively generate ore (8.0*density/tick, cap 50K)
- Refineries: T1 -> T2 (rate 0.3)
- Industrial Hubs: T2 -> T3 (rate 0.15)
- Component Factories: T3 -> T4 (rate 0.08)
- Shipyards: T4 -> T5 (rate 0.04)
- Self-limiting production: throttles based on ticks of supply remaining

### Logistics
- **Contract haulers:** 50 haulers assigned to specific stations, fetch needed inputs
- **Miners:** 20 miners at asteroid fields
- **Sector-wide visibility:** Haulers find nearest source across their cluster
- **Travel:** Inter-system 3-15s, intra-system 30-90s, ship-class align times (2-15s)

### Pricing
- Supply/demand driven with dynamic pressure
- Unfilled demand raises buy price over time
- Oversupply lowers sell price
- Prices recalculate every 10 ticks

### Warfare
- 3 active conflicts (Iron Compact vs Frontier Alliance, Corsairs vs others)
- Skirmishes every 20 ticks (40% chance), 1-3 ships lost per side
- Shipyards rebuild lost ships (consuming T5 products)
- Creates demand sink for the economy

---

## Factions (6)

| Faction | Short | Territory | Philosophy |
|---------|-------|-----------|------------|
| Terran Federation | TFD | Core | Order, navy, regulation |
| Nexus Collective | NXC | Core | Science, innovation |
| Merchants Guild | MGD | Rim | Free trade, profit |
| Frontier Alliance | FRA | Rim | Freedom, self-governance |
| Iron Compact | IRC | Frontier | Military-industrial, expansion |
| The Corsairs | CRS | Frontier | Piracy, smuggling |

Each faction has 4 corporations and 7 military ship classes (fighter through dreadnought). Corsairs have 6 (no dreadnought).

---

## Military Ships (42 total)

7 hull classes per major faction: Fighter, Frigate, Destroyer, Cruiser, Battlecruiser, Battleship, Dreadnought. Each with unique weapons loadout, stats, and build recipe.

---

## API Endpoints

### Game
- `GET /api/positions` - System positions/connections (fetched once)
- `GET /api/ships` - All NPC ship states (polled every 3s)
- `GET /api/market/<system_id>` - Market data for one system (polled every 5s)
- `GET /api/events` - Recent events (polled every 8s)
- `GET /api/system/<id>` - Intra-system detail (system view)
- `GET /api/ship_model/<class_id>` - 3D geometry for ship renderer
- `POST /api/nuke` - Reset simulation state
- `GET/POST /api/speed` - Get/set simulation speed multiplier

### CRUD (game data editing)
- `GET /api/data/commodities` - All items
- `GET/PUT /api/data/commodities/<id>` - Single item
- `GET /api/data/systems` - All systems
- `GET /api/data/military_ships` - All warships
- `GET /api/data/factions` - All factions
- `POST /api/reload_data` - Hot-reload without restart

### Debug
- `GET /api/state` - Full universe state (heavy, avoid polling)
- `GET /api/debug` - Debug summary with production health

---

## Key Design Decisions

- **All data in SQLite.** No hardcoded Python dicts. DB is source of truth.
- **Real-time, always-on.** Economy ticks 24/7.
- **Volume-based cargo.** Common ores 0.1m3 (bulk hauling easy), exotics 2.0m3 (scarce).
- **Contract haulers.** Assigned to stations, not free-roaming arbitrage.
- **Self-limiting production.** Stations throttle based on input availability.
- **Warfare drives demand.** Ships get destroyed, need rebuilding, pulls entire chain.
- **Recipes are logical.** Steel = iron + carbon. Electronics = silicon + copper + gold.
- **Security tiers matter.** Common ores in high-sec, exotics only in null-sec.

---

## Known Issues / Next Steps

### RESOLVED: Simulation Performance
- Migrated from single-threaded tick loop to multi-threaded Supervisor+Workers architecture
- NPC decisions now batched (50/tick round-robin) with O(1) region cache lookups
- Region inventory cache rebuilt every 10 ticks (eliminates per-hauler system scanning)
- 20 regions (9-237 systems each) serve as market visibility boundary
- Intent-queue pattern: workers never mutate shared state directly
- Path to 100K+ ships: increase batch size, move to multiprocessing (same architecture)
- Movement (O(ships) linear scan) stays in supervisor as it's already fast

### IMMEDIATE TODO (from last session)
- [x] **Simulation performance architecture** - DONE. Multi-threaded Supervisor+Workers with intent queues, region cache, batched NPC decisions. See docs/ARCHITECTURE_THREADS.md.
- [ ] **Weapon/module variants and pricing** - Need multiple variants per weapon type at each size. Small ~2,500, Large ~150K, T2 ~10M.
- [ ] **Further market/ships/battle UI polish** based on user feedback after checking current deploy

### Economy Status
- Economy is functional: 645 active / 80 halted production lines at tick 2000
- Baseline input generation prevents total starvation (abstracts local mining)
- Haulers limited to same-region search (50 system cap)
- Ore generation: 50/tick*density at mining colonies, 20/tick at refineries with belts
- Baseline T1/T2 inputs auto-generated at 0.5x production rate for all producing stations
- Production still halts at higher tiers (T3/T4) due to rare ore logistics gap
- Need to fix: basic items (Shield Gen Mk.I) currently require null-sec exotics (Gold Ore) in recipe chain
- Solution: redesign T3 recipes so Mk.I items use only high/med-sec inputs, Mk.II/III use rarer stuff
- Mining colony generation (8/tick) may need tuning vs consumption rates
- Warfare not yet consuming ammo properly (ships destroyed but no ammo deducted)

### Player Integration (Next Phase)
- Player can buy/sell at stations
- Player travel and ship control
- Ship fitting UI
- Player mining
- Fuel consumption

### Future
- Factions/corporations as joinable entities (Mount&Blade style)
- Player-created factions
- Territory control
- Contract system (X4-style station orders)
- Tech levels on items (Mk.I/II/III progression)

---

## Build/Deploy

- Push to master triggers GitHub Actions deploy to fly.io
- `data/game_data.db` deploys with code (in git)
- `data/game.db` persists on fly.io volume (runtime state)
- No manual fly.io steps needed for normal deploys
- Nuke via debug page resets runtime state only (game_data.db untouched)
