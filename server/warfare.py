"""Warfare simulation: faction conflicts that consume ships/ammo and drive demand."""
import random
from server.military import MILITARY_SHIPS, FLEET_TARGETS, MilitaryShipClass
from server.factions import FACTIONS


class WarfareSimulation:
    """Manages faction conflicts, ship destruction, and rebuild orders."""

    def __init__(self):
        # Active fleets: faction -> {ship_class_id: count}
        self.fleets = {}
        for faction_id, targets in FLEET_TARGETS.items():
            self.fleets[faction_id] = dict(targets)  # Start at full strength

        # Conflict zones: pairs of factions currently fighting
        self.conflicts = [
            ("iron_compact", "free_states"),     # Border war
            ("corsairs", "merchants_guild"),      # Pirate raids
            ("corsairs", "terran_fed"),           # Law enforcement
        ]

        # Statistics
        self.ships_destroyed = 0
        self.ships_built = 0
        self.ammo_consumed = 0
        self.recent_battles = []  # [{tick, attacker, defender, a_losses, d_losses}]

    def tick(self, tick_count: int, universe: dict):
        """Run warfare simulation every 20 ticks."""
        if tick_count % 20 != 0:
            return []

        events = []

        # Run each active conflict
        for attacker_id, defender_id in self.conflicts:
            if random.random() < 0.4:  # 40% chance of skirmish per conflict per 20 ticks
                result = self._run_skirmish(attacker_id, defender_id, tick_count)
                if result:
                    events.append(result)

        # Consume ammo for active fleets (ongoing operations)
        for faction_id, fleet in self.fleets.items():
            total_ships = sum(fleet.values())
            if total_ships > 0:
                self.ammo_consumed += total_ships  # 1 ammo unit per ship per 20 ticks

        return events

    def _run_skirmish(self, attacker_id: str, defender_id: str, tick: int) -> dict | None:
        """Simulate a small engagement between two factions."""
        a_fleet = self.fleets.get(attacker_id, {})
        d_fleet = self.fleets.get(defender_id, {})

        if not any(v > 0 for v in a_fleet.values()) or not any(v > 0 for v in d_fleet.values()):
            return None

        # Each side loses 1-3 ships (smaller classes more likely)
        a_losses = {}
        d_losses = {}

        for _ in range(random.randint(1, 3)):
            # Attacker loses a ship
            available = [(k, v) for k, v in a_fleet.items() if v > 0]
            if available:
                # Weight toward smaller ships (more expendable)
                weights = [v * (3 if MILITARY_SHIPS[k].hull_class in ('fighter', 'frigate') else 1) for k, v in available]
                chosen = random.choices(available, weights=weights, k=1)[0]
                a_fleet[chosen[0]] -= 1
                a_losses[chosen[0]] = a_losses.get(chosen[0], 0) + 1
                self.ships_destroyed += 1

        for _ in range(random.randint(1, 3)):
            # Defender loses a ship
            available = [(k, v) for k, v in d_fleet.items() if v > 0]
            if available:
                weights = [v * (3 if MILITARY_SHIPS[k].hull_class in ('fighter', 'frigate') else 1) for k, v in available]
                chosen = random.choices(available, weights=weights, k=1)[0]
                d_fleet[chosen[0]] -= 1
                d_losses[chosen[0]] = d_losses.get(chosen[0], 0) + 1
                self.ships_destroyed += 1

        a_faction = FACTIONS[attacker_id]
        d_faction = FACTIONS[defender_id]

        battle = {
            "tick": tick,
            "attacker": a_faction.name,
            "defender": d_faction.name,
            "a_losses": sum(a_losses.values()),
            "d_losses": sum(d_losses.values()),
            "a_detail": a_losses,
            "d_detail": d_losses,
        }
        self.recent_battles.append(battle)
        if len(self.recent_battles) > 20:
            self.recent_battles = self.recent_battles[-20:]

        return battle

    def get_rebuild_orders(self) -> dict[str, int]:
        """Calculate what needs to be built to restore fleets to target strength.
        Returns: {commodity_id: total_qty_needed}"""
        needed = {}
        for faction_id, targets in FLEET_TARGETS.items():
            current = self.fleets.get(faction_id, {})
            for ship_class_id, target_count in targets.items():
                deficit = target_count - current.get(ship_class_id, 0)
                if deficit > 0:
                    ship = MILITARY_SHIPS[ship_class_id]
                    for commodity_id, qty in ship.build_cost.items():
                        needed[commodity_id] = needed.get(commodity_id, 0) + qty * deficit
        return needed

    def try_build_ships(self, universe: dict) -> list[str]:
        """Try to build replacement ships from shipyard inventories.
        Returns list of event messages."""
        events = []
        for faction_id, targets in FLEET_TARGETS.items():
            current = self.fleets.get(faction_id, {})
            for ship_class_id, target_count in targets.items():
                deficit = target_count - current.get(ship_class_id, 0)
                if deficit <= 0:
                    continue
                ship = MILITARY_SHIPS[ship_class_id]
                # Find a shipyard with the materials
                for sys in universe.values():
                    if sys.faction != faction_id:
                        continue
                    for station in sys.stations:
                        if station.station_type != "shipyard":
                            continue
                        # Check if all materials available
                        can_build = True
                        for commodity_id, qty in ship.build_cost.items():
                            if station.inventory.get(commodity_id, 0) < qty:
                                can_build = False
                                break
                        if can_build:
                            # Consume materials
                            for commodity_id, qty in ship.build_cost.items():
                                station.inventory[commodity_id] -= qty
                            current[ship_class_id] = current.get(ship_class_id, 0) + 1
                            self.ships_built += 1
                            events.append(f"BUILT: {ship.name} for {FACTIONS[faction_id].short} at {station.name}")
                            break
                    if current.get(ship_class_id, 0) >= target_count:
                        break
        return events

    def get_status(self) -> dict:
        """Return warfare status for the debug panel."""
        return {
            "ships_destroyed": self.ships_destroyed,
            "ships_built": self.ships_built,
            "ammo_consumed": self.ammo_consumed,
            "fleet_strength": {fid: sum(f.values()) for fid, f in self.fleets.items()},
            "recent_battles": self.recent_battles[-5:],
            "rebuild_orders": self.get_rebuild_orders(),
        }
