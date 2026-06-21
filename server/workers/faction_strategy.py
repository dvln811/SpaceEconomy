"""Faction Strategy worker: goals, expansion, diplomacy decisions."""
from server.supervisor import WorkerThread
from server.intents import FactionOrder, EventLog


class FactionStrategyWorker(WorkerThread):
    def __init__(self, factions: dict):
        super().__init__("faction_strategy", tick_interval=200)
        self.factions = factions

    def process(self, tick: int, snapshot):
        universe = snapshot['universe']

        # Assess faction territory and production health
        faction_stats = {}
        for sid, sys in universe.items():
            if not sys.faction:
                continue
            fid = sys.faction
            if fid not in faction_stats:
                faction_stats[fid] = {'systems': 0, 'producing': 0, 'halted': 0}
            faction_stats[fid]['systems'] += 1
            for st in sys.stations:
                for prod_id in st.produces:
                    faction_stats[fid]['producing'] += 1
                    if st.effective_rate < 0.01:
                        faction_stats[fid]['halted'] += 1

        # Generate faction status events
        fnames = {
            'terran_fed': 'Federation', 'science_collective': 'Nexus',
            'merchants_guild': 'Guild', 'free_states': 'Alliance',
            'iron_compact': 'Compact', 'corsairs': 'Corsairs'
        }
        for fid, stats in faction_stats.items():
            fname = fnames.get(fid, fid)
            total = stats['producing']
            halted = stats['halted']
            if total > 0:
                if halted > total * 0.5:
                    self.emit(EventLog(tick=tick, msg=f"ECONOMY: {fname} production crisis - {halted}/{total} lines halted"))
                elif halted == 0:
                    self.emit(EventLog(tick=tick, msg=f"ECONOMY: {fname} all production lines operational"))
