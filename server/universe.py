"""Seed data for the 24-system universe."""
from server.models import System, Station, AsteroidField


def build_universe() -> dict[str, System]:
    """Build and return the full 24-system universe."""
    systems = {}

    # ═══════════════════════════════════════════════════════════════════════════
    # CORE CLUSTER (High-Sec)
    # ═══════════════════════════════════════════════════════════════════════════

    systems["cygnus"] = System(
        id="cygnus", name="Cygnus Station", system_type="industrial",
        cluster="core", security="high", faction="Trade Guild",
        x=0, y=0, z=0,
        stations=[
            Station("Orbital Foundry", "cygnus",
                    production={"alloys": 8, "components": 4},
                    consumption={"iron_ore": 12, "fuel": 3, "chemicals": 2},
                    inventory={"alloys": 500, "components": 300, "iron_ore": 800, "fuel": 200}),
            Station("Commerce Hub", "cygnus",
                    production={},
                    consumption={"food": 6, "meds": 2},
                    inventory={"food": 400, "meds": 150, "electronics": 200, "luxuries": 80}),
        ],
        asteroid_fields=[AsteroidField("Iron Belt", "iron_belt", ["iron_ore"], density=1.0)],
        connections=["kepler", "procyon", "tau_ceti", "sirius"],
    )

    systems["kepler"] = System(
        id="kepler", name="Kepler Freeport", system_type="trade",
        cluster="core", security="high", faction="Free Traders",
        x=-200, y=-40, z=150,
        stations=[
            Station("Grand Exchange", "kepler",
                    production={},
                    consumption={"food": 4, "fuel": 2},
                    inventory={"iron_ore": 300, "food": 500, "electronics": 400, "alloys": 350, "luxuries": 200, "meds": 250}),
            Station("Freeport Bazaar", "kepler",
                    production={},
                    consumption={},
                    inventory={"polymers": 200, "chemicals": 150, "narcotics": 20}),
            Station("Fuel Depot", "kepler",
                    production={"fuel": 6},
                    consumption={"helium3": 4},
                    inventory={"fuel": 600, "helium3": 200}),
        ],
        asteroid_fields=[],
        connections=["cygnus", "tau_ceti", "polaris", "altair"],
    )

    systems["tau_ceti"] = System(
        id="tau_ceti", name="Tau Ceti Prime", system_type="agricultural",
        cluster="core", security="high", faction="Agrarian League",
        x=-300, y=-70, z=-120,
        stations=[
            Station("Agri-Orbital", "tau_ceti",
                    production={"food": 15, "organics": 8},
                    consumption={"fuel": 2, "chemicals": 1},
                    inventory={"food": 1200, "organics": 600, "fuel": 100}),
            Station("Seed Vault", "tau_ceti",
                    production={"organics": 3},
                    consumption={"ice": 2},
                    inventory={"organics": 400, "ice": 150}),
        ],
        asteroid_fields=[AsteroidField("Ice Field", "ice_field", ["ice"], density=0.8)],
        connections=["cygnus", "kepler", "fomalhaut", "deneb"],
    )

    systems["procyon"] = System(
        id="procyon", name="Procyon Gate", system_type="nexus",
        cluster="core", security="high", faction="Gateway Authority",
        x=60, y=-90, z=280,
        stations=[
            Station("Jump Gate Alpha", "procyon",
                    production={},
                    consumption={"fuel": 8},
                    inventory={"fuel": 400}),
            Station("Nav Beacon", "procyon",
                    production={},
                    consumption={"electronics": 1},
                    inventory={"electronics": 50}),
        ],
        asteroid_fields=[AsteroidField("Debris Field", "debris", ["salvage"], density=0.5)],
        connections=["cygnus", "polaris", "castor", "arcturus"],
    )

    systems["sirius"] = System(
        id="sirius", name="Sirius Dockyard", system_type="shipyard",
        cluster="core", security="high", faction="Shipwrights Guild",
        x=-380, y=50, z=200,
        stations=[
            Station("Dockyard Prime", "sirius",
                    production={"components": 5},
                    consumption={"alloys": 10, "electronics": 6, "polymers": 4},
                    inventory={"alloys": 600, "electronics": 300, "polymers": 250, "components": 400}),
            Station("Dry Dock Beta", "sirius",
                    production={},
                    consumption={"alloys": 4, "components": 3},
                    inventory={"alloys": 200, "components": 150}),
        ],
        asteroid_fields=[],
        connections=["cygnus", "deneb", "betelgeuse"],
    )

    systems["deneb"] = System(
        id="deneb", name="Deneb Anchorage", system_type="military",
        cluster="core", security="high", faction="Federal Navy",
        x=-480, y=30, z=-50,
        stations=[
            Station("Fleet Command", "deneb",
                    production={},
                    consumption={"fuel": 6, "food": 4, "meds": 3, "alloys": 2},
                    inventory={"fuel": 300, "food": 250, "meds": 200, "alloys": 150}),
            Station("Patrol Base", "deneb",
                    production={},
                    consumption={"fuel": 3, "components": 2},
                    inventory={"fuel": 200, "components": 100}),
        ],
        asteroid_fields=[],
        connections=["tau_ceti", "sirius", "aldebaran"],
    )

    systems["polaris"] = System(
        id="polaris", name="Polaris Haven", system_type="agricultural",
        cluster="core", security="high", faction="Agrarian League",
        x=-100, y=-80, z=420,
        stations=[
            Station("Greenhouse Station", "polaris",
                    production={"food": 10, "organics": 5},
                    consumption={"ice": 3, "chemicals": 1},
                    inventory={"food": 800, "organics": 350, "ice": 100}),
            Station("Bio-Lab", "polaris",
                    production={"meds": 3},
                    consumption={"organics": 4, "chemicals": 2},
                    inventory={"meds": 200, "organics": 200, "chemicals": 100}),
        ],
        asteroid_fields=[AsteroidField("Ice Field", "ice_field", ["ice"], density=0.7)],
        connections=["kepler", "procyon", "capella"],
    )

    systems["fomalhaut"] = System(
        id="fomalhaut", name="Fomalhaut Colony", system_type="agricultural",
        cluster="core", security="high", faction="Agrarian League",
        x=-200, y=110, z=-480,
        stations=[
            Station("Colony Hub", "fomalhaut",
                    production={"food": 8, "organics": 6},
                    consumption={"fuel": 2, "meds": 1},
                    inventory={"food": 700, "organics": 500, "fuel": 80}),
            Station("Livestock Ring", "fomalhaut",
                    production={"food": 5},
                    consumption={"organics": 3, "ice": 2},
                    inventory={"food": 400, "organics": 150, "ice": 80}),
        ],
        asteroid_fields=[AsteroidField("Organic Cluster", "organic", ["organics"], density=0.6, danger=0.05)],
        connections=["tau_ceti", "aldebaran", "barnards"],
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # RIM CLUSTER (Low-Sec)
    # ═══════════════════════════════════════════════════════════════════════════

    systems["vega"] = System(
        id="vega", name="Vega Outpost", system_type="mining",
        cluster="rim", security="medium", faction="Miners Union",
        x=320, y=60, z=-180,
        stations=[
            Station("Mining Platform Alpha", "vega",
                    production={"iron_ore": 12, "titanium": 4},
                    consumption={"food": 4, "meds": 2, "fuel": 3},
                    inventory={"iron_ore": 1000, "titanium": 300, "food": 150, "meds": 80}),
        ],
        asteroid_fields=[AsteroidField("Rich Ore Belt", "iron_belt", ["iron_ore", "titanium"], density=1.5)],
        connections=["altair", "arcturus", "antares"],
    )

    systems["arcturus"] = System(
        id="arcturus", name="Arcturus Refinery", system_type="processing",
        cluster="rim", security="medium", faction="Industrial Corp",
        x=250, y=80, z=200,
        stations=[
            Station("Refinery Omega", "arcturus",
                    production={"fuel": 10, "polymers": 6, "chemicals": 4},
                    consumption={"iron_ore": 6, "helium3": 5, "ice": 3},
                    inventory={"fuel": 500, "polymers": 400, "chemicals": 250, "iron_ore": 300, "helium3": 150}),
        ],
        asteroid_fields=[AsteroidField("Gas Pocket", "gas_pocket", ["helium3"], density=1.2)],
        connections=["procyon", "vega", "antares", "castor"],
    )

    systems["barnards"] = System(
        id="barnards", name="Barnard's Reach", system_type="mining",
        cluster="rim", security="medium", faction="Miners Union",
        x=-150, y=100, z=-320,
        stations=[
            Station("Deep Core Station", "barnards",
                    production={"platinum": 3, "iron_ore": 6},
                    consumption={"food": 3, "fuel": 2, "meds": 1},
                    inventory={"platinum": 150, "iron_ore": 500, "food": 100, "fuel": 80}),
        ],
        asteroid_fields=[AsteroidField("Rare Earth Belt", "rare_earth", ["platinum"], density=0.8, danger=0.1)],
        connections=["fomalhaut", "aldebaran", "altair"],
    )

    systems["altair"] = System(
        id="altair", name="Altair Junction", system_type="trade",
        cluster="rim", security="medium", faction="Free Traders",
        x=150, y=-110, z=-300,
        stations=[
            Station("Junction Market", "altair",
                    production={},
                    consumption={"food": 3, "fuel": 2},
                    inventory={"iron_ore": 400, "platinum": 80, "electronics": 200, "alloys": 250, "meds": 150}),
            Station("Black Market", "altair",
                    production={},
                    consumption={},
                    inventory={"narcotics": 40, "salvage": 100, "luxuries": 60}),
        ],
        asteroid_fields=[AsteroidField("Debris Field", "debris", ["salvage"], density=0.6)],
        connections=["kepler", "vega", "barnards", "castor"],
    )

    systems["antares"] = System(
        id="antares", name="Antares Forge", system_type="processing",
        cluster="rim", security="medium", faction="Industrial Corp",
        x=380, y=40, z=80,
        stations=[
            Station("Smelter One", "antares",
                    production={"alloys": 10, "polymers": 5},
                    consumption={"iron_ore": 14, "chemicals": 4, "fuel": 3},
                    inventory={"alloys": 600, "polymers": 300, "iron_ore": 500, "chemicals": 200}),
            Station("Chemical Works", "antares",
                    production={"chemicals": 8},
                    consumption={"ice": 4, "organics": 2},
                    inventory={"chemicals": 400, "ice": 150, "organics": 100}),
        ],
        asteroid_fields=[AsteroidField("Sulfur Clouds", "sulfur", ["chemicals"], density=1.0, danger=0.1)],
        connections=["vega", "arcturus", "achernar"],
    )

    systems["capella"] = System(
        id="capella", name="Capella Market", system_type="trade",
        cluster="rim", security="medium", faction="Free Traders",
        x=-350, y=90, z=380,
        stations=[
            Station("Free Exchange", "capella",
                    production={},
                    consumption={"food": 3, "fuel": 2},
                    inventory={"food": 300, "fuel": 200, "luxuries": 150, "electronics": 250, "alloys": 200}),
            Station("Smuggler's Dock", "capella",
                    production={},
                    consumption={},
                    inventory={"narcotics": 30, "luxuries": 100, "exotic": 5}),
        ],
        asteroid_fields=[],
        connections=["polaris", "betelgeuse", "castor"],
    )

    systems["betelgeuse"] = System(
        id="betelgeuse", name="Betelgeuse Yard", system_type="shipyard",
        cluster="rim", security="medium", faction="Shipwrights Guild",
        x=200, y=-50, z=450,
        stations=[
            Station("Frontier Drydock", "betelgeuse",
                    production={"components": 4},
                    consumption={"alloys": 8, "electronics": 4, "polymers": 3},
                    inventory={"alloys": 400, "electronics": 200, "polymers": 150, "components": 250}),
        ],
        asteroid_fields=[AsteroidField("Metallic Belt", "metallic", ["iron_ore", "titanium"], density=1.1)],
        connections=["sirius", "capella", "canopus"],
    )

    systems["castor"] = System(
        id="castor", name="Castor Relay", system_type="nexus",
        cluster="rim", security="medium", faction="Gateway Authority",
        x=450, y=80, z=-280,
        stations=[
            Station("Relay Station", "castor",
                    production={},
                    consumption={"fuel": 6, "electronics": 1},
                    inventory={"fuel": 350, "electronics": 40}),
            Station("Toll Gate", "castor",
                    production={},
                    consumption={"fuel": 2},
                    inventory={"fuel": 150}),
        ],
        asteroid_fields=[],
        connections=["procyon", "arcturus", "altair", "capella", "wolf359", "rigel"],
    )

    systems["achernar"] = System(
        id="achernar", name="Achernar Base", system_type="military",
        cluster="rim", security="medium", faction="Federal Navy",
        x=300, y=90, z=-450,
        stations=[
            Station("Forward Operating Base", "achernar",
                    production={},
                    consumption={"fuel": 5, "food": 3, "meds": 2, "alloys": 2},
                    inventory={"fuel": 250, "food": 150, "meds": 120, "alloys": 100}),
        ],
        asteroid_fields=[],
        connections=["antares", "rigel", "castor"],
    )

    systems["aldebaran"] = System(
        id="aldebaran", name="Aldebaran Mine", system_type="mining",
        cluster="rim", security="medium", faction="Miners Union",
        x=-500, y=70, z=-280,
        stations=[
            Station("Strip Mine Alpha", "aldebaran",
                    production={"iron_ore": 10, "copper": 6},
                    consumption={"food": 3, "fuel": 2, "meds": 1},
                    inventory={"iron_ore": 800, "copper": 400, "food": 100, "fuel": 60}),
            Station("Ore Processor", "aldebaran",
                    production={"alloys": 3},
                    consumption={"iron_ore": 5, "fuel": 1},
                    inventory={"alloys": 150, "iron_ore": 300}),
        ],
        asteroid_fields=[AsteroidField("Dense Ore Field", "iron_belt", ["iron_ore", "copper"], density=1.4)],
        connections=["deneb", "fomalhaut", "barnards"],
    )

    systems["regulus"] = System(
        id="regulus", name="Regulus Port", system_type="mining",
        cluster="rim", security="medium", faction="Miners Union",
        x=-600, y=40, z=150,
        stations=[
            Station("Regulus Extraction Hub", "regulus",
                    production={"crystals": 4, "iron_ore": 5},
                    consumption={"food": 2, "fuel": 2, "meds": 1},
                    inventory={"crystals": 200, "iron_ore": 400, "food": 80, "fuel": 60}),
        ],
        asteroid_fields=[AsteroidField("Crystal Formation", "crystal", ["crystals"], density=0.7, danger=0.15)],
        connections=["aldebaran", "deneb", "pollux"],
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # FRONTIER CLUSTER (Null-Sec)
    # ═══════════════════════════════════════════════════════════════════════════

    systems["wolf359"] = System(
        id="wolf359", name="Wolf 359 Depot", system_type="frontier",
        cluster="frontier", security="none", faction="",
        x=480, y=120, z=350,
        stations=[
            Station("Frontier Post", "wolf359",
                    production={},
                    consumption={"food": 2, "fuel": 2, "meds": 1},
                    inventory={"food": 40, "fuel": 30, "salvage": 80, "narcotics": 15}),
        ],
        asteroid_fields=[AsteroidField("Unknown Composition", "anomalous", ["exotic", "salvage"], density=0.5, danger=0.25)],
        connections=["castor", "spica", "canopus"],
    )

    systems["rigel"] = System(
        id="rigel", name="Rigel Depot", system_type="frontier",
        cluster="frontier", security="none", faction="",
        x=500, y=-60, z=-100,
        stations=[
            Station("Salvage Yard", "rigel",
                    production={"salvage": 3},
                    consumption={"fuel": 1, "food": 1},
                    inventory={"salvage": 200, "components": 60, "fuel": 20, "food": 20}),
        ],
        asteroid_fields=[AsteroidField("Wreckage Field", "debris", ["salvage", "components"], density=0.9, danger=0.2)],
        connections=["castor", "achernar", "pollux"],
    )

    systems["pollux"] = System(
        id="pollux", name="Pollux Outpost", system_type="frontier",
        cluster="frontier", security="none", faction="",
        x=-400, y=-60, z=-400,
        stations=[
            Station("Outlaw Station", "pollux",
                    production={},
                    consumption={"fuel": 2, "food": 2, "meds": 1},
                    inventory={"narcotics": 50, "luxuries": 30, "fuel": 40, "food": 30}),
        ],
        asteroid_fields=[AsteroidField("Dark Matter Pocket", "dark_matter", ["exotic"], density=0.4, danger=0.3)],
        connections=["rigel", "regulus", "spica"],
    )

    systems["canopus"] = System(
        id="canopus", name="Canopus Station", system_type="industrial",
        cluster="frontier", security="none", faction="",
        x=100, y=-100, z=600,
        stations=[
            Station("Rogue Foundry", "canopus",
                    production={"alloys": 6, "components": 3},
                    consumption={"iron_ore": 8, "titanium": 3, "fuel": 2},
                    inventory={"alloys": 300, "components": 150, "iron_ore": 400, "titanium": 100}),
        ],
        asteroid_fields=[AsteroidField("Titanium Reef", "metallic", ["titanium"], density=1.3, danger=0.2)],
        connections=["wolf359", "betelgeuse", "spica"],
    )

    systems["spica"] = System(
        id="spica", name="Spica Terminal", system_type="nexus",
        cluster="frontier", security="none", faction="",
        x=600, y=-30, z=200,
        stations=[
            Station("Ghost Gate", "spica",
                    production={},
                    consumption={"fuel": 4},
                    inventory={"fuel": 100, "exotic": 10}),
        ],
        asteroid_fields=[AsteroidField("Debris Storm", "debris", ["salvage", "components"], density=1.2, danger=0.3)],
        connections=["wolf359", "canopus", "pollux", "castor"],
    )

    return systems
