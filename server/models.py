"""Data models for the space economy simulation."""
from dataclasses import dataclass, field


@dataclass
class Commodity:
    name: str
    base_price: float
    tier: int                # 1-5
    elasticity: float = 1.0
    recipe: dict[str, float] = field(default_factory=dict)  # input_commodity_id: qty needed per 1 output


@dataclass
class AsteroidField:
    name: str
    field_type: str          # iron_belt, ice_field, gas_pocket, rare_earth, crystal, deep_core
    yields: list[str] = field(default_factory=list)
    density: float = 1.0
    danger: float = 0.0


@dataclass
class SystemObject:
    """An object within a star system."""
    id: str
    name: str
    obj_type: str            # star, planet, station, asteroid_belt, gate
    distance: float = 0.0
    angle: float = 0.0
    parent: str = ""
    connects_to: str = ""


@dataclass
class Station:
    name: str
    system_id: str
    station_type: str = "trade_hub"  # mining_colony, refinery, industrial_hub, component_factory, shipyard, trade_hub, frontier_outpost, military_base
    produces: list[str] = field(default_factory=list)        # commodity_ids this station can produce
    inventory: dict[str, float] = field(default_factory=dict)
    price_cache: dict[str, float] = field(default_factory=dict)
    production_rate: float = 1.0  # units produced per tick (when inputs available)


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
    state: str = "idle"      # idle, traveling, intra_traveling, loading, unloading, mining
    state_timer: int = 0
    role: str = "trader"     # trader, miner
    ship_class: str = ""
    route_path: list[str] = field(default_factory=list)
    # Intra-system navigation
    intra_position: str = ""
    intra_destination: str = ""
    intra_progress: float = 0.0
    intra_speed: float = 0.2
    # Safety tolerance (0.0 = avoids all danger, 1.0 = will go anywhere)
    risk_tolerance: float = 0.5


# ── Tier 1: Raw Materials (mined from asteroid fields) ───────────────────────

# ── Tier 2: Refined Materials (produced at refineries from T1) ────────────────

# ── Tier 3: Industrial Materials (produced at factories from T2) ──────────────

# ── Tier 4: Components (produced at component factories from T3) ──────────────

# ── Tier 5: Complex Products (produced at shipyards/advanced factories) ───────

COMMODITIES = {
    # ── T1: Raw Materials ──
    "iron_ore":      Commodity("Iron Ore", 50, tier=1, elasticity=0.8),
    "copper_ore":    Commodity("Copper Ore", 65, tier=1, elasticity=0.8),
    "titanium_ore":  Commodity("Titanium Ore", 180, tier=1, elasticity=1.0),
    "platinum":      Commodity("Platinum", 750, tier=1, elasticity=1.4),
    "crystals":      Commodity("Crystals", 600, tier=1, elasticity=1.3),
    "ice":           Commodity("Ice", 25, tier=1, elasticity=0.5),
    "helium3":       Commodity("Helium-3", 280, tier=1, elasticity=1.2),
    "organics":      Commodity("Organics", 55, tier=1, elasticity=0.6),
    "rare_earths":   Commodity("Rare Earths", 500, tier=1, elasticity=1.3),
    "uranium":       Commodity("Uranium", 900, tier=1, elasticity=1.5),

    # ── T2: Refined Materials ──
    "refined_iron":     Commodity("Refined Iron", 120, tier=2, elasticity=0.9,
                                  recipe={"iron_ore": 2}),
    "refined_copper":   Commodity("Refined Copper", 160, tier=2, elasticity=0.9,
                                  recipe={"copper_ore": 2}),
    "refined_titanium": Commodity("Refined Titanium", 420, tier=2, elasticity=1.1,
                                  recipe={"titanium_ore": 2}),
    "water":            Commodity("Water", 60, tier=2, elasticity=0.5,
                                  recipe={"ice": 2}),
    "hydrogen_fuel":    Commodity("Hydrogen Fuel", 200, tier=2, elasticity=1.0,
                                  recipe={"ice": 1, "helium3": 1}),
    "processed_food":   Commodity("Processed Food", 90, tier=2, elasticity=0.5,
                                  recipe={"organics": 1, "water": 1}),
    "chemicals":        Commodity("Chemicals", 140, tier=2, elasticity=0.9,
                                  recipe={"organics": 1, "ice": 1}),
    "enriched_uranium": Commodity("Enriched Uranium", 2000, tier=2, elasticity=1.5,
                                  recipe={"uranium": 3}),

    # ── T3: Industrial Materials ──
    "steel_alloy":      Commodity("Steel Alloy", 320, tier=3, elasticity=1.0,
                                  recipe={"refined_iron": 2, "chemicals": 1}),
    "titanium_alloy":   Commodity("Titanium Alloy", 900, tier=3, elasticity=1.2,
                                  recipe={"refined_titanium": 2, "chemicals": 1}),
    "polymers":         Commodity("Polymers", 250, tier=3, elasticity=0.9,
                                  recipe={"chemicals": 2, "hydrogen_fuel": 1}),
    "composites":       Commodity("Composites", 600, tier=3, elasticity=1.1,
                                  recipe={"polymers": 1, "refined_titanium": 1}),
    "superconductors":  Commodity("Superconductors", 800, tier=3, elasticity=1.2,
                                  recipe={"refined_copper": 2, "rare_earths": 1}),
    "pharmaceuticals":  Commodity("Pharmaceuticals", 450, tier=3, elasticity=1.0,
                                  recipe={"chemicals": 2, "organics": 1}),
    "ceramics":         Commodity("Ceramics", 280, tier=3, elasticity=0.9,
                                  recipe={"refined_iron": 1, "chemicals": 1}),
    "glass":            Commodity("Glass", 350, tier=3, elasticity=1.0,
                                  recipe={"crystals": 1, "chemicals": 1}),

    # ── T4: Components ──
    "electronics":      Commodity("Electronics", 1200, tier=4, elasticity=1.1,
                                  recipe={"superconductors": 1, "glass": 1}),
    "engine_parts":     Commodity("Engine Parts", 1000, tier=4, elasticity=1.0,
                                  recipe={"steel_alloy": 2, "superconductors": 1}),
    "hull_plating":     Commodity("Hull Plating", 850, tier=4, elasticity=1.0,
                                  recipe={"steel_alloy": 2, "composites": 1}),
    "reactor_cores":    Commodity("Reactor Cores", 3500, tier=4, elasticity=1.3,
                                  recipe={"enriched_uranium": 1, "ceramics": 2, "superconductors": 1}),
    "life_support":     Commodity("Life Support Units", 1400, tier=4, elasticity=1.1,
                                  recipe={"polymers": 1, "electronics": 1, "water": 2}),
    "weapon_systems":   Commodity("Weapon Systems", 4000, tier=4, elasticity=1.4,
                                  recipe={"electronics": 1, "titanium_alloy": 1, "reactor_cores": 1}),
    "mining_lasers":    Commodity("Mining Lasers", 2200, tier=4, elasticity=1.2,
                                  recipe={"electronics": 1, "glass": 1, "reactor_cores": 1}),
    "nav_arrays":       Commodity("Navigation Arrays", 1100, tier=4, elasticity=1.1,
                                  recipe={"electronics": 1, "glass": 1}),

    # ── T5: Complex Products ──
    "ship_modules":     Commodity("Ship Modules", 5000, tier=5, elasticity=1.3,
                                  recipe={"hull_plating": 2, "life_support": 1, "engine_parts": 1}),
    "station_modules":  Commodity("Station Modules", 6000, tier=5, elasticity=1.3,
                                  recipe={"hull_plating": 2, "life_support": 1, "reactor_cores": 1}),
    "combat_drones":    Commodity("Combat Drones", 8000, tier=5, elasticity=1.5,
                                  recipe={"electronics": 2, "weapon_systems": 1, "engine_parts": 1}),
    "mining_rigs":      Commodity("Mining Rigs", 5500, tier=5, elasticity=1.2,
                                  recipe={"mining_lasers": 2, "engine_parts": 1, "hull_plating": 1}),
    "medical_bays":     Commodity("Medical Bays", 4500, tier=5, elasticity=1.2,
                                  recipe={"pharmaceuticals": 2, "electronics": 1, "life_support": 1}),
    "jump_drives":      Commodity("Jump Drives", 12000, tier=5, elasticity=1.5,
                                  recipe={"reactor_cores": 2, "nav_arrays": 2, "superconductors": 2}),

    # ── Trade Goods (end-use consumption, no recipe, produced at trade hubs/factories) ──
    "luxury_goods":         Commodity("Luxury Goods", 700, tier=0, elasticity=1.6),
    "consumer_electronics": Commodity("Consumer Electronics", 400, tier=0, elasticity=1.2),
    "gourmet_food":         Commodity("Gourmet Food", 250, tier=0, elasticity=1.0),
    "exotic_textiles":      Commodity("Exotic Textiles", 500, tier=0, elasticity=1.4),
    "entertainment_media":  Commodity("Entertainment Media", 300, tier=0, elasticity=1.1),
    "fine_spirits":         Commodity("Fine Spirits", 350, tier=0, elasticity=1.3),
}

# Station type -> what tier it produces
STATION_PRODUCES_TIER = {
    "mining_colony": 1,
    "refinery": 2,
    "industrial_hub": 3,
    "component_factory": 4,
    "shipyard": 5,
    "trade_hub": 0,
    "frontier_outpost": 0,
    "military_base": 0,
}

# What each station type consumes (as end-use, not for production)
# These create demand that drives trade routes for non-production goods
STATION_CONSUMPTION = {
    "frontier_outpost": ["processed_food", "hydrogen_fuel", "pharmaceuticals", "water", "fine_spirits", "entertainment_media"],
    "military_base": ["weapon_systems", "combat_drones", "ship_modules", "hydrogen_fuel", "processed_food", "entertainment_media"],
    "trade_hub": ["processed_food", "hydrogen_fuel", "luxury_goods", "consumer_electronics", "gourmet_food", "exotic_textiles", "entertainment_media", "fine_spirits"],
    "mining_colony": ["processed_food", "hydrogen_fuel", "water", "fine_spirits", "entertainment_media"],
    "refinery": ["processed_food", "hydrogen_fuel", "water"],
    "industrial_hub": ["processed_food", "hydrogen_fuel", "consumer_electronics"],
    "component_factory": ["processed_food", "hydrogen_fuel", "consumer_electronics"],
    "shipyard": ["processed_food", "hydrogen_fuel", "luxury_goods"],
}

# Security level numeric values for pathfinding
SECURITY_LEVEL = {"high": 1.0, "medium": 0.7, "low": 0.3, "none": 0.0}


def calculate_price(commodity_id: str, supply: float, demand: float) -> float:
    """Calculate current price based on supply/demand ratio."""
    c = COMMODITIES[commodity_id]
    if supply <= 0:
        return c.base_price * 5.0
    ratio = max(0.1, min(10.0, demand / supply))
    return round(c.base_price * (ratio ** c.elasticity), 2)
