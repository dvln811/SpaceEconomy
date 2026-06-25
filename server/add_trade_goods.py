"""Add refined exotic ores + 35 trade goods + station_consumption updates."""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "game_data.db")

# Refined exotic ores
REFINED_ORES = [
    ("refined_gold", "Refined Gold", 900, 2, 0.05, 1.2, "High-purity gold ingots for electronics and luxury manufacturing.", "Materials", "Refined Materials", "Processed"),
    ("refined_platinum", "Refined Platinum", 1050, 2, 0.05, 1.2, "Catalyst-grade platinum for industrial and decorative use.", "Materials", "Refined Materials", "Processed"),
    ("refined_palladium", "Refined Palladium", 1200, 2, 0.05, 1.2, "Heat-resistant palladium for high-temperature alloys.", "Materials", "Refined Materials", "Processed"),
    ("purified_xenon", "Purified Xenon", 250, 2, 0.08, 1.2, "Filtered xenon gas for ion propulsion and lighting.", "Materials", "Refined Materials", "Processed"),
    ("polished_quartz", "Polished Quartz", 400, 2, 0.04, 1.2, "Optically pure quartz for lenses and display panels.", "Materials", "Refined Materials", "Processed"),
    ("refined_lithium", "Refined Lithium", 550, 2, 0.04, 1.2, "Stabilized lithium for batteries and pharmaceutical use.", "Materials", "Refined Materials", "Processed"),
    ("polished_beryllium", "Polished Beryllium", 700, 2, 0.04, 1.2, "Precision-cut beryllium for optics and reactor windows.", "Materials", "Refined Materials", "Processed"),
    ("neutronium_ingot", "Neutronium Ingot", 8000, 3, 0.1, 1.2, "Ultra-dense material for capital armor and jump drives.", "Materials", "Refined Materials", "Processed"),
]

REFINED_ORE_RECIPES = [
    ("refined_gold", "gold_ore", 3),
    ("refined_platinum", "platinum_ore", 3),
    ("refined_palladium", "palladium_ore", 3),
    ("purified_xenon", "xenon_gas", 2),
    ("purified_xenon", "nitrogen_ice", 1),
    ("polished_quartz", "quartz_crystal", 2),
    ("refined_lithium", "lithium_crystal", 2),
    ("refined_lithium", "cobalt_ore", 1),
    ("polished_beryllium", "beryllium_crystal", 2),
    ("polished_beryllium", "nitrogen_ice", 1),
    ("neutronium_ingot", "neutronium", 2),
    ("neutronium_ingot", "refined_platinum", 1),
]

# Trade goods: (id, name, price, tier, volume, elasticity, description, subcategory)
TRADE_GOODS = [
    # Necessities
    ("food_rations", "Food Rations", 50, 4, 1.0, 0.9, "Vacuum-sealed nutrient packs designed for extended space travel. Bland but reliable.", "Necessities"),
    ("oxygen_packs", "Oxygen Packs", 30, 4, 1.0, 0.9, "Compressed breathable atmosphere cartridges. Standard issue on every station.", "Necessities"),
    ("water_recyclers", "Water Recycler Units", 200, 4, 1.5, 0.9, "Closed-loop filtration systems that keep station populations alive between supply runs.", "Necessities"),
    ("life_support_cartridges", "Life Support Cartridges", 150, 4, 1.0, 0.9, "All-in-one atmospheric scrubbers for ship and station HVAC systems.", "Necessities"),
    ("housing_materials", "Prefab Housing Modules", 300, 4, 2.0, 0.9, "Flatpack living quarters for frontier colonists. Some assembly required.", "Necessities"),
    ("clothing_textiles", "Synthetic Textiles", 80, 4, 0.5, 0.9, "Temperature-regulating fabrics woven from petroleum derivatives. Comfortable enough.", "Necessities"),
    ("radiation_meds", "Radiation Medicine", 400, 4, 0.5, 0.8, "Anti-radiation compounds for crews working near reactors or in unshielded sectors.", "Necessities"),
    ("emergency_beacons", "Emergency Beacons", 250, 4, 0.5, 0.9, "Quantum-entangled distress transmitters. The difference between rescue and oblivion.", "Necessities"),
    # Consumer Goods
    ("personal_electronics", "Personal Electronics", 500, 4, 0.5, 0.9, "Tablets, comms, and personal AI assistants. The backbone of civilian connectivity.", "Consumer Goods"),
    ("entertainment_systems", "Entertainment Systems", 800, 4, 1.0, 0.9, "Holovid projectors and neural-link entertainment rigs. Sanity insurance for long voyages.", "Consumer Goods"),
    ("spirits_alcohol", "Distilled Spirits", 120, 4, 1.0, 0.8, "Fermented grain alcohol, aged in zero-G. Every station has a bar.", "Consumer Goods"),
    ("synthetic_tobacco", "Synthetic Tobacco", 90, 4, 0.5, 0.8, "Lab-grown nicotine products. Addiction rates unchanged since Earth.", "Consumer Goods"),
    ("cosmetics", "Cosmetics", 150, 4, 0.5, 0.9, "Beauty products adapted for low-gravity environments. Vanity persists in the void.", "Consumer Goods"),
    ("comm_devices", "Comm Devices", 350, 4, 0.5, 0.9, "Personal quantum-relay communicators. Range limited to system boundaries.", "Consumer Goods"),
    ("personal_weapons", "Personal Sidearms", 600, 4, 0.5, 1.0, "Compact kinetic or energy pistols. Legal in most jurisdictions, required in some.", "Consumer Goods"),
    ("holovid_players", "Holovid Players", 450, 4, 0.5, 0.9, "Portable holographic display units. News, entertainment, and education in your palm.", "Consumer Goods"),
    ("furniture", "Zero-G Furniture", 200, 4, 2.0, 0.9, "Magnetic-lock furnishings designed for variable gravity. Comfort is a luxury.", "Consumer Goods"),
    ("toys_games", "Games and Toys", 100, 4, 0.5, 0.9, "Digital and physical entertainments for children and bored miners alike.", "Consumer Goods"),
    # Industrial
    ("ship_repair_kits", "Ship Repair Kits", 1500, 4, 1.0, 1.0, "Field repair patches for hull breaches and conduit failures. Every captain carries a stack.", "Industrial"),
    ("fuel_cells", "Civilian Fuel Cells", 300, 4, 1.0, 0.9, "Standard fuel cartridges for civilian vessels. Pop in, fly out.", "Industrial"),
    ("escape_pods", "Escape Pods", 2000, 4, 2.0, 1.0, "Single-occupant survival capsules with 72-hour life support. Mandatory on all registered vessels.", "Industrial"),
    ("navigation_chips", "Navigation Data Chips", 400, 4, 0.5, 0.9, "Pre-loaded star charts and jump calculations. Outdated ones get you killed.", "Industrial"),
    ("stim_packs", "Stim Packs", 250, 4, 0.5, 0.8, "Combat stimulants and fatigue suppressors. Popular with miners and mercenaries.", "Industrial"),
    ("neural_implants", "Neural Implants", 3000, 5, 0.5, 1.0, "Brain-computer interfaces for enhanced reflexes and data processing. Not without risks.", "Industrial"),
    ("cybernetic_parts", "Cybernetic Replacement Parts", 2500, 5, 1.0, 1.0, "Artificial limbs and organs. Better than the originals, if you can afford them.", "Industrial"),
    ("drone_repair_kits", "Drone Maintenance Kits", 800, 4, 1.0, 0.9, "Replacement parts and calibration tools for mining and combat drones.", "Industrial"),
    ("industrial_lubricants", "Industrial Lubricants", 60, 4, 1.0, 0.9, "High-temperature greases for machinery in extreme environments.", "Industrial"),
    # Luxury
    ("exotic_wines", "Exotic Wines", 2000, 5, 1.0, 0.8, "Vintages from terraformed worlds. Status symbols among station elites.", "Luxury"),
    ("rare_gems", "Rare Gemstones", 5000, 5, 0.5, 0.8, "Cut and polished crystals from deep-space asteroids. No two alike.", "Luxury"),
    ("quantum_timepieces", "Quantum Timepieces", 8000, 5, 0.5, 0.8, "Atomic-precision chronometers synchronized across light-years. The ultimate executive accessory.", "Luxury"),
    ("zerog_perfume", "Zero-G Perfume", 1500, 5, 0.5, 0.8, "Engineered pheromone compounds that disperse evenly in microgravity. Intoxicating.", "Luxury"),
    ("synthetic_organs", "Synthetic Organs", 6000, 5, 1.0, 0.8, "Lab-grown replacement organs with decade-long warranties. The wealthy never truly die.", "Luxury"),
    ("memory_crystals", "Memory Crystals", 4000, 5, 0.5, 0.8, "Holographic data storage with petabyte capacity. Civilizations archived in your pocket.", "Luxury"),
    ("ai_companions", "AI Companion Cores", 10000, 5, 0.5, 0.8, "Sentient-adjacent artificial personalities. Companions, advisors, or something more.", "Luxury"),
    ("art_collections", "Art Collections", 3000, 5, 1.5, 0.8, "Curated works from across human space. Culture survives even in the void.", "Luxury"),
]

# Trade good recipes: (commodity_id, input_id, quantity)
TRADE_GOOD_RECIPES = [
    # Necessities
    ("food_rations", "processed_protein", 2), ("food_rations", "purified_water", 1),
    ("oxygen_packs", "hydral_ice", 1), ("oxygen_packs", "nitrogen_ice", 1),
    ("water_recyclers", "copper_wiring", 1), ("water_recyclers", "synthetic_polymer", 1),
    ("life_support_cartridges", "purified_water", 1), ("life_support_cartridges", "bio_catalyst", 1), ("life_support_cartridges", "synthetic_polymer", 1),
    ("housing_materials", "steel_plate", 2), ("housing_materials", "synthetic_polymer", 1), ("housing_materials", "copper_wiring", 1),
    ("clothing_textiles", "synthetic_polymer", 2), ("clothing_textiles", "processed_protein", 1),
    ("radiation_meds", "pharma_grade", 1), ("radiation_meds", "refined_lithium", 1),
    ("emergency_beacons", "microprocessor", 1), ("emergency_beacons", "lithium_cell", 1), ("emergency_beacons", "copper_wiring", 1),
    # Consumer Goods
    ("personal_electronics", "microprocessor", 2), ("personal_electronics", "copper_wiring", 1), ("personal_electronics", "polished_quartz", 1),
    ("entertainment_systems", "microprocessor", 2), ("entertainment_systems", "optical_lens", 1), ("entertainment_systems", "polished_quartz", 1),
    ("spirits_alcohol", "biomass", 2), ("spirits_alcohol", "purified_water", 1),
    ("synthetic_tobacco", "biomass", 1), ("synthetic_tobacco", "bio_catalyst", 1),
    ("cosmetics", "bio_catalyst", 1), ("cosmetics", "synthetic_polymer", 1), ("cosmetics", "purified_water", 1),
    ("comm_devices", "microprocessor", 1), ("comm_devices", "refined_gold", 1), ("comm_devices", "copper_wiring", 1),
    ("personal_weapons", "refined_iron", 1), ("personal_weapons", "refined_tungsten", 1), ("personal_weapons", "microprocessor", 1),
    ("holovid_players", "microprocessor", 1), ("holovid_players", "optical_lens", 1), ("holovid_players", "refined_copper", 1),
    ("furniture", "steel_plate", 1), ("furniture", "synthetic_polymer", 2),
    ("toys_games", "synthetic_polymer", 1), ("toys_games", "microprocessor", 1),
    # Industrial
    ("ship_repair_kits", "titanium_alloy", 1), ("ship_repair_kits", "copper_wiring", 1), ("ship_repair_kits", "nanite_paste", 1),
    ("fuel_cells", "hydrogen_fuel", 2), ("fuel_cells", "lithium_cell", 1),
    ("escape_pods", "steel_plate", 1), ("escape_pods", "life_support_cartridges", 1), ("escape_pods", "microprocessor", 1),
    ("navigation_chips", "microprocessor", 1), ("navigation_chips", "polished_quartz", 1),
    ("stim_packs", "pharma_grade", 1), ("stim_packs", "bio_catalyst", 1),
    ("neural_implants", "refined_gold", 1), ("neural_implants", "refined_platinum", 1), ("neural_implants", "microprocessor", 1), ("neural_implants", "nanite_paste", 1),
    ("cybernetic_parts", "refined_titanium", 1), ("cybernetic_parts", "microprocessor", 1), ("cybernetic_parts", "refined_platinum", 1),
    ("drone_repair_kits", "microprocessor", 1), ("drone_repair_kits", "copper_wiring", 1), ("drone_repair_kits", "refined_copper", 1),
    ("industrial_lubricants", "methane_fuel", 1), ("industrial_lubricants", "synthetic_polymer", 1),
    # Luxury
    ("exotic_wines", "biomass", 2), ("exotic_wines", "purified_water", 1), ("exotic_wines", "polished_quartz", 1),
    ("rare_gems", "polished_quartz", 2), ("rare_gems", "polished_beryllium", 1), ("rare_gems", "refined_gold", 1),
    ("quantum_timepieces", "refined_platinum", 1), ("quantum_timepieces", "polished_quartz", 1), ("quantum_timepieces", "microprocessor", 1), ("quantum_timepieces", "neutronium_ingot", 1),
    ("zerog_perfume", "spore_clusters", 1), ("zerog_perfume", "amino_gel", 1), ("zerog_perfume", "polished_quartz", 1),
    ("synthetic_organs", "nanite_paste", 1), ("synthetic_organs", "bio_catalyst", 1), ("synthetic_organs", "refined_platinum", 1), ("synthetic_organs", "pharma_grade", 1),
    ("memory_crystals", "polished_beryllium", 1), ("memory_crystals", "refined_gold", 1), ("memory_crystals", "microprocessor", 1),
    ("ai_companions", "microprocessor", 2), ("ai_companions", "refined_gold", 1), ("ai_companions", "polished_quartz", 1), ("ai_companions", "neutronium_ingot", 1),
    ("art_collections", "refined_gold", 1), ("art_collections", "polished_quartz", 1), ("art_collections", "synthetic_polymer", 1),
]

# New station_consumption entries
NEW_CONSUMPTION = [
    # Refineries consume the new exotic ores (raw inputs to generate buy orders)
    ("refinery", "gold_ore"), ("refinery", "platinum_ore"), ("refinery", "palladium_ore"),
    ("refinery", "xenon_gas"), ("refinery", "quartz_crystal"), ("refinery", "lithium_crystal"),
    ("refinery", "beryllium_crystal"), ("refinery", "neutronium"),
    # Component works consume refined exotic ores
    ("component_works", "refined_gold"), ("component_works", "refined_platinum"),
    ("component_works", "refined_palladium"), ("component_works", "polished_quartz"),
    ("component_works", "refined_lithium"), ("component_works", "polished_beryllium"),
    ("component_works", "neutronium_ingot"),
]


def run():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")

    # Insert refined ores
    for item in REFINED_ORES:
        conn.execute(
            "INSERT OR REPLACE INTO commodities (id, name, base_price, tier, volume, elasticity, description, category, subcategory, group_name, stats) VALUES (?,?,?,?,?,?,?,?,?,?,'{}')",
            item
        )

    # Insert refined ore recipes
    for cid, inp, qty in REFINED_ORE_RECIPES:
        conn.execute("INSERT OR REPLACE INTO recipes (commodity_id, input_id, quantity) VALUES (?,?,?)", (cid, inp, qty))

    # Insert trade goods
    for item in TRADE_GOODS:
        conn.execute(
            "INSERT OR REPLACE INTO commodities (id, name, base_price, tier, volume, elasticity, description, category, subcategory, group_name, stats) VALUES (?,?,?,?,?,?,?,'Trade Goods',?,'Trade Goods','{}')",
            item
        )

    # Insert trade good recipes
    for cid, inp, qty in TRADE_GOOD_RECIPES:
        conn.execute("INSERT OR REPLACE INTO recipes (commodity_id, input_id, quantity) VALUES (?,?,?)", (cid, inp, qty))

    # Insert station_consumption
    for st, cid in NEW_CONSUMPTION:
        conn.execute("INSERT OR IGNORE INTO station_consumption (station_type, commodity_id) VALUES (?,?)", (st, cid))

    # Remove old generic trade goods that are now replaced
    old_ids = ('luxury_goods', 'consumer_elec', 'gourmet_food', 'exotic_textiles', 'entertainment', 'fine_spirits')
    conn.executemany("DELETE FROM commodities WHERE id=?", [(x,) for x in old_ids])
    conn.executemany("DELETE FROM station_consumption WHERE commodity_id=?", [(x,) for x in old_ids])

    conn.commit()
    # Verify counts
    count = conn.execute("SELECT COUNT(*) FROM commodities WHERE category='Trade Goods'").fetchone()[0]
    refined = conn.execute("SELECT COUNT(*) FROM commodities WHERE id IN ('refined_gold','refined_platinum','refined_palladium','purified_xenon','polished_quartz','refined_lithium','polished_beryllium','neutronium_ingot')").fetchone()[0]
    print(f"Trade goods: {count}, New refined ores: {refined}")
    conn.close()


if __name__ == "__main__":
    run()
