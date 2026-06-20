"""Faction and corporation definitions. Data lives in game_data.db."""
from dataclasses import dataclass, field


@dataclass
class Corporation:
    id: str
    name: str
    faction_id: str
    focus: str
    description: str = ""


@dataclass
class Faction:
    id: str
    name: str
    short: str
    philosophy: str
    home_cluster: str
    allies: list[str] = field(default_factory=list)
    enemies: list[str] = field(default_factory=list)
    corporations: list[Corporation] = field(default_factory=list)
    color: str = "#ffffff"
