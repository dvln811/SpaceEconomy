"""Data models for the space economy simulation. Definitions only - data lives in game_data.db."""
from dataclasses import dataclass, field


@dataclass
class Commodity:
    name: str
    base_price: float
    tier: int
    volume: float = 1.0
    elasticity: float = 1.0
    description: str = ""
    recipe: dict[str, float] = field(default_factory=dict)
    stats: dict[str, any] = field(default_factory=dict)


@dataclass
class AsteroidField:
    name: str
    field_type: str
    yields: list[str] = field(default_factory=list)
    density: float = 1.0
    danger: float = 0.0


@dataclass
class SystemObject:
    id: str
    name: str
    obj_type: str
    distance: float = 0.0
    angle: float = 0.0
    parent: str = ""
    connects_to: str = ""


@dataclass
class Station:
    name: str
    system_id: str
    station_type: str = "trade_hub"
    produces: list[str] = field(default_factory=list)
    inventory: dict[str, float] = field(default_factory=dict)
    price_cache: dict[str, float] = field(default_factory=dict)
    production_rate: float = 1.0
    effective_rate: float = 0.0


@dataclass
class System:
    id: str
    name: str
    system_type: str
    cluster: str
    security: str
    faction: str = ""
    region: str = ""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    stations: list[Station] = field(default_factory=list)
    asteroid_fields: list[AsteroidField] = field(default_factory=list)
    connections: list[str] = field(default_factory=list)
    objects: list[SystemObject] = field(default_factory=list)


@dataclass
class NPCShip:
    id: str
    name: str
    cargo: dict[str, float] = field(default_factory=dict)
    cargo_capacity: float = 200.0
    fuel: float = 100.0
    location: str = ""
    destination: str = ""
    progress: float = 0.0
    speed: float = 1.0
    state: str = "idle"
    state_timer: int = 0
    role: str = "trader"
    ship_class: str = ""
    route_path: list[str] = field(default_factory=list)
    intra_position: str = ""
    intra_destination: str = ""
    intra_progress: float = 0.0
    intra_speed: float = 0.2
    align_time: int = 5
    risk_tolerance: float = 0.5
    faction: str = ""
    fitted_modules: list[str] = field(default_factory=list)
    assigned_station: str = ""
    assigned_system: str = ""


# Constants (not data, just lookup values)
SECURITY_LEVEL = {"high": 1.0, "medium": 0.7, "low": 0.3, "none": 0.0}


def calculate_price(commodity_id: str, supply: float, demand: float, commodities: dict) -> float:
    """Calculate current price based on supply/demand ratio."""
    c = commodities[commodity_id]
    if supply <= 0:
        return c.base_price * 5.0
    ratio = max(0.1, min(10.0, demand / supply))
    return round(c.base_price * (ratio ** c.elasticity), 2)
