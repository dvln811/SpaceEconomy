# Faction AI System

## Architecture

### Layer 1: Faction Identity (static/slow-changing)

Each faction has immutable core identity plus slow-evolving strategic posture:

```
Faction:
  identity:
    philosophy: "Order through strength"
    government: "military_junta" | "republic" | "oligarchy" | "theocracy" | "anarchy"
    core_values: [expansion, stability, profit, freedom, innovation, domination]
    historical_context: "Founded by former navy officers after the Collapse..."
  
  leadership:
    leader: Agent (the faction head)
    council: [Agent, Agent, Agent]  # top advisors
    
  posture:
    aggression: 0.0-1.0  # how likely to initiate conflict
    expansion_drive: 0.0-1.0  # desire for new territory
    economic_focus: 0.0-1.0  # prioritize economy over military
    diplomacy_openness: 0.0-1.0  # willingness to negotiate
    
  priorities: [ordered list of current goals]
    e.g., ["secure_border", "expand_south", "build_dreadnought", "trade_agreement_with_guild"]
```

### Layer 2: Agents (the decision-makers)

Agents are individual NPCs with names, roles, and personality:

```
Agent:
  id, name, title
  faction_id
  role: "admiral" | "governor" | "director" | "general" | "spymaster"
  
  personality:
    aggression: 0.0-1.0     # prefers force over diplomacy
    caution: 0.0-1.0        # risk aversion
    competence: 0.0-1.0     # how well they execute orders
    loyalty: 0.0-1.0        # faction loyalty (low = may defect)
    ambition: 0.0-1.0       # seeks personal advancement
    corruption: 0.0-1.0     # skims resources, makes side deals
    
  assignment:
    type: "fleet_command" | "system_governor" | "trade_director" | "intelligence"
    target: system_id or region or fleet_id
    
  record:
    battles_won: int
    battles_lost: int
    systems_developed: int
    reputation: float  # public standing
```

### Layer 3: Decision Engine (every 200 ticks)

The faction strategy worker evaluates:

1. **Assess State** - territory, economy health, military strength, threats
2. **Leader Decides Priority** - based on faction identity + current situation
3. **Issue Orders** - assign agents to execute the priority
4. **Agents Interpret** - each agent filters orders through personality
5. **Execute** - agents emit intents (expand, attack, build, trade)

### Decision Flow Example

```
Situation: Iron Compact has lost 3 border systems to Frontier Alliance

1. Assessment: "We're losing territory. Military strength: 60%. Economy: stable."
2. Leader (aggressive militarist): Priority = "counterattack" 
3. Orders: Admiral Krov assigned to retake systems, Governor Thane to reinforce logistics
4. Agent Interpretation:
   - Admiral Krov (aggressive, competent): Launches immediate assault
   - Governor Thane (cautious, corrupt): Diverts some resources, slow buildup
5. Execution:
   - Krov's fleet attacks (battle_sim intent)
   - Thane's logistics are 70% effective (competence * loyalty modifier)
```

### Layer 4-6: Mechanics (what actually happens)

These are the existing workers, enhanced:

- **Expansion**: Scout system -> Claim -> Build station -> Develop
- **Warfare**: Choose target -> Commit fleet -> Battle resolution -> Occupy/retreat
- **Economy**: Identify gaps -> Build stations to fill gaps -> Assign haulers
- **Diplomacy**: Propose alliance -> Negotiate terms -> Enforce treaty

## Database Schema

### New Tables

```sql
-- Faction agents (leaders, admirals, governors)
CREATE TABLE faction_agents (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  title TEXT DEFAULT '',
  faction_id TEXT NOT NULL,
  role TEXT NOT NULL,  -- admiral, governor, director, general, spymaster
  aggression REAL DEFAULT 0.5,
  caution REAL DEFAULT 0.5,
  competence REAL DEFAULT 0.5,
  loyalty REAL DEFAULT 0.8,
  ambition REAL DEFAULT 0.3,
  corruption REAL DEFAULT 0.1,
  assignment_type TEXT DEFAULT '',  -- fleet_command, system_governor, etc
  assignment_target TEXT DEFAULT '',
  battles_won INTEGER DEFAULT 0,
  battles_lost INTEGER DEFAULT 0,
  reputation REAL DEFAULT 0.5,
  alive INTEGER DEFAULT 1
);

-- Faction strategic state (evolves over time)
CREATE TABLE faction_state (
  faction_id TEXT PRIMARY KEY,
  leader_id TEXT,
  aggression REAL DEFAULT 0.5,
  expansion_drive REAL DEFAULT 0.5,
  economic_focus REAL DEFAULT 0.5,
  diplomacy_openness REAL DEFAULT 0.5,
  treasury REAL DEFAULT 10000,
  priorities TEXT DEFAULT '[]',  -- JSON array of current goals
  relationships TEXT DEFAULT '{}',  -- JSON {faction_id: standing}
  last_decision_tick INTEGER DEFAULT 0
);

-- Historical events (faction memory)
CREATE TABLE faction_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tick INTEGER,
  faction_id TEXT,
  event_type TEXT,  -- war_declared, system_lost, system_gained, agent_defected, etc
  target TEXT,
  details TEXT
);
```

## Faction Personalities

| Faction | Government | Leader Archetype | Core Drive |
|---------|-----------|-----------------|------------|
| Terran Federation | Republic (senate) | Cautious diplomat | Order, stability, navy supremacy |
| Nexus Collective | Technocracy (council) | Visionary scientist | Innovation, expansion through knowledge |
| Merchants Guild | Oligarchy (trade council) | Calculating profiteer | Profit, trade route control, monopoly |
| Frontier Alliance | Confederation (elected leaders) | Populist freedom-fighter | Self-governance, resist centralization |
| Iron Compact | Military junta (supreme commander) | Aggressive warmonger | Territorial expansion, military might |
| The Corsairs | Anarchy (strongest leads) | Opportunistic raider | Chaos, profit through disruption |

## Decision Frequency

- **Faction posture reassessment**: Every 1000 ticks (~17 min at 1x)
- **Strategic orders issued**: Every 200 ticks (~3 min)
- **Agent actions**: Every 50 ticks (~50 sec)
- **Tactical decisions**: Every tick (handled by existing workers)
