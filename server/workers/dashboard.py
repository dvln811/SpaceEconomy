"""Dashboard worker: prepares cached JSON state for API endpoints."""
import threading
from server.supervisor import WorkerThread


class DashboardWorker(WorkerThread):
    def __init__(self, commodities: dict, station_consumption: dict):
        super().__init__("dashboard", tick_interval=5)
        self.commodities = commodities
        self.station_consumption = station_consumption
        self._lock = threading.Lock()
        self._cached_debug = {}
        self._cached_ships = []
        self._cached_events = []

    @property
    def cached_debug(self):
        with self._lock:
            return self._cached_debug

    @property
    def cached_ships(self):
        with self._lock:
            return self._cached_ships

    def process(self, tick: int, snapshot):
        universe = snapshot['universe']
        ships = snapshot['ships']

        # Build ship summary
        ships_data = []
        ships_by_state = {}
        for s in ships:
            ships_by_state[s.state] = ships_by_state.get(s.state, 0) + 1
            loc_name = universe[s.location].name if s.location in universe else s.location or "-"
            dest_name = universe[s.destination].name if s.destination in universe else s.destination or "-"
            ships_data.append({
                "id": s.id, "name": s.name, "state": s.state, "role": s.role,
                "ship_class": s.ship_class, "faction": s.faction,
                "location": loc_name, "location_id": s.location,
                "destination": dest_name, "destination_id": s.destination,
                "cargo": dict(s.cargo), "cargo_capacity": s.cargo_capacity,
                "cargo_used": round(sum(s.cargo.values()), 1),
                "progress": round(s.progress, 3),
                "risk_tolerance": s.risk_tolerance,
                "intra_position": s.intra_position,
                "intra_destination": s.intra_destination,
                "intra_progress": round(s.intra_progress, 3),
            })

        # Build demand data
        demand_data = {}
        for sid, sys in universe.items():
            for st in sys.stations:
                for prod_id in st.produces:
                    com = self.commodities.get(prod_id)
                    if not com or not com.recipe:
                        continue
                    for inp_id, qty_needed in com.recipe.items():
                        if inp_id not in demand_data:
                            demand_data[inp_id] = {"demand_per_tick": 0, "total_supply": 0, "name": self.commodities[inp_id].name}
                        demand_data[inp_id]["demand_per_tick"] += qty_needed * st.production_rate
                for commodity, qty in st.inventory.items():
                    if commodity in demand_data:
                        demand_data[commodity]["total_supply"] += qty

        for v in demand_data.values():
            v["ticks_remaining"] = round(v["total_supply"] / v["demand_per_tick"], 1) if v["demand_per_tick"] > 0 else 9999

        debug = {
            "tick": tick,
            "systems": len(universe),
            "npc_ships": len(ships),
            "ships_by_state": ships_by_state,
            "demand": demand_data,
            "ships": ships_data,
        }

        with self._lock:
            self._cached_debug = debug
            self._cached_ships = ships_data
