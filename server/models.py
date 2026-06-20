"""Data models for the space economy simulation."""
from dataclasses import dataclass, field


@dataclass
class Commodity:
    name: str
    base_price: float
    tier: int                # 0=trade goods, 1=raw, 2=refined, 3=manufactured, 4=components, 5=products
    volume: float = 1.0      # m3 per unit
    elasticity: float = 1.0
    recipe: dict[str, float] = field(default_factory=dict)  # input_commodity_id: qty needed per 1 output


@dataclass
class AsteroidField:
    name: str
    field_type: str          # generic field type
    yields: list[str] = field(default_factory=list)
    density: float = 1.0
    danger: float = 0.0


@dataclass
class SystemObject:
    """An object within a star system."""
    id: str
    name: str
    obj_type: str            # star, planet, station, asteroid_belt, gate, moon
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


# ══════════════════════════════════════════════════════════════════════════════
# COMMODITIES - Full production chain from design docs
# ══════════════════════════════════════════════════════════════════════════════

COMMODITIES = {
    # ── T1: Raw Ores & Resources (mined from asteroids) ──────────────────────
    # Common (high-sec, 1 m3, cheap)
    "iron_ore":       Commodity("Iron Ore", 8, tier=1, volume=0.1),
    "copper_ore":     Commodity("Copper Ore", 10, tier=1, volume=0.1),
    "calcite":        Commodity("Calciumite", 6, tier=1, volume=0.1),
    "carbonite":      Commodity("Carbonite", 7, tier=1, volume=0.1),
    "hydral_ice":     Commodity("Hydral Ice", 5, tier=1, volume=0.15),
    "silicon_ore":    Commodity("Silicon Ore", 9, tier=1, volume=0.1),
    # Uncommon (med-sec, 2-3 m3)
    "cobalt_ore":     Commodity("Cobalt Ore", 25, tier=1, volume=0.2),
    "zinc_ore":       Commodity("Zinc Ore", 18, tier=1, volume=0.2),
    "tin_ore":        Commodity("Tin Ore", 20, tier=1, volume=0.2),
    "nitrogen_ice":   Commodity("Nitrogen Ice", 14, tier=1, volume=0.25),
    "methane_ice":    Commodity("Methane Ice", 16, tier=1, volume=0.25),
    "biomass":        Commodity("Biomass", 30, tier=1, volume=0.3),
    "nickel_ore":     Commodity("Nickel Ore", 22, tier=1, volume=0.2),
    # Rare (low-sec, 4-6 m3)
    "titanium_ore":   Commodity("Titanium Ore", 65, tier=1, volume=0.5),
    "tungsten_ore":   Commodity("Tungsten Ore", 80, tier=1, volume=0.5),
    "chromium_ore":   Commodity("Chromium Ore", 55, tier=1, volume=0.5),
    "helium3":        Commodity("Helium-3 Gas", 120, tier=1, volume=0.6),
    "xenon_gas":      Commodity("Xenon Gas", 90, tier=1, volume=0.6),
    "spore_clusters": Commodity("Spore Clusters", 50, tier=1, volume=0.5),
    "amino_gel":      Commodity("Amino Gel", 70, tier=1, volume=0.5),
    # Exotic (null-sec, 8-20 m3)
    "platinum_ore":   Commodity("Platinum Ore", 350, tier=1, volume=1.0),
    "gold_ore":       Commodity("Gold Ore", 300, tier=1, volume=1.0),
    "palladium_ore":  Commodity("Palladium Ore", 400, tier=1, volume=1.0),
    "quartz_crystal": Commodity("Quartz Crystal", 150, tier=1, volume=1.2),
    "lithium_crystal": Commodity("Lithium Crystal", 200, tier=1, volume=1.2),
    "beryllium_crystal": Commodity("Beryllium Crystal", 280, tier=1, volume=1.2),
    "kraxolite":      Commodity("Kraxolite", 1200, tier=1, volume=1.5),
    "void_shard":     Commodity("Void Shard", 2000, tier=1, volume=2.0),
    "neutronium":     Commodity("Neutronium Flake", 3500, tier=1, volume=2.0),

    # ── T2: Refined Materials ────────────────────────────────────────────────
    # Metals
    "refined_iron":    Commodity("Refined Iron", 80, tier=2, volume=0.3,
                                 recipe={"iron_ore": 3, "carbonite": 1}),
    "refined_copper":  Commodity("Refined Copper", 70, tier=2, volume=0.3,
                                 recipe={"copper_ore": 3}),
    "refined_titanium": Commodity("Refined Titanium", 250, tier=2, volume=0.25,
                                  recipe={"titanium_ore": 3, "xenon_gas": 1}),
    "refined_tungsten": Commodity("Refined Tungsten", 300, tier=2, volume=0.2,
                                  recipe={"tungsten_ore": 2, "carbonite": 1}),
    "chromium_plate":  Commodity("Chromium Plate", 180, tier=2, volume=0.25,
                                 recipe={"chromium_ore": 3, "nickel_ore": 1}),
    "bronze_alloy":    Commodity("Bronze Alloy", 60, tier=2, volume=0.3,
                                 recipe={"copper_ore": 2, "tin_ore": 1}),
    "cobalt_ingot":    Commodity("Cobalt Ingot", 75, tier=2, volume=0.2,
                                 recipe={"cobalt_ore": 2}),
    # Fuels & Chemicals
    "hydrogen_fuel":   Commodity("Hydrogen Fuel", 40, tier=2, volume=0.5,
                                 recipe={"hydral_ice": 2}),
    "liquid_nitrogen": Commodity("Liquid Nitrogen", 35, tier=2, volume=0.5,
                                 recipe={"nitrogen_ice": 2}),
    "methane_fuel":    Commodity("Methane Fuel", 45, tier=2, volume=0.5,
                                 recipe={"methane_ice": 2}),
    "purified_water":  Commodity("Purified Water", 30, tier=2, volume=0.4,
                                 recipe={"hydral_ice": 1, "nitrogen_ice": 1}),
    "industrial_solvent": Commodity("Industrial Solvent", 55, tier=2, volume=0.35,
                                    recipe={"methane_ice": 1, "silicon_ore": 1}),
    "enriched_he3":    Commodity("Enriched Helium-3", 400, tier=2, volume=0.35,
                                 recipe={"helium3": 3}),
    "xenon_propellant": Commodity("Xenon Propellant", 280, tier=2, volume=0.4,
                                  recipe={"xenon_gas": 2}),
    # Organics & Bio
    "processed_protein": Commodity("Processed Protein", 50, tier=2, volume=0.3,
                                   recipe={"biomass": 2, "purified_water": 1}),
    "bio_catalyst":    Commodity("Bio-Catalyst", 120, tier=2, volume=0.2,
                                 recipe={"spore_clusters": 1, "industrial_solvent": 1}),
    "synthetic_polymer": Commodity("Synthetic Polymer", 65, tier=2, volume=0.35,
                                   recipe={"methane_ice": 2, "silicon_ore": 1}),
    # Electronics Base
    "silicon_wafer":   Commodity("Silicon Wafer", 90, tier=2, volume=0.15,
                                 recipe={"silicon_ore": 2, "purified_water": 1}),
    "copper_wiring":   Commodity("Copper Wiring Loom", 160, tier=2, volume=0.25,
                                 recipe={"refined_copper": 2}),
    "lithium_cell":    Commodity("Lithium Cell", 550, tier=2, volume=0.2,
                                 recipe={"lithium_crystal": 2, "cobalt_ingot": 1}),

    # ── T3: Manufactured Materials ───────────────────────────────────────────
    # Structural
    "steel_plate":     Commodity("Steel Plate", 220, tier=3, volume=0.8,
                                 recipe={"refined_iron": 2, "carbonite": 1}),
    "titanium_alloy":  Commodity("Titanium Alloy", 750, tier=3, volume=0.6,
                                 recipe={"refined_titanium": 2, "chromium_plate": 1}),
    "tungsten_carbide": Commodity("Tungsten Carbide", 800, tier=3, volume=0.5,
                                  recipe={"refined_tungsten": 1, "carbonite": 2}),
    "carbon_composite": Commodity("Carbon Composite", 300, tier=3, volume=0.8,
                                  recipe={"carbonite": 3, "synthetic_polymer": 1}),
    "ceramic_plate":   Commodity("Ceramic Plate", 350, tier=3, volume=0.6,
                                 recipe={"calcite": 2, "silicon_ore": 1, "refined_iron": 1}),
    # Electronics & Computing
    "microprocessor":  Commodity("Microprocessor", 900, tier=3, volume=0.3,
                                 recipe={"silicon_wafer": 2, "copper_wiring": 1, "gold_ore": 1}),
    "superconductor":  Commodity("Superconductor", 1100, tier=3, volume=0.5,
                                 recipe={"gold_ore": 1, "refined_copper": 1, "liquid_nitrogen": 1}),
    "optical_lens":    Commodity("Optical Lens", 800, tier=3, volume=0.3,
                                 recipe={"quartz_crystal": 2, "beryllium_crystal": 1}),
    "power_cell":      Commodity("Power Cell", 1400, tier=3, volume=0.6,
                                 recipe={"lithium_cell": 2, "cobalt_ingot": 1, "copper_wiring": 1}),
    "quantum_filament": Commodity("Quantum Filament", 8000, tier=3, volume=0.2,
                                  recipe={"kraxolite": 1, "superconductor": 1, "void_shard": 1}),
    # Propulsion & Energy
    "fusion_pellet":   Commodity("Fusion Pellet", 1200, tier=3, volume=0.5,
                                 recipe={"enriched_he3": 2, "beryllium_crystal": 1}),
    "thruster_nozzle": Commodity("Thruster Nozzle", 2000, tier=3, volume=0.6,
                                 recipe={"refined_tungsten": 1, "ceramic_plate": 1, "titanium_alloy": 1}),
    "plasma_conduit":  Commodity("Plasma Conduit", 1800, tier=3, volume=0.5,
                                 recipe={"superconductor": 1, "ceramic_plate": 1, "xenon_propellant": 1}),
    "magnetic_coil":   Commodity("Magnetic Coil", 1600, tier=3, volume=0.6,
                                 recipe={"cobalt_ingot": 2, "superconductor": 1, "copper_wiring": 1}),
    # Chemical & Biological
    "pharma_grade":    Commodity("Pharmaceutical Grade", 600, tier=3, volume=0.5,
                                 recipe={"bio_catalyst": 1, "amino_gel": 1, "purified_water": 1}),
    "nanite_paste":    Commodity("Nanite Paste", 2500, tier=3, volume=0.3,
                                 recipe={"platinum_ore": 1, "bio_catalyst": 1, "silicon_wafer": 1}),
    "explosive_compound": Commodity("Explosive Compound", 400, tier=3, volume=0.6,
                                    recipe={"nitrogen_ice": 2, "methane_fuel": 1, "carbonite": 1}),
    "rad_shielding":   Commodity("Radiation Shielding", 900, tier=3, volume=0.8,
                                 recipe={"gold_ore": 1, "steel_plate": 2, "synthetic_polymer": 1}),

    # ── T4: Components ───────────────────────────────────────────────────────
    # Weapon
    "beam_emitter":    Commodity("Beam Emitter", 4500, tier=4, volume=1.0,
                                 recipe={"optical_lens": 1, "power_cell": 1, "plasma_conduit": 1}),
    "railgun_barrel":  Commodity("Railgun Barrel", 5200, tier=4, volume=1.5,
                                 recipe={"tungsten_carbide": 2, "magnetic_coil": 1, "superconductor": 1}),
    "missile_chassis": Commodity("Missile Chassis", 3200, tier=4, volume=1.2,
                                 recipe={"titanium_alloy": 1, "explosive_compound": 1, "microprocessor": 1}),
    "plasma_chamber":  Commodity("Plasma Chamber", 4800, tier=4, volume=1.2,
                                 recipe={"plasma_conduit": 1, "ceramic_plate": 1, "magnetic_coil": 1}),
    "warhead_assembly": Commodity("Warhead Assembly", 2800, tier=4, volume=1.0,
                                  recipe={"explosive_compound": 2, "microprocessor": 1, "titanium_alloy": 1}),
    # Defense
    "shield_emitter":  Commodity("Shield Emitter", 5000, tier=4, volume=1.2,
                                 recipe={"power_cell": 1, "magnetic_coil": 1, "superconductor": 1}),
    "armor_laminate":  Commodity("Armor Laminate", 3000, tier=4, volume=1.8,
                                 recipe={"steel_plate": 2, "titanium_alloy": 1, "ceramic_plate": 1}),
    "pd_array":        Commodity("Point Defense Array", 6000, tier=4, volume=1.0,
                                 recipe={"microprocessor": 1, "beam_emitter": 1, "optical_lens": 1}),
    "ecm_core":        Commodity("ECM Module Core", 12000, tier=4, volume=0.8,
                                 recipe={"microprocessor": 2, "power_cell": 1, "quantum_filament": 1}),
    # Propulsion
    "fusion_core":     Commodity("Fusion Core", 8000, tier=4, volume=1.5,
                                 recipe={"fusion_pellet": 2, "rad_shielding": 1, "magnetic_coil": 1}),
    "ion_drive":       Commodity("Ion Drive Assembly", 5500, tier=4, volume=1.5,
                                 recipe={"thruster_nozzle": 1, "xenon_propellant": 1, "power_cell": 1}),
    "warp_coil":       Commodity("Warp Coil", 15000, tier=4, volume=1.0,
                                 recipe={"quantum_filament": 1, "superconductor": 1, "fusion_pellet": 1}),
    "maneuver_thruster": Commodity("Maneuvering Thruster", 4000, tier=4, volume=1.0,
                                   recipe={"thruster_nozzle": 1, "xenon_propellant": 1, "microprocessor": 1}),
    # Electronics & Utility
    "sensor_package":  Commodity("Sensor Package", 3500, tier=4, volume=0.6,
                                 recipe={"optical_lens": 2, "microprocessor": 1, "copper_wiring": 1}),
    "nav_computer":    Commodity("Navigation Computer", 4200, tier=4, volume=0.6,
                                 recipe={"microprocessor": 2, "optical_lens": 1, "power_cell": 1}),
    "life_support_core": Commodity("Life Support Core", 2800, tier=4, volume=1.2,
                                   recipe={"pharma_grade": 1, "purified_water": 1, "microprocessor": 1}),
    "drone_brain":     Commodity("Drone Brain", 7000, tier=4, volume=0.4,
                                 recipe={"microprocessor": 2, "sensor_package": 1, "power_cell": 1}),
    "repair_core":     Commodity("Repair Module Core", 5500, tier=4, volume=1.0,
                                 recipe={"nanite_paste": 1, "microprocessor": 1, "copper_wiring": 1}),
    # Mining & Industrial
    "mining_optic":    Commodity("Mining Laser Optic", 4000, tier=4, volume=1.0,
                                 recipe={"optical_lens": 2, "power_cell": 1, "beam_emitter": 1}),
    "drill_head":      Commodity("Drill Head", 3000, tier=4, volume=1.2,
                                 recipe={"tungsten_carbide": 2, "titanium_alloy": 1}),
    "ore_processor":   Commodity("Ore Processor Unit", 2500, tier=4, volume=1.5,
                                 recipe={"microprocessor": 1, "steel_plate": 1, "industrial_solvent": 1}),
    "tractor_core":    Commodity("Tractor Beam Core", 4500, tier=4, volume=1.0,
                                 recipe={"magnetic_coil": 1, "power_cell": 1, "optical_lens": 1}),

    # ── T5: Final Products ───────────────────────────────────────────────────
    # Weapons
    "pulse_laser":     Commodity("Pulse Laser Mk.I", 12000, tier=5, volume=2.5,
                                 recipe={"beam_emitter": 1, "power_cell": 1, "steel_plate": 1}),
    "beam_laser":      Commodity("Beam Laser Mk.I", 18000, tier=5, volume=3.0,
                                 recipe={"beam_emitter": 1, "power_cell": 2, "optical_lens": 1}),
    "railgun":         Commodity("Railgun Mk.I", 22000, tier=5, volume=3.5,
                                 recipe={"railgun_barrel": 1, "power_cell": 1, "nav_computer": 1}),
    "plasma_cannon":   Commodity("Plasma Cannon Mk.I", 20000, tier=5, volume=3.0,
                                 recipe={"plasma_chamber": 1, "power_cell": 1, "thruster_nozzle": 1}),
    "missile_launcher": Commodity("Missile Launcher Mk.I", 15000, tier=5, volume=3.0,
                                  recipe={"missile_chassis": 1, "sensor_package": 1, "steel_plate": 1}),
    "autocannon":      Commodity("Autocannon Mk.I", 10000, tier=5, volume=2.5,
                                 recipe={"railgun_barrel": 1, "steel_plate": 1, "maneuver_thruster": 1}),
    # Ammo
    "railgun_slugs":   Commodity("Railgun Slugs", 1500, tier=5, volume=1.5,
                                 recipe={"tungsten_carbide": 1, "refined_iron": 1}),
    "light_missiles":  Commodity("Light Missiles", 2000, tier=5, volume=2.0,
                                 recipe={"warhead_assembly": 1, "methane_fuel": 1, "microprocessor": 1}),
    "autocannon_rounds": Commodity("Autocannon Rounds", 800, tier=5, volume=1.5,
                                   recipe={"refined_iron": 1, "explosive_compound": 1}),
    # Shields & Defense
    "shield_generator": Commodity("Shield Generator Mk.I", 25000, tier=5, volume=3.0,
                                  recipe={"shield_emitter": 2, "power_cell": 1, "rad_shielding": 1}),
    "shield_booster":  Commodity("Shield Booster", 15000, tier=5, volume=2.0,
                                 recipe={"shield_emitter": 1, "power_cell": 2}),
    "armor_plates":    Commodity("Armor Plates (Heavy)", 12000, tier=5, volume=4.0,
                                 recipe={"armor_laminate": 2, "titanium_alloy": 1}),
    "armor_repairer":  Commodity("Armor Repairer", 18000, tier=5, volume=2.5,
                                 recipe={"armor_laminate": 1, "nanite_paste": 1, "power_cell": 1}),
    "point_defense":   Commodity("Point Defense System", 20000, tier=5, volume=2.0,
                                 recipe={"pd_array": 1, "sensor_package": 1, "power_cell": 1}),
    "ecm_jammer":      Commodity("ECM Jammer", 30000, tier=5, volume=1.5,
                                 recipe={"ecm_core": 1, "power_cell": 1}),
    # Engines & Propulsion
    "std_engine":      Commodity("Standard Engine Mk.I", 20000, tier=5, volume=4.0,
                                 recipe={"ion_drive": 1, "fusion_core": 1, "steel_plate": 1}),
    "afterburner":     Commodity("Afterburner", 12000, tier=5, volume=2.5,
                                 recipe={"ion_drive": 1, "xenon_propellant": 2, "thruster_nozzle": 1}),
    "maneuver_rig":    Commodity("Maneuvering Rig", 10000, tier=5, volume=2.0,
                                 recipe={"maneuver_thruster": 2, "nav_computer": 1}),
    "jump_drive":      Commodity("Jump Drive Mk.I", 50000, tier=5, volume=3.5,
                                 recipe={"warp_coil": 1, "fusion_core": 1, "nav_computer": 1}),
    # Electronics & Utility
    "scanner_array":   Commodity("Scanner Array", 12000, tier=5, volume=1.5,
                                 recipe={"sensor_package": 2, "nav_computer": 1}),
    "cargo_expander":  Commodity("Cargo Expander", 8000, tier=5, volume=3.5,
                                 recipe={"steel_plate": 2, "carbon_composite": 1, "microprocessor": 1}),
    "tractor_beam":    Commodity("Tractor Beam", 10000, tier=5, volume=2.0,
                                 recipe={"tractor_core": 1, "power_cell": 1}),
    "repair_module":   Commodity("Repair Module", 16000, tier=5, volume=2.0,
                                 recipe={"repair_core": 1, "nanite_paste": 1, "power_cell": 1}),
    # Drones
    "combat_drone":    Commodity("Combat Drone", 25000, tier=5, volume=3.0,
                                 recipe={"drone_brain": 1, "beam_emitter": 1, "maneuver_thruster": 1, "armor_laminate": 1}),
    "mining_drone":    Commodity("Mining Drone", 20000, tier=5, volume=3.0,
                                 recipe={"drone_brain": 1, "mining_optic": 1, "maneuver_thruster": 1}),
    "repair_drone":    Commodity("Repair Drone", 22000, tier=5, volume=3.0,
                                 recipe={"drone_brain": 1, "repair_core": 1, "maneuver_thruster": 1}),
    # Mining Equipment
    "mining_laser":    Commodity("Mining Laser Mk.I", 10000, tier=5, volume=2.5,
                                 recipe={"mining_optic": 1, "power_cell": 1, "steel_plate": 1}),
    "strip_miner_mod": Commodity("Strip Miner Mk.I", 25000, tier=5, volume=3.5,
                                 recipe={"mining_optic": 2, "drill_head": 1, "ore_processor": 1}),
    "survey_scanner":  Commodity("Survey Scanner", 8000, tier=5, volume=1.5,
                                 recipe={"sensor_package": 1, "optical_lens": 1, "nav_computer": 1}),

    # ── T0: Trade Goods (no recipe, generated at hubs, consumed everywhere) ──
    "luxury_goods":    Commodity("Luxury Goods", 700, tier=0, volume=1.0),
    "consumer_elec":   Commodity("Consumer Electronics", 400, tier=0, volume=0.8),
    "gourmet_food":    Commodity("Gourmet Food", 250, tier=0, volume=1.2),
    "exotic_textiles": Commodity("Exotic Textiles", 500, tier=0, volume=1.0),
    "entertainment":   Commodity("Entertainment Media", 300, tier=0, volume=0.5),
    "fine_spirits":    Commodity("Fine Spirits", 350, tier=0, volume=1.5),
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

# What each station type consumes (end-use demand, drives trade)
STATION_CONSUMPTION = {
    "frontier_outpost": ["processed_protein", "hydrogen_fuel", "pharma_grade", "purified_water", "fine_spirits", "entertainment"],
    "military_base": ["railgun_slugs", "light_missiles", "autocannon_rounds", "combat_drone", "hydrogen_fuel", "processed_protein", "entertainment"],
    "trade_hub": ["processed_protein", "hydrogen_fuel", "luxury_goods", "consumer_elec", "gourmet_food", "exotic_textiles", "entertainment", "fine_spirits"],
    "mining_colony": ["processed_protein", "hydrogen_fuel", "purified_water", "fine_spirits", "entertainment"],
    "refinery": ["processed_protein", "hydrogen_fuel", "purified_water"],
    "industrial_hub": ["processed_protein", "hydrogen_fuel", "consumer_elec"],
    "component_factory": ["processed_protein", "hydrogen_fuel", "consumer_elec"],
    "shipyard": ["processed_protein", "hydrogen_fuel", "luxury_goods"],
}

SECURITY_LEVEL = {"high": 1.0, "medium": 0.7, "low": 0.3, "none": 0.0}


def calculate_price(commodity_id: str, supply: float, demand: float) -> float:
    """Calculate current price based on supply/demand ratio."""
    c = COMMODITIES[commodity_id]
    if supply <= 0:
        return c.base_price * 5.0
    ratio = max(0.1, min(10.0, demand / supply))
    return round(c.base_price * (ratio ** c.elasticity), 2)
