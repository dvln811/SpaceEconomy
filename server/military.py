"""Military ship class definitions. Used for faction warfare simulation.
Each faction has a fleet composed of these ship classes."""
from dataclasses import dataclass, field


@dataclass
class MilitaryShipClass:
    id: str
    name: str
    hull_class: str      # fighter, frigate, destroyer, cruiser, battlecruiser, battleship, carrier, dreadnought
    faction: str
    hull_hp: int
    armor_hp: int
    shield_hp: int
    weapons: list[str] = field(default_factory=list)  # weapon commodity IDs fitted
    modules: list[str] = field(default_factory=list)  # other module IDs fitted
    build_cost: dict[str, int] = field(default_factory=dict)  # commodity_id: qty to build
    crew: int = 0
    description: str = ""


# ══════════════════════════════════════════════════════════════════════════════
# HULL CLASSES (smallest to largest)
# ══════════════════════════════════════════════════════════════════════════════
# Fighter:      1-2 S weapons, fast, fragile, cheap. Swarm tactics.
# Frigate:      2-3 S weapons, some defense. Picket/escort duty.
# Destroyer:    4-6 S weapons, anti-frigate specialist.
# Cruiser:      3-4 M weapons, versatile backbone. Can fit M shields.
# Battlecruiser: 4-6 M weapons, heavy armor. Fleet anchor.
# Battleship:   6-8 M/L weapons, massive tank. Slow but devastating.
# Carrier:      Drone bay (50+ drones), minimal direct weapons.
# Dreadnought:  2-4 XL weapons (siege), capital-only. System assault.

MILITARY_SHIPS = {
    # ── TERRAN FEDERATION ─────────────────────────────────────────────────────
    "tf_interceptor": MilitaryShipClass(
        id="tf_interceptor", name="Aquila Interceptor", hull_class="fighter", faction="terran_fed",
        hull_hp=200, armor_hp=100, shield_hp=150,
        weapons=["pulse_laser", "pulse_laser"],
        modules=["shield_booster", "afterburner"],
        build_cost={"hull_plating": 2, "std_engine": 1, "pulse_laser": 2, "shield_booster": 1},
        crew=1, description="Fast Federation interceptor. Dual pulse lasers strip shields at close range."),
    "tf_frigate": MilitaryShipClass(
        id="tf_frigate", name="Centurion Frigate", hull_class="frigate", faction="terran_fed",
        hull_hp=400, armor_hp=300, shield_hp=350,
        weapons=["pulse_laser", "pulse_laser", "missile_launcher"],
        modules=["shield_generator", "afterburner", "sensor_package"],
        build_cost={"hull_plating": 4, "std_engine": 1, "pulse_laser": 2, "missile_launcher": 1, "shield_generator": 1},
        crew=5, description="Workhorse patrol frigate. Point defense escort and picket line duty."),
    "tf_cruiser": MilitaryShipClass(
        id="tf_cruiser", name="Praetor Cruiser", hull_class="cruiser", faction="terran_fed",
        hull_hp=1200, armor_hp=800, shield_hp=1000,
        weapons=["beam_laser_m", "beam_laser_m", "missile_launcher_m", "point_defense"],
        modules=["shield_gen_m", "armor_repairer", "scanner_array", "maneuver_rig"],
        build_cost={"hull_plating": 10, "armor_plates": 4, "std_engine": 2, "beam_laser_m": 2, "missile_launcher_m": 1, "shield_gen_m": 1},
        crew=45, description="Federation line cruiser. Balanced firepower and defense. Fleet backbone."),
    "tf_battleship": MilitaryShipClass(
        id="tf_battleship", name="Imperator Battleship", hull_class="battleship", faction="terran_fed",
        hull_hp=4000, armor_hp=3000, shield_hp=2500,
        weapons=["railgun_l", "railgun_l", "beam_laser_m", "beam_laser_m", "point_defense", "point_defense"],
        modules=["shield_gen_l", "armor_plates_l", "armor_repairer", "jump_drive"],
        build_cost={"hull_plating": 30, "armor_plates_l": 4, "std_engine": 4, "railgun_l": 2, "beam_laser_m": 2, "shield_gen_l": 1, "jump_drive": 1},
        crew=350, description="Capital-class warship. Dual siege railguns can crack stations. The Federation's iron fist."),

    # ── NEXUS COLLECTIVE ──────────────────────────────────────────────────────
    "nc_scout": MilitaryShipClass(
        id="nc_scout", name="Spectre Scout", hull_class="fighter", faction="science_collective",
        hull_hp=150, armor_hp=50, shield_hp=250,
        weapons=["beam_laser"],
        modules=["shield_booster", "ecm_jammer", "scanner_array"],
        build_cost={"hull_plating": 1, "std_engine": 1, "beam_laser": 1, "ecm_jammer": 1, "scanner_array": 1},
        crew=1, description="Electronic warfare scout. Jams targeting while its beam laser picks apart shields."),
    "nc_cruiser": MilitaryShipClass(
        id="nc_cruiser", name="Synthesis Cruiser", hull_class="cruiser", faction="science_collective",
        hull_hp=800, armor_hp=400, shield_hp=1500,
        weapons=["plasma_cannon_m", "plasma_cannon_m", "beam_laser_m"],
        modules=["shield_gen_m", "shield_booster_m", "ecm_jammer", "repair_module"],
        build_cost={"hull_plating": 8, "std_engine": 2, "plasma_cannon_m": 2, "beam_laser_m": 1, "shield_gen_m": 1, "ecm_jammer": 1},
        crew=30, description="Shield-heavy research cruiser. Plasma cannons melt armor while ECM disrupts return fire."),
    "nc_carrier": MilitaryShipClass(
        id="nc_carrier", name="Hivemind Carrier", hull_class="carrier", faction="science_collective",
        hull_hp=3000, armor_hp=1500, shield_hp=3500,
        weapons=["point_defense", "point_defense"],
        modules=["shield_gen_l", "repair_module", "scanner_array", "jump_drive"],
        build_cost={"hull_plating": 20, "std_engine": 3, "combat_drone": 30, "shield_gen_l": 1, "jump_drive": 1, "repair_module": 2},
        crew=80, description="Drone carrier. Deploys swarms of AI-controlled combat drones. Minimal direct armament."),
    "nc_frigate": MilitaryShipClass(
        id="nc_frigate", name="Axiom Frigate", hull_class="frigate", faction="science_collective",
        hull_hp=350, armor_hp=150, shield_hp=500,
        weapons=["beam_laser", "beam_laser", "point_defense"],
        modules=["shield_generator", "ecm_jammer", "scanner_array"],
        build_cost={"hull_plating": 4, "std_engine": 1, "beam_laser": 2, "shield_generator": 1, "ecm_jammer": 1},
        crew=8, description="Shield-heavy EW platform. Layered barriers absorb fire while jammers blind enemy sensors."),
    "nc_battleship": MilitaryShipClass(
        id="nc_battleship", name="Paradigm Battleship", hull_class="battleship", faction="science_collective",
        hull_hp=3500, armor_hp=2000, shield_hp=4000,
        weapons=["plasma_cannon_l", "plasma_cannon_l", "beam_laser_m", "point_defense", "point_defense"],
        modules=["shield_gen_l", "shield_gen_l", "ecm_jammer", "repair_module", "jump_drive"],
        build_cost={"hull_plating": 25, "std_engine": 4, "plasma_cannon_l": 2, "beam_laser_m": 1, "shield_gen_l": 2, "jump_drive": 1, "combat_drone": 20},
        crew=200, description="Drone-assisted capital ship. Autonomous combat drones extend its reach while dual plasma cannons annihilate targets."),

    # ── MERCHANTS GUILD ───────────────────────────────────────────────────────
    "mg_escort": MilitaryShipClass(
        id="mg_escort", name="Bulwark Escort", hull_class="frigate", faction="merchants_guild",
        hull_hp=500, armor_hp=400, shield_hp=300,
        weapons=["autocannon", "autocannon", "point_defense"],
        modules=["armor_plates", "armor_repairer", "afterburner"],
        build_cost={"hull_plating": 5, "armor_plates": 2, "std_engine": 1, "autocannon": 2, "point_defense": 1},
        crew=8, description="Armored convoy escort. Cheap autocannons and thick plating keep pirates at bay."),
    "mg_cruiser": MilitaryShipClass(
        id="mg_cruiser", name="Dividend Cruiser", hull_class="cruiser", faction="merchants_guild",
        hull_hp=1400, armor_hp=1200, shield_hp=600,
        weapons=["autocannon_m", "autocannon_m", "missile_launcher_m", "missile_launcher_m"],
        modules=["armor_plates_m", "armor_repairer", "cargo_expander", "maneuver_rig"],
        build_cost={"hull_plating": 12, "armor_plates_m": 2, "std_engine": 2, "autocannon_m": 2, "missile_launcher_m": 2},
        crew=55, description="Armed merchantman. Quad weapons bays and heavy armor. Trade route enforcer."),
    "mg_picket": MilitaryShipClass(
        id="mg_picket", name="Venture Picket", hull_class="fighter", faction="merchants_guild",
        hull_hp=220, armor_hp=180, shield_hp=100,
        weapons=["autocannon", "missile_launcher"],
        modules=["armor_plates", "afterburner"],
        build_cost={"hull_plating": 2, "std_engine": 1, "autocannon": 1, "missile_launcher": 1, "armor_plates": 1},
        crew=1, description="Cheap convoy screen. Mass-produced to patrol trade lanes and deter opportunistic raiders."),
    "mg_battlecruiser": MilitaryShipClass(
        id="mg_battlecruiser", name="Sovereign Battlecruiser", hull_class="battlecruiser", faction="merchants_guild",
        hull_hp=2800, armor_hp=2200, shield_hp=1200,
        weapons=["autocannon_m", "autocannon_m", "autocannon_m", "missile_launcher_m", "missile_launcher_m", "point_defense", "point_defense"],
        modules=["armor_plates_m", "armor_plates_m", "armor_repairer", "maneuver_rig", "jump_drive"],
        build_cost={"hull_plating": 20, "armor_plates_m": 4, "std_engine": 3, "autocannon_m": 3, "missile_launcher_m": 2, "jump_drive": 1},
        crew=150, description="Trade lane enforcer. The Guild's answer to organized piracy—overwhelming firepower protecting profit margins."),

    # ── FRONTIER ALLIANCE ─────────────────────────────────────────────────────
    "fa_skirmisher": MilitaryShipClass(
        id="fa_skirmisher", name="Wasp Skirmisher", hull_class="fighter", faction="free_states",
        hull_hp=180, armor_hp=120, shield_hp=100,
        weapons=["autocannon", "autocannon"],
        modules=["afterburner", "maneuver_rig"],
        build_cost={"hull_plating": 2, "std_engine": 1, "autocannon": 2, "afterburner": 1},
        crew=1, description="Hit-and-run fighter. Blazing fast with dual autocannons. Cheap to replace."),
    "fa_destroyer": MilitaryShipClass(
        id="fa_destroyer", name="Hornet Destroyer", hull_class="destroyer", faction="free_states",
        hull_hp=700, armor_hp=500, shield_hp=300,
        weapons=["autocannon", "autocannon", "autocannon", "autocannon", "missile_launcher"],
        modules=["armor_plates", "afterburner", "maneuver_rig"],
        build_cost={"hull_plating": 6, "armor_plates": 2, "std_engine": 1, "autocannon": 4, "missile_launcher": 1},
        crew=15, description="Anti-frigate gunboat. Wall of autocannon fire shreds small ships."),
    "fa_battlecruiser": MilitaryShipClass(
        id="fa_battlecruiser", name="Thunderhead Battlecruiser", hull_class="battlecruiser", faction="free_states",
        hull_hp=2500, armor_hp=2000, shield_hp=1000,
        weapons=["autocannon_m", "autocannon_m", "autocannon_m", "missile_launcher_m", "missile_launcher_m", "point_defense"],
        modules=["armor_plates_m", "armor_plates_m", "armor_repairer", "maneuver_rig", "jump_drive"],
        build_cost={"hull_plating": 18, "armor_plates_m": 4, "std_engine": 3, "autocannon_m": 3, "missile_launcher_m": 2, "jump_drive": 1},
        crew=120, description="Militia flagship. Overwhelming volume of fire from massed autocannons. Built in hidden dockyards."),
    "fa_cruiser": MilitaryShipClass(
        id="fa_cruiser", name="Mantis Cruiser", hull_class="cruiser", faction="free_states",
        hull_hp=1100, armor_hp=900, shield_hp=600,
        weapons=["autocannon_m", "autocannon_m", "missile_launcher_m", "point_defense"],
        modules=["armor_plates_m", "afterburner", "ecm_jammer", "maneuver_rig"],
        build_cost={"hull_plating": 10, "armor_plates_m": 2, "std_engine": 2, "autocannon_m": 2, "missile_launcher_m": 1, "ecm_jammer": 1},
        crew=40, description="Guerrilla warfare platform. Fast enough to choose engagements, tough enough to survive them. Strike and fade."),

    # ── IRON COMPACT ──────────────────────────────────────────────────────────
    "ic_interceptor": MilitaryShipClass(
        id="ic_interceptor", name="Talon Interceptor", hull_class="fighter", faction="iron_compact",
        hull_hp=250, armor_hp=200, shield_hp=100,
        weapons=["railgun", "railgun"],
        modules=["armor_plates", "afterburner"],
        build_cost={"hull_plating": 3, "armor_plates": 1, "std_engine": 1, "railgun": 2},
        crew=1, description="Armored strike fighter. Twin railguns deliver devastating alpha strikes."),
    "ic_cruiser": MilitaryShipClass(
        id="ic_cruiser", name="Anvil Cruiser", hull_class="cruiser", faction="iron_compact",
        hull_hp=1500, armor_hp=1400, shield_hp=500,
        weapons=["railgun_m", "railgun_m", "autocannon_m", "autocannon_m"],
        modules=["armor_plates_m", "armor_plates_m", "armor_repairer", "maneuver_rig"],
        build_cost={"hull_plating": 14, "armor_plates_m": 4, "std_engine": 2, "railgun_m": 2, "autocannon_m": 2},
        crew=60, description="Heavily armored line cruiser. Railguns crack shields, autocannons finish the hull."),
    "ic_dreadnought": MilitaryShipClass(
        id="ic_dreadnought", name="Colossus Dreadnought", hull_class="dreadnought", faction="iron_compact",
        hull_hp=8000, armor_hp=6000, shield_hp=3000,
        weapons=["railgun_l", "railgun_l", "railgun_l", "railgun_l", "point_defense", "point_defense", "point_defense"],
        modules=["armor_plates_l", "armor_plates_l", "armor_plates_l", "shield_gen_l", "jump_drive", "repair_module"],
        build_cost={"hull_plating": 50, "armor_plates_l": 6, "std_engine": 6, "railgun_l": 4, "shield_gen_l": 1, "jump_drive": 1},
        crew=800, description="Siege capital ship. Four large railguns reduce stations to scrap. The Iron Compact's ultimate weapon."),
    "ic_destroyer": MilitaryShipClass(
        id="ic_destroyer", name="Hammer Destroyer", hull_class="destroyer", faction="iron_compact",
        hull_hp=800, armor_hp=700, shield_hp=200,
        weapons=["railgun", "railgun", "railgun", "railgun", "autocannon", "autocannon"],
        modules=["armor_plates", "armor_plates", "maneuver_rig"],
        build_cost={"hull_plating": 7, "armor_plates": 3, "std_engine": 1, "railgun": 4, "autocannon": 2},
        crew=20, description="Anti-fighter screen. Quad railguns deliver withering salvos that shred anything smaller than a cruiser."),

    # ── CORSAIRS ──────────────────────────────────────────────────────────────
    "crs_raider": MilitaryShipClass(
        id="crs_raider", name="Fang Raider", hull_class="frigate", faction="corsairs",
        hull_hp=350, armor_hp=200, shield_hp=200,
        weapons=["autocannon", "autocannon", "missile_launcher"],
        modules=["afterburner", "afterburner", "ecm_jammer"],
        build_cost={"hull_plating": 3, "std_engine": 1, "autocannon": 2, "missile_launcher": 1, "ecm_jammer": 1},
        crew=6, description="Pirate raider. Fast, cheap, expendable. Swarms overwhelm lone traders."),
    "crs_cruiser": MilitaryShipClass(
        id="crs_cruiser", name="Reaver Cruiser", hull_class="cruiser", faction="corsairs",
        hull_hp=1000, armor_hp=700, shield_hp=800,
        weapons=["plasma_cannon_m", "plasma_cannon_m", "autocannon_m", "autocannon_m"],
        modules=["shield_gen_m", "afterburner", "ecm_jammer", "cargo_expander"],
        build_cost={"hull_plating": 10, "std_engine": 2, "plasma_cannon_m": 2, "autocannon_m": 2, "shield_gen_m": 1, "ecm_jammer": 1},
        crew=40, description="Pirate flagship. Fast enough to catch traders, armed enough to kill escorts. Cargo bay for loot."),
    "crs_interceptor": MilitaryShipClass(
        id="crs_interceptor", name="Gnat Interceptor", hull_class="fighter", faction="corsairs",
        hull_hp=160, armor_hp=80, shield_hp=120,
        weapons=["autocannon", "autocannon"],
        modules=["afterburner", "afterburner", "ecm_jammer"],
        build_cost={"hull_plating": 1, "std_engine": 1, "autocannon": 2, "afterburner": 2, "ecm_jammer": 1},
        crew=1, description="Fast tackle/scrambler. Dual afterburners close distance before jammers disable warp drives. Disposable and deadly in packs."),
    "crs_battleship": MilitaryShipClass(
        id="crs_battleship", name="Dread Pirate", hull_class="battleship", faction="corsairs",
        hull_hp=3000, armor_hp=2000, shield_hp=2000,
        weapons=["plasma_cannon_l", "plasma_cannon_l", "autocannon_m", "autocannon_m", "missile_launcher_m", "point_defense"],
        modules=["shield_gen_l", "armor_plates_m", "afterburner", "ecm_jammer", "cargo_expander", "jump_drive"],
        build_cost={"hull_plating": 22, "armor_plates_m": 2, "std_engine": 4, "plasma_cannon_l": 2, "autocannon_m": 2, "shield_gen_l": 1, "jump_drive": 1},
        crew=250, description="Pirate flagship for raids. A terror of the shipping lanes—jumps in, disables escorts, loots everything that moves."),
}

# Fleet composition per faction (how many of each to maintain)
FLEET_TARGETS = {
    "terran_fed": {"tf_interceptor": 8, "tf_frigate": 6, "tf_cruiser": 4, "tf_battleship": 1},
    "science_collective": {"nc_scout": 6, "nc_cruiser": 4, "nc_carrier": 1, "nc_frigate": 4, "nc_battleship": 1},
    "merchants_guild": {"mg_escort": 8, "mg_cruiser": 3, "mg_picket": 6, "mg_battlecruiser": 1},
    "free_states": {"fa_skirmisher": 10, "fa_destroyer": 5, "fa_battlecruiser": 2, "fa_cruiser": 3},
    "iron_compact": {"ic_interceptor": 8, "ic_cruiser": 5, "ic_dreadnought": 1, "ic_destroyer": 4},
    "corsairs": {"crs_raider": 12, "crs_cruiser": 3, "crs_interceptor": 8, "crs_battleship": 1},
}
