"""Corsair/Spawn worker: assesses universe state and determines spawn locations."""
from server.supervisor import WorkerThread
from server.intents import SpawnCommand, EventLog


class CorsairSpawnWorker(WorkerThread):
    def __init__(self):
        super().__init__("corsair_spawn", tick_interval=50)

    def process(self, tick: int, snapshot):
        universe = snapshot['universe']
        ships = snapshot['ships']

        # Assess current NPC distribution by region
        ships_per_region = {}
        for ship in ships:
            loc = universe.get(ship.location)
            if loc:
                region = loc.region
                ships_per_region[region] = ships_per_region.get(region, 0) + 1

        # Find under-served regions (fewer than 5 ships per region)
        for sys_id, sys in universe.items():
            if not sys.region:
                continue
            count = ships_per_region.get(sys.region, 0)
            if count < 5 and sys.security == "low":
                # Could spawn corsair patrol here
                self.emit(SpawnCommand(
                    ship_type="pirate", system_id=sys_id, count=1, faction="corsairs"
                ))
                break  # One spawn per tick cycle

        # Trade volume event
        trade_vol = sum(1 for s in ships if s.state in ("loading", "unloading"))
        if trade_vol > 0 and tick % 200 == 0:
            self.emit(EventLog(tick=tick, msg=f"TRADE: {trade_vol} active transactions"))
