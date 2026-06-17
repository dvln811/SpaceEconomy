# Kiro Handoff - SpaceEconomy

## What This Is

A browser-based space economy simulation game. Single-player. The core appeal is a living, agent-driven commodity market spread across a network of star systems. You are one actor (a hauler/trader) in a functioning economy, not the god of it.

**Owner:** Devlyn Napoli

---

## WORKFLOW RULES

1. **Commit and push automatically after completing each task/change.** Use `GIT_TERMINAL_PROMPT=0 git push` to avoid interactive prompt hangs.
2. Read this file at the start of every session.
3. Check `git log --oneline -5` and `git status` before starting.
4. Ask the user what they want to work on.
5. **NO M-DASHES (—) IN REPLIES.** Use commas, periods, or rewrite the sentence instead.

---

## Concept

**Genre:** Space trading/economy sim (think Eve Online's economy + X4 Foundations, but less micromanagement)

**Core Loop:**
- Star systems produce and consume goods based on their industry type
- Prices are driven by actual supply/demand (not fixed tables)
- NPC haulers, miners, and traders create a living market
- You participate as one actor: buy low, haul cargo, sell high, upgrade
- Disruptions ripple through supply chains (blockades, refinery fires, shortages)
- Fleets/NPCs act autonomously based on doctrine, not player micromanagement

**Design Pillars:**
- Economy simulation is the game (agent-based, emergent, realistic)
- High-level decisions, not unit-level commands
- Atmospheric "space trucker" vibe (Alien-era industrial space, not Star Trek polish)
- Browser-based, no install
- Single-player (for now, maybe forever)

**Inspirations:**
- Eve Online (economy depth, market dynamics)
- X4 Foundations (trading, but less tedious)
- Stellaris (grand scale, but less micromanagement)
- Alien (1979) (aesthetic, working-class space)
- Euro Truck Simulator (the satisfaction of hauling)

---

## Current State

### What Exists
- `mockup.html` - Visual UI mockup (fully functional interactive demo)
  - Star map with 24 systems (pan/zoom via mouse drag + scroll wheel)
  - Animated NPC ships moving along auto-generated trade routes
  - Parallax starfield background
  - Left panel: system list with station types, populations, price movements
  - Right panel: commodity market with sparkline charts, prices, % changes
  - Bottom bar: ship stats, activity feed, profitable route suggestions
  - Fonts: Orbitron (titles/labels), JetBrains Mono (data/body)
  - Color palette: dark navy bg, cyan accents (#4fc3f7), gold currency (#ffd54f), green profit (#66bb6a), red loss (#ef5350)

### What Does NOT Exist Yet
- No backend/game logic
- No economy simulation
- No actual trading mechanics
- No save/load
- No progression system
- No ship upgrades
- No NPC AI decision-making
- No events/disruptions system

---

## Potential Architecture

**Frontend:** Vanilla JS + Canvas (star map) + HTML/CSS panels (UI)
**Backend:** Python/Flask (if needed for persistence) or pure client-side with localStorage
**Economy Engine:** Agent-based simulation (similar approach to PatternFoundry's tick engine)

### Economy Simulation Ideas
- Each system has production/consumption rates per commodity
- NPC traders run route optimization (buy cheapest, sell highest, account for distance/fuel/risk)
- Prices follow supply/demand curves: `price = base_price * (demand / supply)^elasticity`
- Events (random or triggered) disrupt supply chains
- Player actions affect the economy (large trades move prices)
- Time progresses in cycles (not real-time, player-controlled tick speed)

### Commodity Types (from mockup)
Iron Ore, Processed Food, Medical Supplies, Fuel Cells, Electronics, Luxury Goods, Polymers, Alloys, Narcotics (illegal/high-risk)

### System Types (from mockup)
Industrial Hub, Mining Colony, Trade Hub, Processing, Agricultural, Frontier, Jump Nexus, Shipyard, Military

---

## Tech Decisions (TBD)

- [ ] Pure client-side vs. server-backed?
- [ ] Real-time vs. turn-based vs. player-controlled time?
- [ ] Scope: how many systems, commodities, ship types at v1?
- [ ] Progression: what does the player work toward?
- [ ] Risk: combat/piracy as simulation or avoidance mechanic?

---

## Design Questions to Resolve

1. **What's the win condition?** (Or is it sandbox/endless?)
2. **How does time work?** (Pause/play/speed like Stellaris? Or turn-based?)
3. **What can you spend money on?** (Ships, upgrades, stations, reputation?)
4. **How much do you directly control?** (Just your ship? A fleet? A company?)
5. **What makes it NOT boring after 2 hours?** (Events? Escalating risk? Unlocking new regions?)

---

## Related Project

PatternFoundry (`/media/devlyn/Leviathan/Projects/PatternFoundry`) uses a similar agent-based simulation approach for financial market microstructure. The economy engine here could borrow architectural patterns from the tick engine (agents with different behaviors producing emergent dynamics).

---

## Contact

- Owner: Devlyn Napoli (devlynnapoli@protonmail.com)
