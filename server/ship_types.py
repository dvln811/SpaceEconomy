"""Ship type/class definitions with full specs."""
from dataclasses import dataclass, field


@dataclass
class ShipType:
    id: str
    name: str
    role: str                    # hauler, miner, military, explorer
    tier: int                    # 1=starter, 2=mid, 3=late, 4=endgame
    cargo_capacity: int
    fuel_capacity: int
    speed: float                 # inter-system travel multiplier
    intra_speed: float           # intra-system travel multiplier
    hull_hp: int
    align_time: int = 5          # seconds to align/warmup before moving
    hardpoints: dict[str, int] = field(default_factory=dict)  # slot_type: count
    description: str = ""


# ── Hauler/Transport hulls ────────────────────────────────────────────────────
HAULER_SHIPS = {
    "pinto_runner": ShipType(
        id="pinto_runner", name="Pinto Runner", role="hauler", tier=1,
        cargo_capacity=120, fuel_capacity=60, speed=1.2, intra_speed=0.25,
        hull_hp=80, align_time=3, hardpoints={"utility": 1, "defense": 1},
        description="Fast, light courier. Low capacity but quick turnaround."
    ),
    "mule_freighter": ShipType(
        id="mule_freighter", name="Mule Freighter", role="hauler", tier=1,
        cargo_capacity=200, fuel_capacity=80, speed=0.9, intra_speed=0.2,
        hull_hp=120, align_time=5, hardpoints={"utility": 1, "defense": 1},
        description="Reliable workhorse. Balanced capacity and speed."
    ),
    "bison_mk3": ShipType(
        id="bison_mk3", name="Bison Mk.III", role="hauler", tier=2,
        cargo_capacity=350, fuel_capacity=100, speed=1.0, intra_speed=0.2,
        hull_hp=180, align_time=7, hardpoints={"utility": 2, "defense": 1, "industrial": 1},
        description="Medium freighter. Solid all-rounder for established haulers."
    ),
    "mammoth": ShipType(
        id="mammoth", name="Mammoth", role="hauler", tier=3,
        cargo_capacity=600, fuel_capacity=140, speed=0.85, intra_speed=0.15,
        hull_hp=320, align_time=12, hardpoints={"utility": 2, "defense": 2, "industrial": 2},
        description="Heavy transport. High capacity with decent defenses for low-sec runs."
    ),
    "ox_hauler": ShipType(
        id="ox_hauler", name="Ox Hauler", role="hauler", tier=3,
        cargo_capacity=500, fuel_capacity=120, speed=0.8, intra_speed=0.15,
        hull_hp=250, align_time=10, hardpoints={"utility": 2, "defense": 2, "industrial": 1},
        description="Proven heavy hauler. Massive hold but slow and fuel-hungry."
    ),
    "clydesdale": ShipType(
        id="clydesdale", name="Clydesdale", role="hauler", tier=4,
        cargo_capacity=800, fuel_capacity=160, speed=0.7, intra_speed=0.12,
        hull_hp=400, align_time=15, hardpoints={"utility": 3, "defense": 2, "industrial": 2},
        description="Bulk freighter. Enormous capacity, requires convoy protection in low-sec."
    ),
}

# ── Miner hulls ───────────────────────────────────────────────────────────────
MINER_SHIPS = {
    "prospect_skiff": ShipType(
        id="prospect_skiff", name="Prospect Skiff", role="miner", tier=1,
        cargo_capacity=80, fuel_capacity=50, speed=1.1, intra_speed=0.25,
        hull_hp=60, align_time=3, hardpoints={"mining": 1, "utility": 1},
        description="Entry-level mining vessel. Quick but tiny ore hold."
    ),
    "rock_hopper": ShipType(
        id="rock_hopper", name="Rock Hopper", role="miner", tier=1,
        cargo_capacity=100, fuel_capacity=55, speed=1.0, intra_speed=0.22,
        hull_hp=75, align_time=4, hardpoints={"mining": 1, "utility": 1, "defense": 1},
        description="Nimble belt runner. Better survivability than the Skiff for contested fields."
    ),
    "strip_miner": ShipType(
        id="strip_miner", name="Strip Miner", role="miner", tier=2,
        cargo_capacity=180, fuel_capacity=80, speed=0.9, intra_speed=0.2,
        hull_hp=140, align_time=6, hardpoints={"mining": 2, "utility": 1, "defense": 1},
        description="Dedicated mining platform. Dual lasers, good ore compression."
    ),
    "excavator": ShipType(
        id="excavator", name="Excavator", role="miner", tier=2,
        cargo_capacity=220, fuel_capacity=90, speed=0.85, intra_speed=0.18,
        hull_hp=160, align_time=8, hardpoints={"mining": 2, "utility": 2, "defense": 1},
        description="Industrial extraction vessel. Enhanced scanning and dual bore arrays."
    ),
    "deep_core_borer": ShipType(
        id="deep_core_borer", name="Deep Core Borer", role="miner", tier=3,
        cargo_capacity=300, fuel_capacity=100, speed=0.7, intra_speed=0.15,
        hull_hp=220, align_time=12, hardpoints={"mining": 3, "utility": 2, "defense": 1},
        description="Heavy mining rig. Can crack dense asteroids, huge ore bay."
    ),
}

# ── Military/Patrol hulls (NPC only for now) ──────────────────────────────────
MILITARY_SHIPS = {
    "viper_interceptor": ShipType(
        id="viper_interceptor", name="Viper Interceptor", role="military", tier=2,
        cargo_capacity=20, fuel_capacity=40, speed=1.8, intra_speed=0.4,
        hull_hp=100, align_time=2, hardpoints={"weapon": 2, "defense": 1},
        description="Fast patrol craft. Interdiction and escort duties."
    ),
    "sentinel_corvette": ShipType(
        id="sentinel_corvette", name="Sentinel Corvette", role="military", tier=3,
        cargo_capacity=50, fuel_capacity=80, speed=1.3, intra_speed=0.3,
        hull_hp=300, align_time=4, hardpoints={"weapon": 3, "defense": 2, "utility": 1},
        description="Medium patrol vessel. System security and convoy escort."
    ),
    "warden_frigate": ShipType(
        id="warden_frigate", name="Warden Frigate", role="military", tier=3,
        cargo_capacity=80, fuel_capacity=100, speed=1.1, intra_speed=0.25,
        hull_hp=450, align_time=6, hardpoints={"weapon": 4, "defense": 3, "utility": 1},
        description="Heavy enforcement frigate. Gate camps, blockade duty, anti-piracy ops."
    ),
}

ALL_SHIPS = {**HAULER_SHIPS, **MINER_SHIPS, **MILITARY_SHIPS}


def get_ship_type(ship_class_name: str) -> ShipType | None:
    """Look up ship type by display name."""
    for st in ALL_SHIPS.values():
        if st.name == ship_class_name:
            return st
    return None
