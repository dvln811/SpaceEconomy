"""Tracks per-tick changes for delta/diff API responses."""


class ChangeTracker:
    def __init__(self, window_size=100):
        self.window_size = window_size
        self._changes = {}  # {tick: {"ships": set(), "systems": set()}}

    def record_ship_change(self, tick, ship_id):
        self._ensure_tick(tick)
        self._changes[tick]["ships"].add(ship_id)

    def record_system_change(self, tick, system_id):
        self._ensure_tick(tick)
        self._changes[tick]["systems"].add(system_id)

    def get_changes_since(self, since_tick):
        ships = set()
        systems = set()
        for t, changes in self._changes.items():
            if t > since_tick:
                ships.update(changes["ships"])
                systems.update(changes["systems"])
        return {"ships": ships, "systems": systems}

    def has_tick(self, tick):
        return tick in self._changes

    def tick_cleanup(self, current_tick):
        self._ensure_tick(current_tick)
        cutoff = current_tick - self.window_size
        to_remove = [t for t in self._changes if t <= cutoff]
        for t in to_remove:
            del self._changes[t]

    def _ensure_tick(self, tick):
        if tick not in self._changes:
            self._changes[tick] = {"ships": set(), "systems": set()}
