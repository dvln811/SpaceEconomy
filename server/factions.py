"""Faction and corporation definitions for the space economy."""
from dataclasses import dataclass, field


@dataclass
class Corporation:
    id: str
    name: str
    faction_id: str
    focus: str          # mining, manufacturing, trade, military, research
    description: str = ""


@dataclass
class Faction:
    id: str
    name: str
    short: str          # 3-4 letter abbreviation
    philosophy: str     # core ideology
    home_cluster: str   # primary territory
    allies: list[str] = field(default_factory=list)
    enemies: list[str] = field(default_factory=list)
    corporations: list[Corporation] = field(default_factory=list)
    color: str = "#ffffff"


# ══════════════════════════════════════════════════════════════════════════════
# MAJOR FACTIONS
# ══════════════════════════════════════════════════════════════════════════════

FACTIONS = {
    "terran_fed": Faction(
        id="terran_fed",
        name="Terran Federation",
        short="TFD",
        philosophy="Order through unity. Central governance, regulated markets, strong navy.",
        home_cluster="core",
        allies=["science_collective"],
        enemies=["free_states", "corsairs"],
        color="#4fc3f7",
        corporations=[
            Corporation("tf_navy", "Federal Navy", "terran_fed", "military",
                       "The armed forces of the Federation. Patrols core space, enforces law."),
            Corporation("tf_stellarcorp", "StellarCorp Industries", "terran_fed", "manufacturing",
                       "Largest manufacturer in Federation space. Hull plating, engines, stations."),
            Corporation("tf_aegis", "Aegis Defense Systems", "terran_fed", "military",
                       "Premier weapons and shield manufacturer. Military contracts only."),
            Corporation("tf_transit", "Federal Transit Authority", "terran_fed", "trade",
                       "Operates jump gates and regulates interstellar commerce."),
        ],
    ),

    "science_collective": Faction(
        id="science_collective",
        name="Nexus Collective",
        short="NXC",
        philosophy="Knowledge is power. Research, innovation, technological supremacy.",
        home_cluster="core",
        allies=["terran_fed"],
        enemies=["corsairs"],
        color="#ab47bc",
        corporations=[
            Corporation("nc_labs", "Nexus Research Labs", "science_collective", "research",
                       "Cutting-edge R&D. Quantum filaments, exotic materials, prototype tech."),
            Corporation("nc_biotech", "Helix Biomedical", "science_collective", "research",
                       "Pharmaceuticals, nanite paste, life support systems, cloning."),
            Corporation("nc_quantum", "QuantumCore Ltd", "science_collective", "manufacturing",
                       "Superconductors, processors, AI cores, drone brains."),
            Corporation("nc_survey", "Deep Space Cartography", "science_collective", "research",
                       "System surveys, anomaly research, navigation data."),
        ],
    ),

    "merchants_guild": Faction(
        id="merchants_guild",
        name="Merchants Guild",
        short="MGD",
        philosophy="Profit is progress. Free markets, minimal regulation, trade above all.",
        home_cluster="rim",
        allies=["free_states"],
        enemies=["terran_fed"],
        color="#ffd54f",
        corporations=[
            Corporation("mg_exchange", "Galactic Exchange", "merchants_guild", "trade",
                       "Operates the largest commodity markets. Sets baseline prices."),
            Corporation("mg_logistics", "Voidway Logistics", "merchants_guild", "trade",
                       "Bulk hauling, supply chain management, courier services."),
            Corporation("mg_bank", "Aurelia Banking Consortium", "merchants_guild", "trade",
                       "Financial services, insurance, contracts, escrow."),
            Corporation("mg_refinery", "Smelter's Union", "merchants_guild", "mining",
                       "Refinery operations across rim space. Bulk ore processing."),
        ],
    ),

    "free_states": Faction(
        id="free_states",
        name="Frontier Alliance",
        short="FRA",
        philosophy="Freedom above all. Self-governance, personal liberty, no central authority.",
        home_cluster="rim",
        allies=["merchants_guild"],
        enemies=["terran_fed"],
        color="#66bb6a",
        corporations=[
            Corporation("fs_miners", "Rockbreaker Collective", "free_states", "mining",
                       "Independent mining cooperatives. Deep core, rare ore specialists."),
            Corporation("fs_militia", "Frontier Militia", "free_states", "military",
                       "Volunteer defense force. Anti-pirate patrols in rim space."),
            Corporation("fs_salvage", "Wraith Salvage", "free_states", "mining",
                       "Wreck recovery, decommissioning, scrap recycling."),
            Corporation("fs_ranch", "Terraform Pioneers", "free_states", "trade",
                       "Colony establishment, bio-dome farming, frontier supply."),
        ],
    ),

    "iron_compact": Faction(
        id="iron_compact",
        name="Iron Compact",
        short="IRC",
        philosophy="Strength through industry. Military-industrial complex, expansion, conquest.",
        home_cluster="frontier",
        allies=[],
        enemies=["science_collective", "free_states"],
        color="#ff8a65",
        corporations=[
            Corporation("ic_forge", "Crucible Forge Works", "iron_compact", "manufacturing",
                       "Heavy weapons, capital ship components, orbital platforms."),
            Corporation("ic_fleet", "Compact Armada", "iron_compact", "military",
                       "The war machine. Battlecruisers, carriers, conquest fleets."),
            Corporation("ic_mining", "Deepvein Extraction", "iron_compact", "mining",
                       "Strip mining operations. Aggressive resource acquisition."),
            Corporation("ic_intel", "Shadow Bureau", "iron_compact", "military",
                       "Intelligence, espionage, sabotage, black ops."),
        ],
    ),

    "corsairs": Faction(
        id="corsairs",
        name="The Corsairs",
        short="CRS",
        philosophy="Take what you can. Piracy, smuggling, black markets, no rules.",
        home_cluster="frontier",
        allies=[],
        enemies=["terran_fed", "science_collective", "merchants_guild"],
        color="#ef5350",
        corporations=[
            Corporation("crs_raiders", "Blood Fangs", "corsairs", "military",
                       "Pirate fleet. Ambushes, gate camps, ransom operations."),
            Corporation("crs_market", "Black Bazaar", "corsairs", "trade",
                       "Contraband, stolen goods, illegal modifications, fencing."),
            Corporation("crs_smuggle", "Shadow Runners", "corsairs", "trade",
                       "Smuggling networks. Moves banned goods through blockades."),
            Corporation("crs_tech", "Scrapyard Genius", "corsairs", "manufacturing",
                       "Jury-rigged weapons, illegal mods, boosters, hacked drones."),
        ],
    ),
}

# System -> primary faction ownership
SYSTEM_FACTIONS = {
    # Core - Terran Federation
    "cygnus": "terran_fed", "kepler": "terran_fed", "tau_ceti": "terran_fed",
    "sirius": "terran_fed", "deneb": "terran_fed", "polaris": "terran_fed",
    # Core - Nexus Collective
    "procyon": "science_collective", "fomalhaut": "science_collective",
    "sol": "science_collective", "haven": "science_collective",
    # Core - Shared
    "vega_prime": "merchants_guild", "meridian": "merchants_guild",
    # Rim - Merchants Guild
    "arcturus": "merchants_guild", "vega": "merchants_guild", "altair": "merchants_guild",
    "capella": "merchants_guild", "aldebaran": "merchants_guild", "regulus": "merchants_guild",
    "novus": "merchants_guild",
    # Rim - Frontier Alliance
    "barnards": "free_states", "antares": "free_states", "betelgeuse": "free_states",
    "castor": "free_states", "achernar": "free_states", "draconis": "free_states",
    "lyra": "free_states", "serpentis": "free_states", "havens_edge": "free_states",
    "helios": "free_states", "osiris": "free_states",
    # Rim - Mixed
    "corvus": "iron_compact", "fornax": "iron_compact",
    "hydra": "merchants_guild", "aquila": "free_states", "mira": "free_states",
    # Frontier - Iron Compact
    "wolf359": "iron_compact", "rigel": "iron_compact", "canopus": "iron_compact",
    "spica": "iron_compact", "terminus": "iron_compact",
    # Frontier - Corsairs
    "the_void": "corsairs", "obsidian": "corsairs", "erebus": "corsairs",
    "phantom": "corsairs", "the_abyss": "corsairs", "nyx": "corsairs",
    # Frontier - Contested
    "pollux": "corsairs", "pyxis": "iron_compact",
}


def get_faction(faction_id: str) -> Faction | None:
    return FACTIONS.get(faction_id)


def get_system_faction(system_id: str) -> str:
    return SYSTEM_FACTIONS.get(system_id, "")


def get_corps_for_faction(faction_id: str) -> list[Corporation]:
    f = FACTIONS.get(faction_id)
    return f.corporations if f else []
