"""Intent types for inter-thread communication.
Workers produce intents; Supervisor consumes and applies them."""
from dataclasses import dataclass, field


@dataclass
class InventoryDelta:
    """Economy thread: station produced/consumed items."""
    system_id: str
    station_name: str
    deltas: dict[str, float]  # {commodity_id: +/- amount}


@dataclass
class ShipMoveIntent:
    """NPC thread: ship wants to travel somewhere."""
    ship_id: str
    destination: str  # system_id
    route_path: list[str] = field(default_factory=list)


@dataclass
class ShipIntraIntent:
    """NPC thread: ship wants intra-system travel."""
    ship_id: str
    dest_obj_id: str


@dataclass
class ShipBuyIntent:
    """NPC thread: ship wants to buy from a station (pre-pay reservation)."""
    ship_id: str
    system_id: str
    station_name: str
    commodity_id: str
    quantity: float
    route_home: list[str] = field(default_factory=list)


@dataclass
class ShipSellIntent:
    """NPC thread: ship wants to sell cargo at current station."""
    ship_id: str
    system_id: str
    station_name: str
    commodity_id: str
    quantity: float


@dataclass
class ShipMineIntent:
    """NPC thread: ship starts mining."""
    ship_id: str


@dataclass
class ShipDestroyedEvent:
    """Battle thread: ship was destroyed."""
    faction_id: str
    ship_class_id: str


@dataclass
class ShipBuiltEvent:
    """Battle thread: shipyard built a replacement."""
    faction_id: str
    ship_class_id: str
    system_id: str
    station_name: str
    cost: dict[str, float]  # hull materials consumed from shipyard
    fitting_cost: dict[str, float] = None  # weapons/modules deducted from factories


@dataclass
class SpawnCommand:
    """Corsair thread: spawn new NPC ships."""
    ship_type: str  # 'hauler', 'miner', 'pirate'
    system_id: str
    count: int = 1
    faction: str = ""


@dataclass
class FactionOrder:
    """Faction thread: strategic decision."""
    faction_id: str
    order_type: str  # 'declare_war', 'cease_fire', 'expand', 'reinforce'
    target: str = ""  # faction_id or system_id depending on type


@dataclass
class PriceUpdate:
    """Economy thread: new price for a commodity at a station."""
    system_id: str
    station_name: str
    commodity_id: str
    new_price: float


@dataclass
class EventLog:
    """Any thread: log message for the event feed."""
    tick: int
    msg: str
    agent_id: str = ""
    agent_name: str = ""
    category: str = ""
