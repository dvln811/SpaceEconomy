"""Data models for the space economy simulation."""
from dataclasses import dataclass, field


@dataclass
class Commodity:
    name: str
    base_price: float
    tier: int                # 0=trade goods, 1=raw, 2=refined, 3=manufactured, 4=components, 5=products
    volume: float = 1.0      # m3 per unit
    elasticity: float = 1.0
    description: str = ""
    recipe: dict[str, float] = field(default_factory=dict)
    stats: dict[str, any] = field(default_factory=dict)  # fitting stats: cpu, pg, rof, damage, etc


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
    # Contract assignment (for haulers)
    assigned_station: str = ""   # station name this hauler serves
    assigned_system: str = ""    # system where the station is


# ══════════════════════════════════════════════════════════════════════════════
# COMMODITIES - Full production chain from design docs
# ══════════════════════════════════════════════════════════════════════════════

COMMODITIES = {
    # ── T1: Raw Ores & Resources (mined from asteroids) ──────────────────────
    # Common (high-sec, 1 m3, cheap)
    "iron_ore":       Commodity("Iron Ore", 8, tier=1, volume=0.1, description="Common ferrous rock extracted from Veltorite asteroids. The backbone of industrial manufacturing."),
    "copper_ore":     Commodity("Copper Ore", 10, tier=1, volume=0.1, description="Reddish metalite veins found in most belt systems. Prized for its electrical conductivity."),
    "calcite":        Commodity("Calciumite", 6, tier=1, volume=0.1, description="Calcium-rich mineral deposits scraped from dead moon surfaces. Used in ceramic and composite production."),
    "carbonite":      Commodity("Carbonite", 7, tier=1, volume=0.1, description="Dense carbon aggregate found in abundance throughout high-sec belts. Essential for alloy hardening."),
    "hydral_ice":     Commodity("Hydral Ice", 5, tier=1, volume=0.15, description="Frozen water-hydrogen mix harvested from comet trails. Primary source of hydrogen fuel."),
    "silicon_ore":    Commodity("Silicon Ore", 9, tier=1, volume=0.1, description="Glassy silicate chunks common in rocky asteroid fields. Foundation of all electronics manufacturing."),
    # Uncommon (med-sec, 2-3 m3)
    "cobalt_ore":     Commodity("Cobalt Ore", 25, tier=1, volume=0.2, description="Blue-tinted metallic ore found in medium-security belts. Critical for magnetic applications and battery tech."),
    "zinc_ore":       Commodity("Zinc Ore", 18, tier=1, volume=0.2, description="Brittle silvery ore mined from mid-belt deposits. Used in corrosion-resistant coatings and alloys."),
    "tin_ore":        Commodity("Tin Ore", 20, tier=1, volume=0.2, description="Soft metallic deposits found alongside copper veins. Alloyed with copper to produce bronze."),
    "nitrogen_ice":   Commodity("Nitrogen Ice", 14, tier=1, volume=0.25, description="Pale blue frozen nitrogen harvested from outer system ice rings. Used as industrial coolant and propellant base."),
    "methane_ice":    Commodity("Methane Ice", 16, tier=1, volume=0.25, description="Volatile hydrocarbon ice found in deep-cold asteroid clusters. Refined into fuel and chemical feedstock."),
    "biomass":        Commodity("Biomass", 30, tier=1, volume=0.3, description="Organic matter cultivated in zero-g bio-domes or harvested from living asteroids. Base material for food and pharmaceuticals."),
    "nickel_ore":     Commodity("Nickel Ore", 22, tier=1, volume=0.2, description="Heavy ferromagnetic ore from iron-nickel asteroids. Strengthens alloys and resists extreme heat."),
    # Rare (low-sec, 4-6 m3)
    "titanium_ore":   Commodity("Titanium Ore", 65, tier=1, volume=0.5, description="Lightweight yet incredibly strong ore found in low-security systems. The premier material for military-grade hulls."),
    "tungsten_ore":   Commodity("Tungsten Ore", 80, tier=1, volume=0.5, description="Extremely dense ore mined from deep-core asteroids in contested space. Withstands tremendous heat and pressure."),
    "chromium_ore":   Commodity("Chromium Ore", 55, tier=1, volume=0.5, description="Lustrous hard metal ore from volcanic planetoid belts. Essential for corrosion-resistant plating."),
    "helium3":        Commodity("Helium-3 Gas", 120, tier=1, volume=0.6, description="Rare isotope siphoned from gas giant atmospheres in low-sec. The cleanest known fusion fuel source."),
    "xenon_gas":      Commodity("Xenon Gas", 90, tier=1, volume=0.6, description="Noble gas collected from nebular pockets in disputed regions. Primary propellant for ion drive systems."),
    "spore_clusters": Commodity("Spore Clusters", 50, tier=1, volume=0.5, description="Alien fungal spores found on bioactive asteroids in frontier space. Potent catalytic properties when processed."),
    "amino_gel":      Commodity("Amino Gel", 70, tier=1, volume=0.5, description="Viscous organic compound secreted by extremophile colonies on acidic moons. Key ingredient in pharmaceuticals."),
    # Exotic (null-sec, 8-20 m3)
    "platinum_ore":   Commodity("Platinum Ore", 350, tier=1, volume=1.0, description="Ultra-rare precious metal found only in null-sec anomaly fields. Unmatched catalyst for nanite fabrication."),
    "gold_ore":       Commodity("Gold Ore", 300, tier=1, volume=1.0, description="Dense precious metal mined from shattered planetoid cores in lawless space. Superb conductor for high-end electronics."),
    "palladium_ore":  Commodity("Palladium Ore", 400, tier=1, volume=1.0, description="Silvery-white noble metal from deep null-sec deposits. Highly sought for advanced catalytic and electronic applications."),
    "quartz_crystal": Commodity("Quartz Crystal", 150, tier=1, volume=1.2, description="Perfectly formed piezoelectric crystals grown in zero-gravity cavities. Essential for precision optics and sensors."),
    "lithium_crystal": Commodity("Lithium Crystal", 200, tier=1, volume=1.2, description="Reactive crystalline lithium from irradiated asteroid cores. Powers the most advanced energy storage systems."),
    "beryllium_crystal": Commodity("Beryllium Crystal", 280, tier=1, volume=1.2, description="Toxic lightweight crystal found in neutron-bombarded fields. Critical for reactor windows and focusing lenses."),
    "kraxolite":      Commodity("Kraxolite", 1200, tier=1, volume=1.5, description="An unstable crystalline substance found only in null-sec anomalies. Essential for jump drive technology."),
    "void_shard":     Commodity("Void Shard", 2000, tier=1, volume=2.0, description="Mysterious dark-matter infused fragments pulled from spatial rifts. Exhibits quantum-entangled properties."),
    "neutronium":     Commodity("Neutronium Flake", 3500, tier=1, volume=2.0, description="Impossibly dense material shed from collapsed stellar remnants. A single flake outweighs a cargo pod of steel."),

    # ── T2: Refined Materials ────────────────────────────────────────────────
    # Metals
    "refined_iron":    Commodity("Refined Iron", 80, tier=2, volume=0.05, description="Smelted iron ingots with impurities burned away. Standard building block for structural components.",
                                 recipe={"iron_ore": 3, "carbonite": 1}),
    "refined_copper":  Commodity("Refined Copper", 70, tier=2, volume=0.05, description="High-purity copper bars electroplated in orbital refineries. Optimal for wiring and heat exchange.",
                                 recipe={"copper_ore": 3}),
    "refined_titanium": Commodity("Refined Titanium", 250, tier=2, volume=0.06, description="Titanium processed in xenon atmosphere to prevent oxidation. Lightweight and extraordinarily strong.",
                                  recipe={"titanium_ore": 3, "xenon_gas": 1}),
    "refined_tungsten": Commodity("Refined Tungsten", 300, tier=2, volume=0.04, description="Ultra-hard tungsten bars sintered at extreme temperatures. Used where nothing else can withstand the heat.",
                                  recipe={"tungsten_ore": 2, "carbonite": 1}),
    "chromium_plate":  Commodity("Chromium Plate", 180, tier=2, volume=0.06, description="Polished chromium sheets bonded with nickel. Provides mirror-finish corrosion resistance.",
                                 recipe={"chromium_ore": 3, "nickel_ore": 1}),
    "bronze_alloy":    Commodity("Bronze Alloy", 60, tier=2, volume=0.05, description="Copper-tin alloy valued for low friction and spark resistance. Common in mechanical fittings.",
                                 recipe={"copper_ore": 2, "tin_ore": 1}),
    "cobalt_ingot":    Commodity("Cobalt Ingot", 75, tier=2, volume=0.04, description="Dense blue-grey metal bars with powerful magnetic properties. Critical for coil and battery production.",
                                 recipe={"cobalt_ore": 2}),
    # Fuels & Chemicals
    "hydrogen_fuel":   Commodity("Hydrogen Fuel", 40, tier=2, volume=0.08, description="Compressed liquid hydrogen stored in cryo-tanks. Standard propellant for sublight engines.",
                                 recipe={"hydral_ice": 2}),
    "liquid_nitrogen": Commodity("Liquid Nitrogen", 35, tier=2, volume=0.08, description="Cryogenic nitrogen at minus 196 degrees. Industrial coolant and superconductor enabler.",
                                 recipe={"nitrogen_ice": 2}),
    "methane_fuel":    Commodity("Methane Fuel", 45, tier=2, volume=0.08, description="Purified methane stored under pressure. Burns hot and clean in atmospheric thrusters.",
                                 recipe={"methane_ice": 2}),
    "purified_water":  Commodity("Purified Water", 30, tier=2, volume=0.06, description="Triple-filtered water free of all contaminants. Required for life support, cooling, and chemical processing.",
                                 recipe={"hydral_ice": 1, "nitrogen_ice": 1}),
    "industrial_solvent": Commodity("Industrial Solvent", 55, tier=2, volume=0.06, description="Aggressive chemical solution that dissolves organic bonds. Used in refining and bio-catalytic processes.",
                                    recipe={"methane_ice": 1, "silicon_ore": 1}),
    "enriched_he3":    Commodity("Enriched Helium-3", 400, tier=2, volume=0.08, description="Weapons-grade helium-3 concentrate with isotopic purity above 99.7%. Powers fusion reactors.",
                                 recipe={"helium3": 3}),
    "xenon_propellant": Commodity("Xenon Propellant", 280, tier=2, volume=0.08, description="Ionized xenon gas pressurized for ion drive consumption. Provides efficient low-thrust acceleration.",
                                  recipe={"xenon_gas": 2}),
    # Organics & Bio
    "processed_protein": Commodity("Processed Protein", 50, tier=2, volume=0.05, description="Nutrient-dense food concentrate derived from biomass. Feeds station crews across the cluster.",
                                   recipe={"biomass": 2, "purified_water": 1}),
    "bio_catalyst":    Commodity("Bio-Catalyst", 120, tier=2, volume=0.04, description="Enzymatic compound derived from alien spores. Accelerates chemical reactions at room temperature.",
                                 recipe={"spore_clusters": 1, "industrial_solvent": 1}),
    "synthetic_polymer": Commodity("Synthetic Polymer", 65, tier=2, volume=0.06, description="Flexible carbon-chain plastic synthesized from methane and silicon. Used in seals, insulation, and composites.",
                                   recipe={"methane_ice": 2, "silicon_ore": 1}),
    # Electronics Base
    "silicon_wafer":   Commodity("Silicon Wafer", 90, tier=2, volume=0.02, description="Atom-thin silicon discs cut in cleanroom orbital labs. The substrate for all microprocessor fabrication.",
                                 recipe={"silicon_ore": 2, "purified_water": 1}),
    "copper_wiring":   Commodity("Copper Wiring Loom", 160, tier=2, volume=0.04, description="Pre-assembled bundles of insulated copper conductors. Routes power and data through ship systems.",
                                 recipe={"refined_copper": 2}),
    "lithium_cell":    Commodity("Lithium Cell", 550, tier=2, volume=0.04, description="High-density energy storage unit using crystalline lithium electrodes. Stores charge for days without decay.",
                                 recipe={"lithium_crystal": 2, "cobalt_ingot": 1}),

    # ── T3: Manufactured Materials ───────────────────────────────────────────
    # Structural
    "steel_plate":     Commodity("Steel Plate", 220, tier=3, volume=0.15, description="Hardened alloy of iron and carbon. Primary structural material for hulls and station frameworks.",
                                 recipe={"refined_iron": 2, "carbonite": 1}),
    "titanium_alloy":  Commodity("Titanium Alloy", 750, tier=3, volume=0.12, description="Chromium-reinforced titanium composite. Military-grade armor standard across all combat vessels.",
                                 recipe={"refined_titanium": 2, "chromium_plate": 1}),
    "tungsten_carbide": Commodity("Tungsten Carbide", 800, tier=3, volume=0.08, description="Carbon-bonded tungsten ceramic harder than diamond. Used for projectile tips and drill surfaces.",
                                  recipe={"refined_tungsten": 1, "carbonite": 2}),
    "carbon_composite": Commodity("Carbon Composite", 300, tier=3, volume=0.15, description="Layered carbon-fiber sheeting reinforced with polymer resin. Lightweight structural material for non-combat applications.",
                                  recipe={"carbonite": 3, "synthetic_polymer": 1}),
    "ceramic_plate":   Commodity("Ceramic Plate", 350, tier=3, volume=0.12, description="Heat-resistant ceramic tiles rated for plasma exposure. Lines engine nozzles and reactor chambers.",
                                 recipe={"calcite": 2, "silicon_ore": 1, "refined_iron": 1}),
    # Electronics & Computing
    "microprocessor":  Commodity("Microprocessor", 900, tier=3, volume=0.02, description="Multi-core processing chip etched onto silicon wafer with gold traces. The brain of every shipboard computer.",
                                 recipe={"silicon_wafer": 2, "copper_wiring": 1, "gold_ore": 1}),
    "superconductor":  Commodity("Superconductor", 1100, tier=3, volume=0.06, description="Zero-resistance conductor cooled by liquid nitrogen. Enables lossless power transfer at massive scales.",
                                 recipe={"gold_ore": 1, "refined_copper": 1, "liquid_nitrogen": 1}),
    "optical_lens":    Commodity("Optical Lens", 800, tier=3, volume=0.03, description="Precision-ground crystal optic with beryllium coating. Focuses energy beams and sensor arrays with nanometer accuracy.",
                                 recipe={"quartz_crystal": 2, "beryllium_crystal": 1}),
    "power_cell":      Commodity("Power Cell", 1400, tier=3, volume=0.1, description="Stacked lithium cells in a shielded casing with regulated output. Standard modular power supply for ship modules.",
                                 recipe={"lithium_cell": 2, "cobalt_ingot": 1, "copper_wiring": 1}),
    "quantum_filament": Commodity("Quantum Filament", 8000, tier=3, volume=0.01, description="Thread-thin strand exhibiting quantum superposition. Enables instantaneous signal propagation across short distances.",
                                  recipe={"kraxolite": 1, "superconductor": 1, "void_shard": 1}),
    # Propulsion & Energy
    "fusion_pellet":   Commodity("Fusion Pellet", 1200, tier=3, volume=0.06, description="Compressed He-3 fuel capsule encased in beryllium. Each pellet sustains a fusion burn for approximately one hour.",
                                 recipe={"enriched_he3": 2, "beryllium_crystal": 1}),
    "thruster_nozzle": Commodity("Thruster Nozzle", 2000, tier=3, volume=0.12, description="Precision-machined exhaust cone rated for extreme thermal output. Shapes plasma flow for maximum thrust efficiency.",
                                 recipe={"refined_tungsten": 1, "ceramic_plate": 1, "titanium_alloy": 1}),
    "plasma_conduit":  Commodity("Plasma Conduit", 1800, tier=3, volume=0.08, description="Magnetically-lined pipe that channels superheated plasma without melting. Critical for weapons and engines alike.",
                                 recipe={"superconductor": 1, "ceramic_plate": 1, "xenon_propellant": 1}),
    "magnetic_coil":   Commodity("Magnetic Coil", 1600, tier=3, volume=0.1, description="Tightly wound superconducting coil generating powerful magnetic fields. Heart of shields and rail weapons.",
                                 recipe={"cobalt_ingot": 2, "superconductor": 1, "copper_wiring": 1}),
    # Chemical & Biological
    "pharma_grade":    Commodity("Pharmaceutical Grade", 600, tier=3, volume=0.05, description="Medical-quality biochemical compound meeting interstellar purity standards. Treats combat injuries and radiation sickness.",
                                 recipe={"bio_catalyst": 1, "amino_gel": 1, "purified_water": 1}),
    "nanite_paste":    Commodity("Nanite Paste", 2500, tier=3, volume=0.03, description="Grey goo of programmable repair nanobots suspended in platinum medium. Rebuilds damaged materials at molecular level.",
                                 recipe={"platinum_ore": 1, "bio_catalyst": 1, "silicon_wafer": 1}),
    "explosive_compound": Commodity("Explosive Compound", 400, tier=3, volume=0.1, description="Stabilized nitrogen-methane explosive with controlled detonation velocity. Used in warheads and mining charges.",
                                    recipe={"nitrogen_ice": 2, "methane_fuel": 1, "carbonite": 1}),
    "rad_shielding":   Commodity("Radiation Shielding", 900, tier=3, volume=0.15, description="Gold-lined lead-polymer sandwich that blocks ionizing radiation. Protects crew from reactor emissions and cosmic rays.",
                                 recipe={"gold_ore": 1, "steel_plate": 2, "synthetic_polymer": 1}),

    # ── T4: Components ───────────────────────────────────────────────────────
    # Weapon
    "beam_emitter":    Commodity("Beam Emitter", 4500, tier=4, volume=0.3, description="Focused energy projection unit combining optics and plasma conduits. Core assembly of all laser-class weapons.",
                                 recipe={"optical_lens": 1, "power_cell": 1, "plasma_conduit": 1}),
    "railgun_barrel":  Commodity("Railgun Barrel", 5200, tier=4, volume=0.5, description="Magnetically-accelerated projectile tube built from tungsten carbide. Launches slugs at a fraction of lightspeed.",
                                 recipe={"tungsten_carbide": 2, "magnetic_coil": 1, "superconductor": 1}),
    "missile_chassis": Commodity("Missile Chassis", 3200, tier=4, volume=0.4, description="Aerodynamic guided munition frame with onboard targeting. Houses warhead, fuel, and guidance electronics.",
                                 recipe={"titanium_alloy": 1, "explosive_compound": 1, "microprocessor": 1}),
    "plasma_chamber":  Commodity("Plasma Chamber", 4800, tier=4, volume=0.4, description="Magnetically-contained plasma heating vessel. Superheats gas to millions of degrees for cannon discharge.",
                                 recipe={"plasma_conduit": 1, "ceramic_plate": 1, "magnetic_coil": 1}),
    "warhead_assembly": Commodity("Warhead Assembly", 2800, tier=4, volume=0.3, description="Pre-armed explosive payload with proximity detonator. Snaps into standard missile chassis mounts.",
                                  recipe={"explosive_compound": 2, "microprocessor": 1, "titanium_alloy": 1}),
    # Defense
    "shield_emitter":  Commodity("Shield Emitter", 5000, tier=4, volume=0.4, description="Electromagnetic field projector that generates protective energy barriers. Requires constant power to maintain.",
                                 recipe={"power_cell": 1, "magnetic_coil": 1, "superconductor": 1}),
    "armor_laminate":  Commodity("Armor Laminate", 3000, tier=4, volume=0.6, description="Multi-layer composite armor panel combining steel, titanium, and ceramic. Distributes impact across all layers.",
                                 recipe={"steel_plate": 2, "titanium_alloy": 1, "ceramic_plate": 1}),
    "pd_array":        Commodity("Point Defense Array", 6000, tier=4, volume=0.3, description="Rapid-tracking turret assembly with auto-targeting optics. Intercepts incoming missiles and drones.",
                                 recipe={"microprocessor": 1, "beam_emitter": 1, "optical_lens": 1}),
    "ecm_core":        Commodity("ECM Module Core", 12000, tier=4, volume=0.2, description="Quantum-encrypted signal scrambler that disrupts enemy targeting systems. Renders the user nearly untargetable.",
                                 recipe={"microprocessor": 2, "power_cell": 1, "quantum_filament": 1}),
    # Propulsion
    "fusion_core":     Commodity("Fusion Core", 8000, tier=4, volume=0.5, description="Self-contained fusion reactor providing megawatts of sustained power. The beating heart of capital-class vessels.",
                                 recipe={"fusion_pellet": 2, "rad_shielding": 1, "magnetic_coil": 1}),
    "ion_drive":       Commodity("Ion Drive Assembly", 5500, tier=4, volume=0.5, description="Complete ion propulsion package with nozzle and fuel injection. Efficient sublight drive for extended voyages.",
                                 recipe={"thruster_nozzle": 1, "xenon_propellant": 1, "power_cell": 1}),
    "warp_coil":       Commodity("Warp Coil", 15000, tier=4, volume=0.3, description="Quantum-entangled coil that bends local spacetime when energized. Enables faster-than-light jump capability.",
                                 recipe={"quantum_filament": 1, "superconductor": 1, "fusion_pellet": 1}),
    "maneuver_thruster": Commodity("Maneuvering Thruster", 4000, tier=4, volume=0.3, description="Compact directional thruster for attitude control and evasive maneuvers. Responds in milliseconds.",
                                   recipe={"thruster_nozzle": 1, "xenon_propellant": 1, "microprocessor": 1}),
    # Electronics & Utility
    "sensor_package":  Commodity("Sensor Package", 3500, tier=4, volume=0.2, description="Multi-spectrum detection suite combining visual, thermal, and gravimetric sensors. Eyes and ears of any vessel.",
                                 recipe={"optical_lens": 2, "microprocessor": 1, "copper_wiring": 1}),
    "nav_computer":    Commodity("Navigation Computer", 4200, tier=4, volume=0.15, description="Dedicated astrogation processor that calculates jump trajectories and plots safe routes through hazards.",
                                 recipe={"microprocessor": 2, "optical_lens": 1, "power_cell": 1}),
    "life_support_core": Commodity("Life Support Core", 2800, tier=4, volume=0.4, description="Atmospheric recycling and medical monitoring system. Keeps crews alive in the void between stars.",
                                   recipe={"pharma_grade": 1, "purified_water": 1, "microprocessor": 1}),
    "drone_brain":     Commodity("Drone Brain", 7000, tier=4, volume=0.1, description="Autonomous AI core with sensor fusion and decision-making capabilities. Gives drones independent combat judgment.",
                                 recipe={"microprocessor": 2, "sensor_package": 1, "power_cell": 1}),
    "repair_core":     Commodity("Repair Module Core", 5500, tier=4, volume=0.3, description="Nanite deployment system with damage assessment logic. Directs repair bots to hull breaches automatically.",
                                 recipe={"nanite_paste": 1, "microprocessor": 1, "copper_wiring": 1}),
    # Mining & Industrial
    "mining_optic":    Commodity("Mining Laser Optic", 4000, tier=4, volume=0.3, description="High-power focusing array tuned to fracture rock at specific resonant frequencies. Cuts ore cleanly from stone.",
                                 recipe={"optical_lens": 2, "power_cell": 1, "beam_emitter": 1}),
    "drill_head":      Commodity("Drill Head", 3000, tier=4, volume=0.4, description="Rotating tungsten-carbide bore assembly for deep-core extraction. Chews through solid asteroid in minutes.",
                                 recipe={"tungsten_carbide": 2, "titanium_alloy": 1}),
    "ore_processor":   Commodity("Ore Processor Unit", 2500, tier=4, volume=0.5, description="Onboard sorting and crushing system that separates valuable minerals from waste rock in real-time.",
                                 recipe={"microprocessor": 1, "steel_plate": 1, "industrial_solvent": 1}),
    "tractor_core":    Commodity("Tractor Beam Core", 4500, tier=4, volume=0.3, description="Graviton projection unit that locks onto objects and pulls them toward the ship. Essential for cargo retrieval.",
                                 recipe={"magnetic_coil": 1, "power_cell": 1, "optical_lens": 1}),

    # ── T5: Final Products ───────────────────────────────────────────────────
    # Weapons
    "pulse_laser":     Commodity("Pulse Laser Mk.I", 12000, tier=5, volume=1.5, description="Short-range energy weapon with rapid fire rate. Drains capacitor quickly but deals consistent thermal damage.",
                                 recipe={"beam_emitter": 1, "power_cell": 1, "steel_plate": 1}, stats={"cpu": 25, "pg": 15, "dps": 80, "rof": 2, "range": 5, "tracking": 8, "size": "S", "damage_type": "thermal", "slot": "high"}),
    "beam_laser":      Commodity("Beam Laser Mk.I", 18000, tier=5, volume=2.0, description="Sustained-fire laser that maintains a continuous damage beam. Superior range and tracking at the cost of higher power draw.",
                                 recipe={"beam_emitter": 1, "power_cell": 2, "optical_lens": 1}, stats={"cpu": 25, "pg": 15, "dps": 60, "rof": 4, "range": 20, "tracking": 4, "size": "S", "damage_type": "thermal", "slot": "high"}),
    "railgun":         Commodity("Railgun Mk.I", 22000, tier=5, volume=2.5, description="Electromagnetic mass driver that hurls tungsten slugs at hypersonic velocity. Devastating alpha strike at extreme range.",
                                 recipe={"railgun_barrel": 1, "power_cell": 1, "nav_computer": 1}, stats={"cpu": 25, "pg": 15, "dps": 100, "rof": 6, "range": 40, "tracking": 2, "size": "S", "damage_type": "kinetic", "slot": "high"}),
    "plasma_cannon":   Commodity("Plasma Cannon Mk.I", 20000, tier=5, volume=2.0, description="Superheated plasma bolt projector dealing massive thermal and kinetic damage. Short range but melts through armor.",
                                 recipe={"plasma_chamber": 1, "power_cell": 1, "thruster_nozzle": 1}, stats={"cpu": 25, "pg": 15, "dps": 90, "rof": 5, "range": 10, "tracking": 6, "size": "S", "damage_type": "thermal", "slot": "high"}),
    "missile_launcher": Commodity("Missile Launcher Mk.I", 15000, tier=5, volume=2.0, description="Guided ordnance delivery system with target-lock capability. Deals explosive damage that ignores shield resistances.",
                                  recipe={"missile_chassis": 1, "sensor_package": 1, "steel_plate": 1}, stats={"cpu": 25, "pg": 15, "dps": 70, "rof": 8, "range": 30, "tracking": 10, "size": "S", "damage_type": "explosive", "slot": "high"}),
    "autocannon":      Commodity("Autocannon Mk.I", 10000, tier=5, volume=1.5, description="Rapid-fire ballistic turret spewing kinetic rounds. Cheap to operate and effective against unshielded targets.",
                                 recipe={"railgun_barrel": 1, "steel_plate": 1, "maneuver_thruster": 1}, stats={"cpu": 25, "pg": 15, "dps": 65, "rof": 1.5, "range": 3, "tracking": 10, "size": "S", "damage_type": "kinetic", "slot": "high"}),
    # Ammo
    "railgun_slugs":   Commodity("Railgun Slugs", 1500, tier=5, volume=0.5, description="Fin-stabilized tungsten penetrators designed for electromagnetic launch. Punches through multiple armor layers on impact.",
                                 recipe={"tungsten_carbide": 1, "refined_iron": 1}, stats={"damage": 50, "size": "S", "slot": "ammo"}),
    "light_missiles":  Commodity("Light Missiles", 2000, tier=5, volume=0.8, description="Self-guided explosive ordnance with proximity fuses. Effective against fast-moving frigates and drones.",
                                 recipe={"warhead_assembly": 1, "methane_fuel": 1, "microprocessor": 1}, stats={"damage": 200, "size": "S", "slot": "ammo"}),
    "autocannon_rounds": Commodity("Autocannon Rounds", 800, tier=5, volume=0.4, description="Belted kinetic ammunition with iron-core projectiles. Cheap, plentiful, and brutally effective in volume.",
                                   recipe={"refined_iron": 1, "explosive_compound": 1}, stats={"damage": 15, "size": "S", "slot": "ammo"}),
    # Shields & Defense
    "shield_generator": Commodity("Shield Generator Mk.I", 25000, tier=5, volume=2.5, description="Full-coverage energy barrier projector with omni-directional protection. The first line of defense for any combat vessel.",
                                  recipe={"shield_emitter": 2, "power_cell": 1, "rad_shielding": 1}, stats={"cpu": 30, "pg": 30, "shield_hp": 500, "regen": 10, "size": "S", "slot": "mid"}),
    "shield_booster":  Commodity("Shield Booster", 15000, tier=5, volume=1.5, description="Auxiliary shield amplifier that increases barrier hit points. Stacks with existing shield generators.",
                                 recipe={"shield_emitter": 1, "power_cell": 2}, stats={"cpu": 30, "pg": 30, "shield_hp": 200, "regen": 30, "size": "S", "slot": "mid"}),
    "armor_plates":    Commodity("Armor Plates (Heavy)", 12000, tier=5, volume=3.0, description="Thick composite armor panels bolted to hull hardpoints. Massive passive protection at the cost of added mass.",
                                 recipe={"armor_laminate": 2, "titanium_alloy": 1}, stats={"cpu": 5, "pg": 20, "armor_hp": 800, "mass_penalty": 5000, "size": "S", "slot": "low"}),
    "armor_repairer":  Commodity("Armor Repairer", 18000, tier=5, volume=1.8, description="Active armor restoration system using nanite paste to fill breaches in real-time during combat.",
                                 recipe={"armor_laminate": 1, "nanite_paste": 1, "power_cell": 1}, stats={"cpu": 5, "pg": 20, "repair_rate": 25, "size": "S", "slot": "low"}),
    "point_defense":   Commodity("Point Defense System", 20000, tier=5, volume=1.5, description="Automated anti-missile turret network with predictive tracking. Shoots down incoming ordnance before impact.",
                                 recipe={"pd_array": 1, "sensor_package": 1, "power_cell": 1}, stats={"cpu": 30, "pg": 15, "intercept_rate": 0.75, "range": 5, "slot": "mid"}),
    "ecm_jammer":      Commodity("ECM Jammer", 30000, tier=5, volume=1.0, description="Electronic warfare suite that breaks target locks and scrambles hostile sensors. Makes the pilot a ghost on scanners.",
                                 recipe={"ecm_core": 1, "power_cell": 1}, stats={"cpu": 40, "pg": 10, "jam_strength": 8, "jam_range": 20, "slot": "mid"}),
    # Engines & Propulsion
    "std_engine":      Commodity("Standard Engine Mk.I", 20000, tier=5, volume=3.0, description="Reliable fusion-powered main drive suitable for most vessel classes. Balanced thrust-to-weight ratio.",
                                 recipe={"ion_drive": 1, "fusion_core": 1, "steel_plate": 1}, stats={"cpu": 10, "pg": 30, "speed_bonus": "base", "slot": "engine"}),
    "afterburner":     Commodity("Afterburner", 12000, tier=5, volume=1.5, description="Overclocked thruster module that dumps extra propellant for short speed bursts. Essential for pursuit or escape.",
                                 recipe={"ion_drive": 1, "xenon_propellant": 2, "thruster_nozzle": 1}, stats={"cpu": 15, "pg": 20, "speed_bonus": "+50%", "slot": "mid"}),
    "maneuver_rig":    Commodity("Maneuvering Rig", 10000, tier=5, volume=1.2, description="Integrated attitude control system with paired thrusters. Dramatically improves turning speed and agility.",
                                 recipe={"maneuver_thruster": 2, "nav_computer": 1}, stats={"cpu": 20, "pg": 10, "speed_bonus": "+25% agility", "slot": "mid"}),
    "jump_drive":      Commodity("Jump Drive Mk.I", 50000, tier=5, volume=2.5, description="Faster-than-light propulsion system utilizing quantum-warped spacetime. Crosses star systems in seconds.",
                                 recipe={"warp_coil": 1, "fusion_core": 1, "nav_computer": 1}, stats={"cpu": 30, "pg": 40, "speed_bonus": "warp", "slot": "engine"}),
    # Electronics & Utility
    "scanner_array":   Commodity("Scanner Array", 12000, tier=5, volume=1.0, description="Long-range detection system that reveals hidden objects and anomalies. Essential for exploration and threat awareness.",
                                 recipe={"sensor_package": 2, "nav_computer": 1}, stats={"cpu": 25, "pg": 5, "scan_range": 50, "scan_strength": 30, "slot": "mid"}),
    "cargo_expander":  Commodity("Cargo Expander", 8000, tier=5, volume=2.5, description="Structural reinforcement module that increases hold capacity by compressing existing frame space.",
                                 recipe={"steel_plate": 2, "carbon_composite": 1, "microprocessor": 1}, stats={"cpu": 15, "pg": 5, "cargo_bonus": 50, "slot": "low"}),
    "tractor_beam":    Commodity("Tractor Beam", 10000, tier=5, volume=1.2, description="Ship-mounted graviton projector that pulls cargo, wrecks, and ore chunks into the hold from distance.",
                                 recipe={"tractor_core": 1, "power_cell": 1}, stats={"cpu": 20, "pg": 10, "range": 20, "pull_speed": 500, "slot": "high"}),
    "repair_module":   Commodity("Repair Module", 16000, tier=5, volume=1.5, description="Automated hull restoration system deploying nanites to patch damage. Can repair friendly ships in close proximity.",
                                 recipe={"repair_core": 1, "nanite_paste": 1, "power_cell": 1}, stats={"cpu": 25, "pg": 15, "repair_rate": 40, "range": 5, "slot": "high"}),
    # Drones
    "combat_drone":    Commodity("Combat Drone", 25000, tier=5, volume=2.0, description="Autonomous attack craft with integrated weapons and evasion protocols. Fights alongside its owner without pilot input.",
                                 recipe={"drone_brain": 1, "beam_emitter": 1, "maneuver_thruster": 1, "armor_laminate": 1}, stats={"cpu": 20, "pg": 0, "bandwidth": 25, "dps": 40, "slot": "drone"}),
    "mining_drone":    Commodity("Mining Drone", 20000, tier=5, volume=2.0, description="Self-directed extraction unit that mines asteroids and returns ore to the mothership. Tireless mechanical worker.",
                                 recipe={"drone_brain": 1, "mining_optic": 1, "maneuver_thruster": 1}, stats={"cpu": 15, "pg": 0, "bandwidth": 20, "mining_yield": 15, "slot": "drone"}),
    "repair_drone":    Commodity("Repair Drone", 22000, tier=5, volume=2.0, description="Autonomous maintenance craft that patches hull damage on friendly vessels mid-flight. A fleet commander's best friend.",
                                 recipe={"drone_brain": 1, "repair_core": 1, "maneuver_thruster": 1}, stats={"cpu": 15, "pg": 0, "bandwidth": 20, "repair_rate": 20, "slot": "drone"}),
    # Mining Equipment
    "mining_laser":    Commodity("Mining Laser Mk.I", 10000, tier=5, volume=1.5, description="Ship-mounted extraction beam that fractures asteroids along crystal fault lines. Standard equipment for any miner.",
                                 recipe={"mining_optic": 1, "power_cell": 1, "steel_plate": 1}, stats={"cpu": 20, "pg": 10, "mining_yield": 10, "cycle_time": 5, "slot": "high"}),
    "strip_miner_mod": Commodity("Strip Miner Mk.I", 25000, tier=5, volume=2.5, description="Industrial-grade deep-core extractor that strips entire asteroid faces in one cycle. Slow but enormously productive.",
                                 recipe={"mining_optic": 2, "drill_head": 1, "ore_processor": 1}, stats={"cpu": 35, "pg": 20, "mining_yield": 25, "cycle_time": 10, "slot": "high"}),
    "survey_scanner":  Commodity("Survey Scanner", 8000, tier=5, volume=0.8, description="Specialized geological scanner that reveals asteroid composition before mining. Saves time by identifying rich deposits.",
                                 recipe={"sensor_package": 1, "optical_lens": 1, "nav_computer": 1}, stats={"cpu": 25, "pg": 5, "mining_yield": 0, "cycle_time": 3, "slot": "mid"}),

    # ── T0: Trade Goods (no recipe, generated at hubs, consumed everywhere) ──
    "luxury_goods":    Commodity("Luxury Goods", 700, tier=0, volume=0.5, description="Artisan-crafted items of exceptional quality from core worlds. Status symbols coveted on every frontier station."),
    "consumer_elec":   Commodity("Consumer Electronics", 400, tier=0, volume=0.3, description="Personal devices, datapads, and entertainment systems for station inhabitants. Always in demand."),
    "gourmet_food":    Commodity("Gourmet Food", 250, tier=0, volume=0.6, description="Vacuum-sealed delicacies from agricultural worlds. A welcome change from processed protein rations."),
    "exotic_textiles": Commodity("Exotic Textiles", 500, tier=0, volume=0.4, description="Rare fabrics woven from bio-silk and synthetic fibers. Prized for fashion and environmental suits alike."),
    "entertainment":   Commodity("Entertainment Media", 300, tier=0, volume=0.2, description="Holographic films, neural-link games, and music crystals. Keeps crews sane on long deep-space deployments."),
    "fine_spirits":    Commodity("Fine Spirits", 350, tier=0, volume=0.8, description="Distilled beverages aged in zero-gravity barrels. Every pilot's reward after a successful haul."),

    # ── T5: Sized Weapons (Medium & Large variants) ──────────────────────────
    # Pulse Laser M/L
    "pulse_laser_m":   Commodity("Pulse Laser Mk.II (M)", 24000, tier=5, volume=2.25,
                                 description="Medium-frame pulse laser with doubled capacitor banks. Hits harder per shot with improved heat dissipation.",
                                 recipe={"beam_emitter": 2, "power_cell": 2, "steel_plate": 2}, stats={"cpu": 40, "pg": 25, "dps": 160, "rof": 2, "range": 5, "tracking": 8, "size": "M", "damage_type": "thermal", "slot": "high"}),
    "pulse_laser_l":   Commodity("Pulse Laser Mk.III (L)", 48000, tier=5, volume=3.75,
                                 description="Capital-class pulse laser array delivering devastating burst fire. Requires dedicated power routing to sustain.",
                                 recipe={"beam_emitter": 3, "power_cell": 3, "steel_plate": 3}, stats={"cpu": 60, "pg": 40, "dps": 320, "rof": 2, "range": 5, "tracking": 8, "size": "L", "damage_type": "thermal", "slot": "high"}),
    # Beam Laser M/L
    "beam_laser_m":    Commodity("Beam Laser Mk.II (M)", 36000, tier=5, volume=3.0,
                                 description="Medium-bore sustained laser with extended focal range. Carves through cruiser-weight armor with ease.",
                                 recipe={"beam_emitter": 2, "power_cell": 4, "optical_lens": 2}, stats={"cpu": 40, "pg": 25, "dps": 120, "rof": 4, "range": 20, "tracking": 4, "size": "M", "damage_type": "thermal", "slot": "high"}),
    "beam_laser_l":    Commodity("Beam Laser Mk.III (L)", 72000, tier=5, volume=5.0,
                                 description="Battleship-grade beam weapon that maintains a cutting lance across thousands of kilometers. Melts capital hulls.",
                                 recipe={"beam_emitter": 3, "power_cell": 6, "optical_lens": 3}, stats={"cpu": 60, "pg": 40, "dps": 240, "rof": 4, "range": 20, "tracking": 4, "size": "L", "damage_type": "thermal", "slot": "high"}),
    # Railgun M/L
    "railgun_m":       Commodity("Railgun Mk.II (M)", 44000, tier=5, volume=3.75,
                                 description="Medium-caliber electromagnetic accelerator with enhanced barrel length. Greater muzzle velocity means deeper penetration.",
                                 recipe={"railgun_barrel": 2, "power_cell": 2, "nav_computer": 2}, stats={"cpu": 40, "pg": 25, "dps": 200, "rof": 6, "range": 40, "tracking": 2, "size": "M", "damage_type": "kinetic", "slot": "high"}),
    "railgun_l":       Commodity("Railgun Mk.III (L)", 88000, tier=5, volume=6.25,
                                 description="Siege-class railgun capable of punching through station bulkheads. The sound of its capacitor charging terrifies crews.",
                                 recipe={"railgun_barrel": 3, "power_cell": 3, "nav_computer": 3}, stats={"cpu": 60, "pg": 40, "dps": 400, "rof": 6, "range": 40, "tracking": 2, "size": "L", "damage_type": "kinetic", "slot": "high"}),
    # Plasma Cannon M/L
    "plasma_cannon_m": Commodity("Plasma Cannon Mk.II (M)", 40000, tier=5, volume=3.0,
                                 description="Medium plasma projector with dual containment chambers. Launches larger bolts that splash across hull surfaces.",
                                 recipe={"plasma_chamber": 2, "power_cell": 2, "thruster_nozzle": 2}, stats={"cpu": 40, "pg": 25, "dps": 180, "rof": 5, "range": 10, "tracking": 6, "size": "M", "damage_type": "thermal", "slot": "high"}),
    "plasma_cannon_l": Commodity("Plasma Cannon Mk.III (L)", 80000, tier=5, volume=5.0,
                                 description="Capital-grade plasma siege weapon that fires building-sized bolts of stellar matter. Reduces battleships to slag.",
                                 recipe={"plasma_chamber": 3, "power_cell": 3, "thruster_nozzle": 3}, stats={"cpu": 60, "pg": 40, "dps": 360, "rof": 5, "range": 10, "tracking": 6, "size": "L", "damage_type": "thermal", "slot": "high"}),
    # Missile Launcher M/L
    "missile_launcher_m": Commodity("Missile Launcher Mk.II (M)", 30000, tier=5, volume=3.0,
                                    description="Medium missile battery with expanded magazine and multi-target lock capability. Fires salvos of guided ordnance.",
                                    recipe={"missile_chassis": 2, "sensor_package": 2, "steel_plate": 2}, stats={"cpu": 40, "pg": 25, "dps": 140, "rof": 8, "range": 30, "tracking": 10, "size": "M", "damage_type": "explosive", "slot": "high"}),
    "missile_launcher_l": Commodity("Missile Launcher Mk.III (L)", 60000, tier=5, volume=5.0,
                                    description="Capital torpedo delivery system housing heavy anti-ship munitions. Each launch can cripple a battlecruiser.",
                                    recipe={"missile_chassis": 3, "sensor_package": 3, "steel_plate": 3}, stats={"cpu": 60, "pg": 40, "dps": 280, "rof": 8, "range": 30, "tracking": 10, "size": "L", "damage_type": "explosive", "slot": "high"}),
    # Autocannon M/L
    "autocannon_m":    Commodity("Autocannon Mk.II (M)", 20000, tier=5, volume=2.25,
                                 description="Twin-linked medium autocannon with belt-fed ammunition. Puts out a withering hail of kinetic projectiles.",
                                 recipe={"railgun_barrel": 2, "steel_plate": 2, "maneuver_thruster": 2}, stats={"cpu": 40, "pg": 25, "dps": 130, "rof": 1.5, "range": 3, "tracking": 10, "size": "M", "damage_type": "kinetic", "slot": "high"}),
    "autocannon_l":    Commodity("Autocannon Mk.III (L)", 40000, tier=5, volume=3.75,
                                 description="Heavy rotary cannon designed for capital ship broadsides. Chews through armor with sheer volume of fire.",
                                 recipe={"railgun_barrel": 3, "steel_plate": 3, "maneuver_thruster": 3}, stats={"cpu": 60, "pg": 40, "dps": 260, "rof": 1.5, "range": 3, "tracking": 10, "size": "L", "damage_type": "kinetic", "slot": "high"}),

    # ── T5: Sized Shields & Armor (Medium & Large variants) ──────────────────
    # Shield Generator M/L
    "shield_gen_m":    Commodity("Shield Generator Mk.II (M)", 50000, tier=5, volume=3.75,
                                 description="Medium-class shield projector with reinforced emitters. Provides cruiser-grade protection against sustained fire.",
                                 recipe={"shield_emitter": 4, "power_cell": 2, "rad_shielding": 2}, stats={"cpu": 45, "pg": 50, "shield_hp": 1200, "regen": 25, "size": "M", "slot": "mid"}),
    "shield_gen_l":    Commodity("Shield Generator Mk.III (L)", 100000, tier=5, volume=6.25,
                                 description="Capital shield array projecting an immense energy barrier. Can absorb dreadnought-class bombardment before failing.",
                                 recipe={"shield_emitter": 6, "power_cell": 3, "rad_shielding": 3}, stats={"cpu": 65, "pg": 80, "shield_hp": 3000, "regen": 60, "size": "L", "slot": "mid"}),
    # Shield Booster M/L
    "shield_booster_m": Commodity("Shield Booster Mk.II (M)", 30000, tier=5, volume=2.25,
                                  description="Medium auxiliary shield amplifier with dedicated power feeds. Significantly extends barrier endurance under fire.",
                                  recipe={"shield_emitter": 2, "power_cell": 4}, stats={"cpu": 45, "pg": 50, "shield_hp": 500, "regen": 70, "size": "M", "slot": "mid"}),
    "shield_booster_l": Commodity("Shield Booster Mk.III (L)", 60000, tier=5, volume=3.75,
                                  description="Capital-grade shield reinforcement module. Adds enormous hit point reserves to existing shield arrays.",
                                  recipe={"shield_emitter": 3, "power_cell": 6}, stats={"cpu": 65, "pg": 80, "shield_hp": 1200, "regen": 150, "size": "L", "slot": "mid"}),
    # Armor Plates M/L
    "armor_plates_m":  Commodity("Armor Plates Mk.II (M)", 24000, tier=5, volume=4.5,
                                 description="Cruiser-weight composite armor panels with enhanced laminate layering. Shrugs off medium-caliber weapons fire.",
                                 recipe={"armor_laminate": 4, "titanium_alloy": 2}, stats={"cpu": 8, "pg": 35, "armor_hp": 2000, "mass_penalty": 15000, "size": "M", "slot": "low"}),
    "armor_plates_l":  Commodity("Armor Plates Mk.III (L)", 48000, tier=5, volume=7.5,
                                 description="Battleship-grade armor plating meters thick. Requires structural reinforcement to mount but renders hulls nearly impervious.",
                                 recipe={"armor_laminate": 6, "titanium_alloy": 3}, stats={"cpu": 12, "pg": 55, "armor_hp": 5000, "mass_penalty": 40000, "size": "L", "slot": "low"}),

    # ── T5: Sized Ammo (Medium & Large variants) ─────────────────────────────
    # Railgun Slugs M/L
    "railgun_slugs_m": Commodity("Railgun Slugs (M)", 3000, tier=5, volume=0.75,
                                 description="Medium-caliber tungsten penetrators with sabot casings. Designed for cruiser-class railgun bores.",
                                 recipe={"tungsten_carbide": 2, "refined_iron": 2}, stats={"damage": 100, "size": "M", "slot": "ammo"}),
    "railgun_slugs_l": Commodity("Railgun Slugs (L)", 6000, tier=5, volume=1.25,
                                 description="Massive armor-piercing darts for capital railguns. Each slug weighs as much as a small shuttle.",
                                 recipe={"tungsten_carbide": 3, "refined_iron": 3}, stats={"damage": 200, "size": "L", "slot": "ammo"}),
    # Missiles S/M/L (S = existing light_missiles)
    "missiles_m":      Commodity("Medium Missiles", 4000, tier=5, volume=1.2,
                                 description="Cruiser-weight guided munitions with enlarged warheads and extended fuel reserves. Tracks targets across vast distances.",
                                 recipe={"warhead_assembly": 2, "methane_fuel": 2, "microprocessor": 2}, stats={"damage": 400, "size": "M", "slot": "ammo"}),
    "missiles_l":      Commodity("Heavy Torpedoes", 8000, tier=5, volume=2.0,
                                 description="Capital-class anti-ship torpedoes with massive explosive yield. Slow but devastating on impact with large targets.",
                                 recipe={"warhead_assembly": 3, "methane_fuel": 3, "microprocessor": 3}, stats={"damage": 800, "size": "L", "slot": "ammo"}),
    # Autocannon Rounds M/L
    "autocannon_rounds_m": Commodity("Autocannon Rounds (M)", 1600, tier=5, volume=0.6,
                                     description="Medium-bore belted ammunition with hardened steel cores. Feeds twin-linked autocannon systems.",
                                     recipe={"refined_iron": 2, "explosive_compound": 2}, stats={"damage": 30, "size": "M", "slot": "ammo"}),
    "autocannon_rounds_l": Commodity("Autocannon Rounds (L)", 3200, tier=5, volume=1.0,
                                     description="Heavy rotary cannon shells the size of a fist. Punches through armor plating with brute kinetic force.",
                                     recipe={"refined_iron": 3, "explosive_compound": 3}, stats={"damage": 60, "size": "L", "slot": "ammo"}),
    # Heavy Torpedoes (L-only, standalone)
    "heavy_torpedoes": Commodity("Heavy Torpedoes (Siege)", 12000, tier=5, volume=2.5,
                                 description="Siege-grade anti-capital torpedoes with shaped-charge warheads. Designed to crack station armor and dreadnought hulls.",
                                 recipe={"warhead_assembly": 3, "explosive_compound": 2, "fusion_pellet": 1, "microprocessor": 1}, stats={"damage": 2000, "size": "L", "slot": "ammo"}),
    # Plasma Charges S/M/L (new ammo type for plasma cannons)
    "plasma_charges_s": Commodity("Plasma Charges (S)", 1200, tier=5, volume=0.4,
                                  description="Compressed plasma cartridges pre-heated to ignition temperature. Feed small plasma cannons for rapid bolt discharge.",
                                  recipe={"enriched_he3": 1, "ceramic_plate": 1}, stats={"damage": 40, "size": "S", "slot": "ammo"}),
    "plasma_charges_m": Commodity("Plasma Charges (M)", 2400, tier=5, volume=0.6,
                                  description="Medium plasma fuel cells with magnetic containment. Powers cruiser-class plasma cannons for sustained engagements.",
                                  recipe={"enriched_he3": 2, "ceramic_plate": 2}, stats={"damage": 80, "size": "M", "slot": "ammo"}),
    "plasma_charges_l": Commodity("Plasma Charges (L)", 4800, tier=5, volume=1.0,
                                  description="Massive plasma fuel canisters for capital weapons. Each charge contains enough superheated matter to slag a frigate.",
                                  recipe={"enriched_he3": 3, "ceramic_plate": 3}, stats={"damage": 160, "size": "L", "slot": "ammo"}),
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
