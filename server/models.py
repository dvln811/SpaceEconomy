"""Data models for the space economy simulation."""
from dataclasses import dataclass, field


@dataclass
class Commodity:
    name: str
    base_price: float
    elasticity: float = 1.0  # price sensitivity to supply/demand ratio
    category: str = "raw"    # raw, basic, essential, advanced, illegal


@dataclass
class AsteroidField:
    name: str
    field_type: str          # iron_belt, ice_field, gas_pocket, rare_earth, etc.
    yields: list[str] = field(default_factory=list)  # commodity names produced
    density: float = 1.0     # extraction speed multiplier
    danger: float = 0.0      # 0-1, chance of hazard per tick while mining


@dataclass
class SystemObject:
    """An object within a star system (planet, station, belt, gate, etc.)."""
    id: str
    name: str
    obj_type: str            # star, planet, station, asteroid_belt, gate
    distance: float = 0.0    # AU from star (0 = center)
    angle: float = 0.0       # radians, position on orbital ring
    parent: str = ""         # id of parent object (e.g. planet for a moon/station)
    connects_to: str = ""    # for gates: which system_id this gate leads to


@dataclass
class Station:
    name: str
    system_id: str
    production: dict[str, float] = field(default_factory=dict)   # commodity: units/tick
    consumption: dict[str, float] = field(default_factory=dict)  # commodity: units/tick
    inventory: dict[str, float] = field(default_factory=dict)    # commodity: current stock
    price_cache: dict[str, float] = field(default_factory=dict)  # commodity: current price


@dataclass
class System:
    id: str
    name: str
    system_type: str         # industrial, mining, trade, agricultural, processing, frontier, nexus, shipyard, military
    cluster: str             # core, rim, frontier
    security: str            # high, medium, low, none
    faction: str = ""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    stations: list[Station] = field(default_factory=list)
    asteroid_fields: list[AsteroidField] = field(default_factory=list)
    connections: list[str] = field(default_factory=list)  # system IDs this connects to
    objects: list[SystemObject] = field(default_factory=list)  # all objects in-system (planets, gates, etc.)


@dataclass
class NPCShip:
    id: str
    name: str
    cargo: dict[str, float] = field(default_factory=dict)
    cargo_capacity: float = 200.0
    fuel: float = 100.0
    location: str = ""       # system_id
    destination: str = ""    # system_id (inter-system destination)
    progress: float = 0.0    # 0-1 travel progress (inter-system)
    speed: float = 1.0
    state: str = "idle"      # idle, traveling, intra_traveling, loading, unloading, mining
    state_timer: int = 0     # ticks remaining in current state
    role: str = "trader"     # trader, miner
    ship_class: str = ""     # hull class name
    route_path: list[str] = field(default_factory=list)  # multi-hop path (system IDs)
    # Intra-system navigation
    intra_position: str = ""       # object_id the ship is currently at (or "" if in transit)
    intra_destination: str = ""    # object_id the ship is traveling to within system
    intra_progress: float = 0.0   # 0-1 progress toward intra_destination
    intra_speed: float = 0.2        # AU per tick equivalent (intra-system speed)


# All commodities in the game
COMMODITIES = {
    "iron_ore":     Commodity("Iron Ore", 50, elasticity=0.8, category="raw"),
    "copper":       Commodity("Copper", 80, elasticity=0.9, category="raw"),
    "titanium":     Commodity("Titanium", 200, elasticity=1.2, category="raw"),
    "platinum":     Commodity("Platinum", 800, elasticity=1.5, category="raw"),
    "ice":          Commodity("Ice/Water", 20, elasticity=0.5, category="raw"),
    "helium3":      Commodity("Helium-3", 300, elasticity=1.3, category="raw"),
    "chemicals":    Commodity("Chemicals", 120, elasticity=1.0, category="raw"),
    "crystals":     Commodity("Rare Crystals", 600, elasticity=1.4, category="raw"),
    "salvage":      Commodity("Salvage", 150, elasticity=0.7, category="raw"),
    "exotic":       Commodity("Exotic Matter", 2000, elasticity=2.0, category="raw"),
    "food":         Commodity("Processed Food", 40, elasticity=0.4, category="basic"),
    "organics":     Commodity("Organics", 60, elasticity=0.6, category="basic"),
    "meds":         Commodity("Medical Supplies", 400, elasticity=1.2, category="essential"),
    "fuel":         Commodity("Fuel Cells", 150, elasticity=0.9, category="essential"),
    "electronics":  Commodity("Electronics", 500, elasticity=1.1, category="advanced"),
    "alloys":       Commodity("Alloys", 250, elasticity=1.0, category="advanced"),
    "polymers":     Commodity("Polymers", 100, elasticity=0.8, category="advanced"),
    "components":   Commodity("Components", 350, elasticity=1.0, category="advanced"),
    "luxuries":     Commodity("Luxury Goods", 900, elasticity=1.8, category="advanced"),
    "narcotics":    Commodity("Narcotics", 1200, elasticity=2.0, category="illegal"),
}


def calculate_price(commodity_id: str, supply: float, demand: float) -> float:
    """Calculate current price based on supply/demand ratio."""
    c = COMMODITIES[commodity_id]
    if supply <= 0:
        return c.base_price * 5.0  # scarcity cap
    ratio = max(0.1, min(10.0, demand / supply))
    return round(c.base_price * (ratio ** c.elasticity), 2)
