# Multi-Threaded Simulation Architecture

## Overview

The simulation is split into specialized worker threads coordinated by a central Supervisor.
Each worker operates on a read-only snapshot of world state and produces **intents** (deltas/commands).
The Supervisor merges intents atomically between ticks, ensuring no partial state is ever visible.

This design targets 100,000+ NPC ships at 1 tick/second on modest hardware.

## Thread Model

| # | Thread | Frequency | Input | Output |
|---|--------|-----------|-------|--------|
| 0 | Supervisor | 1/sec (tick clock) | All intent queues | Canonical state commits |
| 1 | Economy | Every tick | Station inventories, recipes | Inventory deltas (produced/consumed) |
| 2 | NPC Decisions | Every tick (batched) | Region inventory cache, ship states | Ship intents (move/buy/sell) |
| 3 | Faction Strategy | Every 50-200 ticks | Faction state, territory, fleets | Strategic orders (war, expansion) |
| 4 | Battle Simulation | Every tick (if combatants) | Ship positions, fleet compositions | Destruction events, loot |
| 5 | Corsair/Spawn | Every 20-50 ticks | Full universe snapshot (read-only) | Spawn commands |
| 6 | Dashboard | On-demand / every 5 ticks | Full state snapshot (read-only) | JSON payloads for API |

## Supervisor (Thread 0)

The Supervisor owns the tick clock and orchestrates all workers:

1. Increment tick counter
2. Create a frozen snapshot of current world state
3. Distribute snapshot to workers + signal "go"
4. Wait for all workers to report done (with timeout)
5. Collect intents from all worker queues
6. Apply intents to canonical state in deterministic order:
   - Economy deltas first (production)
   - NPC intents (buy/sell reservations, movement)
   - Battle results (ship destruction)
   - Faction orders (state changes)
   - Spawn commands (new entities)
7. Save state periodically

## Data Flow

```
Tick N:
  Supervisor creates snapshot
       |
       v
  [Economy] [NPC] [Battle] [Faction] [Corsair] [Dashboard]
       |      |      |         |         |          |
       v      v      v         v         v          v
  intents  intents intents  intents   intents    (read-only)
       \     |      |        /         /
        v    v      v       v         v
       Supervisor merges all intents
       |
       v
  Canonical state updated (Tick N complete)
```

Workers never mutate shared state directly. Each produces typed intent objects
placed on thread-safe queues consumed by the Supervisor.

## Regions (distinct from Clusters)

- **Cluster:** Spatial grouping for universe generation (138 clusters, 1-25 systems each)
- **Region:** Gameplay boundary for economic visibility (~20 regions, ~125 systems each)

Regions define:
- NPC hauler market search boundary (ships only see prices/inventory within their region)
- Region inventory cache unit (pre-computed per region, rebuilt with prices every 10 ticks)
- Faction strategic territory unit

The 12 existing regions (from assign_regions.py) will be expanded/rebalanced to ~20.

## Pre-pay Trade Model

Unlike the current instant-transfer model, trades use pre-payment:
- Buyer commits credits at purchase time, inventory is **reserved** at source
- Hauler physically picks up reserved goods and delivers
- Seller receives credits only on delivery
- No race conditions on inventory (reservation is atomic at decision time)
- NPC Decision thread only needs to find inventory + commit reservation intent

## Region Inventory Cache

Built by Economy thread every 10 ticks (alongside price updates):
- Per-region dict: `{region_id: {commodity_id: [(station_ref, qty, system_id), ...]}}`
- Sorted by quantity descending
- NPC Decision thread does O(1) lookup instead of iterating systems

## Python Threading Notes

Python's GIL limits CPU parallelism, but this architecture still wins because:
1. Workers are decoupled: slow faction calculation doesn't block production
2. NPC decisions can span multiple ticks (batched, results applied when ready)
3. Dashboard reads never block simulation
4. Migration path to `multiprocessing` requires only changing transport (queues already message-based)

For true 100K+ scale, the intent-queue model translates directly to multiprocessing
or even distributed services with no architectural changes.

## Implementation Modules

| File | Purpose |
|------|---------|
| `server/supervisor.py` | Tick clock, snapshot, intent merge, worker lifecycle |
| `server/workers/economy.py` | Production, consumption, ore generation, price updates |
| `server/workers/npc_decisions.py` | Hauler/miner AI, region cache lookups |
| `server/workers/faction_strategy.py` | War declarations, expansion, diplomacy |
| `server/workers/battle_sim.py` | Fleet combat resolution |
| `server/workers/corsair_spawn.py` | Pirate AI, universe assessment, spawn logic |
| `server/workers/dashboard.py` | State serialization for API endpoints |
