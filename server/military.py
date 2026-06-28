"""Military ship class definitions. Data lives in game_data.db."""
from dataclasses import dataclass, field


@dataclass
class MilitaryShipClass:
    id: str
    name: str
    hull_class: str
    faction: str
    hull_hp: int
    armor_hp: int
    shield_hp: int
    weapons: list[str] = field(default_factory=list)
    modules: list[str] = field(default_factory=list)
    build_cost: dict[str, int] = field(default_factory=dict)
    fitting_cost: dict[str, int] = field(default_factory=dict)
    crew: int = 0
    description: str = ""
