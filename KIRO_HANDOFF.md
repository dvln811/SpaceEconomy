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

## Current State (Phase 1 COMPLETE + Production Chain Economy)

### Architecture
- **Backend:** Python (Flask), always-on server on fly.io (shared-cpu-2x, 1GB)
- **Frontend:** Vanilla JS + Three.js (3D star map) + HTML/CSS panels + Canvas (intra-system map)
- **Economy Engine:** Real-time agent-based tick simulation (1 tick/sec, background thread)
- **Database:** SQLite on persistent fly.io volume (`/app/data/game.db`), saves every 10 ticks
- **Deployment:** fly.io, auto-deploy via GitHub Actions on push to master
- **Local dev:** `restart_server.ps1` runs Flask with debug=True on port 8000

### What Exists

**Server (`server/`)**
- `server/main.py` - Flask app, tick loop thread, API endpoints (including `/api/debug` with full production chain data)
- `server/simulation.py` - Economy engine: recipe-driven production, NPC AI with safety-aware pathfinding, mining, intra-system travel
- `server/models.py` - Dataclasses: Commodity (38 types, 5 tiers, recipes), Station (typed), System, SystemObject, NPCShip (risk_tolerance)
- `server/universe.py` - 48-system universe seed data (3 clusters, connections, asteroid fields, intra-system objects)
- `server/persistence.py` - SQLite save/load state, nuke/reset

**Frontend**
- `game.html` - Main game UI with live 3D star map + inline system view window
  - 48 star systems with CSS2D labels, billboarded ship sprites
  - Ships visible on star map during inter-system travel
  - Inline draggable/resizable system view window (ISM) opened via "View System Map" button
  - ISM shows: radar-style schematic, orbital lines, planets with moons, gates, stations, belts
  - ISM ships: deterministic linear interpolation, visible only when traveling or mining (not docked)
  - Left panel: tabbed (Systems list / Ships list)
  - Right panel: tabbed (System Info / Market)
  - Bottom panel: ship schematic, activity feed, routes

- `debug.html` - Comprehensive debug dashboard at /debug
  - **Overview tab:** Sim stats, production health (active vs halted lines), economy inventory, recent events
  - **Stations tab:** All production lines with input levels, halt status, output stock (sticky headers)
  - **Ships tab:** Filterable ship list with drill-down (cargo, route, risk tolerance, capacity). Filters persist across refreshes.
  - **Market tab:** Tabular format with commodity and system filter dropdowns (Commodity/Tier/System/Station/Price/Stock)
  - **Systems tab:** Select any system to see station production, inventory, ships, asteroid fields
  - All filter/dropdown state persists across 2-second auto-refresh
  - Nuke button for simulation reset

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

### Production Chain Economy (IMPLEMENTED)

**5-tier commodity chain (38 production + 6 trade goods = 44 commodities):**
- **T1 Raw (10):** Iron Ore, Copper Ore, Titanium Ore, Platinum, Crystals, Ice, Helium-3, Organics, Rare Earths, Uranium
- **T2 Refined (8):** Refined Iron, Refined Copper, Refined Titanium, Water, Hydrogen Fuel, Processed Food, Chemicals, Enriched Uranium
- **T3 Industrial (8):** Steel Alloy, Titanium Alloy, Polymers, Composites, Superconductors, Pharmaceuticals, Ceramics, Glass
- **T4 Components (8):** Electronics, Engine Parts, Hull Plating, Reactor Cores, Life Support Units, Weapon Systems, Mining Lasers, Navigation Arrays
- **T5 Complex (6):** Ship Modules, Station Modules, Combat Drones, Mining Rigs, Medical Bays, Jump Drives
- **Trade Goods (6):** Luxury Goods, Consumer Electronics, Gourmet Food, Exotic Textiles, Entertainment Media, Fine Spirits

**Trade goods** are tier-0 (no recipe, no production chain). They exist purely to create end-use demand at stations. All station types consume various trade goods, creating constant demand-driven trade routes independent of the production chain.

**Recipe-driven production:**
- Each non-T1 commodity has a recipe (dict of input commodity: quantity needed)
- Stations consume inputs per tick and produce outputs
- If any input is missing, production halts (zero output that tick)
- Scarcity cascades up the chain naturally

**Station types:**
- Mining Colony: buys T1 from miners, sells to haulers
- Refinery: T1 -> T2
- Industrial Hub: T2 -> T3
- Component Factory: T3 -> T4
- Shipyard: T4 -> T5
- Trade Hub: produces nothing, buys/sells everything
- Frontier Outpost: consumes essentials (food, fuel, meds, water)
- Military Base: consumes weapons, combat drones, ship modules

### 48-System Universe

**3 Clusters:**
- **Core (High-Sec, 12 systems):** Cygnus, Kepler, Tau Ceti, Procyon, Sirius, Deneb, Polaris, Fomalhaut, Sol, Haven, Vega Prime, Meridian
- **Rim (Low/Med-Sec, 23 systems):** Arcturus, Vega, Altair, Barnard's Star, Antares, Capella, Betelgeuse, Castor, Achernar, Aldebaran, Regulus, Mira, Draconis, Lyra, Novus, Serpentis, Haven's Edge, Helios, Osiris, Corvus, Fornax, Hydra, Aquila
- **Frontier (Null-Sec, 13 systems):** Wolf 359, Rigel, Pollux, Canopus, Spica, The Void, Terminus, Obsidian, Erebus, Phantom, The Abyss, Pyxis, Nyx

**Chokepoints:** Procyon (core-to-rim), Castor (rim-to-frontier), Spica (frontier nexus)

**Ore distribution rules:**
- Common ores (Iron, Copper, Ice, Organics): Available in core systems, can coexist with local refineries
- Moderate ores (Titanium, Helium-3): Rim systems, minimum 1 jump from processors
- Rare ores (Platinum, Crystals, Rare Earths, Uranium): Frontier/null-sec only, minimum 2 jumps from any buyer, high danger

**58 stations, 34 asteroid fields across 48 systems.**

### NPC Fleet (70 ships)

**50 Traders (5 classes, risk-based):**
- Pinto Runner (120 cargo, risk 0.2) - safe routes only
- Mule Freighter (180 cargo, risk 0.3) - mostly safe
- Bison Mk.III (250 cargo, risk 0.5) - moderate risk
- Ox Hauler (350 cargo, risk 0.7) - takes some risk
- Clydesdale (500 cargo, risk 0.9) - goes almost anywhere

**20 Miners (3 classes, risk-based):**
- Prospect Skiff (80 cargo, risk 0.2) - safe belts only
- Strip Miner (150 cargo, risk 0.5) - moderate danger
- Deep Core Borer (250 cargo, risk 0.8) - goes to dangerous fields

**Safety-aware pathfinding:** BFS skips systems exceeding the ship's risk tolerance. Ships will route around dangerous systems to find safe paths. If stuck, they pick the least dangerous exit.

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

### API Endpoints
- `GET /` - Game UI
- `GET /design` - Design document
- `GET /universe` - Universe design document
- `GET /economy` - Economy design document
- `GET /docs` - Documentation hub
- `GET /system_view` - Standalone system view
- `GET /debug` - Debug dashboard (comprehensive monitoring)
- `GET /health` - Health check (tick count)
- `GET /api/state` - Full universe state (systems, stations, prices, inventories, objects)
- `GET /api/ships` - All NPC ship positions, states, intra-system path data
- `GET /api/system/<id>` - Detailed system view (objects + ships with intra coords)
- `GET /api/debug` - Full debug data (systems with production health, ships with routes/risk, prices)
- `POST /api/nuke` - Reset simulation to initial state

---

## Known Issues

- **Frontend not updated for 48 systems:** The game.html star map still references the old 24-system layout. The 3D positions exist in the data but the frontend may need adjustment for the larger universe.
- **Initial starvation period:** After a nuke, higher-tier stations (T3+) will be halted for a while as the supply chain bootstraps from raw ores upward. This is expected behavior.
- **Trade clustering may still occur** in core systems since that's where most refineries and factories are. Monitoring needed.

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
- **5-tier production chain (38 commodities, recipes, halt-on-shortage)**
- **48-system universe (3 clusters, ore distribution rules)**
- **Safety-aware NPC pathfinding (risk tolerance per ship class)**
- **Comprehensive debug dashboard**

### Phase 2: Player Can Trade (NEXT)
- Player can buy/sell commodities at current station
- Player can set destination, travel takes real time
- Fuel consumption during travel
- Balance and cargo tracking
- Ship upgrades (cargo capacity, fuel efficiency, speed)
- Player mining (use mining laser hardpoint on asteroid fields)

### Phase 3: Blueprints and Fittings
- Blueprint system (recipes as discoverable/tradeable items)
- Weapons and ship fittings as equippable items (not just trade commodities)
- Ship loadout system (hardpoints, slots)
- Fittings affect ship stats (speed, cargo, mining yield, survivability)
- Damage/wear creates ongoing demand (replace broken modules)

### Phase 4: Tech Levels
- Tech 1/2/3 quality multipliers on T3-T5 products
- Higher tech requires rarer inputs (Platinum, Crystals, Rare Earths)
- Prototype tier (unique anomaly materials, one-offs)

### Phase 5: Information and Risk
- Price data staleness (only see prices from last visit)
- Security zones with piracy risk (random cargo loss in low-sec)
- Basic events (supply disruptions, price spikes, faction skirmishes)
- Contracts and reputation

### Phase 6: Factions and Depth
- Faction territories, diplomacy, warfare
- Shifting borders that reshape trade routes
- Smuggling mechanics in embargoed systems
- Fleet ownership and infrastructure (late-game)
- Multiplayer (shared persistent world)

---

## Key Design Decisions

- **Real-time, always-on.** Economy ticks 24/7, world persists whether player is online or not.
- **Mining as safety net.** You can always mine. Slow money but guaranteed. No going broke.
- **Progression as access, not power.** You gain access to more of the system, not raw strength.
- **NOT a combat game.** Conflict is an economic hazard, not a gameplay mechanic.
- **Two-layer navigation:** Inter-system (star map) + intra-system (system map). Space is big.
- **Universe generated once, persists forever.** Not procedurally regenerated. Grows and evolves slowly on its own. MMO-first design.
- **No tier restrictions on cargo.** Any ship can haul anything (volume permitting). Ship behavior is class-driven (risk tolerance), not commodity-restricted.
- **Production halts on shortage.** No magic inputs. Every unit of steel requires iron ore that was mined and refined. Scarcity cascades naturally.

---

## Future Notes (Captured for Later)

- **Blueprint system:** Recipes as discoverable/tradeable items. Player-owned production installs blueprints at facilities. Rare/prototype blueprints for high-value goods.
- **Weapons and ship fittings:** T4/T5 products become equippable items, not just trade commodities. Ship loadout system with hardpoints. Fittings affect stats. Damage/wear creates demand sink.
- **Tech levels:** Quality multiplier on T3-T5. Higher tech = rarer inputs + more value. Deferred until base chain is stable.

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
