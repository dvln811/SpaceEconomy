"""Ship type/class definitions with full specs."""
from dataclasses import dataclass, field


@dataclass
class ShipType:
    id: str
    name: str
    role: str                    # trader, miner, military, explorer
    tier: int                    # 1=starter, 2=mid, 3=late, 4=endgame
    cargo_capacity: int
    fuel_capacity: int
    speed: float                 # inter-system travel multiplier
    intra_speed: float           # intra-system travel multiplier
    hull_hp: int
    hardpoints: dict[str, int] = field(default_factory=dict)  # slot_type: count
    description: str = ""


# ── Trader hulls ──────────────────────────────────────────────────────────────
TRADER_SHIPS = {
    "pinto_runner": ShipType(
        id="pinto_runner", name="Pinto Runner", role="trader", tier=1,
        cargo_capacity=120, fuel_capacity=60, speed=1.2, intra_speed=0.25,
        hull_hp=80, hardpoints={"utility": 1, "defense": 1},
        description="Fast, light courier. Low capacity but quick turnaround."
    ),
    "mule_freighter": ShipType(
        id="mule_freighter", name="Mule Freighter", role="trader", tier=1,
        cargo_capacity=200, fuel_capacity=80, speed=0.9, intra_speed=0.2,
        hull_hp=120, hardpoints={"utility": 1, "defense": 1},
        description="Reliable workhorse. Balanced capacity and speed."
    ),
    "bison_mk3": ShipType(
        id="bison_mk3", name="Bison Mk.III", role="trader", tier=2,
        cargo_capacity=350, fuel_capacity=100, speed=1.0, intra_speed=0.2,
        hull_hp=180, hardpoints={"utility": 2, "defense": 1, "industrial": 1},
        description="Medium freighter. Solid all-rounder for established traders."
    ),
    "ox_hauler": ShipType(
        id="ox_hauler", name="Ox Hauler", role="trader", tier=3,
        cargo_capacity=500, fuel_capacity=120, speed=0.8, intra_speed=0.15,
        hull_hp=250, hardpoints={"utility": 2, "defense": 2, "industrial": 1},
        description="Heavy hauler. Massive hold but slow and fuel-hungry."
    ),
    "clydesdale": ShipType(
        id="clydesdale", name="Clydesdale", role="trader", tier=4,
        cargo_capacity=800, fuel_capacity=160, speed=0.7, intra_speed=0.12,
        hull_hp=400, hardpoints={"utility": 3, "defense": 2, "industrial": 2},
        description="Bulk freighter. Enormous capacity, requires convoy protection in low-sec."
    ),
}

# ── Miner hulls ───────────────────────────────────────────────────────────────
MINER_SHIPS = {
    "prospect_skiff": ShipType(
        id="prospect_skiff", name="Prospect Skiff", role="miner", tier=1,
        cargo_capacity=80, fuel_capacity=50, speed=1.1, intra_speed=0.25,
        hull_hp=60, hardpoints={"mining": 1, "utility": 1},
        description="Entry-level mining vessel. Quick but tiny ore hold."
    ),
    "strip_miner": ShipType(
        id="strip_miner", name="Strip Miner", role="miner", tier=2,
        cargo_capacity=180, fuel_capacity=80, speed=0.9, intra_speed=0.2,
        hull_hp=140, hardpoints={"mining": 2, "utility": 1, "defense": 1},
        description="Dedicated mining platform. Dual lasers, good ore compression."
    ),
    "deep_core_borer": ShipType(
        id="deep_core_borer", name="Deep Core Borer", role="miner", tier=3,
        cargo_capacity=300, fuel_capacity=100, speed=0.7, intra_speed=0.15,
        hull_hp=220, hardpoints={"mining": 3, "utility": 2, "defense": 1},
        description="Heavy mining rig. Can crack dense asteroids, huge ore bay."
    ),
}

# ── Military/Patrol hulls (NPC only for now) ──────────────────────────────────
MILITARY_SHIPS = {
    "viper_interceptor": ShipType(
        id="viper_interceptor", name="Viper Interceptor", role="military", tier=2,
        cargo_capacity=20, fuel_capacity=40, speed=1.8, intra_speed=0.4,
        hull_hp=100, hardpoints={"weapon": 2, "defense": 1},
        description="Fast patrol craft. Interdiction and escort duties."
    ),
    "sentinel_corvette": ShipType(
        id="sentinel_corvette", name="Sentinel Corvette", role="military", tier=3,
        cargo_capacity=50, fuel_capacity=80, speed=1.3, intra_speed=0.3,
        hull_hp=300, hardpoints={"weapon": 3, "defense": 2, "utility": 1},
        description="Medium patrol vessel. System security and convoy escort."
    ),
}

ALL_SHIPS = {**TRADER_SHIPS, **MINER_SHIPS, **MILITARY_SHIPS}


def get_ship_type(ship_class_name: str) -> ShipType | None:
    """Look up ship type by display name."""
    for st in ALL_SHIPS.values():
        if st.name == ship_class_name:
            return st
    return None
