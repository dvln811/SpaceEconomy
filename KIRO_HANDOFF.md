# Kiro Handoff - SpaceEconomy

## What This Is

A browser-based space economy simulation. Single-player (Devlyn) with a living, agent-driven commodity market across 2,500 star systems. 6 NPC factions mine, trade, build, expand, and wage war autonomously. The player participates as one actor - flying ships, trading, building a corporation, eventually leading a faction. Built on assets from GCS: Salvage Rat (previously on Steam).

**Goal:** A 24/7/365 persistent simulation that self-sustains over months/years without collapsing (unlike X4 Foundations). Eve Online economy depth + Mount & Blade delegation + actual working long-term sustainability.

**Owner:** Devlyn Napoli
**Repo:** https://github.com/dvln811/SpaceEconomy (PRIVATE, Pro plan $4/mo, 3000 Actions min/month)
**Live:** https://spaceeconomy.fly.dev
**Debug:** https://spaceeconomy.fly.dev/debug
**Local Dev:** `python dev.py [speed] [duration]` (e.g., `python dev.py 120 60`)

---

## WORKFLOW RULES

1. **Batch pushes** - commit locally as we work, only push when validated/milestone reached (saves Actions minutes)
2. Read this file at the start of every session.
3. **NO M-DASHES in replies.**
4. **No raw IDs displayed anywhere** - always title case or lookup names.
5. Item names must NOT include size labels (size is a separate column/badge).
6. **Ask before coding** when user asks a question vs requests a change. **NEVER start coding just because the visionary asks a question.** Discuss first, confirm approach, THEN code.
7. Use `python dev.py` or `python _sim.py` for local testing.
8. Nuke button on /debug resets runtime state after breaking changes.
9. **ALL scrollbars must be themed** (dark track, subtle thumb) on every page.
10. **1 tick = 6 minutes** of game time (10 ticks/hour, 240 ticks/day, ~87,600 ticks/year).

---

## Architecture

### Tech Stack
- **Backend:** Python (Flask + gunicorn), fly.io (shared-cpu-2x, 1GB RAM)
- **Frontend:** Vanilla JS + Three.js (3D maps), single-page app with left nav panel
- **Simulation:** Multi-threaded Supervisor + 6 Workers, ~8 t/s headless with 2757 ships
- **Databases:** SQLite (game_data.db in git, game.db runtime on volume)
- **Performance ceiling:** ~8-16 t/s headless (Python GIL limits true parallelism). Live server runs 1 tick/sec with ~80ms budget - plenty of headroom.

### Simulation Architecture
- **Supervisor** - tick clock (1/sec), snapshot distribution, intent merge, station index, ship movement
- **Economy Worker** (every tick) - production, population-scaled consumption, ore generation, price updates (every 60 ticks)
- **NPC Decision Worker** (every tick) - contract-based hauler AI, miner AI, freelance AI, batched 200/tick
- **Faction Strategy Worker** (every 100 ticks) - decisions, corp tasks, build project material consumption
- **Battle Sim Worker** (every 20 ticks) - faction skirmishes, ship destruction, shipyard rebuilding
- **Corsair Spawn Worker** - corsair raid generation
- **Dashboard Worker** (every 10 ticks) - pre-computed dashboard aggregates

### Key Files

| File | Purpose |
|------|---------|
| server/main.py | Flask app, all API endpoints, simulation startup |
| server/supervisor.py | Tick loop, intent merge, station index, ship movement |
| server/simulation.py | Universe init, ship spawning (~2757 NPCs) |
| server/workers/economy.py | Production/consumption/prices with population scaling |
| server/workers/npc_decisions.py | Contract-based hauler AI, miner AI |
| server/workers/faction_strategy.py | Faction decisions, build project material consumption |
| server/workers/battle_sim.py | Faction skirmishes, ship destruction/rebuilding |
| server/combat_engine.py | Standalone 3D combat simulation (spatial, per-shot) |
| server/ship_geometry.py | 79 ship 3D models (component-based, Three.js) |
| server/models.py | Dataclass definitions (System, Station, NPCShip, etc) |
| server/data_access.py | DB loading functions |
| economy_config.yaml | Tunable economy parameters |
| dev.py | Local dev runner (headless, high-speed) |
| _sim.py | Economy simulation with progress bar + results dump |
| _telemetry.py | Detailed per-100-tick telemetry for economy analysis |
| sim_events.py | Event injection stress tester |
| tuning_log.txt | History of all economy tuning rounds |

---

## Database Schema (game_data.db)

| Table | Purpose |
|-------|---------|
| commodities (1540) | Items with category/subcategory/group_name, stats JSON (includes cpu_cost, pg_cost), recipes |
| recipes (3399) | Production chain inputs (commodity_id, input_id, quantity) |
| ships (91) | All ships with full fitting stats (cpu, powergrid, high/mid/low slots, turret/launcher hardpoints, signature, scan_res, etc.) |
| systems (2500) | Positions, sec_level (0.0-1.0), faction_id, region, population (up to 2B) |
| stations (535) | Types: mining_colony(93), refinery(185), component_works(60), factory(82), trade_hub(100), military_base(9), shipyard(6) |
| station_produces (1586) | What each station manufactures |
| station_consumption (117) | Passive demand per station type (includes weapons/ammo for military, fuel for trade hubs) |
| fleet_targets (42) | Target fleet composition per faction for battle_sim rebuilding |
| build_projects (10+) | Faction construction projects - now actually consume materials |
| corporations (45) | Sub-factions with specialties |
| faction_agents (72) | Named agents with traits |
| faction_state (6) | Personality values |
| faction_decisions | Rolling decision log |

---

## Ship Fitting System (NEW - June 27)

### Slot System
- **High Slots** (red) - Weapons, mining lasers, salvagers, tractor beams, remote repair, cloaks
- **Mid Slots** (yellow) - Shield mods, propulsion (AB/MWD), EWAR, tackle, cap boosters, scanners
- **Low Slots** (green) - Armor plates/repairers/hardeners, damage mods, engineering, cargo expanders

### Hardpoints (sub-limit within High Slots)
- **Turret Hardpoints** - max turrets (lasers, railguns, autocannons, blasters)
- **Launcher Hardpoints** - max missile/torpedo launchers

### Fitting Resources
- CPU (tf) - processing capacity, EWAR/electronics intensive
- Power Grid (MW) - energy output, weapons/shields/propulsion intensive
- Capacitor (GJ) - energy pool, active modules drain per cycle

### Ships (91 total, 79 geometries)
- Removed: Viper Interceptor, Warden Frigate (prototypes)
- Hull classes: Fighter(12), Frigate(12), Destroyer(13), Cruiser(12), Battlecruiser(12), Battleship(12), Carrier(2), Dreadnought(5), Industrial(6), Mining Barge(5)
- Each has: CPU, PG, cap, cap_recharge, signature, scan_res, sensor_strength, target_range, max_targets, high/mid/low slots, turret/launcher hardpoints, manufacturer
- Realistic dimensions: Fighter 30-50m, Frigate 60-110m, Cruiser 300-500m, Dreadnought 2200-3800m
- Realistic speeds (m/s): Fighter ~400, Frigate ~330, Cruiser ~175, BS ~103, Dread ~54
- Cargo: Fighter 15, Frigate 50, Destroyer 120, Cruiser 300, BC 500, BS 800, Carrier 2500, Dread 1500
- Industrials: Pinto 120, Mule 1500, Bison 5000, Ox 15000, Mammoth 30000, Clydesdale 100000
- Mining Barges: Prospect 500, Rock Hopper 800, Strip Miner 2500, Excavator 4000, Deep Core 10000

### Module Fitting Costs
- All 940 Ship Equipment + Weapons items have cpu_cost and pg_cost in stats JSON
- Quality modifiers: Standard 1.0x, Named 0.85x, T2 1.20x, Faction 0.90x
- Stacking penalty: effectiveness(n) = 0.5 ^ ((n-1) / 2.22)^2

### Manufacturers
- Terran Fed: Apex Fleet
- Free States: Nova Logistics
- Iron Compact: Meridian Collective
- Merchants Guild: Talon Solutions
- Science Collective: Citadel Syndicate
- Corsairs: Black Shipwrights
- Civilian: Frontier Shipworks

### Reference Docs
- `docs/FITTING_SPEC.md` - Complete fitting specification
- `/fitting` page - Mechanics reference (no ship lists)
- `/ships_db` - All ships with fitting stats from DB
- `/ships` - 3D viewer with spec panel showing CPU/PG/slots/defense/nav/sensors

---

## Economy System (MAJOR REBALANCE - June 27-28)

### Timescale
- 1 tick = 6 minutes game time
- 240 ticks = 1 game day
- 87,600 ticks = 1 game year

### Population-Driven Consumption
- `consumption_rate = 2.0 * max(0.5, system_population / 100,000,000)`
- 1B population system: 20x base consumption per commodity per tick
- 500K population (null-sec): 1x base (floor of 0.5 * 2 = 1.0/tick)
- Creates natural demand hotspots in high-sec

### Station Consumption (117 entries)
- Refineries: 22 ore types (recipe inputs)
- Component Works: 16 refined materials
- Factories: 11 manufactured inputs
- Military Bases: 32 items (weapons, ammo, equipment, fuel, materials)
- Shipyards: 77 items (ALL ship build materials + hull components)
- Trade Hubs: 4 items (fuel, water, protein)
- Mining Colonies: 2 items (food, water only - NO fuel)

### Military Self-Supply
- Military bases and shipyards generate consumed items at 1.5x consumption rate
- Capped at 500 units per item (prevents hoarding)
- Represents internal manufacturing/logistics

### Pricing
- Soft price anchor: pulls back 70% when above 1.5x or below 0.67x base
- Absolute safety cap: 0.33x - 3.0x (rarely hit)
- Pressure: +/-0.2 per 60-tick update, cap +/-15, decay 0.90
- Still being tuned (see Economy Tuning Status below)

### Mining & Production
```yaml
mining:
  yield_multiplier: 400          # ore per cycle = 400 * field_density
  cycle_ticks: 50
  unload_ticks: 25
passive_generation:
  rate_multiplier: 3.0           # ore/tick = 3 * density per type per colony
  inventory_cap: 500000
economy:
  production_rate: 1.0           # (refineries: 3.0 in DB)
  baseline_trickle_mult: 0.3
  price_update_interval: 60
```

### NPC Fleet (2757 ships)
- **Haulers (~1300)**: Contract-based AI, 72% utilization, 6M units in transit
- **Freelancers (~320)**: Profit-seeking, buy cheap sell expensive
- **Miners (584)**: 5 per mining system, yield 400*density/cycle
- **Military patrol (573)**: Idle (patrol routes not yet implemented)

### Hauler AI: Contract System (NEW)
- Every 50 ticks: scans ALL stations for deficits (recipe inputs + consumption items)
- Builds sorted contract list (biggest deficits first)
- Haulers claim cargo-capacity-sized slices, find nearest source, buy, deliver
- Inter-regional hauling as fallback
- Load balancing via qty_claimed prevents dogpiling
- Replaces old assigned-station system (which left 85% idle)

### Combat Attrition (demand sink)
- Battle Sim Worker: 4 faction conflict pairs
- Skirmishes every 20 ticks at 0.3 probability, 1-2 losses per side
- ~14-15 ships destroyed per 100 ticks
- Shipyards rebuild from inventory (consuming real materials)
- ~1300 ships rebuilt per 10K ticks
- Fleet strength maintains at ~45 ships across factions

### Faction Build Projects (NOW CONSUMING MATERIALS)
- Station expansion: requires station_hull_plating, reactor_module, life_support, etc.
- Fleet builds: uses REAL ship build costs from DB (battleships = 23K materials)
- During "constructing" phase, pulls materials from faction shipyards/factories
- Completes when accumulated >= requirements
- New projects auto-created on expand/attack decisions

---

## Economy Tuning Status (IN PROGRESS)

### What's Working
- Fuel economy stable (avg 1.10x base)
- Military bases stocked (4500 ammo, 9500 weapons, 1000 fuel)
- Hauler utilization 72% (1200/1600 carrying cargo)
- 6M units actively in transit
- Combat attrition consuming ~1400 ships/10K ticks
- Faction build projects consuming materials from shipyards
- Production chains functional (ore -> refined -> manufactured -> components)

### Known Issues Being Investigated
- **Ore prices elevated** (Iron 1.46x, Copper 1.60x, rare ores at 3x) - 185 refineries demanding ore from 93 mining colonies, logistics bottleneck
- **Weapons crashing** (0.49x) - Military self-supply generates faster than consumption (no real combat drain from station inventory yet)
- **Refined intermediates oversupplied** - Lithium Cell, Chromium Plate, etc. produced by 25+ stations, consumed by nobody
- **Growth rate 9,300 units/tick** - ore stockpiling at mining colonies (will self-limit at 500K cap)
- **Price distribution** - 52% at 3x ceiling, 35% below 0.5x floor. Soft anchor not strong enough for current imbalance.

### Root Causes Identified
1. Refinery count (185) too high relative to ore supply (93 colonies) - each colony must feed 2 refineries
2. Military self-supply at 1.5x consumption creates surplus (should be < 1.0x or conditional on market availability)
3. Rare ores (Palladium, Neutronium, Quartz Crystal) only generated at 1 colony each, consumed by 185 refineries
4. Weapons produced via trickle at military bases but never actually consumed (combat doesn't drain station ammo inventory)

### Telemetry System
- `_telemetry.py` - detailed per-100-tick logging of ore flow, hauler activity, miner states, refinery throughput, military inventory, price history
- Outputs to `sim_telemetry.json` (large file, ~5-50MB)
- Use for tracing exactly WHERE supply chain breaks down

### Next Tuning Steps
1. Analyze telemetry data to trace exact breakdown points
2. Fix military self-supply (conditional on market, not always-on)
3. Add more mining colonies for rare ores
4. Consider reducing refinery count or lowering their production rate
5. May need to revert to hard price clamp until structural issues fixed

---

## Combat System

### 3D Combat Viewer (/combat)
- Full 3D spatial simulation with ship models
- 4 damage types: EM, Thermal, Kinetic, Explosive with resistance profiles
- Per-shot resolution, angular velocity tracking, range falloff
- Missiles as spatial entities with lead prediction
- Movement in full 3D (x/y/z) - ships use vertical space
- Post-battle: ships hold position (no orbit/fly-off)
- Destroyed BC+ ships: gray wrecks with trails removed
- Camera: WASD free fly, orbit, follow ship
- Ship models from ship_geometry.py (79 geometries)
- Performance: 200 ships at 60fps, 500 at 44fps (RTX 4060 Ti)

### Battle Sim (abstract, in-sim)
- Fleet targets per faction in DB
- Skirmishes at faction borders (4 conflict pairs)
- Ships destroyed -> ShipDestroyedEvent -> supervisor decrements fleet
- Ships rebuilt when shipyard has materials -> ShipBuiltEvent -> supervisor increments fleet
- ~14.7 destroyed per 100 ticks, maintains ~45 fleet strength

---

## Frontend Pages

| URL | Purpose |
|-----|---------|
| / (game.html) | 3D star map, system view, route planning |
| /ship | Player ship - docked hangar + flight view with local space |
| /agents | Agent encyclopedia (split-pane, detail with family/history) |
| /inventory | Stub - cargo/assets |
| /market | Live market (treeview, buy/sell, right-click) |
| /docs | Encyclopedia hub |
| /ships_db | All ships - unified by class, shows CPU/PG/slots/hardpoints |
| /ships | 3D ship viewer with full spec panel from DB |
| /fitting | Fitting mechanics reference |
| /items | Items database |
| /chain | Production chain calculator |
| /universe | Universe/factions with expandable lore |
| /combat | 3D combat viewer (stations as scale reference) |
| /design | Game design document (includes expansion spec) |
| /debug | Dashboard (overview, factions, stations, ships, combat, market) |
| /ship_designer | Ship + Station generator, review, component library |
| /settings | Stub |

---

## Design Vision (from /design page)

- **Living simulation, not a game to "beat"** - runs 24/7, evolves over years
- **Eve-scale economy** - millions of units, weeks to build capitals, real scarcity
- **M&B delegation** - appoint governors, admirals, set policy. NPCs execute.
- **Economy that doesn't collapse** - the core engineering challenge
- **Warfare as demand sink** - perpetual cycle prevents stagnation
- **Geographic friction** - 2,500 systems, rare resources far away and dangerous
- **Player flies a ship** - trade, fight, explore. Combat is strategic (M&B auto-resolve style with visibility)
- **Faction politics** - join/create faction, rise through ranks, get elected ruler
- **Put game down for months** - come back, universe has evolved autonomously

---

## Build/Deploy

- Push to master auto-deploys to fly.io via GitHub Actions
- `data/game_data.db` ships with code (Dockerfile copies to volume)
- Nuke via /debug resets game.db + faction_decisions + corp activities
- Local testing: `python _sim.py 10000` (10K ticks with progress bar -> sim_results.txt)
- Telemetry: `python _telemetry.py 10000` (detailed -> sim_telemetry.json)
- Event injection: `python sim_events.py 10000` (stress test with faction build events)

---

## Revert Points

- `d296047` - Last stable state before soft price anchor (hard clamp 0.5x-2.0x working)
- `6e573c5` - Current HEAD: full economy with events, combat fix, news ticker
- `fbea1a9` - Build_cost/fitting_cost split first working

## Recent Session Summary (June 29-30, 2026)

### Major Achievements This Session
1. **Faction Lore** - 6 factions with 5.5-7K chars detailed histories, cultures, politics, military doctrine
2. **Agent Population** - 295 M&B-style agents with clans, families, ages, bios, traits, patron/rival relationships
3. **Agent Detail Page** (/agents) - Split-pane with list + full detail (traits, family, history)
4. **Structured Event Framework** - 50+ faction-specific event types, chains, agent lifecycle effects
5. **Station Generator** - 210 pre-generated station designs (5 factions x 7 types x 6 variants)
6. **3D Stations in System View** - Merged geometry, faction-appropriate models
7. **Combat Viewer Stations** - Stations as scale reference in battles
8. **Ship System View Labels** - Callout flags with names instead of 3D models
9. **Intra-system Warp Speed** - Based on ship.speed * 0.0015 AU/s (realistically scaled)
10. **NPC Decision Optimization** - Only on state change (14+ t/s, was 2 t/s)
11. **Security Redistribution** - Distance-based from empire centers, unclaimed = null-sec
12. **Station Redistribution** - 712 stations, proper sec-level density (high-sec dense, low-sec sparse)
13. **News System Overhaul** - Category coloring, agent links, price ticker tape, battle narratives
14. **Player Ship Flight** (WIP) - Local space, undock/dock, client-side physics, SSE for NPCs
15. **LocalSpaceWorker** - Server-side persistent 3D simulation of player's current system
16. **Territorial Expansion Design Spec** - Multi-year real-time expansion pipeline documented

### Architecture Decisions Made (New)
- **Local space scale**: 1 unit = 1 meter. Station ~2km away on undock.
- **Player ship**: Client-authoritative for local movement, server tracks position
- **NPC ships in local space**: Server-authoritative, client interpolates from SSE stream
- **Warp/dock/jump**: Server-authoritative commands
- **Security = distance to nearest empire center** (not faction-specific)
- **Unclaimed space**: Always 0.0-0.1 security
- **Expansion timeline**: 2-3 real years to settle all unclaimed systems
- **Sim performance**: 14+ t/s achieved via NPC decisions only on state change + 50-ship batch cap

### Player Ship System (NEW - /ship page)
- **Docked view**: Dark hangar, pedestal, ship model, stats, cargo, undock button
- **Flight view**: 3D space, station nearby, NPC ships, engine trail
- **Controls**: Double-click to fly direction, S to stop, right-click nav for warp
- **Camera**: Left-drag orbit, right-drag freelook (WIP), scroll zoom
- **Local Space Worker**: Server thread maintains all ships in system at 1 tick/sec
- **SSE stream**: /api/player/local_space/stream pushes NPC state each tick
- **Position reporting**: Client reports player position every 3 seconds

### Key Files (New)
| File | Purpose |
|------|---------|
| server/local_space.py | LocalSpaceWorker - 3D simulation of player's system |
| server/event_framework.py | Structured event generator (50+ faction-specific types) |
| server/agent_lifecycle.py | Agent death/replacement/history logging |
| server/agent_population.py | M&B-style agent population generator |
| ship.html | Player ship page (docked + flight views) |
| agents.html | Agent encyclopedia (split-pane, detail view) |
| tools/ship_designer/station_generator.py | Station assembly from components |
| tools/ship_designer/station_components.py | Station component primitives (30 styles) |
| tools/ship_designer/station_designs/ | 210 pre-generated station JSON files |

### Known Issues (Current)
- **Price bimodality** - 70% inflated / 30% crashed (structural pricing algorithm issue, not supply)
- **NPC ship models in flight** - Falling back to cone shapes (ship_class key mismatch with geometry IDs)
- **Solar body labels** - Projection not quite right, especially when zoomed out
- **Freelook camera** - Works partially, needs cleanup (OrbitControls conflict resolved but lerp-back imperfect)
- **System map ship labels** - May not fully clean up when switching between systems
- **Nav list interaction** - Context menu positioning fixed but needs testing

### Immediate Next Steps
1. **Fix NPC ship_class -> geometry_id mapping** so real models load
2. **Polish freelook camera** - write fully custom controller (no OrbitControls)
3. **Warp implementation** - transition between local grids (AU travel animation)
4. **Jump gate travel** - system-to-system transition
5. **Market interaction from ship** - buy/sell while docked
6. **Player progression** - renown system, faction membership
7. **Pricing algorithm rework** - fix the bimodal price distribution

### Economy Status (end of session, 10K tick sim)
- Performance: 14 t/s (3411 ships, 712 stations)
- Inventory: 165M, Growth: 16.5K/tick
- Fleet: 109 ships rebuilt, combat attrition working
- Haulers: 80% utilization, 5.1M cargo in transit
- Price: 70% inflated / 30% crashed (structural - needs pricing rework)
- Shipyards: ~3000 inventory each, actively building

### Simulation Tools
- `python _sim.py [ticks]` - economy sim (14 t/s, ~7 min for 5K)
- `python sim_faction_events.py [ticks]` - test faction event generation
- `python -m server.main` - local dev server
- Nuke via /debug to reset runtime state after DB changes
