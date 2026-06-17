# Kiro Handoff - SpaceEconomy

## What This Is

A browser-based space economy simulation game. Single-player. The core appeal is a living, agent-driven commodity market spread across a network of star systems. You are one actor (a hauler/trader) in a functioning economy, not the god of it.

**Owner:** Devlyn Napoli
**Repo:** https://github.com/dvln811/SpaceEconomy

---

## WORKFLOW RULES

1. **Commit and push automatically after completing each task/change.** Use `GIT_TERMINAL_PROMPT=0 git push` to avoid interactive prompt hangs.
2. Read this file at the start of every session.
3. Check `git log --oneline -5` and `git status` before starting.
4. Ask the user what they want to work on.
5. **NO M-DASHES (—) IN REPLIES.** Use commas, periods, or rewrite the sentence instead.

---

## Core Design (Decided)

**The Player Fantasy:** "I'm navigating a complex, living system that I can never fully master."

Knowing how the economy works does not trivialize it. The system is emergent and NPC agents constantly change conditions. You read signals, make educated bets, never guaranteed plays.

**Genre:** Space trading/economy sim (Eve Online's economy + X4 Foundations, minus micromanagement)

**Design Pillars:**
- Economy simulation IS the game (agent-based, emergent, realistic)
- High-level decisions, not unit-level commands
- Imperfect information (stale price data, limited visibility)
- Atmospheric "space trucker" vibe (Alien-era industrial space, working-class)
- Browser-based, no install, single-player

**NOT a combat game.** Conflict exists (faction warfare, piracy, blockades) but as economic hazards you navigate around, not fight through.

---

## Progression Model (Decided)

**Progression as access, not power.** You gain access to more of the system, not raw strength.

- **Early:** Small cargo shuttle, high-sec only, safe low-margin routes
- **Mid:** Proper freighter, low-sec accessible, faction contracts, riskier goods
- **Late:** Specialized vessels, null-sec/frontier, rare goods, smuggling, infrastructure ownership
- **Endgame:** Fleet/flagship, own stations, shape the economy as a major actor

**Money sinks:** Ships, upgrades, reputation, infrastructure, information (market intel)

---

## Conflict and Opposition (Decided)

- **Security gradient:** High-sec (safe, low margins) > Low-sec (risky, better margins) > Null-sec (lawless, huge margins) > Frontier (unknown, exploration)
- **Faction warfare:** NPC factions fight over territory, borders shift, supply chains break
- **Blockades/interdiction:** Avoid pirates, pay them, or find alternate routes
- **Choke points:** Key jump routes control trade flow between regions
- **Economic warfare:** Embargoes, smuggling opportunities, price spikes
- **Mystery/intrigue:** Anomalous signals, derelicts, rare commodity sources, espionage contracts

---

## Time Model (Decided)

Player-controlled tick speed (Stellaris-style). Pause/play/2x/4x. Time does not pass when not playing. Economy advances in discrete cycles.

---

## Current State

### What Exists
- `mockup.html` - Interactive UI mockup with **3D star map** (Three.js)
  - 24 star systems with 3D positioning (OrbitControls: rotate, zoom, pan)
  - Animated NPC ships moving along auto-generated trade routes
  - Glowing system nodes with color-coded types
  - Left panel: system list with station types, populations, price movements
  - Right panel: commodity market with sparkline charts
  - Bottom bar: ship stats, activity feed, profitable route suggestions
  - Header nav linking to design doc
  - Fonts: Orbitron (titles/labels), JetBrains Mono (data/body)
  - Palette: dark navy bg, cyan accents (#4fc3f7), gold currency (#ffd54f), green profit (#66bb6a), red loss (#ef5350)

- `design.html` - Game design document (dark-themed, matching mockup aesthetic)
  - Full writeup of vision, progression, economy, conflict, systems
  - Accessible via nav button in mockup header

- `KIRO_HANDOFF.md` - This file

### What Does NOT Exist Yet
- No economy simulation engine (agent-based tick system)
- No actual trading mechanics (buy/sell/haul)
- No save/load
- No progression system
- No ship upgrades or ship variety
- No NPC AI decision-making (current ships are visual only)
- No events/disruptions system
- No faction system
- No security zones
- No information fog (stale price data)

---

## Architecture Direction

- **Frontend:** Vanilla JS + Three.js (3D star map) + HTML/CSS panels (UI)
- **Backend:** Pure client-side with localStorage (no server for single-player)
- **Economy Engine:** Agent-based tick simulation (borrow patterns from PatternFoundry's tick engine)
- **Save/Load:** localStorage + JSON export/import

---

## Open Questions

1. **V1 scope:** How many systems, commodities, ship types for first playable?
2. **NPC agent count:** How many agents can browser handle performantly?
3. **Faction depth:** How complex is faction AI in v1?
4. **Minimum viable economy:** What is the smallest system that produces interesting emergent behavior?
5. **Win condition:** Sandbox/endless, or are there goals/milestones?

---

## Related Project

PatternFoundry (`/media/devlyn/Leviathan/Projects/PatternFoundry`) uses a similar agent-based simulation for financial market microstructure. The economy engine here could borrow architectural patterns from its tick engine.

---

## Contact

- Owner: Devlyn Napoli (devlynnapoli@protonmail.com)
