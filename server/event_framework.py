"""Structured event framework: faction-specific event pools, chains, agent interactions.

Event model:
- category: economic, military, political, social, disaster, discovery
- severity: 1 (minor local), 2 (regional), 3 (faction-wide), 4 (galaxy-shaking)
- effects: JSON array of {type, target, value} dicts
- chain_id: links sequential events (cause -> consequence)

Replaces the old EventGeneratorWorker with richer, agent-driven events.
"""
import random
import json
import uuid


# Severity levels
MINOR = 1      # local color, no real effect
NOTABLE = 2    # regional, minor effects
MAJOR = 3      # faction-wide, real gameplay impact
CRITICAL = 4   # galaxy-shaking, chain-starting

CATEGORIES = ('economic', 'military', 'political', 'social', 'disaster', 'discovery')


class StructuredEvent:
    """A single structured event."""
    __slots__ = ('tick', 'category', 'severity', 'faction_id', 'system_id',
                 'agent_id', 'title', 'detail', 'effects', 'chain_id', 'chain_step')

    def __init__(self, tick, category, severity, title, detail='',
                 faction_id='', system_id='', agent_id='',
                 effects=None, chain_id='', chain_step=0):
        self.tick = tick
        self.category = category
        self.severity = severity
        self.faction_id = faction_id
        self.system_id = system_id
        self.agent_id = agent_id
        self.title = title
        self.detail = detail
        self.effects = effects or []
        self.chain_id = chain_id
        self.chain_step = chain_step

    def to_dict(self):
        return {
            'tick': self.tick, 'category': self.category, 'severity': self.severity,
            'faction_id': self.faction_id, 'system_id': self.system_id,
            'agent_id': self.agent_id, 'title': self.title, 'detail': self.detail,
            'effects': json.dumps(self.effects), 'chain_id': self.chain_id,
            'chain_step': self.chain_step,
        }

    @property
    def news_msg(self):
        """Generate a NEWS: prefixed string for the existing ticker."""
        prefix = {1: '', 2: 'REGIONAL: ', 3: 'BREAKING: ', 4: 'URGENT: '}
        return f"NEWS: {prefix.get(self.severity, '')}{self.title}"


def new_chain_id():
    return uuid.uuid4().hex[:12]


# ─── FACTION-SPECIFIC EVENT POOLS ───────────────────────────────────────────

# Each pool entry: (weight, severity, generator_name)
# Generators are methods on FactionEventPool that take (tick, faction_id, agents, systems, stations)

TERRAN_FED_EVENTS = [
    (15, MINOR, 'senate_debate'),
    (10, NOTABLE, 'admiralty_order'),
    (8, NOTABLE, 'frontier_patrol'),
    (5, MAJOR, 'senate_vote'),
    (3, MAJOR, 'admiralty_crisis'),
    (2, CRITICAL, 'emergency_powers'),
    (10, MINOR, 'academy_graduation'),
    (8, MINOR, 'fleet_exercise'),
    (5, NOTABLE, 'corruption_scandal'),
]

SCIENCE_COLLECTIVE_EVENTS = [
    (15, MINOR, 'research_paper'),
    (10, NOTABLE, 'breakthrough'),
    (8, NOTABLE, 'experiment_failure'),
    (5, MAJOR, 'archon_decree'),
    (3, MAJOR, 'ethics_violation'),
    (2, CRITICAL, 'gate_anomaly'),
    (10, MINOR, 'convergence_talk'),
    (8, MINOR, 'lab_accident'),
    (5, NOTABLE, 'brain_drain'),
]

MERCHANTS_GUILD_EVENTS = [
    (15, MINOR, 'contract_dispute'),
    (10, NOTABLE, 'hostile_takeover'),
    (8, NOTABLE, 'price_manipulation'),
    (5, MAJOR, 'guild_election'),
    (3, MAJOR, 'embargo'),
    (2, CRITICAL, 'market_collapse'),
    (10, MINOR, 'trade_delegation'),
    (8, MINOR, 'insurance_claim'),
    (5, NOTABLE, 'labor_strike'),
]

FREE_STATES_EVENTS = [
    (15, MINOR, 'militia_drill'),
    (10, NOTABLE, 'assembly_dispute'),
    (8, NOTABLE, 'pirate_sighting'),
    (5, MAJOR, 'system_referendum'),
    (3, MAJOR, 'secession_threat'),
    (2, CRITICAL, 'confederation_crisis'),
    (10, MINOR, 'harvest_festival'),
    (8, MINOR, 'colonist_arrival'),
    (5, NOTABLE, 'border_raid'),
]

IRON_COMPACT_EVENTS = [
    (15, MINOR, 'production_quota'),
    (10, NOTABLE, 'war_council'),
    (8, NOTABLE, 'defection'),
    (5, MAJOR, 'marshal_decree'),
    (3, MAJOR, 'succession_rumor'),
    (2, CRITICAL, 'coup_attempt'),
    (10, MINOR, 'founding_day'),
    (8, MINOR, 'conscription_wave'),
    (5, NOTABLE, 'purge'),
]

CORSAIR_EVENTS = [
    (15, MINOR, 'turf_dispute'),
    (10, NOTABLE, 'raid_planning'),
    (8, NOTABLE, 'fence_betrayal'),
    (5, MAJOR, 'captain_duel'),
    (3, MAJOR, 'fleet_mutiny'),
    (2, CRITICAL, 'dread_lord_challenge'),
    (10, MINOR, 'black_market_deal'),
    (8, MINOR, 'crew_recruitment'),
    (5, NOTABLE, 'bounty_posted'),
]

FACTION_POOLS = {
    'terran_fed': TERRAN_FED_EVENTS,
    'science_collective': SCIENCE_COLLECTIVE_EVENTS,
    'merchants_guild': MERCHANTS_GUILD_EVENTS,
    'free_states': FREE_STATES_EVENTS,
    'iron_compact': IRON_COMPACT_EVENTS,
    'corsairs': CORSAIR_EVENTS,
}

# ─── CROSS-FACTION EVENTS (can involve any faction) ─────────────────────────

CROSS_FACTION_EVENTS = [
    (10, NOTABLE, 'diplomatic_incident'),
    (8, NOTABLE, 'trade_dispute'),
    (5, MAJOR, 'border_skirmish'),
    (3, MAJOR, 'alliance_proposal'),
    (2, CRITICAL, 'war_declaration'),
    (8, MINOR, 'refugee_wave'),
    (5, NOTABLE, 'spy_caught'),
    (3, NOTABLE, 'assassination_attempt'),
]



# ─── EVENT GENERATOR CLASS ──────────────────────────────────────────────────

class FactionEventGenerator:
    """Generates structured events from faction-specific pools.
    
    Usage:
        gen = FactionEventGenerator()
        events = gen.generate_tick_events(tick, agents, universe_data)
    """

    def __init__(self):
        self.active_chains = {}  # chain_id -> {faction, step, next_tick, template}
        self.pending_followups = []  # events scheduled for future ticks

    def generate_tick_events(self, tick, agents_by_faction, systems_by_faction, stations_by_faction):
        """Generate 1-3 events per cycle. Returns list of StructuredEvent."""
        events = []

        # Check pending chain followups
        for followup in list(self.pending_followups):
            if tick >= followup['tick']:
                events.append(followup['event'])
                self.pending_followups.remove(followup)

        # Roll faction-specific event (pick a random faction)
        faction_id = random.choice(list(FACTION_POOLS.keys()))
        pool = FACTION_POOLS[faction_id]
        agents = agents_by_faction.get(faction_id, [])
        systems = systems_by_faction.get(faction_id, [])
        stations = stations_by_faction.get(faction_id, [])

        weights = [e[0] for e in pool]
        chosen = random.choices(pool, weights=weights, k=1)[0]
        handler = getattr(self, f'_evt_{chosen[2]}', None)
        if handler:
            evt = handler(tick, faction_id, agents, systems, stations)
            if evt:
                events.append(evt)

        # 30% chance of a second event (cross-faction)
        if random.random() < 0.3:
            weights = [e[0] for e in CROSS_FACTION_EVENTS]
            chosen = random.choices(CROSS_FACTION_EVENTS, weights=weights, k=1)[0]
            handler = getattr(self, f'_evt_{chosen[2]}', None)
            if handler:
                fids = list(FACTION_POOLS.keys())
                evt = handler(tick, random.choice(fids), agents_by_faction, systems_by_faction, stations_by_faction)
                if evt:
                    events.append(evt)

        return events

    def _pick_agent(self, agents, roles=None):
        """Pick a random living agent, optionally filtered by role."""
        pool = [a for a in agents if a.get('alive', 1)]
        if roles:
            pool = [a for a in pool if a.get('role') in roles]
        return random.choice(pool) if pool else None

    def _pick_system(self, systems):
        return random.choice(systems) if systems else None

    def _schedule_followup(self, tick_delay, event):
        """Schedule a chain followup event for a future tick."""
        self.pending_followups.append({'tick': event.tick + tick_delay, 'event': event})


    # ─── TERRAN FEDERATION EVENTS ───────────────────────────────────────────

    def _evt_senate_debate(self, tick, fid, agents, systems, stations):
        agent = self._pick_agent(agents, ['governor', 'director', 'diplomat'])
        topics = ['military spending', 'frontier defense', 'trade regulations', 'immigration policy', 'tax reform']
        topic = random.choice(topics)
        name = agent['name'] if agent else 'Senator'
        return StructuredEvent(tick, 'political', MINOR, f"{name} introduces {topic} bill in Senate",
            detail=f"Debate expected to last several sessions. Opposition forming.",
            faction_id=fid, agent_id=agent['id'] if agent else '')

    def _evt_admiralty_order(self, tick, fid, agents, systems, stations):
        agent = self._pick_agent(agents, ['admiral', 'fleet_captain', 'leader'])
        sys = self._pick_system(systems)
        name = agent['name'] if agent else 'Admiralty'
        sys_name = sys[1] if sys else 'frontier sector'
        return StructuredEvent(tick, 'military', NOTABLE, f"{name} orders fleet redeployment to {sys_name}",
            detail=f"Naval assets repositioning in response to increased threat assessment.",
            faction_id=fid, system_id=sys[0] if sys else '', agent_id=agent['id'] if agent else '',
            effects=[{'type': 'fleet_move', 'target': sys[0] if sys else '', 'value': 1}])

    def _evt_frontier_patrol(self, tick, fid, agents, systems, stations):
        agent = self._pick_agent(agents, ['fleet_captain'])
        sys = self._pick_system(systems)
        name = agent['name'] if agent else 'Patrol squadron'
        return StructuredEvent(tick, 'military', NOTABLE, f"Captain {name} reports hostile contacts near {sys[1] if sys else 'border'}",
            faction_id=fid, system_id=sys[0] if sys else '', agent_id=agent['id'] if agent else '')

    def _evt_senate_vote(self, tick, fid, agents, systems, stations):
        agent = self._pick_agent(agents, ['leader', 'governor'])
        outcomes = [
            ('War Powers Extension Act passes narrowly', [{'type': 'aggression_boost', 'value': 0.05}]),
            ('Defense Budget Increase approved', [{'type': 'military_spending', 'value': 1.2}]),
            ('Trade Embargo Proposal defeated', []),
            ('Frontier Development Fund established', [{'type': 'expansion_boost', 'value': 0.1}]),
        ]
        outcome, effects = random.choice(outcomes)
        return StructuredEvent(tick, 'political', MAJOR, outcome,
            detail=f"Senate vote concluded after weeks of debate.",
            faction_id=fid, agent_id=agent['id'] if agent else '', effects=effects)

    def _evt_admiralty_crisis(self, tick, fid, agents, systems, stations):
        agent = self._pick_agent(agents, ['admiral'])
        chain_id = new_chain_id()
        name = agent['name'] if agent else 'Senior Admiral'
        evt = StructuredEvent(tick, 'political', MAJOR, f"Admiral {name} publicly challenges Admiralty policy",
            detail="Internal rift in Federation command structure threatens unity.",
            faction_id=fid, agent_id=agent['id'] if agent else '', chain_id=chain_id, chain_step=1)
        # Schedule followup
        followup = StructuredEvent(tick + random.randint(100, 300), 'political', NOTABLE,
            f"Admiral {name} reassigned to frontier post after dispute",
            faction_id=fid, agent_id=agent['id'] if agent else '', chain_id=chain_id, chain_step=2)
        self._schedule_followup(random.randint(100, 300), followup)
        return evt

    def _evt_emergency_powers(self, tick, fid, agents, systems, stations):
        agent = self._pick_agent(agents, ['leader'])
        name = agent['name'] if agent else 'High Admiral'
        return StructuredEvent(tick, 'political', CRITICAL, f"{name} invokes Emergency Powers Act",
            detail="Senate suspended. Military assumes direct control of civilian infrastructure.",
            faction_id=fid, agent_id=agent['id'] if agent else '',
            effects=[{'type': 'aggression_boost', 'value': 0.15}, {'type': 'production_boost', 'value': 1.3}])

    def _evt_academy_graduation(self, tick, fid, agents, systems, stations):
        count = random.randint(200, 500)
        return StructuredEvent(tick, 'social', MINOR, f"Federation Academy graduates {count} new officers",
            detail="Largest class in a decade assigned to active duty.", faction_id=fid)

    def _evt_fleet_exercise(self, tick, fid, agents, systems, stations):
        agent = self._pick_agent(agents, ['admiral', 'fleet_captain'])
        name = agent['name'] if agent else 'Fleet Command'
        return StructuredEvent(tick, 'military', MINOR, f"{name} conducts live-fire exercises near border",
            faction_id=fid, agent_id=agent['id'] if agent else '')

    def _evt_corruption_scandal(self, tick, fid, agents, systems, stations):
        agent = self._pick_agent(agents, ['director', 'governor', 'merchant_lord'])
        name = agent['name'] if agent else 'Senior official'
        return StructuredEvent(tick, 'political', NOTABLE, f"{name} implicated in procurement scandal",
            detail="Internal Affairs investigating misuse of defense contracts.",
            faction_id=fid, agent_id=agent['id'] if agent else '')


    # ─── NEXUS COLLECTIVE EVENTS ────────────────────────────────────────────

    def _evt_research_paper(self, tick, fid, agents, systems, stations):
        agent = self._pick_agent(agents, ['director', 'station_commander', 'factory_overseer'])
        fields = ['quantum entanglement', 'gate harmonics', 'shield resonance', 'neural mapping', 'dark matter']
        return StructuredEvent(tick, 'discovery', MINOR, f"Dr. {agent['name'] if agent else 'Researcher'} publishes paper on {random.choice(fields)}",
            faction_id=fid, agent_id=agent['id'] if agent else '')

    def _evt_breakthrough(self, tick, fid, agents, systems, stations):
        agent = self._pick_agent(agents, ['director', 'leader'])
        techs = ['improved sensor arrays', 'next-gen shield harmonics', 'advanced propulsion theory', 'gate stabilization method']
        tech = random.choice(techs)
        return StructuredEvent(tick, 'discovery', NOTABLE, f"Collective announces breakthrough in {tech}",
            detail=f"Research team led by {agent['name'] if agent else 'senior researcher'}.",
            faction_id=fid, agent_id=agent['id'] if agent else '',
            effects=[{'type': 'tech_advance', 'target': tech, 'value': 1}])

    def _evt_experiment_failure(self, tick, fid, agents, systems, stations):
        agent = self._pick_agent(agents, ['station_commander', 'factory_overseer'])
        sys = self._pick_system(systems)
        return StructuredEvent(tick, 'disaster', NOTABLE, f"Experiment goes critical at {sys[1] if sys else 'research station'}",
            detail=f"Containment breach. {agent['name'] if agent else 'Staff'} reports casualties.",
            faction_id=fid, system_id=sys[0] if sys else '', agent_id=agent['id'] if agent else '',
            effects=[{'type': 'production_halt', 'target': sys[0] if sys else '', 'value': 200}])

    def _evt_archon_decree(self, tick, fid, agents, systems, stations):
        agent = self._pick_agent(agents, ['leader'])
        decrees = ['mandatory research quotas', 'increased defense allocation', 'new ethics guidelines', 'expanded territory claims']
        return StructuredEvent(tick, 'political', MAJOR, f"Archon {agent['name'] if agent else ''} issues decree: {random.choice(decrees)}",
            faction_id=fid, agent_id=agent['id'] if agent else '')

    def _evt_ethics_violation(self, tick, fid, agents, systems, stations):
        agent = self._pick_agent(agents, ['director', 'station_commander'])
        return StructuredEvent(tick, 'political', MAJOR, f"{agent['name'] if agent else 'Senior researcher'} censured for unauthorized experiments",
            detail="Ethics Council convenes emergency session.",
            faction_id=fid, agent_id=agent['id'] if agent else '')

    def _evt_gate_anomaly(self, tick, fid, agents, systems, stations):
        sys = self._pick_system(systems)
        chain_id = new_chain_id()
        evt = StructuredEvent(tick, 'discovery', CRITICAL, f"Jump gate anomaly detected in {sys[1] if sys else 'deep space'}",
            detail="Readings unlike anything since the Isolation Wars. All research assets mobilizing.",
            faction_id=fid, system_id=sys[0] if sys else '', chain_id=chain_id, chain_step=1)
        followup = StructuredEvent(tick + random.randint(200, 500), 'discovery', MAJOR,
            f"Gate anomaly in {sys[1] if sys else 'deep space'} stabilizes - data being analyzed",
            faction_id=fid, system_id=sys[0] if sys else '', chain_id=chain_id, chain_step=2)
        self._schedule_followup(random.randint(200, 500), followup)
        return evt

    def _evt_convergence_talk(self, tick, fid, agents, systems, stations):
        agent = self._pick_agent(agents)
        return StructuredEvent(tick, 'social', MINOR, f"{agent['name'] if agent else 'Researcher'} presents at annual Convergence",
            faction_id=fid, agent_id=agent['id'] if agent else '')

    def _evt_lab_accident(self, tick, fid, agents, systems, stations):
        sys = self._pick_system(systems)
        return StructuredEvent(tick, 'disaster', MINOR, f"Minor lab accident at {sys[1] if sys else 'station'} - no casualties",
            faction_id=fid, system_id=sys[0] if sys else '')

    def _evt_brain_drain(self, tick, fid, agents, systems, stations):
        agent = self._pick_agent(agents, ['director', 'factory_overseer'])
        return StructuredEvent(tick, 'economic', NOTABLE, f"{agent['name'] if agent else 'Researcher'} defects to Merchants Guild for private sector salary",
            faction_id=fid, agent_id=agent['id'] if agent else '')

    # ─── MERCHANTS GUILD EVENTS ─────────────────────────────────────────────

    def _evt_contract_dispute(self, tick, fid, agents, systems, stations):
        agent = self._pick_agent(agents, ['merchant_lord', 'director'])
        return StructuredEvent(tick, 'economic', MINOR, f"{agent['name'] if agent else 'Trader'} files arbitration over broken contract",
            faction_id=fid, agent_id=agent['id'] if agent else '')

    def _evt_hostile_takeover(self, tick, fid, agents, systems, stations):
        agent = self._pick_agent(agents, ['merchant_lord', 'director'])
        target = self._pick_agent(agents, ['merchant_lord', 'station_commander'])
        if not agent or not target or agent['id'] == target['id']:
            return None
        return StructuredEvent(tick, 'economic', NOTABLE, f"{agent['name']} launches hostile takeover of {target['name']}'s holdings",
            detail="Board of Directors watching closely.",
            faction_id=fid, agent_id=agent['id'],
            effects=[{'type': 'wealth_transfer', 'from': target['id'], 'to': agent['id'], 'value': 100}])

    def _evt_price_manipulation(self, tick, fid, agents, systems, stations):
        agent = self._pick_agent(agents, ['merchant_lord', 'smuggler'])
        commodities = ['fuel cells', 'refined titanium', 'weapons components', 'medical supplies']
        return StructuredEvent(tick, 'economic', NOTABLE, f"Trade Wardens investigate {agent['name'] if agent else 'unknown trader'} for {random.choice(commodities)} price fixing",
            faction_id=fid, agent_id=agent['id'] if agent else '')

    def _evt_guild_election(self, tick, fid, agents, systems, stations):
        agents_pool = [a for a in agents if a.get('role') in ('merchant_lord', 'director', 'leader')]
        if len(agents_pool) < 2:
            return None
        candidates = random.sample(agents_pool, 2)
        return StructuredEvent(tick, 'political', MAJOR, f"Guild Board election: {candidates[0]['name']} vs {candidates[1]['name']}",
            detail="Largest shareholders positioning their votes.",
            faction_id=fid, agent_id=candidates[0]['id'])

    def _evt_embargo(self, tick, fid, agents, systems, stations):
        targets = ['Terran Federation', 'Iron Compact', 'Frontier Alliance']
        target = random.choice(targets)
        return StructuredEvent(tick, 'economic', MAJOR, f"Guild imposes trade embargo on {target}",
            detail="All Guild-affiliated haulers ordered to cease deliveries.",
            faction_id=fid, effects=[{'type': 'embargo', 'target': target, 'value': 500}])

    def _evt_market_collapse(self, tick, fid, agents, systems, stations):
        chain_id = new_chain_id()
        commodities = ['rare earth metals', 'ship components', 'fuel derivatives']
        commodity = random.choice(commodities)
        evt = StructuredEvent(tick, 'economic', CRITICAL, f"{commodity.title()} market collapses - losses in billions",
            detail="Panic selling across all Guild exchanges. Board of Directors in emergency session.",
            faction_id=fid, chain_id=chain_id, chain_step=1,
            effects=[{'type': 'price_crash', 'target': commodity, 'value': 0.5}])
        followup = StructuredEvent(tick + random.randint(100, 300), 'economic', MAJOR,
            f"Guild stabilization fund deployed - {commodity} prices recovering",
            faction_id=fid, chain_id=chain_id, chain_step=2)
        self._schedule_followup(random.randint(100, 300), followup)
        return evt

    def _evt_trade_delegation(self, tick, fid, agents, systems, stations):
        agent = self._pick_agent(agents, ['diplomat', 'merchant_lord'])
        return StructuredEvent(tick, 'social', MINOR, f"{agent['name'] if agent else 'Guild delegation'} arrives for trade negotiations",
            faction_id=fid, agent_id=agent['id'] if agent else '')

    def _evt_insurance_claim(self, tick, fid, agents, systems, stations):
        agent = self._pick_agent(agents, ['fleet_captain', 'merchant_lord'])
        return StructuredEvent(tick, 'economic', MINOR, f"Massive insurance claim filed after {agent['name'] if agent else 'hauler'} loses cargo to pirates",
            faction_id=fid, agent_id=agent['id'] if agent else '')

    def _evt_labor_strike(self, tick, fid, agents, systems, stations):
        sys = self._pick_system(systems)
        return StructuredEvent(tick, 'economic', NOTABLE, f"Dock workers strike at {sys[1] if sys else 'Guild station'} - cargo backlog growing",
            faction_id=fid, system_id=sys[0] if sys else '',
            effects=[{'type': 'production_halt', 'target': sys[0] if sys else '', 'value': 300}])


    # ─── FRONTIER ALLIANCE EVENTS ───────────────────────────────────────────

    def _evt_militia_drill(self, tick, fid, agents, systems, stations):
        agent = self._pick_agent(agents, ['fleet_captain', 'mercenary_leader'])
        sys = self._pick_system(systems)
        return StructuredEvent(tick, 'military', MINOR, f"Militia drill in {sys[1] if sys else 'outer system'} led by {agent['name'] if agent else 'local commander'}",
            faction_id=fid, system_id=sys[0] if sys else '', agent_id=agent['id'] if agent else '')

    def _evt_assembly_dispute(self, tick, fid, agents, systems, stations):
        agent = self._pick_agent(agents, ['governor', 'leader', 'diplomat'])
        issues = ['collective defense funding', 'inter-system trade tariffs', 'refugee policy', 'Guild dependence']
        return StructuredEvent(tick, 'political', NOTABLE, f"Assembly deadlocked over {random.choice(issues)}",
            detail=f"{agent['name'] if agent else 'Multiple delegates'} storms out of session.",
            faction_id=fid, agent_id=agent['id'] if agent else '')

    def _evt_pirate_sighting(self, tick, fid, agents, systems, stations):
        sys = self._pick_system(systems)
        return StructuredEvent(tick, 'military', NOTABLE, f"Corsair scout ships spotted in {sys[1] if sys else 'Alliance space'}",
            detail="Local militia placed on alert.", faction_id=fid, system_id=sys[0] if sys else '')

    def _evt_system_referendum(self, tick, fid, agents, systems, stations):
        sys = self._pick_system(systems)
        issues = ['join collective defense pact', 'increase militia funding', 'allow Guild exclusive contracts', 'restrict immigration']
        return StructuredEvent(tick, 'political', MAJOR, f"{sys[1] if sys else 'Border system'} holds referendum on {random.choice(issues)}",
            faction_id=fid, system_id=sys[0] if sys else '')

    def _evt_secession_threat(self, tick, fid, agents, systems, stations):
        sys = self._pick_system(systems)
        agent = self._pick_agent(agents, ['governor', 'station_commander'])
        chain_id = new_chain_id()
        evt = StructuredEvent(tick, 'political', MAJOR, f"{sys[1] if sys else 'Rim system'} threatens to leave Alliance",
            detail=f"{agent['name'] if agent else 'Local leader'} claims Alliance provides nothing in return for dues.",
            faction_id=fid, system_id=sys[0] if sys else '', agent_id=agent['id'] if agent else '',
            chain_id=chain_id, chain_step=1)
        followup = StructuredEvent(tick + random.randint(200, 400), 'political', NOTABLE,
            f"Crisis averted: {sys[1] if sys else 'system'} agrees to stay after concessions",
            faction_id=fid, system_id=sys[0] if sys else '', chain_id=chain_id, chain_step=2)
        self._schedule_followup(random.randint(200, 400), followup)
        return evt

    def _evt_confederation_crisis(self, tick, fid, agents, systems, stations):
        agent = self._pick_agent(agents, ['leader'])
        return StructuredEvent(tick, 'political', CRITICAL, f"President {agent['name'] if agent else ''} calls emergency Assembly session",
            detail="Multiple systems refusing to honor collective defense obligations. Alliance may fracture.",
            faction_id=fid, agent_id=agent['id'] if agent else '',
            effects=[{'type': 'stability_loss', 'value': 0.2}])

    def _evt_harvest_festival(self, tick, fid, agents, systems, stations):
        sys = self._pick_system(systems)
        return StructuredEvent(tick, 'social', MINOR, f"Harvest festival celebrations in {sys[1] if sys else 'colony'}",
            faction_id=fid, system_id=sys[0] if sys else '')

    def _evt_colonist_arrival(self, tick, fid, agents, systems, stations):
        sys = self._pick_system(systems)
        count = random.randint(500, 5000)
        return StructuredEvent(tick, 'social', MINOR, f"{count:,} new colonists arrive at {sys[1] if sys else 'frontier world'}",
            faction_id=fid, system_id=sys[0] if sys else '')

    def _evt_border_raid(self, tick, fid, agents, systems, stations):
        sys = self._pick_system(systems)
        return StructuredEvent(tick, 'military', NOTABLE, f"Iron Compact raiders hit mining operation in {sys[1] if sys else 'border system'}",
            detail="Militia responding but outnumbered.", faction_id=fid, system_id=sys[0] if sys else '')

    # ─── IRON COMPACT EVENTS ───────────────────────────────────────────────

    def _evt_production_quota(self, tick, fid, agents, systems, stations):
        agent = self._pick_agent(agents, ['factory_overseer', 'station_commander'])
        return StructuredEvent(tick, 'economic', MINOR, f"{agent['name'] if agent else 'Sector Commander'} announces new production quotas exceeded by 12%",
            faction_id=fid, agent_id=agent['id'] if agent else '')

    def _evt_war_council(self, tick, fid, agents, systems, stations):
        agent = self._pick_agent(agents, ['leader', 'admiral'])
        targets = ['Nexus Collective border', 'Frontier Alliance southern systems', 'contested Deklein region']
        return StructuredEvent(tick, 'military', NOTABLE, f"War Council convenes to discuss operations against {random.choice(targets)}",
            detail=f"Marshal {agent['name'] if agent else 'Novak'} presiding.",
            faction_id=fid, agent_id=agent['id'] if agent else '')

    def _evt_defection(self, tick, fid, agents, systems, stations):
        agent = self._pick_agent(agents, ['fleet_captain', 'factory_overseer', 'spy'])
        if not agent:
            return None
        destinations = ['Frontier Alliance', 'Merchants Guild', 'neutral space']
        return StructuredEvent(tick, 'political', NOTABLE, f"{agent['name']} defects to {random.choice(destinations)}",
            detail="Security forces ordered to intercept. Spymaster investigating breach.",
            faction_id=fid, agent_id=agent['id'],
            effects=[{'type': 'agent_lost', 'target': agent['id'], 'value': 1}])

    def _evt_marshal_decree(self, tick, fid, agents, systems, stations):
        agent = self._pick_agent(agents, ['leader'])
        decrees = ['total war mobilization', 'doubled production shifts', 'expanded conscription', 'resource seizure authorization']
        return StructuredEvent(tick, 'political', MAJOR, f"Supreme Marshal {agent['name'] if agent else 'Novak'} decrees {random.choice(decrees)}",
            faction_id=fid, agent_id=agent['id'] if agent else '',
            effects=[{'type': 'production_boost', 'value': 1.2}])

    def _evt_succession_rumor(self, tick, fid, agents, systems, stations):
        agents_pool = [a for a in agents if a.get('role') in ('admiral', 'general', 'fleet_captain')]
        if not agents_pool:
            return None
        contender = random.choice(agents_pool)
        return StructuredEvent(tick, 'political', MAJOR, f"Rumors: {contender['name']} positioning for succession",
            detail="War Council members quietly choosing sides.",
            faction_id=fid, agent_id=contender['id'])

    def _evt_coup_attempt(self, tick, fid, agents, systems, stations):
        agent = self._pick_agent(agents, ['admiral', 'general'])
        chain_id = new_chain_id()
        name = agent['name'] if agent else 'Senior Commander'
        evt = StructuredEvent(tick, 'political', CRITICAL, f"COUP: {name} attempts to seize power",
            detail="Loyalist and rebel forces clash. Communications jammed.",
            faction_id=fid, agent_id=agent['id'] if agent else '', chain_id=chain_id, chain_step=1,
            effects=[{'type': 'stability_loss', 'value': 0.4}])
        # Coups rarely succeed -- 15-20% chance based on agent's competence/ambition
        coup_chance = 0.1 + (agent.get('competence', 0.5) * 0.1 if agent else 0)
        outcome = 'succeeds' if random.random() < coup_chance else 'fails'
        if outcome == 'fails':
            followup = StructuredEvent(tick + random.randint(50, 150), 'political', MAJOR,
                f"Coup crushed: {name} executed for treason",
                faction_id=fid, agent_id=agent['id'] if agent else '', chain_id=chain_id, chain_step=2,
                effects=[{'type': 'agent_killed', 'target': agent['id'] if agent else '', 'value': 1}])
        else:
            followup = StructuredEvent(tick + random.randint(50, 150), 'political', CRITICAL,
                f"{name} seizes control - new Supreme Marshal declared",
                faction_id=fid, agent_id=agent['id'] if agent else '', chain_id=chain_id, chain_step=2,
                effects=[{'type': 'leader_change', 'target': agent['id'] if agent else '', 'value': 1}])
        self._schedule_followup(random.randint(50, 150), followup)
        return evt

    def _evt_founding_day(self, tick, fid, agents, systems, stations):
        return StructuredEvent(tick, 'social', MINOR, "Iron Compact celebrates Founding Day - military parades across all systems",
            faction_id=fid)

    def _evt_conscription_wave(self, tick, fid, agents, systems, stations):
        count = random.randint(10000, 50000)
        return StructuredEvent(tick, 'military', MINOR, f"New conscription wave: {count:,} citizens report for service",
            faction_id=fid)

    def _evt_purge(self, tick, fid, agents, systems, stations):
        agent = self._pick_agent(agents, ['spy', 'director', 'governor'])
        return StructuredEvent(tick, 'political', NOTABLE, f"Loyalty purge: {agent['name'] if agent else 'Officials'} detained for \"insufficient dedication\"",
            faction_id=fid, agent_id=agent['id'] if agent else '')


    # ─── CORSAIR EVENTS ─────────────────────────────────────────────────────

    def _evt_turf_dispute(self, tick, fid, agents, systems, stations):
        a1 = self._pick_agent(agents, ['fleet_captain', 'mercenary_leader'])
        a2 = self._pick_agent(agents, ['fleet_captain', 'mercenary_leader'])
        if not a1 or not a2 or a1['id'] == a2['id']:
            return StructuredEvent(tick, 'military', MINOR, "Two pirate crews clash over salvage rights",
                faction_id=fid)
        return StructuredEvent(tick, 'military', MINOR, f"{a1['name']} and {a2['name']} clash over territory",
            faction_id=fid, agent_id=a1['id'])

    def _evt_raid_planning(self, tick, fid, agents, systems, stations):
        agent = self._pick_agent(agents, ['fleet_captain', 'leader'])
        targets = ['Guild convoy route', 'Federation supply line', 'mining colony', 'trade hub']
        return StructuredEvent(tick, 'military', NOTABLE, f"{agent['name'] if agent else 'Fleet Captain'} assembles raiders for {random.choice(targets)} strike",
            faction_id=fid, agent_id=agent['id'] if agent else '')

    def _evt_fence_betrayal(self, tick, fid, agents, systems, stations):
        agent = self._pick_agent(agents, ['smuggler', 'merchant_lord'])
        return StructuredEvent(tick, 'economic', NOTABLE, f"Fence network betrayal: {agent['name'] if agent else 'Broker'} sells crew locations to authorities",
            detail="Multiple captains calling for blood.", faction_id=fid, agent_id=agent['id'] if agent else '')

    def _evt_captain_duel(self, tick, fid, agents, systems, stations):
        a1 = self._pick_agent(agents, ['fleet_captain', 'mercenary_leader'])
        a2 = self._pick_agent(agents, ['fleet_captain', 'mercenary_leader'])
        if not a1 or not a2 or a1['id'] == a2['id']:
            return None
        winner, loser = (a1, a2) if random.random() < (0.3 + a1.get('aggression',0.5)*0.4) else (a2, a1)
        return StructuredEvent(tick, 'military', MAJOR, f"Captain's Duel: {winner['name']} defeats {loser['name']}",
            detail=f"{loser['name']}'s crew absorbed into {winner['name']}'s fleet.",
            faction_id=fid, agent_id=winner['id'],
            effects=[{'type': 'agent_killed', 'target': loser['id'], 'value': 1}])

    def _evt_fleet_mutiny(self, tick, fid, agents, systems, stations):
        agent = self._pick_agent(agents, ['fleet_captain'])
        if not agent:
            return None
        return StructuredEvent(tick, 'military', MAJOR, f"Mutiny aboard {agent['name']}'s flagship - crew seizes control",
            detail="Captain set adrift. New leadership forming.",
            faction_id=fid, agent_id=agent['id'],
            effects=[{'type': 'agent_lost', 'target': agent['id'], 'value': 1}])

    def _evt_dread_lord_challenge(self, tick, fid, agents, systems, stations):
        challenger = self._pick_agent(agents, ['fleet_captain', 'mercenary_leader'])
        leader = self._pick_agent(agents, ['leader'])
        if not challenger or not leader:
            return None
        chain_id = new_chain_id()
        c_name = challenger['name']
        l_name = leader['name']
        evt = StructuredEvent(tick, 'political', CRITICAL, f"{c_name} challenges {l_name} for the throne",
            detail="All Fleet Captains called to witness. No quarter asked or given.",
            faction_id=fid, agent_id=challenger['id'], chain_id=chain_id, chain_step=1)
        # Odds based on traits: leader has massive advantage (incumbency + reputation)
        # Challenger needs to be significantly better to win (~15-25% base chance)
        leader_power = 0.6 + leader.get('aggression', 0.5) * 0.2 + leader.get('competence', 0.5) * 0.2
        challenger_power = challenger.get('aggression', 0.5) * 0.3 + challenger.get('competence', 0.5) * 0.2
        challenger_wins = random.random() < (challenger_power / (leader_power + challenger_power)) * 0.6
        if challenger_wins:
            winner, loser = challenger, leader
        else:
            winner, loser = leader, challenger
        followup_tick = tick + random.randint(30, 100)
        followup = StructuredEvent(followup_tick, 'political', CRITICAL,
            f"Challenge resolved: {winner['name']} emerges victorious. {loser['name']} is dead.",
            faction_id=fid, agent_id=winner['id'], chain_id=chain_id, chain_step=2,
            effects=[
                {'type': 'agent_killed', 'target': loser['id'], 'value': 1},
                {'type': 'leader_change', 'target': winner['id'], 'value': 1},
            ])
        self._schedule_followup(followup_tick - tick, followup)
        return evt

    def _evt_black_market_deal(self, tick, fid, agents, systems, stations):
        agent = self._pick_agent(agents, ['smuggler', 'merchant_lord'])
        goods = ['stolen weapons', 'military intel', 'contraband stimulants', 'forged credentials']
        return StructuredEvent(tick, 'economic', MINOR, f"{agent['name'] if agent else 'Fence'} moves shipment of {random.choice(goods)}",
            faction_id=fid, agent_id=agent['id'] if agent else '')

    def _evt_crew_recruitment(self, tick, fid, agents, systems, stations):
        agent = self._pick_agent(agents, ['fleet_captain'])
        return StructuredEvent(tick, 'social', MINOR, f"{agent['name'] if agent else 'Captain'} recruiting at freeport - offering double shares",
            faction_id=fid, agent_id=agent['id'] if agent else '')

    def _evt_bounty_posted(self, tick, fid, agents, systems, stations):
        agent = self._pick_agent(agents, ['fleet_captain', 'leader', 'mercenary_leader'])
        bounty = random.randint(5000, 50000)
        return StructuredEvent(tick, 'military', NOTABLE, f"Federation posts {bounty:,} credit bounty on {agent['name'] if agent else 'pirate captain'}",
            faction_id=fid, agent_id=agent['id'] if agent else '')

    # ─── CROSS-FACTION EVENTS ───────────────────────────────────────────────

    def _evt_diplomatic_incident(self, tick, fid, agents_by_faction, systems_by_faction, stations_by_faction):
        fids = [f for f in FACTION_POOLS.keys() if f != 'corsairs']
        f1, f2 = random.sample(fids, 2)
        a1 = self._pick_agent(agents_by_faction.get(f1, []), ['diplomat', 'fleet_captain'])
        names = {'terran_fed': 'Federation', 'science_collective': 'Collective', 'merchants_guild': 'Guild',
                 'free_states': 'Alliance', 'iron_compact': 'Compact', 'corsairs': 'Corsairs'}
        return StructuredEvent(tick, 'political', NOTABLE,
            f"Diplomatic incident between {names[f1]} and {names[f2]}",
            detail=f"{a1['name'] if a1 else 'Official'} expelled from {names[f2]} space.",
            faction_id=f1, agent_id=a1['id'] if a1 else '')

    def _evt_trade_dispute(self, tick, fid, agents_by_faction, systems_by_faction, stations_by_faction):
        fids = list(FACTION_POOLS.keys())
        f1, f2 = random.sample(fids, 2)
        names = {'terran_fed': 'Federation', 'science_collective': 'Collective', 'merchants_guild': 'Guild',
                 'free_states': 'Alliance', 'iron_compact': 'Compact', 'corsairs': 'Corsairs'}
        return StructuredEvent(tick, 'economic', NOTABLE,
            f"Trade dispute: {names[f1]} accuses {names[f2]} of dumping subsidized goods",
            faction_id=f1)

    def _evt_border_skirmish(self, tick, fid, agents_by_faction, systems_by_faction, stations_by_faction):
        fids = [f for f in FACTION_POOLS.keys() if f != 'corsairs']
        f1, f2 = random.sample(fids, 2)
        a1 = self._pick_agent(agents_by_faction.get(f1, []), ['fleet_captain'])
        names = {'terran_fed': 'Federation', 'science_collective': 'Collective', 'merchants_guild': 'Guild',
                 'free_states': 'Alliance', 'iron_compact': 'Compact', 'corsairs': 'Corsairs'}
        return StructuredEvent(tick, 'military', MAJOR,
            f"Border skirmish: {names[f1]} and {names[f2]} forces exchange fire",
            detail=f"Captain {a1['name'] if a1 else 'unknown'} reports engagement. Casualties on both sides.",
            faction_id=f1, agent_id=a1['id'] if a1 else '',
            effects=[{'type': 'relation_damage', 'target': f2, 'value': -0.1}])

    def _evt_alliance_proposal(self, tick, fid, agents_by_faction, systems_by_faction, stations_by_faction):
        fids = [f for f in FACTION_POOLS.keys() if f != 'corsairs']
        f1, f2 = random.sample(fids, 2)
        names = {'terran_fed': 'Federation', 'science_collective': 'Collective', 'merchants_guild': 'Guild',
                 'free_states': 'Alliance', 'iron_compact': 'Compact', 'corsairs': 'Corsairs'}
        return StructuredEvent(tick, 'political', MAJOR,
            f"{names[f1]} proposes mutual defense pact with {names[f2]}",
            faction_id=f1)

    def _evt_war_declaration(self, tick, fid, agents_by_faction, systems_by_faction, stations_by_faction):
        fids = list(FACTION_POOLS.keys())
        f1, f2 = random.sample(fids, 2)
        names = {'terran_fed': 'Federation', 'science_collective': 'Collective', 'merchants_guild': 'Guild',
                 'free_states': 'Alliance', 'iron_compact': 'Compact', 'corsairs': 'Corsairs'}
        return StructuredEvent(tick, 'military', CRITICAL,
            f"{names[f1]} declares state of war against {names[f2]}",
            detail="All diplomatic channels severed. Military assets mobilizing.",
            faction_id=f1, effects=[{'type': 'war', 'target': f2, 'value': 1}])

    def _evt_refugee_wave(self, tick, fid, agents_by_faction, systems_by_faction, stations_by_faction):
        fids = list(FACTION_POOLS.keys())
        f1, f2 = random.sample(fids, 2)
        names = {'terran_fed': 'Federation', 'science_collective': 'Collective', 'merchants_guild': 'Guild',
                 'free_states': 'Alliance', 'iron_compact': 'Compact', 'corsairs': 'Corsairs'}
        count = random.randint(1000, 20000)
        return StructuredEvent(tick, 'social', MINOR,
            f"{count:,} refugees flee {names[f1]} space into {names[f2]} territory",
            faction_id=f2)

    def _evt_spy_caught(self, tick, fid, agents_by_faction, systems_by_faction, stations_by_faction):
        fids = [f for f in FACTION_POOLS.keys() if f != 'corsairs']
        f1, f2 = random.sample(fids, 2)
        agent = self._pick_agent(agents_by_faction.get(f1, []), ['spy', 'bounty_hunter'])
        names = {'terran_fed': 'Federation', 'science_collective': 'Collective', 'merchants_guild': 'Guild',
                 'free_states': 'Alliance', 'iron_compact': 'Compact', 'corsairs': 'Corsairs'}
        return StructuredEvent(tick, 'political', NOTABLE,
            f"{names[f2]} counterintelligence captures {names[f1]} operative",
            detail=f"Agent {agent['name'] if agent else 'unknown'} detained. Diplomatic fallout expected.",
            faction_id=f1, agent_id=agent['id'] if agent else '')

    def _evt_assassination_attempt(self, tick, fid, agents_by_faction, systems_by_faction, stations_by_faction):
        fids = list(FACTION_POOLS.keys())
        target_fid = random.choice(fids)
        target = self._pick_agent(agents_by_faction.get(target_fid, []), ['leader', 'admiral', 'governor'])
        if not target:
            return None
        success = random.random() < 0.2
        if success:
            return StructuredEvent(tick, 'political', CRITICAL,
                f"ASSASSINATION: {target['name']} killed by unknown assailant",
                detail="Security forces on highest alert. Suspects from multiple factions.",
                faction_id=target_fid, agent_id=target['id'],
                effects=[{'type': 'agent_killed', 'target': target['id'], 'value': 1}])
        return StructuredEvent(tick, 'political', NOTABLE,
            f"Assassination attempt on {target['name']} foiled",
            detail="Assailant captured. Interrogation underway.",
            faction_id=target_fid, agent_id=target['id'])
