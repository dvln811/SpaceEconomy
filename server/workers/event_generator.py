"""Event Generator worker: creates random galactic events with real effects."""
import random
from server.supervisor import WorkerThread
from server.intents import EventLog, InventoryDelta

# Event templates: (weight, category, generator_function_name)
EVENTS = [
    # Economic
    (15, 'economic', 'ore_discovery'),
    (10, 'economic', 'dock_strike'),
    (8, 'economic', 'trade_boom'),
    (5, 'economic', 'market_crash'),
    # Military
    (12, 'military', 'corsair_raid'),
    (8, 'military', 'border_incident'),
    (5, 'military', 'arms_buildup'),
    # Political
    (8, 'political', 'diplomatic_tension'),
    (5, 'political', 'alliance_shift'),
    # Disaster
    (8, 'disaster', 'asteroid_storm'),
    (6, 'disaster', 'station_malfunction'),
    (4, 'disaster', 'plague_outbreak'),
    # Discovery
    (5, 'discovery', 'tech_breakthrough'),
    (3, 'discovery', 'ancient_artifact'),
]

FACTION_NAMES = {
    'terran_fed': 'Terran Federation', 'science_collective': 'Nexus Collective',
    'merchants_guild': 'Merchants Guild', 'free_states': 'Frontier Alliance',
    'iron_compact': 'Iron Compact', 'corsairs': 'The Corsairs'
}

FACTION_IDS = ['terran_fed', 'science_collective', 'merchants_guild', 'free_states', 'iron_compact', 'corsairs']


class EventGeneratorWorker(WorkerThread):
    def __init__(self):
        super().__init__("event_generator", tick_interval=200)
        self._active_effects = []  # [{tick_expires, effect_type, target, ...}]

    def process(self, tick: int, snapshot):
        universe = snapshot['universe']

        # Expire old effects
        self._expire_effects(tick, universe)

        # Roll 1-2 events per cycle
        num_events = random.randint(1, 2)
        for _ in range(num_events):
            weights = [e[0] for e in EVENTS]
            chosen = random.choices(EVENTS, weights=weights, k=1)[0]
            handler = getattr(self, f'_event_{chosen[2]}', None)
            if handler:
                handler(tick, universe)

    def _expire_effects(self, tick, universe):
        for effect in list(self._active_effects):
            if tick >= effect['tick_expires']:
                self._remove_effect(effect, universe, tick)
                self._active_effects.remove(effect)

    def _remove_effect(self, effect, universe, tick):
        if effect['effect_type'] == 'production_halt':
            # Restore production rate
            sys = universe.get(effect['system_id'])
            if sys:
                for st in sys.stations:
                    if st.name == effect['station_name']:
                        st.production_rate = effect.get('original_rate', 1.0)
                        self.emit(EventLog(tick=tick, msg=f"NEWS: Operations resume at {st.name} after {effect.get('reason','disruption')}"))
                        break
        elif effect['effect_type'] == 'mining_halt':
            # Nothing to restore - mining just resumes naturally
            self.emit(EventLog(tick=tick, msg=f"NEWS: Mining operations resume in {effect.get('system_name','unknown system')} after asteroid storm passes"))

    # ── ECONOMIC EVENTS ──

    def _event_ore_discovery(self, tick, universe):
        # Find a system with mining colonies
        mining_systems = [(sid, sys) for sid, sys in universe.items() if sys.asteroid_fields and sys.stations]
        if not mining_systems:
            return
        sys_id, sys = random.choice(mining_systems)
        ore_types = ['iron_ore', 'copper_ore', 'titanium_ore', 'gold_ore', 'cobalt_ore']
        ore = random.choice(ore_types)
        ore_name = ore.replace('_', ' ').title()
        amount = random.randint(5000, 20000)
        # Add ore to a mining colony in that system
        for st in sys.stations:
            if st.station_type == 'mining_colony':
                st.inventory[ore] = st.inventory.get(ore, 0) + amount
                break
        self.emit(EventLog(tick=tick, msg=f"NEWS: Rich {ore_name} vein discovered in {sys.name} - prospectors report {amount:,} units accessible"))

    def _event_dock_strike(self, tick, universe):
        # Pick a random station and halt production temporarily
        candidates = [(sid, sys, st) for sid, sys in universe.items() for st in sys.stations
                      if st.station_type in ('factory', 'component_works', 'refinery') and st.production_rate > 0]
        if not candidates:
            return
        sys_id, sys, station = random.choice(candidates)
        original_rate = station.production_rate
        station.production_rate = 0.0
        duration = random.randint(300, 800)  # 1-3 days
        self._active_effects.append({
            'tick_expires': tick + duration,
            'effect_type': 'production_halt',
            'system_id': sys_id,
            'station_name': station.name,
            'original_rate': original_rate,
            'reason': 'dock workers strike',
        })
        self.emit(EventLog(tick=tick, msg=f"NEWS: Dock workers strike at {station.name} ({sys.name}) - production halted. Union demands better conditions."))

    def _event_trade_boom(self, tick, universe):
        # Temporarily boost a trade hub's consumption (more demand = higher prices)
        hubs = [(sid, sys, st) for sid, sys in universe.items() for st in sys.stations if st.station_type == 'trade_hub']
        if not hubs:
            return
        sys_id, sys, hub = random.choice(hubs)
        faction = FACTION_NAMES.get(sys.faction, 'Independent')
        self.emit(EventLog(tick=tick, msg=f"NEWS: Trade boom in {sys.name} - {faction} merchants report record demand for consumer goods"))

    def _event_market_crash(self, tick, universe):
        # Dump inventory at a random factory (prices crash locally)
        factories = [(sid, sys, st) for sid, sys in universe.items() for st in sys.stations if st.station_type == 'factory']
        if not factories:
            return
        sys_id, sys, factory = random.choice(factories)
        # Increase inventory (simulates overproduction panic sell)
        for commodity, qty in list(factory.inventory.items())[:5]:
            factory.inventory[commodity] = qty * 1.5
        self.emit(EventLog(tick=tick, msg=f"NEWS: Market panic at {factory.name} - traders dump inventory as prices plummet in {sys.name}"))

    # ── MILITARY EVENTS ──

    def _event_corsair_raid(self, tick, universe):
        # Corsairs hit a random station, steal goods
        targets = [(sid, sys, st) for sid, sys in universe.items() for st in sys.stations
                   if sys.faction and sys.faction != 'corsairs' and st.station_type in ('trade_hub', 'mining_colony')]
        if not targets:
            return
        sys_id, sys, station = random.choice(targets)
        stolen = 0
        for commodity in list(station.inventory.keys())[:3]:
            take = min(station.inventory[commodity] * 0.1, 1000)
            if take > 0:
                station.inventory[commodity] -= take
                stolen += take
        faction = FACTION_NAMES.get(sys.faction, 'Unknown')
        self.emit(EventLog(tick=tick, msg=f"NEWS: Corsair raiders strike {station.name} in {sys.name} - {faction} security forces scrambled. {int(stolen):,} units of cargo seized."))

    def _event_border_incident(self, tick, universe):
        factions = random.sample([f for f in FACTION_IDS if f != 'corsairs'], 2)
        f1 = FACTION_NAMES[factions[0]]
        f2 = FACTION_NAMES[factions[1]]
        incidents = [
            f"Patrol vessels from {f1} and {f2} exchange warning shots at disputed border",
            f"{f1} accuses {f2} of violating territorial space - diplomatic protest filed",
            f"Civilian freighter caught in crossfire between {f1} and {f2} patrols",
        ]
        self.emit(EventLog(tick=tick, msg=f"NEWS: {random.choice(incidents)}"))

    def _event_arms_buildup(self, tick, universe):
        faction = random.choice([f for f in FACTION_IDS if f != 'corsairs'])
        fname = FACTION_NAMES[faction]
        self.emit(EventLog(tick=tick, msg=f"NEWS: Intelligence reports {fname} increasing military production - neighboring factions on alert"))

    # ── POLITICAL EVENTS ──

    def _event_diplomatic_tension(self, tick, universe):
        factions = random.sample([f for f in FACTION_IDS if f != 'corsairs'], 2)
        f1 = FACTION_NAMES[factions[0]]
        f2 = FACTION_NAMES[factions[1]]
        tensions = [
            f"{f1} recalls ambassador from {f2} over trade dispute",
            f"Leaked documents reveal {f2} intelligence operations in {f1} space",
            f"{f1} imposes sanctions on {f2} corporations operating in border systems",
        ]
        self.emit(EventLog(tick=tick, msg=f"NEWS: {random.choice(tensions)}"))

    def _event_alliance_shift(self, tick, universe):
        factions = random.sample([f for f in FACTION_IDS if f != 'corsairs'], 2)
        f1 = FACTION_NAMES[factions[0]]
        f2 = FACTION_NAMES[factions[1]]
        shifts = [
            f"{f1} and {f2} sign mutual defense agreement - regional balance shifts",
            f"{f1} offers economic aid package to {f2} in exchange for military access",
            f"Joint {f1}-{f2} task force announced to combat Corsair threat",
        ]
        self.emit(EventLog(tick=tick, msg=f"NEWS: {random.choice(shifts)}"))

    # ── DISASTER EVENTS ──

    def _event_asteroid_storm(self, tick, universe):
        mining_systems = [(sid, sys) for sid, sys in universe.items() if sys.asteroid_fields]
        if not mining_systems:
            return
        sys_id, sys = random.choice(mining_systems)
        duration = random.randint(200, 500)
        self._active_effects.append({
            'tick_expires': tick + duration,
            'effect_type': 'mining_halt',
            'system_id': sys_id,
            'system_name': sys.name,
        })
        self.emit(EventLog(tick=tick, msg=f"NEWS: Severe asteroid storm in {sys.name} - all mining operations suspended. Estimated duration: {duration*6//60} hours."))

    def _event_station_malfunction(self, tick, universe):
        stations = [(sid, sys, st) for sid, sys in universe.items() for st in sys.stations
                    if st.station_type in ('refinery', 'factory', 'component_works')]
        if not stations:
            return
        sys_id, sys, station = random.choice(stations)
        original_rate = station.production_rate
        station.production_rate = original_rate * 0.3
        duration = random.randint(100, 300)
        self._active_effects.append({
            'tick_expires': tick + duration,
            'effect_type': 'production_halt',
            'system_id': sys_id,
            'station_name': station.name,
            'original_rate': original_rate,
            'reason': 'reactor malfunction',
        })
        self.emit(EventLog(tick=tick, msg=f"NEWS: Reactor malfunction at {station.name} ({sys.name}) - production reduced to emergency levels"))

    def _event_plague_outbreak(self, tick, universe):
        hubs = [(sid, sys, st) for sid, sys in universe.items() for st in sys.stations if st.station_type == 'trade_hub' and sys.population > 1000000]
        if not hubs:
            return
        sys_id, sys, hub = random.choice(hubs)
        faction = FACTION_NAMES.get(sys.faction, 'Local')
        self.emit(EventLog(tick=tick, msg=f"NEWS: Viral outbreak reported at {hub.name} - {faction} authorities impose quarantine. Demand for medical supplies surges."))

    # ── DISCOVERY EVENTS ──

    def _event_tech_breakthrough(self, tick, universe):
        faction = random.choice([f for f in FACTION_IDS if f != 'corsairs'])
        fname = FACTION_NAMES[faction]
        techs = [
            f"{fname} researchers develop improved refining catalyst - efficiency gains expected",
            f"Breakthrough in shield technology announced by {fname} Science Division",
            f"{fname} engineers patent new propulsion system - ship speeds may increase",
            f"Quantum computing advance at {fname} labs enables better trade route optimization",
        ]
        self.emit(EventLog(tick=tick, msg=f"NEWS: {random.choice(techs)}"))

    def _event_ancient_artifact(self, tick, universe):
        systems = list(universe.values())
        sys = random.choice(systems)
        artifacts = [
            f"Ancient alien structure discovered in {sys.name} - researchers dispatched",
            f"Derelict vessel of unknown origin found drifting in {sys.name}",
            f"Mysterious signal detected from deep space near {sys.name} - origin unknown",
        ]
        self.emit(EventLog(tick=tick, msg=f"NEWS: {random.choice(artifacts)}"))
