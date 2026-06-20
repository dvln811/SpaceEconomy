"""Ship type definitions. Data lives in game_data.db."""
from dataclasses import dataclass, field


@dataclass
class ShipType:
    id: str
    name: str
    role: str
    tier: int
    cargo_capacity: int
    fuel_capacity: int
    speed: float
    intra_speed: float
    hull_hp: int
    align_time: int = 5
    hardpoints: dict[str, int] = field(default_factory=dict)
    build_cost: dict[str, int] = field(default_factory=dict)
    description: str = ""
