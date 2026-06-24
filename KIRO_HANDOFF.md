# Kiro Handoff - SpaceEconomy

## What This Is

A browser-based space economy simulation (GCS: SpaceEconomy). Single-player with a living, agent-driven commodity market across 2,500 star systems. 6 NPC factions mine, trade, build, expand, and will eventually wage war autonomously. The player participates as one actor in this economy. Built on assets from the developer's prior game (GCS: Salvage Rat, previously on Steam).

**Owner:** Devlyn Napoli
**Repo:** https://github.com/dvln811/SpaceEconomy
**Live:** https://spaceeconomy.fly.dev
**Debug:** https://spaceeconomy.fly.dev/debug
**Local Dev:** `python dev.py [speed] [duration]` (e.g., `python dev.py 120 60`)

---

## WORKFLOW RULES

1. **Commit and push after completing each task/change.**
2. Read this file at the start of every session.
3. **NO M-DASHES in replies.**
4. **No raw IDs displayed anywhere** - always title case or lookup names.
5. Item names must NOT include size labels (size is a separate column/badge).
6. **Ask before coding** when user asks a question vs requests a change.
7. Use `python dev.py` for local testing instead of deploying for every change.
8. Nuke button on /debug resets runtime state after breaking changes.

---

## Architecture

### Tech Stack
- **Backend:** Python (Flask + gunicorn), fly.io (shared-cpu-2x, 1GB RAM)
- **Frontend:** Vanilla JS + Three.js (3D maps), single-page app with left nav panel
- **Simulation:** Multi-threaded Supervisor + 6 Workers, ~25ms/tick with 1476 ships
- **Databases:** SQLite (game_data.db in git, game.db runtime on volume)

### Navigation Structure
- Left nav panel (persistent): Map | Ship (stub) | Inventory (stub) | Market | Encyclopedia | Settings (stub) | Dashboard (red)
- Clicking nav loads content in iframe overlay on the map area
- Encyclopedia loads /docs hub, which has tab navigation to all doc pages
- Market opens filtered to player's region (The Forge), debug version has region dropdown

### Simulation Architecture
- **Supervisor** - tick clock (1/sec), snapshot distribution, intent merge, station index
- **Economy Worker** - production, consumption (2/tick), ore generation, price updates (every 60 ticks)
- **NPC Decision Worker** - hauler/miner/freelance AI, batched 200/tick
- **Faction Strategy Worker** - decisions every 100 ticks, corp task assignment, project phases
- **Battle Sim Worker** - fleet combat (every 20 ticks)
- **Dashboard Worker** - pre-computes all dashboard aggregates every 10 ticks (25KB response vs former 3MB)
- Performance: ~25ms/tick, ~40 ticks/sec at 120x

### Key Performance Design
- `/api/debug` returns pre-computed 25KB summary (NOT raw data)
- `/api/market/orders` builds order book on request, filtered by region
- Delta mode on `/api/ships` for game map (only changed ships sent)
- Station index in supervisor for O(1) intent application

---

## Database Schema (game_data.db)

| Table | Purpose |
|-------|---------|
| commodities (1540) | Items with category/subcategory/group_name, stats JSON, recipes |
| recipes (3399) | Production chain inputs |
| ships (79) | 14 civilian + 42 original military + 37 new variants |
| systems (2500) | Positions, sec_level (0.0-1.0), faction_id, region, population |
| stations (435) | Types: mining_colony, refinery, component_works, factory, trade_hub, military_base, shipyard |
| station_produces (1540) | What each station manufactures |
| station_consumption (56) | Passive demand per station type |
| build_projects (10+) | Faction construction projects (stations, dreadnoughts, fleets) |
| corporations (45) | Sub-factions with emblems, heads, specialties, history |
| faction_agents (72) | Named agents with portraits, traits, bios |
| faction_state (6) | Personality values, treasury, priorities |
| faction_decisions | Rolling decision log with reasoning |

---

## Economy

### Pricing
- Base prices calibrated: S Standard weapon ~3,500, C Faction ~16M
- Ships: Pinto Runner 8K, Frigates 3.5M, Destroyers 15M, Dreads 65B
- Ammo: S=10, M=30, L=90, C=300
- Buy orders capped at 2x base price, sell never below base

### Production Chain
Raw ores (T1) -> Refined materials (T2) -> Manufactured (T3) -> Components (T4) -> Final products (T5)
- Mining colonies generate ore passively
- Baseline input trickle keeps stations from permanently stalling
- 197 producing stations, ~1490 active at any time

### Market Orders
- Production demand: stations buy inputs when below 100-tick buffer
- Station consumption: 56 entries, 2/tick passive drain
- Population demand: civilian buy orders at all stations in populated systems
- Military demand: military bases buy weapons/ammo/drones at 1.3x
- Build project demand: cascaded material needs for faction construction
- Sell orders: any inventory with price > base_price

### NPC Fleet (1476 ships)
- **Haulers (507)**: assigned to stations, haul needed inputs from region
- **Freelancers (133)**: profit-seeking, buy cheap sell expensive
- **Regular miners (214)**: mine at station systems, sell locally
- **Deep miners (49-100)**: mine exotic ores at remote systems, haul to nearby stations
- **Military patrol (573)**: idle (combat AI not yet implemented)

### Mining Cycle
- Regular: mine(50t) -> unload(25t) -> mine again (same system)
- Deep: mine(50t) -> travel to station(15-30t) -> unload(25t) -> travel back(15-30t) -> mine
- Yield: ~25 * field_density per 50-tick cycle
- Ships fill over 3-4 cycles before selling

---

## Factions & Territory

### 6 Factions
| Faction | Systems | Avg Sec | Archetype |
|---------|---------|---------|-----------|
| Merchants Guild | 170 | 0.55 | Corporate |
| Free States | 152 | 0.55 | Military |
| Science Collective | 150 | 0.45 | Corporate |
| Iron Compact | 140 | 0.45 | Military |
| Terran Federation | 90 | 0.44 | Military (boxed in) |
| Corsairs | 71 | 0.44 | Renegade |

- 10 border zones between factions (up to 44 connections at major fronts)
- 70% unclaimed space for expansion
- Security: 0.3+ in all claimed space, gradient from border (low) to core (high)
- Population: high-sec ~1B, mid ~23M, low ~520K, null ~2500

### Faction AI
- Decisions every 100 ticks with reasoning logged
- Corp task assignment (mining, hauling, patrol, production)
- Build projects: station expansion + dreadnought programs per faction
- Project phases: scouting -> staging -> constructing

### Corporations (45)
- Each has: emblem, head agent (portrait), specialty, history, members, stations
- Assigned tasks by faction leadership
- Head agent regenerates with faction

---

## Frontend Pages

| Nav Button | URL | Purpose |
|-----------|-----|---------|
| Map | / (game.html) | 3D star map, system view, route planning |
| Ship | /ship | Stub - player ship status |
| Inventory | /inventory | Stub - cargo/assets |
| Market | /market | Live market (treeview, buy/sell, right-click actions) |
| Encyclopedia | /docs | Hub -> Items DB, Ships DB, Chain Calc, Ships 3D, Fitting, Universe, Resources, Materials, Products, Design |
| Settings | /settings | Stub |
| Dashboard | /debug | Overview, Factions, Stations, Ships, Combat, Market |

### Star Map Features
- Color modes: Star Type, Faction, Security, Region
- System search box (Enter to zoom)
- Right-click: Set Route, Add Waypoint, View System
- Route planning: BFS pathfinding, green-yellow path overlay
- Route panel in right sidebar (CURR/WPT/DEST badges)
- System info panel shows sec_level, faction, region, constellation
- Hover tooltip: faction, security (color-coded), region, constellation

### Market Features
- Treeview: category > subcategory > group_name > individual items (4 levels deep)
- Buy/sell panes with sortable columns (item, qty, price, jumps, station, system, region)
- Item info panel with stats when selected
- Right-click context menu: Buy/Sell (stubs), Navigate, Set Route, Add Waypoint, Copy
- Region filter (debug mode only shows dropdown)
- Size prefix in item names (S Beam Laser, C Autocannon)

---

## Key Files

| File | Purpose |
|------|---------|
| server/main.py | Flask app, all API endpoints |
| server/supervisor.py | Tick loop, intent merge, station index, ship movement |
| server/simulation.py | Universe init, ship spawning (_populate_universe) |
| server/workers/economy.py | Production/consumption/prices |
| server/workers/npc_decisions.py | Hauler/miner/freelance AI |
| server/workers/faction_strategy.py | Faction decisions, corp tasks |
| server/workers/dashboard.py | Pre-computed dashboard cache |
| server/dashboard_cache.py | DashboardCache class |
| server/persistence.py | Save/load game.db |
| server/models.py | Dataclass definitions (System, Station, NPCShip, etc) |
| server/data_access.py | DB loading functions |
| server/change_tracker.py | Delta tracking for /api/ships |
| dev.py | Local dev runner (high-speed simulation + status output) |

---

## Current Status

### Working Well
- Multi-threaded sim at 25ms/tick with 1476 ships
- Full mining economy: 263 miners active (regular + deep), cycling continuously
- Market with buy/sell orders across all categories (weapons, ammo, equipment, materials)
- Faction AI with decisions, corp tasks, build projects
- Dashboard with pre-computed aggregates (25KB, <5ms)
- Route planning with pathfinding
- Population-based civilian demand

### Not Yet Implemented
- Combat system (damage model, weapons + ammo interaction)
- Faction orders actually doing things (expand builds stations, attack triggers battles)
- Build projects completing (materials never accumulate at targets)
- Player ship control (docking, undocking, travel, mining)
- Player trading (buy/sell at stations)
- Ship fitting (equipping modules)
- Corp fleet building (ships appearing on market when built)
- Corsair raids on deep miners
- IPO events (new corps spawning)

### Known Issues
- Route options (Prefer Safe/Avoid Null) are UI only, not wired to pathfinding
- Some haulers still go idle if region cache empties (rare)
- The `_tag_portraits.html` and `_tag_emblems.html` utility files are in the repo (can clean up)

---

## Build/Deploy

- Push to master auto-deploys to fly.io
- `data/game_data.db` ships with code (Dockerfile copies to volume on deploy)
- `data/portrait_tags.json` and `data/emblem_tags.json` also copied to volume
- Nuke via /debug resets game.db + faction_decisions + corp activities
- Local: `python dev.py 120 60` for fast simulation testing
