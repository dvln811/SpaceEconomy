"""Seed data for the 48-system universe with 5-tier production chain economy."""
import math
from server.models import System, Station, AsteroidField, SystemObject


# Ore pools by security level
_COMMON_ORES = ["iron_ore", "copper_ore", "calcite", "carbonite", "hydral_ice", "silicon_ore"]
_UNCOMMON_ORES = ["cobalt_ore", "zinc_ore", "tin_ore", "nitrogen_ice", "methane_ice", "biomass", "nickel_ore"]
_RARE_ORES = ["titanium_ore", "tungsten_ore", "chromium_ore", "helium3", "xenon_gas", "spore_clusters", "amino_gel"]
_EXOTIC_ORES = ["platinum_ore", "gold_ore", "palladium_ore", "quartz_crystal", "lithium_crystal", "beryllium_crystal", "kraxolite", "void_shard", "neutronium"]


def _generate_system_objects(system: System) -> list[SystemObject]:
    """Generate intra-system objects (star, gates, stations, belts, planets) with polar positions."""
    objects = []

    objects.append(SystemObject(
        id=f"{system.id}_star", name=f"{system.name} Star",
        obj_type="star", distance=0, angle=0
    ))

    for i, conn in enumerate(system.connections):
        angle = (2 * math.pi * i) / max(len(system.connections), 1)
        objects.append(SystemObject(
            id=f"{system.id}_gate_{conn}", name=f"Gate to {conn.title()}",
            obj_type="gate", distance=10.0 + (i % 3) * 1.5, angle=angle,
            connects_to=conn
        ))

    for i, station in enumerate(system.stations):
        angle = (2 * math.pi * i) / max(len(system.stations), 1) + 0.5
        objects.append(SystemObject(
            id=f"{system.id}_st_{i}", name=station.name,
            obj_type="station", distance=3.0 + i * 1.5, angle=angle
        ))

    for i, belt in enumerate(system.asteroid_fields):
        angle = (2 * math.pi * (i + 0.3)) / max(len(system.asteroid_fields), 1) + 1.2
        objects.append(SystemObject(
            id=f"{system.id}_belt_{i}", name=belt.name,
            obj_type="asteroid_belt", distance=5.0 + i * 2.0, angle=angle
        ))

    planet_count = 2 + (hash(system.id) % 3)
    for i in range(planet_count):
        angle = (2 * math.pi * i) / planet_count + 0.8
        planet_id = f"{system.id}_planet_{i}"
        objects.append(SystemObject(
            id=planet_id, name=f"{system.name} {['I','II','III','IV'][i]}",
            obj_type="planet", distance=1.5 + i * 1.2, angle=angle
        ))
        moon_count = (hash(planet_id) % 3)
        for m in range(moon_count):
            objects.append(SystemObject(
                id=f"{planet_id}_moon_{m}", name=f"{['I','II','III','IV'][i]}-{'ab'[m]}",
                obj_type="moon", distance=1.5 + i * 1.2 + 0.3 + m * 0.2,
                angle=angle + 0.05 + m * 0.08, parent=planet_id
            ))

    return objects


def _core_systems() -> dict[str, System]:
    """Core cluster: 12 high-sec systems."""
    s = {}

    s["cygnus"] = System(
        id="cygnus", name="Cygnus", system_type="industrial",
        cluster="core", security="high", x=0, y=0, z=0,
        stations=[
            Station("Cygnus Refinery", "cygnus", station_type="refinery",
                    produces=["refined_iron", "refined_copper", "purified_water"],
                    inventory={"iron_ore": 1200, "copper_ore": 1000, "refined_iron": 400, "refined_copper": 300, "purified_water": 200},
                    production_rate=0.3),
            Station("Cygnus Trade Hub", "cygnus", station_type="trade_hub",
                    inventory={"hydrogen_fuel": 300, "purified_water": 200, "steel_plate": 80, "power_cell": 30}),
        ],
        asteroid_fields=[AsteroidField("Cygnus Iron Belt", "iron_belt", ["iron_ore", "copper_ore", "calcite"], density=1.0)],
        connections=["kepler", "procyon", "tau_ceti", "sirius"],
    )

    s["kepler"] = System(
        id="kepler", name="Kepler", system_type="trade",
        cluster="core", security="high", x=-200, y=-40, z=150,
        stations=[
            Station("Grand Exchange", "kepler", station_type="trade_hub",
                    inventory={"refined_iron": 400, "refined_copper": 300, "steel_plate": 80, "titanium_alloy": 60, "hydrogen_fuel": 500, "purified_water": 300, "pulse_laser": 15, "shield_generator": 12}),
            Station("Kepler Fuel Depot", "kepler", station_type="refinery",
                    produces=["hydrogen_fuel", "purified_water"],
                    inventory={"hydral_ice": 1200, "silicon_ore": 800, "hydrogen_fuel": 500, "purified_water": 300},
                    production_rate=0.3),
        ],
        asteroid_fields=[AsteroidField("Kepler Ice Ring", "ice_field", ["hydral_ice", "silicon_ore"], density=0.8)],
        connections=["cygnus", "tau_ceti", "polaris", "altair"],
    )

    s["tau_ceti"] = System(
        id="tau_ceti", name="Tau Ceti", system_type="agricultural",
        cluster="core", security="high", x=-300, y=-70, z=-120,
        stations=[
            Station("Tau Ceti Agri-Hub", "tau_ceti", station_type="refinery",
                    produces=["processed_protein", "bio_catalyst", "purified_water"],
                    inventory={"carbonite": 1500, "hydral_ice": 1000, "processed_protein": 400, "bio_catalyst": 200, "purified_water": 300},
                    production_rate=0.3),
        ],
        asteroid_fields=[
            AsteroidField("Bio-Rich Field", "organic", ["carbonite", "calcite"], density=1.2),
            AsteroidField("Tau Ceti Ice Band", "ice_field", ["hydral_ice", "silicon_ore"], density=0.7),
        ],
        connections=["cygnus", "kepler", "fomalhaut", "deneb"],
    )

    s["procyon"] = System(
        id="procyon", name="Procyon", system_type="nexus",
        cluster="core", security="high", x=60, y=-90, z=280,
        stations=[
            Station("Procyon Component Works", "procyon", station_type="component_factory",
                    produces=["nav_computer", "sensor_package", "ecm_core"],
                    inventory={"microprocessor": 80, "optical_lens": 50, "superconductor": 40, "nav_computer": 25, "sensor_package": 20, "ecm_core": 20},
                    production_rate=0.08),
            Station("Gateway Station", "procyon", station_type="trade_hub",
                    inventory={"hydrogen_fuel": 400, "purified_water": 200, "steel_plate": 60}),
        ],
        connections=["cygnus", "polaris", "castor", "arcturus", "sol"],
    )

    s["sirius"] = System(
        id="sirius", name="Sirius", system_type="shipyard",
        cluster="core", security="high", x=-380, y=50, z=200,
        stations=[
            Station("Sirius Dockyard", "sirius", station_type="shipyard",
                    produces=["pulse_laser", "shield_generator", "std_engine", "armor_plates"],
                    inventory={"beam_emitter": 30, "shield_emitter": 25, "fusion_core": 20, "ion_drive": 15, "pulse_laser": 10, "shield_generator": 8, "std_engine": 8, "armor_plates": 12},
                    production_rate=0.04),
            Station("Sirius Supply Depot", "sirius", station_type="trade_hub",
                    inventory={"hydrogen_fuel": 300, "purified_water": 150, "steel_plate": 50}),
        ],
        connections=["cygnus", "deneb", "betelgeuse", "vega_prime"],
    )

    s["deneb"] = System(
        id="deneb", name="Deneb", system_type="military",
        cluster="core", security="high", x=-480, y=30, z=-50,
        stations=[
            Station("Fleet Command", "deneb", station_type="military_base",
                    inventory={"pulse_laser": 15, "combat_drone": 10, "shield_generator": 12, "hydrogen_fuel": 400, "purified_water": 200}),
            Station("Deneb Arms Factory", "deneb", station_type="component_factory",
                    produces=["beam_emitter", "warhead_assembly", "plasma_chamber"],
                    inventory={"microprocessor": 60, "superconductor": 40, "power_cell": 30, "beam_emitter": 25, "warhead_assembly": 20, "plasma_chamber": 20},
                    production_rate=0.08),
        ],
        connections=["tau_ceti", "sirius", "aldebaran", "sol"],
    )

    s["polaris"] = System(
        id="polaris", name="Polaris", system_type="industrial",
        cluster="core", security="high", x=-100, y=-80, z=420,
        stations=[
            Station("Polaris Industrial Complex", "polaris", station_type="industrial_hub",
                    produces=["steel_plate", "ceramic_plate", "synthetic_polymer"],
                    inventory={"refined_iron": 400, "refined_copper": 300, "industrial_solvent": 200, "steel_plate": 80, "ceramic_plate": 60, "synthetic_polymer": 50},
                    production_rate=0.15),
            Station("Polaris Market", "polaris", station_type="trade_hub",
                    inventory={"hydrogen_fuel": 300, "purified_water": 200, "steel_plate": 70}),
        ],
        connections=["kepler", "procyon", "capella", "haven", "hydra"],
    )

    s["fomalhaut"] = System(
        id="fomalhaut", name="Fomalhaut", system_type="processing",
        cluster="core", security="high", x=-200, y=110, z=-480,
        stations=[
            Station("Fomalhaut Refinery", "fomalhaut", station_type="refinery",
                    produces=["refined_iron", "refined_titanium", "industrial_solvent"],
                    inventory={"iron_ore": 1500, "copper_ore": 1000, "refined_iron": 400, "refined_titanium": 200, "industrial_solvent": 250},
                    production_rate=0.3),
        ],
        asteroid_fields=[AsteroidField("Fomalhaut Ore Belt", "iron_belt", ["iron_ore", "copper_ore", "silicon_ore"], density=0.9)],
        connections=["tau_ceti", "aldebaran", "barnards", "meridian", "osiris"],
    )

    s["sol"] = System(
        id="sol", name="Sol", system_type="industrial",
        cluster="core", security="high", x=-50, y=20, z=100,
        stations=[
            Station("Earth Orbital Factory", "sol", station_type="industrial_hub",
                    produces=["microprocessor", "superconductor", "optical_lens"],
                    inventory={"silicon_wafer": 200, "copper_wiring": 150, "lithium_cell": 100, "microprocessor": 80, "superconductor": 60, "optical_lens": 50},
                    production_rate=0.15),
            Station("Mars Trade Port", "sol", station_type="trade_hub",
                    inventory={"hydrogen_fuel": 400, "purified_water": 300, "steel_plate": 70, "pulse_laser": 12, "shield_generator": 10, "std_engine": 8}),
        ],
        connections=["procyon", "deneb", "haven", "arcturus"],
    )

    s["haven"] = System(
        id="haven", name="Haven", system_type="industrial",
        cluster="core", security="high", x=-150, y=-30, z=300,
        stations=[
            Station("Haven Bioworks", "haven", station_type="industrial_hub",
                    produces=["pharma_grade", "nanite_paste", "processed_protein"],
                    inventory={"bio_catalyst": 200, "processed_protein": 300, "industrial_solvent": 150, "pharma_grade": 60, "nanite_paste": 50, "processed_protein": 300},
                    production_rate=0.15),
            Station("Haven Life Systems", "haven", station_type="component_factory",
                    produces=["life_support_core", "mining_optic", "repair_core"],
                    inventory={"power_cell": 40, "microprocessor": 30, "optical_lens": 25, "life_support_core": 20, "mining_optic": 20, "repair_core": 15},
                    production_rate=0.08),
        ],
        connections=["polaris", "sol", "capella", "hydra"],
    )

    s["vega_prime"] = System(
        id="vega_prime", name="Vega Prime", system_type="mining",
        cluster="core", security="high", x=-420, y=80, z=100,
        stations=[
            Station("Vega Prime Mining Co.", "vega_prime", station_type="mining_colony",
                    inventory={"iron_ore": 2000, "copper_ore": 1500, "calcite": 1000, "hydrogen_fuel": 100}),
            Station("Vega Prime Smelter", "vega_prime", station_type="refinery",
                    produces=["refined_iron", "refined_copper"],
                    inventory={"iron_ore": 1000, "copper_ore": 800, "refined_iron": 300, "refined_copper": 250},
                    production_rate=0.3),
        ],
        asteroid_fields=[
            AsteroidField("Vega Prime Iron Belt", "iron_belt", ["iron_ore", "copper_ore", "calcite", "carbonite"], density=1.3),
        ],
        connections=["sirius", "meridian", "betelgeuse"],
    )

    s["meridian"] = System(
        id="meridian", name="Meridian", system_type="processing",
        cluster="core", security="high", x=-350, y=100, z=-300,
        stations=[
            Station("Meridian Refinery", "meridian", station_type="refinery",
                    produces=["refined_titanium", "refined_tungsten", "chromium_plate"],
                    inventory={"iron_ore": 800, "copper_ore": 600, "refined_titanium": 250, "refined_tungsten": 150, "chromium_plate": 150},
                    production_rate=0.3),
        ],
        connections=["fomalhaut", "vega_prime", "aldebaran", "regulus"],
    )

    return s



def _rim_systems() -> dict[str, System]:
    """Rim cluster: 23 med/low-sec systems."""
    s = {}

    s["arcturus"] = System(
        id="arcturus", name="Arcturus", system_type="processing",
        cluster="rim", security="medium", x=250, y=80, z=200,
        stations=[
            Station("Arcturus Gas Refinery", "arcturus", station_type="refinery",
                    produces=["hydrogen_fuel", "methane_fuel", "liquid_nitrogen"],
                    inventory={"methane_ice": 800, "nitrogen_ice": 600, "hydral_ice": 500, "hydrogen_fuel": 400, "methane_fuel": 250, "liquid_nitrogen": 200},
                    production_rate=0.3),
        ],
        asteroid_fields=[AsteroidField("Arcturus Gas Cloud", "gas_pocket", ["methane_ice", "nitrogen_ice", "hydral_ice"], density=1.3)],
        connections=["procyon", "sol", "vega", "antares", "castor", "helios"],
    )

    s["vega"] = System(
        id="vega", name="Vega", system_type="mining",
        cluster="rim", security="medium", x=320, y=60, z=-180,
        stations=[
            Station("Vega Mining Colony", "vega", station_type="mining_colony",
                    inventory={"iron_ore": 2000, "copper_ore": 1200, "cobalt_ore": 600, "nickel_ore": 500, "hydrogen_fuel": 100}),
        ],
        asteroid_fields=[
            AsteroidField("Vega Rich Belt", "iron_belt", ["iron_ore", "copper_ore", "cobalt_ore", "nickel_ore"], density=1.5),
            AsteroidField("Vega Deep Vein", "metallic", ["zinc_ore", "tin_ore", "silicon_ore"], density=0.8),
        ],
        connections=["arcturus", "altair", "antares", "mira"],
    )

    s["altair"] = System(
        id="altair", name="Altair", system_type="trade",
        cluster="rim", security="medium", x=150, y=-110, z=-300,
        stations=[
            Station("Altair Junction Market", "altair", station_type="trade_hub",
                    inventory={"refined_iron": 300, "refined_copper": 250, "steel_plate": 60, "titanium_alloy": 40, "hydrogen_fuel": 300, "purified_water": 200, "pulse_laser": 10, "shield_generator": 8}),
        ],
        connections=["kepler", "vega", "barnards", "castor", "draconis"],
    )

    s["barnards"] = System(
        id="barnards", name="Barnard's Star", system_type="mining",
        cluster="rim", security="medium", x=-150, y=100, z=-320,
        stations=[
            Station("Barnard's Mining Outpost", "barnards", station_type="mining_colony",
                    inventory={"cobalt_ore": 800, "iron_ore": 1500, "nickel_ore": 600, "tin_ore": 500, "hydrogen_fuel": 80}),
        ],
        asteroid_fields=[
            AsteroidField("Barnard's Mixed Field", "metallic", ["cobalt_ore", "iron_ore", "nickel_ore", "tin_ore"], density=1.2),
        ],
        connections=["fomalhaut", "altair", "aldebaran", "wolf359", "osiris", "fornax"],
    )

    s["antares"] = System(
        id="antares", name="Antares", system_type="industrial",
        cluster="rim", security="medium", x=380, y=40, z=80,
        stations=[
            Station("Antares Forge", "antares", station_type="industrial_hub",
                    produces=["steel_plate", "titanium_alloy", "carbon_composite"],
                    inventory={"refined_iron": 350, "refined_titanium": 200, "industrial_solvent": 150, "steel_plate": 70, "titanium_alloy": 50, "carbon_composite": 50},
                    production_rate=0.15),
        ],
        connections=["arcturus", "vega", "achernar", "mira"],
    )

    s["capella"] = System(
        id="capella", name="Capella", system_type="trade",
        cluster="rim", security="medium", x=-350, y=90, z=380,
        stations=[
            Station("Capella Free Market", "capella", station_type="trade_hub",
                    inventory={"steel_plate": 60, "titanium_alloy": 40, "microprocessor": 50, "hydrogen_fuel": 300, "purified_water": 200, "pharma_grade": 40, "shield_generator": 10, "std_engine": 8}),
        ],
        connections=["polaris", "haven", "betelgeuse", "castor", "lyra", "helios"],
    )

    s["betelgeuse"] = System(
        id="betelgeuse", name="Betelgeuse", system_type="shipyard",
        cluster="rim", security="medium", x=200, y=-50, z=450,
        stations=[
            Station("Betelgeuse Drydock", "betelgeuse", station_type="shipyard",
                    produces=["mining_laser", "mining_drone", "repair_module"],
                    inventory={"mining_optic": 25, "drill_head": 20, "drone_brain": 15, "repair_core": 12, "mining_laser": 10, "mining_drone": 8, "repair_module": 8},
                    production_rate=0.04),
        ],
        asteroid_fields=[AsteroidField("Betelgeuse Metallic Belt", "metallic", ["iron_ore", "cobalt_ore", "copper_ore", "zinc_ore"], density=1.0)],
        connections=["sirius", "vega_prime", "capella", "canopus", "corvus"],
    )

    s["castor"] = System(
        id="castor", name="Castor", system_type="nexus",
        cluster="rim", security="medium", x=450, y=80, z=-280,
        stations=[
            Station("Castor Relay", "castor", station_type="trade_hub",
                    inventory={"hydrogen_fuel": 500, "purified_water": 200, "steel_plate": 50}),
        ],
        connections=["procyon", "arcturus", "altair", "capella", "achernar", "wolf359", "rigel"],
    )

    s["achernar"] = System(
        id="achernar", name="Achernar", system_type="military",
        cluster="rim", security="medium", x=300, y=90, z=-450,
        stations=[
            Station("Achernar Forward Base", "achernar", station_type="military_base",
                    inventory={"pulse_laser": 10, "combat_drone": 8, "shield_generator": 8, "hydrogen_fuel": 300, "purified_water": 150}),
        ],
        connections=["antares", "castor", "rigel", "mira"],
    )

    s["aldebaran"] = System(
        id="aldebaran", name="Aldebaran", system_type="mining",
        cluster="rim", security="medium", x=-500, y=70, z=-280,
        stations=[
            Station("Aldebaran Mining Hub", "aldebaran", station_type="mining_colony",
                    inventory={"iron_ore": 2000, "copper_ore": 1200, "cobalt_ore": 700, "biomass": 500, "hydrogen_fuel": 80}),
        ],
        asteroid_fields=[AsteroidField("Aldebaran Dense Belt", "iron_belt", ["iron_ore", "copper_ore", "cobalt_ore", "biomass"], density=1.4)],
        connections=["deneb", "fomalhaut", "meridian", "barnards", "regulus", "osiris"],
    )

    s["regulus"] = System(
        id="regulus", name="Regulus", system_type="mining",
        cluster="rim", security="low", x=-600, y=40, z=150,
        stations=[
            Station("Regulus Crystal Mine", "regulus", station_type="mining_colony",
                    inventory={"titanium_ore": 100, "tungsten_ore": 100, "chromium_ore": 100, "iron_ore": 800, "hydrogen_fuel": 60}),
        ],
        asteroid_fields=[AsteroidField("Regulus Deep Vein", "metallic", ["titanium_ore", "tungsten_ore", "chromium_ore", "iron_ore", "copper_ore"], density=0.8, danger=0.1)],
        connections=["meridian", "aldebaran", "pollux", "lyra"],
    )

    s["mira"] = System(
        id="mira", name="Mira", system_type="industrial",
        cluster="rim", security="medium", x=400, y=-20, z=-80,
        stations=[
            Station("Mira Polymer Works", "mira", station_type="industrial_hub",
                    produces=["synthetic_polymer", "carbon_composite", "copper_wiring"],
                    inventory={"refined_copper": 300, "industrial_solvent": 150, "hydrogen_fuel": 200, "synthetic_polymer": 70, "carbon_composite": 50, "copper_wiring": 60},
                    production_rate=0.15),
        ],
        connections=["vega", "antares", "achernar", "novus", "aquila"],
    )

    s["draconis"] = System(
        id="draconis", name="Draconis", system_type="industrial",
        cluster="rim", security="medium", x=100, y=-180, z=-400,
        stations=[
            Station("Draconis Engine Works", "draconis", station_type="component_factory",
                    produces=["ion_drive", "maneuver_thruster", "thruster_nozzle"],
                    inventory={"steel_plate": 60, "titanium_alloy": 40, "superconductor": 30, "ion_drive": 20, "maneuver_thruster": 20, "thruster_nozzle": 25},
                    production_rate=0.08),
        ],
        connections=["altair", "novus", "serpentis", "fornax"],
    )

    s["lyra"] = System(
        id="lyra", name="Lyra", system_type="trade",
        cluster="rim", security="medium", x=-450, y=120, z=250,
        stations=[
            Station("Lyra Medical Station", "lyra", station_type="industrial_hub",
                    produces=["pharma_grade", "nanite_paste", "bio_catalyst"],
                    inventory={"processed_protein": 300, "bio_catalyst": 200, "industrial_solvent": 150, "pharma_grade": 60, "nanite_paste": 50},
                    production_rate=0.15),
            Station("Lyra Bazaar", "lyra", station_type="trade_hub",
                    inventory={"hydrogen_fuel": 200, "purified_water": 150, "pharma_grade": 40, "nanite_paste": 30}),
        ],
        connections=["capella", "regulus", "haven_rim", "pollux", "hydra"],
    )

    s["novus"] = System(
        id="novus", name="Novus", system_type="industrial",
        cluster="rim", security="low", x=500, y=-100, z=-200,
        stations=[
            Station("Novus Alloy Works", "novus", station_type="industrial_hub",
                    produces=["tungsten_carbide", "titanium_alloy", "steel_plate"],
                    inventory={"refined_iron": 300, "refined_titanium": 200, "refined_tungsten": 150, "tungsten_carbide": 50, "titanium_alloy": 50, "steel_plate": 70},
                    production_rate=0.15),
        ],
        connections=["mira", "draconis", "rigel", "serpentis", "aquila"],
    )

    s["serpentis"] = System(
        id="serpentis", name="Serpentis", system_type="trade",
        cluster="rim", security="low", x=350, y=-150, z=-500,
        stations=[
            Station("Serpentis Black Market", "serpentis", station_type="trade_hub",
                    inventory={"pulse_laser": 8, "combat_drone": 5, "explosive_compound": 40, "hydrogen_fuel": 100, "purified_water": 60}),
        ],
        connections=["draconis", "novus", "pollux", "void", "nyx"],
    )

    s["haven_rim"] = System(
        id="haven_rim", name="Haven's Edge", system_type="frontier",
        cluster="rim", security="low", x=-500, y=150, z=350,
        stations=[
            Station("Haven's Edge Outpost", "haven_rim", station_type="frontier_outpost",
                    inventory={"hydrogen_fuel": 100, "purified_water": 80, "pharma_grade": 30, "processed_protein": 100}),
        ],
        asteroid_fields=[AsteroidField("Edge Ice Field", "ice_field", ["hydral_ice", "nitrogen_ice", "methane_ice", "biomass"], density=0.9)],
        connections=["lyra", "canopus", "erebus"],
    )

    s["helios"] = System(
        id="helios", name="Helios", system_type="mining",
        cluster="rim", security="medium", x=180, y=130, z=300,
        stations=[
            Station("Helios Gas Platform", "helios", station_type="mining_colony",
                    inventory={"methane_ice": 800, "nitrogen_ice": 600, "hydral_ice": 500, "hydrogen_fuel": 100}),
        ],
        asteroid_fields=[
            AsteroidField("Helios Gas Giant Rings", "gas_pocket", ["methane_ice", "nitrogen_ice", "cobalt_ore"], density=1.5),
            AsteroidField("Helios Ice Halo", "ice_field", ["hydral_ice", "silicon_ore", "calcite"], density=1.0),
        ],
        connections=["arcturus", "capella", "canopus", "corvus"],
    )

    s["osiris"] = System(
        id="osiris", name="Osiris", system_type="agricultural",
        cluster="rim", security="medium", x=-250, y=-50, z=-500,
        stations=[
            Station("Osiris Bio-Farm", "osiris", station_type="refinery",
                    produces=["processed_protein", "bio_catalyst", "purified_water"],
                    inventory={"biomass": 800, "carbonite": 600, "hydral_ice": 500, "processed_protein": 400, "bio_catalyst": 250, "purified_water": 300},
                    production_rate=0.3),
        ],
        asteroid_fields=[AsteroidField("Osiris Organic Cloud", "organic", ["biomass", "carbonite", "calcite"], density=1.3)],
        connections=["barnards", "fomalhaut", "aldebaran", "fornax"],
    )

    s["corvus"] = System(
        id="corvus", name="Corvus", system_type="industrial",
        cluster="rim", security="medium", x=50, y=160, z=500,
        stations=[
            Station("Corvus Assembly Plant", "corvus", station_type="component_factory",
                    produces=["fusion_core", "warp_coil", "life_support_core"],
                    inventory={"superconductor": 40, "power_cell": 30, "magnetic_coil": 25, "fusion_core": 20, "warp_coil": 15, "life_support_core": 18},
                    production_rate=0.08),
        ],
        connections=["helios", "betelgeuse", "canopus", "pyxis"],
    )

    s["fornax"] = System(
        id="fornax", name="Fornax", system_type="processing",
        cluster="rim", security="medium", x=-80, y=-130, z=-250,
        stations=[
            Station("Fornax Titanium Refinery", "fornax", station_type="refinery",
                    produces=["refined_titanium", "refined_iron", "cobalt_ingot"],
                    inventory={"cobalt_ore": 600, "iron_ore": 1000, "nickel_ore": 500, "refined_titanium": 250, "refined_iron": 300, "cobalt_ingot": 200},
                    production_rate=0.3),
        ],
        connections=["barnards", "draconis", "osiris"],
    )

    s["hydra"] = System(
        id="hydra", name="Hydra", system_type="mining",
        cluster="rim", security="medium", x=-300, y=-100, z=200,
        stations=[
            Station("Hydra Ice Works", "hydra", station_type="refinery",
                    produces=["purified_water", "hydrogen_fuel", "liquid_nitrogen"],
                    inventory={"hydral_ice": 1200, "nitrogen_ice": 800, "silicon_ore": 600, "purified_water": 400, "hydrogen_fuel": 350, "liquid_nitrogen": 200},
                    production_rate=0.3),
        ],
        asteroid_fields=[
            AsteroidField("Hydra Ice Shelf", "ice_field", ["hydral_ice", "silicon_ore", "calcite"], density=1.4),
            AsteroidField("Hydra Gas Pocket", "gas_pocket", ["nitrogen_ice", "methane_ice", "carbonite"], density=0.8),
        ],
        connections=["polaris", "haven", "lyra"],
    )

    s["aquila"] = System(
        id="aquila", name="Aquila", system_type="industrial",
        cluster="rim", security="low", x=600, y=50, z=-100,
        stations=[
            Station("Aquila Conductor Labs", "aquila", station_type="industrial_hub",
                    produces=["superconductor", "silicon_wafer", "lithium_cell"],
                    inventory={"refined_copper": 250, "silicon_ore": 500, "lithium_crystal": 100, "superconductor": 50, "silicon_wafer": 60, "lithium_cell": 50},
                    production_rate=0.15),
        ],
        connections=["novus", "mira", "wolf359"],
    )

    return s



def _frontier_systems() -> dict[str, System]:
    """Frontier cluster: 13 low/null-sec systems."""
    s = {}

    s["wolf359"] = System(
        id="wolf359", name="Wolf 359", system_type="frontier",
        cluster="frontier", security="low", x=480, y=120, z=350,
        stations=[
            Station("Wolf 359 Depot", "wolf359", station_type="frontier_outpost",
                    inventory={"hydrogen_fuel": 80, "purified_water": 60, "titanium_ore": 100, "tungsten_ore": 100, "helium3": 100}),
        ],
        asteroid_fields=[AsteroidField("Wolf 359 Rare Deposit", "rare_earth", ["titanium_ore", "tungsten_ore", "helium3", "iron_ore", "cobalt_ore"], density=0.9, danger=0.15)],
        connections=["castor", "barnards", "spica", "obsidian", "aquila"],
    )

    s["rigel"] = System(
        id="rigel", name="Rigel", system_type="frontier",
        cluster="frontier", security="none", x=500, y=-60, z=-100,
        stations=[
            Station("Rigel Salvage Yard", "rigel", station_type="frontier_outpost",
                    inventory={"hydrogen_fuel": 50, "purified_water": 30, "chromium_ore": 100, "xenon_gas": 100}),
        ],
        asteroid_fields=[AsteroidField("Rigel Rare Belt", "rare_earth", ["chromium_ore", "xenon_gas", "titanium_ore", "tungsten_ore", "cobalt_ore", "iron_ore"], density=1.0, danger=0.2)],
        connections=["castor", "achernar", "novus", "void", "terminus"],
    )

    s["pollux"] = System(
        id="pollux", name="Pollux", system_type="frontier",
        cluster="frontier", security="none", x=-400, y=-60, z=-400,
        stations=[
            Station("Pollux Wildcat Mine", "pollux", station_type="mining_colony",
                    inventory={"platinum_ore": 100, "gold_ore": 100, "palladium_ore": 100, "titanium_ore": 100, "hydrogen_fuel": 40}),
        ],
        asteroid_fields=[
            AsteroidField("Pollux Platinum Vein", "dense_asteroid", ["platinum_ore", "gold_ore", "palladium_ore", "titanium_ore", "tungsten_ore"], density=0.7, danger=0.2),
        ],
        connections=["regulus", "lyra", "serpentis", "erebus", "void", "nyx"],
    )

    s["canopus"] = System(
        id="canopus", name="Canopus", system_type="industrial",
        cluster="frontier", security="low", x=100, y=-100, z=600,
        stations=[
            Station("Canopus Rogue Foundry", "canopus", station_type="industrial_hub",
                    produces=["titanium_alloy", "tungsten_carbide", "carbon_composite"],
                    inventory={"refined_titanium": 200, "refined_tungsten": 150, "industrial_solvent": 100, "titanium_alloy": 50, "tungsten_carbide": 40, "carbon_composite": 40},
                    production_rate=0.15),
        ],
        asteroid_fields=[AsteroidField("Canopus Titanium Reef", "metallic", ["titanium_ore", "tungsten_ore", "chromium_ore", "cobalt_ore", "iron_ore"], density=1.2, danger=0.15)],
        connections=["betelgeuse", "haven_rim", "helios", "corvus", "spica", "obsidian", "pyxis"],
    )

    s["spica"] = System(
        id="spica", name="Spica", system_type="nexus",
        cluster="frontier", security="none", x=600, y=-30, z=200,
        stations=[
            Station("Spica Ghost Gate", "spica", station_type="frontier_outpost",
                    inventory={"hydrogen_fuel": 60, "purified_water": 30, "xenon_gas": 100}),
        ],
        connections=["wolf359", "canopus", "terminus", "obsidian", "abyss"],
    )

    s["void"] = System(
        id="void", name="The Void", system_type="frontier",
        cluster="frontier", security="none", x=550, y=-180, z=-350,
        stations=[
            Station("Void Station", "void", station_type="frontier_outpost",
                    inventory={"neutronium": 100, "void_shard": 100, "hydrogen_fuel": 30, "purified_water": 20}),
        ],
        asteroid_fields=[AsteroidField("Void Deep Core", "deep_core", ["neutronium", "void_shard", "platinum_ore", "gold_ore", "xenon_gas", "helium3"], density=0.5, danger=0.3)],
        connections=["serpentis", "rigel", "pollux", "terminus", "abyss"],
    )

    s["terminus"] = System(
        id="terminus", name="Terminus", system_type="frontier",
        cluster="frontier", security="none", x=700, y=-100, z=0,
        stations=[
            Station("Terminus Outpost", "terminus", station_type="frontier_outpost",
                    inventory={"quartz_crystal": 100, "lithium_crystal": 100, "beryllium_crystal": 100, "hydrogen_fuel": 25, "purified_water": 20}),
        ],
        asteroid_fields=[AsteroidField("Terminus Crystal Formation", "crystal", ["quartz_crystal", "lithium_crystal", "beryllium_crystal", "platinum_ore"], density=0.9, danger=0.25)],
        connections=["rigel", "spica", "void", "abyss"],
    )

    s["obsidian"] = System(
        id="obsidian", name="Obsidian", system_type="frontier",
        cluster="frontier", security="none", x=350, y=200, z=500,
        stations=[
            Station("Obsidian Rock", "obsidian", station_type="mining_colony",
                    inventory={"kraxolite": 100, "void_shard": 100, "quartz_crystal": 100, "platinum_ore": 100, "hydrogen_fuel": 25}),
        ],
        asteroid_fields=[
            AsteroidField("Obsidian Exotic Deposit", "rare_earth", ["kraxolite", "void_shard", "platinum_ore", "gold_ore", "titanium_ore"], density=1.1, danger=0.2),
            AsteroidField("Obsidian Crystal Cave", "crystal", ["quartz_crystal", "lithium_crystal", "beryllium_crystal"], density=0.6, danger=0.25),
        ],
        connections=["wolf359", "canopus", "spica", "phantom", "pyxis"],
    )

    s["erebus"] = System(
        id="erebus", name="Erebus", system_type="frontier",
        cluster="frontier", security="none", x=-550, y=180, z=400,
        stations=[
            Station("Erebus Deep Mine", "erebus", station_type="mining_colony",
                    inventory={"palladium_ore": 100, "neutronium": 100, "void_shard": 100, "gold_ore": 100, "hydrogen_fuel": 20}),
        ],
        asteroid_fields=[
            AsteroidField("Erebus Exotic Pocket", "dense_asteroid", ["palladium_ore", "gold_ore", "platinum_ore", "neutronium"], density=0.6, danger=0.25),
            AsteroidField("Erebus Void Belt", "deep_core", ["void_shard", "neutronium", "kraxolite"], density=0.4, danger=0.35),
        ],
        connections=["haven_rim", "pollux", "phantom", "nyx"],
    )

    s["phantom"] = System(
        id="phantom", name="Phantom", system_type="frontier",
        cluster="frontier", security="none", x=-300, y=250, z=600,
        stations=[
            Station("Phantom Station", "phantom", station_type="frontier_outpost",
                    inventory={"hydrogen_fuel": 15, "purified_water": 10, "neutronium": 100, "kraxolite": 100, "void_shard": 100}),
        ],
        asteroid_fields=[
            AsteroidField("Phantom Anomaly", "deep_core", ["neutronium", "kraxolite", "void_shard", "platinum_ore", "palladium_ore", "beryllium_crystal"], density=0.5, danger=0.35),
        ],
        connections=["erebus", "obsidian", "abyss"],
    )

    s["abyss"] = System(
        id="abyss", name="The Abyss", system_type="frontier",
        cluster="frontier", security="none", x=650, y=-200, z=400,
        stations=[
            Station("Abyss Beacon", "abyss", station_type="frontier_outpost",
                    inventory={"hydrogen_fuel": 10, "purified_water": 10}),
        ],
        asteroid_fields=[
            AsteroidField("Abyss Neutronium Trench", "deep_core", ["neutronium", "void_shard", "kraxolite", "palladium_ore"], density=0.8, danger=0.4),
            AsteroidField("Abyss Crystal Rift", "crystal", ["beryllium_crystal", "lithium_crystal", "quartz_crystal", "gold_ore", "platinum_ore"], density=0.7, danger=0.35),
        ],
        connections=["spica", "void", "terminus", "phantom"],
    )

    s["pyxis"] = System(
        id="pyxis", name="Pyxis", system_type="mining",
        cluster="frontier", security="low", x=250, y=250, z=550,
        stations=[
            Station("Pyxis Fuel Cache", "pyxis", station_type="frontier_outpost",
                    inventory={"helium3": 100, "xenon_gas": 100, "spore_clusters": 100, "hydrogen_fuel": 80, "purified_water": 50}),
        ],
        asteroid_fields=[
            AsteroidField("Pyxis Gas Nebula", "gas_pocket", ["helium3", "xenon_gas", "spore_clusters", "amino_gel", "methane_ice"], density=1.4, danger=0.1),
            AsteroidField("Pyxis Ice Drift", "ice_field", ["hydral_ice", "nitrogen_ice", "silicon_ore"], density=1.0),
        ],
        connections=["corvus", "canopus", "obsidian"],
    )

    s["nyx"] = System(
        id="nyx", name="Nyx", system_type="industrial",
        cluster="frontier", security="none", x=-200, y=-150, z=-550,
        stations=[
            Station("Nyx Shadow Factory", "nyx", station_type="component_factory",
                    produces=["warhead_assembly", "plasma_chamber", "railgun_barrel"],
                    inventory={"explosive_compound": 40, "titanium_alloy": 50, "microprocessor": 30, "warhead_assembly": 20, "plasma_chamber": 15, "railgun_barrel": 15},
                    production_rate=0.08),
        ],
        connections=["pollux", "serpentis", "erebus"],
    )

    return s


def build_universe() -> dict[str, System]:
    """Build and return the full 48-system universe."""
    systems = {}
    systems.update(_core_systems())
    systems.update(_rim_systems())
    systems.update(_frontier_systems())

    for sys in systems.values():
        sys.objects = _generate_system_objects(sys)

    return systems
