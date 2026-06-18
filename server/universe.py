"""Seed data for the 48-system universe with 5-tier production chain economy."""
import math
from server.models import System, Station, AsteroidField, SystemObject


def _generate_system_objects(system: System) -> list[SystemObject]:
    """Generate intra-system objects (star, gates, stations, belts, planets) with polar positions."""
    objects = []

    # Star at center
    objects.append(SystemObject(
        id=f"{system.id}_star", name=f"{system.name} Star",
        obj_type="star", distance=0, angle=0
    ))

    # Jump gates - outer ring (10-13 AU)
    for i, conn in enumerate(system.connections):
        angle = (2 * math.pi * i) / max(len(system.connections), 1)
        objects.append(SystemObject(
            id=f"{system.id}_gate_{conn}", name=f"Gate to {conn.title()}",
            obj_type="gate", distance=10.0 + (i % 3) * 1.5, angle=angle,
            connects_to=conn
        ))

    # Stations - mid ring (3-7 AU)
    for i, station in enumerate(system.stations):
        angle = (2 * math.pi * i) / max(len(system.stations), 1) + 0.5
        objects.append(SystemObject(
            id=f"{system.id}_st_{i}", name=station.name,
            obj_type="station", distance=3.0 + i * 1.5, angle=angle
        ))

    # Asteroid belts (4-9 AU)
    for i, belt in enumerate(system.asteroid_fields):
        angle = (2 * math.pi * (i + 0.3)) / max(len(system.asteroid_fields), 1) + 1.2
        objects.append(SystemObject(
            id=f"{system.id}_belt_{i}", name=belt.name,
            obj_type="asteroid_belt", distance=5.0 + i * 2.0, angle=angle
        ))

    # Planets (1.5-4 AU)
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
    """Core cluster: 12 high-sec systems. Refineries, factories, shipyards, trade hubs."""
    s = {}

    # ── Cygnus: Industrial hub, refinery ──
    s["cygnus"] = System(
        id="cygnus", name="Cygnus", system_type="industrial",
        cluster="core", security="high", x=0, y=0, z=0,
        stations=[
            Station("Cygnus Refinery", "cygnus", station_type="refinery",
                    produces=["refined_iron", "refined_copper"],
                    inventory={"iron_ore": 200, "copper_ore": 150, "refined_iron": 80, "refined_copper": 60},
                    production_rate=2.0),
            Station("Cygnus Trade Hub", "cygnus", station_type="trade_hub",
                    inventory={"processed_food": 100, "hydrogen_fuel": 80, "water": 60, "luxury_goods": 40, "consumer_electronics": 50, "gourmet_food": 30, "fine_spirits": 25}),
        ],
        asteroid_fields=[AsteroidField("Cygnus Iron Belt", "iron_belt", ["iron_ore", "copper_ore"], density=1.0)],
        connections=["kepler", "procyon", "tau_ceti", "sirius"],
    )

    # ── Kepler: Major trade hub ──
    s["kepler"] = System(
        id="kepler", name="Kepler", system_type="trade",
        cluster="core", security="high", x=-200, y=-40, z=150,
        stations=[
            Station("Grand Exchange", "kepler", station_type="trade_hub",
                    inventory={"refined_iron": 100, "steel_alloy": 60, "electronics": 40, "processed_food": 200, "hydrogen_fuel": 150, "luxury_goods": 60, "exotic_textiles": 40, "entertainment_media": 50, "consumer_electronics": 45, "gourmet_food": 35, "fine_spirits": 30}),
            Station("Kepler Fuel Depot", "kepler", station_type="refinery",
                    produces=["hydrogen_fuel", "water"],
                    inventory={"ice": 100, "helium3": 80, "hydrogen_fuel": 200, "water": 100},
                    production_rate=1.5),
        ],
        asteroid_fields=[AsteroidField("Kepler Ice Ring", "ice_field", ["ice"], density=0.8)],
        connections=["cygnus", "tau_ceti", "polaris", "altair"],
    )

    # ── Tau Ceti: Agricultural, organics processing ──
    s["tau_ceti"] = System(
        id="tau_ceti", name="Tau Ceti", system_type="agricultural",
        cluster="core", security="high", x=-300, y=-70, z=-120,
        stations=[
            Station("Tau Ceti Agri-Hub", "tau_ceti", station_type="refinery",
                    produces=["processed_food", "chemicals"],
                    inventory={"organics": 300, "ice": 100, "water": 80, "processed_food": 400, "chemicals": 150},
                    production_rate=2.5),
        ],
        asteroid_fields=[
            AsteroidField("Bio-Rich Field", "organic", ["organics"], density=1.2),
            AsteroidField("Tau Ceti Ice Band", "ice_field", ["ice"], density=0.7),
        ],
        connections=["cygnus", "kepler", "fomalhaut", "deneb"],
    )

    # ── Procyon: Nexus chokepoint, component factory ──
    s["procyon"] = System(
        id="procyon", name="Procyon", system_type="nexus",
        cluster="core", security="high", x=60, y=-90, z=280,
        stations=[
            Station("Procyon Component Works", "procyon", station_type="component_factory",
                    produces=["electronics", "nav_arrays"],
                    inventory={"superconductors": 40, "glass": 30, "electronics": 60, "nav_arrays": 25},
                    production_rate=1.0),
            Station("Gateway Station", "procyon", station_type="trade_hub",
                    inventory={"hydrogen_fuel": 200, "processed_food": 100}),
        ],
        connections=["cygnus", "polaris", "castor", "arcturus", "sol"],
    )

    # ── Sirius: Shipyard ──
    s["sirius"] = System(
        id="sirius", name="Sirius", system_type="shipyard",
        cluster="core", security="high", x=-380, y=50, z=200,
        stations=[
            Station("Sirius Dockyard", "sirius", station_type="shipyard",
                    produces=["ship_modules", "station_modules"],
                    inventory={"hull_plating": 30, "life_support": 20, "engine_parts": 25, "reactor_cores": 10, "ship_modules": 8, "station_modules": 5},
                    production_rate=0.5),
            Station("Sirius Supply Depot", "sirius", station_type="trade_hub",
                    inventory={"processed_food": 80, "hydrogen_fuel": 100, "water": 50}),
        ],
        connections=["cygnus", "deneb", "betelgeuse", "vega_prime"],
    )

    # ── Deneb: Military base ──
    s["deneb"] = System(
        id="deneb", name="Deneb", system_type="military",
        cluster="core", security="high", x=-480, y=30, z=-50,
        stations=[
            Station("Fleet Command", "deneb", station_type="military_base",
                    inventory={"weapon_systems": 10, "combat_drones": 5, "ship_modules": 8, "hydrogen_fuel": 150, "processed_food": 120}),
            Station("Deneb Arms Factory", "deneb", station_type="component_factory",
                    produces=["weapon_systems", "reactor_cores"],
                    inventory={"electronics": 30, "titanium_alloy": 20, "reactor_cores": 8, "enriched_uranium": 5, "ceramics": 15, "superconductors": 10, "weapon_systems": 6},
                    production_rate=0.4),
        ],
        connections=["tau_ceti", "sirius", "aldebaran", "sol"],
    )

    # ── Polaris: Industrial hub (T3 production) ──
    s["polaris"] = System(
        id="polaris", name="Polaris", system_type="industrial",
        cluster="core", security="high", x=-100, y=-80, z=420,
        stations=[
            Station("Polaris Industrial Complex", "polaris", station_type="industrial_hub",
                    produces=["steel_alloy", "polymers", "ceramics"],
                    inventory={"refined_iron": 100, "chemicals": 80, "hydrogen_fuel": 50, "steel_alloy": 60, "polymers": 40, "ceramics": 30},
                    production_rate=1.5),
            Station("Polaris Market", "polaris", station_type="trade_hub",
                    inventory={"processed_food": 80, "water": 60}),
        ],
        connections=["kepler", "procyon", "capella", "haven", "hydra"],
    )

    # ── Fomalhaut: Refinery cluster ──
    s["fomalhaut"] = System(
        id="fomalhaut", name="Fomalhaut", system_type="processing",
        cluster="core", security="high", x=-200, y=110, z=-480,
        stations=[
            Station("Fomalhaut Refinery", "fomalhaut", station_type="refinery",
                    produces=["refined_iron", "refined_titanium", "chemicals"],
                    inventory={"iron_ore": 150, "titanium_ore": 60, "organics": 80, "ice": 60, "refined_iron": 100, "refined_titanium": 30, "chemicals": 70},
                    production_rate=2.0),
        ],
        asteroid_fields=[AsteroidField("Fomalhaut Ore Belt", "iron_belt", ["iron_ore"], density=0.9)],
        connections=["tau_ceti", "aldebaran", "barnards", "meridian", "osiris"],
    )

    # ── Sol: Industrial hub, component factory ──
    s["sol"] = System(
        id="sol", name="Sol", system_type="industrial",
        cluster="core", security="high", x=-50, y=20, z=100,
        stations=[
            Station("Earth Orbital Factory", "sol", station_type="industrial_hub",
                    produces=["composites", "superconductors", "glass"],
                    inventory={"polymers": 40, "refined_titanium": 30, "refined_copper": 50, "rare_earths": 15, "crystals": 10, "chemicals": 40, "composites": 25, "superconductors": 20, "glass": 15},
                    production_rate=1.0),
            Station("Mars Trade Port", "sol", station_type="trade_hub",
                    inventory={"processed_food": 150, "hydrogen_fuel": 120, "water": 80, "luxury_goods": 50, "consumer_electronics": 60, "entertainment_media": 40, "exotic_textiles": 30}),
        ],
        connections=["procyon", "deneb", "haven", "arcturus"],
    )

    # ── Haven: Pharmaceutical/life support production ──
    s["haven"] = System(
        id="haven", name="Haven", system_type="industrial",
        cluster="core", security="high", x=-150, y=-30, z=300,
        stations=[
            Station("Haven Bioworks", "haven", station_type="industrial_hub",
                    produces=["pharmaceuticals"],
                    inventory={"chemicals": 60, "organics": 40, "pharmaceuticals": 50},
                    production_rate=1.5),
            Station("Haven Life Systems", "haven", station_type="component_factory",
                    produces=["life_support", "mining_lasers"],
                    inventory={"polymers": 30, "electronics": 20, "water": 40, "glass": 15, "reactor_cores": 5, "life_support": 12, "mining_lasers": 8},
                    production_rate=0.8),
        ],
        connections=["polaris", "sol", "capella", "hydra"],
    )

    # ── Vega Prime: High-sec mining with local refinery ──
    s["vega_prime"] = System(
        id="vega_prime", name="Vega Prime", system_type="mining",
        cluster="core", security="high", x=-420, y=80, z=100,
        stations=[
            Station("Vega Prime Mining Co.", "vega_prime", station_type="mining_colony",
                    inventory={"iron_ore": 400, "copper_ore": 250, "processed_food": 50, "hydrogen_fuel": 40}),
            Station("Vega Prime Smelter", "vega_prime", station_type="refinery",
                    produces=["refined_iron", "refined_copper"],
                    inventory={"iron_ore": 100, "copper_ore": 80, "refined_iron": 60, "refined_copper": 40},
                    production_rate=1.5),
        ],
        asteroid_fields=[
            AsteroidField("Vega Prime Iron Belt", "iron_belt", ["iron_ore", "copper_ore"], density=1.3),
        ],
        connections=["sirius", "meridian", "betelgeuse"],
    )

    # ── Meridian: Refinery, border of core/rim ──
    s["meridian"] = System(
        id="meridian", name="Meridian", system_type="processing",
        cluster="core", security="high", x=-350, y=100, z=-300,
        stations=[
            Station("Meridian Refinery", "meridian", station_type="refinery",
                    produces=["refined_titanium", "enriched_uranium"],
                    inventory={"titanium_ore": 60, "uranium": 10, "refined_titanium": 40, "enriched_uranium": 5},
                    production_rate=1.0),
        ],
        connections=["fomalhaut", "vega_prime", "aldebaran", "regulus"],
    )

    return s


def _rim_systems() -> dict[str, System]:
    """Rim cluster: 22 low-sec systems. Mixed industrial, mining, trade."""
    s = {}

    # ── Arcturus: Refinery + gas mining ──
    s["arcturus"] = System(
        id="arcturus", name="Arcturus", system_type="processing",
        cluster="rim", security="medium", x=250, y=80, z=200,
        stations=[
            Station("Arcturus Gas Refinery", "arcturus", station_type="refinery",
                    produces=["hydrogen_fuel", "chemicals"],
                    inventory={"ice": 80, "helium3": 100, "organics": 50, "hydrogen_fuel": 150, "chemicals": 80},
                    production_rate=2.0),
        ],
        asteroid_fields=[AsteroidField("Arcturus Gas Cloud", "gas_pocket", ["helium3"], density=1.3)],
        connections=["procyon", "sol", "vega", "antares", "castor", "helios"],
    )

    # ── Vega: Major ore mining ──
    s["vega"] = System(
        id="vega", name="Vega", system_type="mining",
        cluster="rim", security="medium", x=320, y=60, z=-180,
        stations=[
            Station("Vega Mining Colony", "vega", station_type="mining_colony",
                    inventory={"iron_ore": 600, "copper_ore": 300, "titanium_ore": 100, "processed_food": 60, "hydrogen_fuel": 50}),
        ],
        asteroid_fields=[
            AsteroidField("Vega Rich Belt", "iron_belt", ["iron_ore", "copper_ore"], density=1.5),
            AsteroidField("Vega Titanium Vein", "metallic", ["titanium_ore"], density=0.8),
        ],
        connections=["arcturus", "altair", "antares", "mira"],
    )

    # ── Altair: Trade junction ──
    s["altair"] = System(
        id="altair", name="Altair", system_type="trade",
        cluster="rim", security="medium", x=150, y=-110, z=-300,
        stations=[
            Station("Altair Junction Market", "altair", station_type="trade_hub",
                    inventory={"refined_iron": 80, "steel_alloy": 40, "electronics": 30, "processed_food": 100, "hydrogen_fuel": 80, "luxury_goods": 25, "exotic_textiles": 20, "gourmet_food": 20}),
        ],
        connections=["kepler", "vega", "barnards", "castor", "draconis"],
    )

    # ── Barnards: Mining (titanium/moderate ores) ──
    s["barnards"] = System(
        id="barnards", name="Barnard's Star", system_type="mining",
        cluster="rim", security="medium", x=-150, y=100, z=-320,
        stations=[
            Station("Barnard's Mining Outpost", "barnards", station_type="mining_colony",
                    inventory={"titanium_ore": 200, "iron_ore": 300, "processed_food": 40, "hydrogen_fuel": 30}),
        ],
        asteroid_fields=[
            AsteroidField("Barnard's Titanium Field", "metallic", ["titanium_ore", "iron_ore"], density=1.2),
        ],
        connections=["fomalhaut", "altair", "aldebaran", "wolf359", "osiris", "fornax"],
    )

    # ── Antares: Industrial hub (T3) ──
    s["antares"] = System(
        id="antares", name="Antares", system_type="industrial",
        cluster="rim", security="medium", x=380, y=40, z=80,
        stations=[
            Station("Antares Forge", "antares", station_type="industrial_hub",
                    produces=["steel_alloy", "titanium_alloy", "ceramics"],
                    inventory={"refined_iron": 80, "refined_titanium": 40, "chemicals": 60, "steel_alloy": 50, "titanium_alloy": 20, "ceramics": 30},
                    production_rate=1.5),
        ],
        connections=["arcturus", "vega", "achernar", "mira"],
    )

    # ── Capella: Trade hub, rim side ──
    s["capella"] = System(
        id="capella", name="Capella", system_type="trade",
        cluster="rim", security="medium", x=-350, y=90, z=380,
        stations=[
            Station("Capella Free Market", "capella", station_type="trade_hub",
                    inventory={"steel_alloy": 40, "polymers": 30, "electronics": 25, "processed_food": 80, "hydrogen_fuel": 60, "pharmaceuticals": 20, "luxury_goods": 35, "fine_spirits": 30, "entertainment_media": 25}),
        ],
        connections=["polaris", "haven", "betelgeuse", "castor", "lyra", "helios"],
    )

    # ── Betelgeuse: Shipyard (rim) ──
    s["betelgeuse"] = System(
        id="betelgeuse", name="Betelgeuse", system_type="shipyard",
        cluster="rim", security="medium", x=200, y=-50, z=450,
        stations=[
            Station("Betelgeuse Drydock", "betelgeuse", station_type="shipyard",
                    produces=["ship_modules", "mining_rigs"],
                    inventory={"hull_plating": 20, "life_support": 12, "engine_parts": 15, "mining_lasers": 8, "ship_modules": 4, "mining_rigs": 3},
                    production_rate=0.4),
        ],
        asteroid_fields=[AsteroidField("Betelgeuse Metallic Belt", "metallic", ["iron_ore", "titanium_ore"], density=1.0)],
        connections=["sirius", "vega_prime", "capella", "canopus", "corvus"],
    )

    # ── Castor: Nexus chokepoint (rim-to-frontier) ──
    s["castor"] = System(
        id="castor", name="Castor", system_type="nexus",
        cluster="rim", security="medium", x=450, y=80, z=-280,
        stations=[
            Station("Castor Relay", "castor", station_type="trade_hub",
                    inventory={"hydrogen_fuel": 200, "processed_food": 80}),
        ],
        connections=["procyon", "arcturus", "altair", "capella", "achernar", "wolf359", "rigel"],
    )

    # ── Achernar: Military outpost (rim) ──
    s["achernar"] = System(
        id="achernar", name="Achernar", system_type="military",
        cluster="rim", security="medium", x=300, y=90, z=-450,
        stations=[
            Station("Achernar Forward Base", "achernar", station_type="military_base",
                    inventory={"weapon_systems": 5, "combat_drones": 3, "hydrogen_fuel": 100, "processed_food": 60}),
        ],
        connections=["antares", "castor", "rigel", "mira"],
    )

    # ── Aldebaran: Major mining (iron/copper) ──
    s["aldebaran"] = System(
        id="aldebaran", name="Aldebaran", system_type="mining",
        cluster="rim", security="medium", x=-500, y=70, z=-280,
        stations=[
            Station("Aldebaran Mining Hub", "aldebaran", station_type="mining_colony",
                    inventory={"iron_ore": 500, "copper_ore": 300, "processed_food": 40, "hydrogen_fuel": 30}),
        ],
        asteroid_fields=[AsteroidField("Aldebaran Dense Belt", "iron_belt", ["iron_ore", "copper_ore"], density=1.4)],
        connections=["deneb", "fomalhaut", "meridian", "barnards", "regulus", "osiris"],
    )

    # ── Regulus: Crystal mining ──
    s["regulus"] = System(
        id="regulus", name="Regulus", system_type="mining",
        cluster="rim", security="low", x=-600, y=40, z=150,
        stations=[
            Station("Regulus Crystal Mine", "regulus", station_type="mining_colony",
                    inventory={"crystals": 100, "iron_ore": 200, "processed_food": 30, "hydrogen_fuel": 20}),
        ],
        asteroid_fields=[AsteroidField("Crystal Caverns", "crystal", ["crystals", "iron_ore"], density=0.8, danger=0.1)],
        connections=["meridian", "aldebaran", "pollux", "lyra"],
    )

    # ── Mira: Industrial (T3 polymers/composites) ──
    s["mira"] = System(
        id="mira", name="Mira", system_type="industrial",
        cluster="rim", security="medium", x=400, y=-20, z=-80,
        stations=[
            Station("Mira Polymer Works", "mira", station_type="industrial_hub",
                    produces=["polymers", "composites"],
                    inventory={"chemicals": 60, "hydrogen_fuel": 40, "refined_titanium": 30, "polymers": 50, "composites": 20},
                    production_rate=1.2),
        ],
        connections=["vega", "antares", "achernar", "novus", "aquila"],
    )

    # ── Draconis: Component factory ──
    s["draconis"] = System(
        id="draconis", name="Draconis", system_type="industrial",
        cluster="rim", security="medium", x=100, y=-180, z=-400,
        stations=[
            Station("Draconis Engine Works", "draconis", station_type="component_factory",
                    produces=["engine_parts", "hull_plating"],
                    inventory={"steel_alloy": 50, "composites": 25, "superconductors": 20, "engine_parts": 15, "hull_plating": 12},
                    production_rate=0.8),
        ],
        connections=["altair", "novus", "serpentis", "fornax"],
    )

    # ── Lyra: Pharmaceutical/trade ──
    s["lyra"] = System(
        id="lyra", name="Lyra", system_type="trade",
        cluster="rim", security="medium", x=-450, y=120, z=250,
        stations=[
            Station("Lyra Medical Station", "lyra", station_type="industrial_hub",
                    produces=["pharmaceuticals", "glass"],
                    inventory={"chemicals": 40, "organics": 30, "crystals": 15, "pharmaceuticals": 35, "glass": 20},
                    production_rate=1.0),
            Station("Lyra Bazaar", "lyra", station_type="trade_hub",
                    inventory={"processed_food": 60, "hydrogen_fuel": 50, "pharmaceuticals": 25}),
        ],
        connections=["capella", "regulus", "haven_rim", "pollux", "hydra"],
    )

    # ── Novus: Frontier-adjacent industrial ──
    s["novus"] = System(
        id="novus", name="Novus", system_type="industrial",
        cluster="rim", security="low", x=500, y=-100, z=-200,
        stations=[
            Station("Novus Alloy Works", "novus", station_type="industrial_hub",
                    produces=["steel_alloy", "titanium_alloy"],
                    inventory={"refined_iron": 60, "refined_titanium": 25, "chemicals": 40, "steel_alloy": 35, "titanium_alloy": 15},
                    production_rate=1.0),
        ],
        connections=["mira", "draconis", "rigel", "serpentis", "aquila"],
    )

    # ── Serpentis: Low-sec trade/smuggling ──
    s["serpentis"] = System(
        id="serpentis", name="Serpentis", system_type="trade",
        cluster="rim", security="low", x=350, y=-150, z=-500,
        stations=[
            Station("Serpentis Black Market", "serpentis", station_type="trade_hub",
                    inventory={"weapon_systems": 3, "electronics": 20, "hydrogen_fuel": 40, "processed_food": 30}),
        ],
        connections=["draconis", "novus", "pollux", "void", "nyx"],
    )

    # ── Haven Rim: Frontier outpost ──
    s["haven_rim"] = System(
        id="haven_rim", name="Haven's Edge", system_type="frontier",
        cluster="rim", security="low", x=-500, y=150, z=350,
        stations=[
            Station("Haven's Edge Outpost", "haven_rim", station_type="frontier_outpost",
                    inventory={"processed_food": 30, "hydrogen_fuel": 25, "pharmaceuticals": 10, "water": 20}),
        ],
        asteroid_fields=[AsteroidField("Edge Ice Field", "ice_field", ["ice", "organics"], density=0.9)],
        connections=["lyra", "canopus", "erebus"],
    )

    # ── Helios: Helium-3 mining ──
    s["helios"] = System(
        id="helios", name="Helios", system_type="mining",
        cluster="rim", security="medium", x=180, y=130, z=300,
        stations=[
            Station("Helios Gas Platform", "helios", station_type="mining_colony",
                    inventory={"helium3": 250, "ice": 100, "processed_food": 30, "hydrogen_fuel": 40}),
        ],
        asteroid_fields=[
            AsteroidField("Helios Gas Giant Rings", "gas_pocket", ["helium3"], density=1.5),
            AsteroidField("Helios Ice Halo", "ice_field", ["ice"], density=1.0),
        ],
        connections=["arcturus", "capella", "canopus", "corvus"],
    )

    # ── Osiris: Organics/agricultural rim ──
    s["osiris"] = System(
        id="osiris", name="Osiris", system_type="agricultural",
        cluster="rim", security="medium", x=-250, y=-50, z=-500,
        stations=[
            Station("Osiris Bio-Farm", "osiris", station_type="refinery",
                    produces=["processed_food", "chemicals"],
                    inventory={"organics": 200, "ice": 80, "water": 60, "processed_food": 150, "chemicals": 60},
                    production_rate=2.0),
        ],
        asteroid_fields=[AsteroidField("Osiris Organic Cloud", "organic", ["organics"], density=1.3)],
        connections=["barnards", "fomalhaut", "aldebaran", "fornax"],
    )

    # ── Corvus: Component factory (rim-side) ──
    s["corvus"] = System(
        id="corvus", name="Corvus", system_type="industrial",
        cluster="rim", security="medium", x=50, y=160, z=500,
        stations=[
            Station("Corvus Assembly Plant", "corvus", station_type="component_factory",
                    produces=["engine_parts", "life_support"],
                    inventory={"steel_alloy": 40, "superconductors": 15, "polymers": 20, "electronics": 10, "water": 30, "engine_parts": 10, "life_support": 8},
                    production_rate=0.7),
        ],
        connections=["helios", "betelgeuse", "canopus", "pyxis"],
    )

    # ── Fornax: Refinery (rim, processes titanium) ──
    s["fornax"] = System(
        id="fornax", name="Fornax", system_type="processing",
        cluster="rim", security="medium", x=-80, y=-130, z=-250,
        stations=[
            Station("Fornax Titanium Refinery", "fornax", station_type="refinery",
                    produces=["refined_titanium", "refined_iron"],
                    inventory={"titanium_ore": 80, "iron_ore": 120, "refined_titanium": 40, "refined_iron": 60},
                    production_rate=1.5),
        ],
        connections=["barnards", "draconis", "osiris"],
    )

    # ── Hydra: Ice mining, water/fuel production ──
    s["hydra"] = System(
        id="hydra", name="Hydra", system_type="mining",
        cluster="rim", security="medium", x=-300, y=-100, z=200,
        stations=[
            Station("Hydra Ice Works", "hydra", station_type="refinery",
                    produces=["water", "hydrogen_fuel"],
                    inventory={"ice": 150, "helium3": 60, "water": 80, "hydrogen_fuel": 100},
                    production_rate=2.0),
        ],
        asteroid_fields=[
            AsteroidField("Hydra Ice Shelf", "ice_field", ["ice"], density=1.4),
            AsteroidField("Hydra Gas Pocket", "gas_pocket", ["helium3"], density=0.8),
        ],
        connections=["polaris", "haven", "lyra"],
    )

    # ── Aquila: Superconductor production ──
    s["aquila"] = System(
        id="aquila", name="Aquila", system_type="industrial",
        cluster="rim", security="low", x=600, y=50, z=-100,
        stations=[
            Station("Aquila Conductor Labs", "aquila", station_type="industrial_hub",
                    produces=["superconductors", "glass"],
                    inventory={"refined_copper": 40, "rare_earths": 15, "crystals": 10, "chemicals": 20, "superconductors": 20, "glass": 12},
                    production_rate=0.8),
        ],
        connections=["novus", "mira", "wolf359"],
    )

    return s


def _frontier_systems() -> dict[str, System]:
    """Frontier cluster: 14 null-sec systems. Rare ores, danger, sparse infrastructure."""
    s = {}

    # ── Wolf 359: Gateway to frontier, rare earths ──
    s["wolf359"] = System(
        id="wolf359", name="Wolf 359", system_type="frontier",
        cluster="frontier", security="low", x=480, y=120, z=350,
        stations=[
            Station("Wolf 359 Depot", "wolf359", station_type="frontier_outpost",
                    inventory={"processed_food": 25, "hydrogen_fuel": 20, "water": 15, "rare_earths": 30}),
        ],
        asteroid_fields=[AsteroidField("Wolf 359 Rare Earth Deposit", "rare_earth", ["rare_earths", "iron_ore"], density=0.9, danger=0.15)],
        connections=["castor", "barnards", "spica", "obsidian", "aquila"],
    )

    # ── Rigel: Frontier mining/trade ──
    s["rigel"] = System(
        id="rigel", name="Rigel", system_type="frontier",
        cluster="frontier", security="none", x=500, y=-60, z=-100,
        stations=[
            Station("Rigel Salvage Yard", "rigel", station_type="frontier_outpost",
                    inventory={"processed_food": 15, "hydrogen_fuel": 15, "rare_earths": 20}),
        ],
        asteroid_fields=[AsteroidField("Rigel Rare Belt", "rare_earth", ["rare_earths", "titanium_ore"], density=1.0, danger=0.2)],
        connections=["castor", "achernar", "novus", "void", "terminus"],
    )

    # ── Pollux: Deep frontier, platinum ──
    s["pollux"] = System(
        id="pollux", name="Pollux", system_type="frontier",
        cluster="frontier", security="none", x=-400, y=-60, z=-400,
        stations=[
            Station("Pollux Wildcat Mine", "pollux", station_type="mining_colony",
                    inventory={"platinum": 60, "titanium_ore": 80, "processed_food": 15, "hydrogen_fuel": 10}),
        ],
        asteroid_fields=[
            AsteroidField("Pollux Platinum Vein", "dense_asteroid", ["platinum", "titanium_ore"], density=0.7, danger=0.2),
        ],
        connections=["regulus", "lyra", "serpentis", "erebus", "void", "nyx"],
    )

    # ── Canopus: Frontier industrial (rogue factory) ──
    s["canopus"] = System(
        id="canopus", name="Canopus", system_type="industrial",
        cluster="frontier", security="low", x=100, y=-100, z=600,
        stations=[
            Station("Canopus Rogue Foundry", "canopus", station_type="industrial_hub",
                    produces=["titanium_alloy", "composites"],
                    inventory={"refined_titanium": 30, "chemicals": 20, "polymers": 15, "titanium_alloy": 15, "composites": 10},
                    production_rate=0.8),
        ],
        asteroid_fields=[AsteroidField("Canopus Titanium Reef", "metallic", ["titanium_ore"], density=1.2, danger=0.15)],
        connections=["betelgeuse", "haven_rim", "helios", "corvus", "spica", "obsidian", "pyxis"],
    )

    # ── Spica: Frontier nexus ──
    s["spica"] = System(
        id="spica", name="Spica", system_type="nexus",
        cluster="frontier", security="none", x=600, y=-30, z=200,
        stations=[
            Station("Spica Ghost Gate", "spica", station_type="frontier_outpost",
                    inventory={"hydrogen_fuel": 40, "processed_food": 15}),
        ],
        connections=["wolf359", "canopus", "terminus", "obsidian", "abyss"],
    )

    # ── Void: Deep null, uranium ──
    s["void"] = System(
        id="void", name="The Void", system_type="frontier",
        cluster="frontier", security="none", x=550, y=-180, z=-350,
        stations=[
            Station("Void Station", "void", station_type="frontier_outpost",
                    inventory={"uranium": 15, "processed_food": 10, "hydrogen_fuel": 10}),
        ],
        asteroid_fields=[AsteroidField("Void Deep Core", "deep_core", ["uranium", "platinum"], density=0.5, danger=0.3)],
        connections=["serpentis", "rigel", "pollux", "terminus", "abyss"],
    )

    # ── Terminus: End of the line, crystals ──
    s["terminus"] = System(
        id="terminus", name="Terminus", system_type="frontier",
        cluster="frontier", security="none", x=700, y=-100, z=0,
        stations=[
            Station("Terminus Outpost", "terminus", station_type="frontier_outpost",
                    inventory={"crystals": 25, "processed_food": 10, "hydrogen_fuel": 8}),
        ],
        asteroid_fields=[AsteroidField("Terminus Crystal Formation", "crystal", ["crystals"], density=0.9, danger=0.25)],
        connections=["rigel", "spica", "void", "abyss"],
    )

    # ── Obsidian: Rare earths + danger ──
    s["obsidian"] = System(
        id="obsidian", name="Obsidian", system_type="frontier",
        cluster="frontier", security="none", x=350, y=200, z=500,
        stations=[
            Station("Obsidian Rock", "obsidian", station_type="mining_colony",
                    inventory={"rare_earths": 40, "crystals": 20, "processed_food": 10, "hydrogen_fuel": 8}),
        ],
        asteroid_fields=[
            AsteroidField("Obsidian Rare Earth Deposit", "rare_earth", ["rare_earths"], density=1.1, danger=0.2),
            AsteroidField("Obsidian Crystal Cave", "crystal", ["crystals", "rare_earths"], density=0.6, danger=0.25),
        ],
        connections=["wolf359", "canopus", "spica", "phantom", "pyxis"],
    )

    # ── Erebus: Deep frontier, platinum/uranium ──
    s["erebus"] = System(
        id="erebus", name="Erebus", system_type="frontier",
        cluster="frontier", security="none", x=-550, y=180, z=400,
        stations=[
            Station("Erebus Deep Mine", "erebus", station_type="mining_colony",
                    inventory={"platinum": 30, "uranium": 8, "processed_food": 8, "hydrogen_fuel": 5}),
        ],
        asteroid_fields=[
            AsteroidField("Erebus Platinum Pocket", "dense_asteroid", ["platinum"], density=0.6, danger=0.25),
            AsteroidField("Erebus Radioactive Belt", "deep_core", ["uranium"], density=0.4, danger=0.35),
        ],
        connections=["haven_rim", "pollux", "phantom", "nyx"],
    )

    # ── Phantom: Deepest frontier, all rare ores ──
    s["phantom"] = System(
        id="phantom", name="Phantom", system_type="frontier",
        cluster="frontier", security="none", x=-300, y=250, z=600,
        stations=[
            Station("Phantom Station", "phantom", station_type="frontier_outpost",
                    inventory={"processed_food": 5, "hydrogen_fuel": 5, "platinum": 10, "crystals": 10, "uranium": 5}),
        ],
        asteroid_fields=[
            AsteroidField("Phantom Anomaly", "deep_core", ["uranium", "platinum", "crystals"], density=0.5, danger=0.35),
        ],
        connections=["erebus", "obsidian", "abyss"],
    )

    # ── Abyss: Most dangerous system, highest value ores ──
    s["abyss"] = System(
        id="abyss", name="The Abyss", system_type="frontier",
        cluster="frontier", security="none", x=650, y=-200, z=400,
        stations=[
            Station("Abyss Beacon", "abyss", station_type="frontier_outpost",
                    inventory={"hydrogen_fuel": 5, "processed_food": 5}),
        ],
        asteroid_fields=[
            AsteroidField("Abyss Uranium Trench", "deep_core", ["uranium"], density=0.8, danger=0.4),
            AsteroidField("Abyss Crystal Rift", "crystal", ["crystals", "rare_earths"], density=0.7, danger=0.35),
        ],
        connections=["spica", "void", "terminus", "phantom"],
    )

    # ── Pyxis: Frontier helium-3 (fuel source for deep ops) ──
    s["pyxis"] = System(
        id="pyxis", name="Pyxis", system_type="mining",
        cluster="frontier", security="low", x=250, y=250, z=550,
        stations=[
            Station("Pyxis Fuel Cache", "pyxis", station_type="frontier_outpost",
                    inventory={"helium3": 80, "ice": 60, "hydrogen_fuel": 30, "processed_food": 15}),
        ],
        asteroid_fields=[
            AsteroidField("Pyxis Gas Nebula", "gas_pocket", ["helium3"], density=1.4, danger=0.1),
            AsteroidField("Pyxis Ice Drift", "ice_field", ["ice"], density=1.0),
        ],
        connections=["corvus", "canopus", "obsidian"],
    )

    # ── Nyx: Frontier component production (illegal arms) ──
    s["nyx"] = System(
        id="nyx", name="Nyx", system_type="industrial",
        cluster="frontier", security="none", x=-200, y=-150, z=-550,
        stations=[
            Station("Nyx Shadow Factory", "nyx", station_type="component_factory",
                    produces=["weapon_systems", "combat_drones"],
                    inventory={"electronics": 15, "titanium_alloy": 10, "reactor_cores": 5, "engine_parts": 8, "weapon_systems": 4, "combat_drones": 2},
                    production_rate=0.3),
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

    # Generate intra-system objects for all systems
    for sys in systems.values():
        sys.objects = _generate_system_objects(sys)

    return systems
