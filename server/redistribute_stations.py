"""Redistribute stations with full production chains per faction.

Rules:
- High-sec: 3-5 stations per system
- Med-sec: 2-3 stations per system  
- Low-sec: 1-2 stations per system
- Null-sec: 0 (future expansion)
- Each faction gets complete production chain
- Allied stations in ally territory
- Station services assigned by type
"""
import sqlite3
import json
import random
import os

random.seed(42)

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "game_data.db")

# What each station type produces (commodity IDs)
STATION_PRODUCTION = {
    'mining_colony': [],  # Miners deliver ore here, doesn't produce itself
    'refinery': ['refined_iron', 'refined_copper', 'refined_titanium', 'refined_tungsten', 
                 'chromium_plate', 'bronze_alloy', 'cobalt_ingot', 'hydrogen_fuel',
                 'liquid_nitrogen', 'methane_fuel', 'purified_water', 'industrial_solvent',
                 'enriched_he3', 'xenon_propellant', 'processed_protein', 'bio_catalyst',
                 'synthetic_polymer', 'silicon_wafer', 'copper_wiring', 'lithium_cell'],
    'factory': ['steel_plate', 'titanium_alloy', 'tungsten_carbide', 'carbon_composite',
                'ceramic_plate', 'microprocessor', 'superconductor', 'optical_lens',
                'power_cell', 'fusion_pellet', 'thruster_nozzle', 'plasma_conduit',
                'magnetic_coil', 'pharma_grade', 'nanite_paste', 'explosive_compound',
                'rad_shielding', 'hull_plating', 'quantum_filament'],
    'component_works': ['beam_emitter', 'railgun_barrel', 'missile_chassis', 'plasma_chamber',
                        'warhead_assembly', 'shield_emitter', 'armor_laminate', 'pd_array',
                        'ecm_core', 'fusion_core', 'ion_drive', 'warp_coil',
                        'maneuver_thruster', 'sensor_package', 'nav_computer',
                        'life_support_core', 'drone_brain', 'repair_core',
                        'mining_optic', 'drill_head', 'ore_processor', 'tractor_core'],
    'shipyard': ['pulse_laser', 'beam_laser', 'railgun', 'plasma_cannon', 
                 'missile_launcher', 'autocannon', 'shield_generator', 'armor_plates',
                 'std_engine', 'jump_drive', 'combat_drone', 'mining_laser'],
    'trade_hub': [],  # No production, just market
    'military_base': [],  # Fleet staging, no production
}

# Services by station type
STATION_SERVICES = {
    'mining_colony': ['market', 'refuel', 'storage'],
    'refinery': ['market', 'refuel', 'storage', 'repair'],
    'factory': ['market', 'storage', 'repair'],
    'component_works': ['market', 'storage', 'fitting'],
    'shipyard': ['market', 'repair', 'refuel', 'fitting', 'storage'],
    'trade_hub': ['market', 'repair', 'refuel', 'agents', 'fitting', 'storage'],
    'military_base': ['market', 'repair', 'refuel', 'agents', 'storage'],
}

# Production rates by security
RATES = {'high': 1.0, 'medium': 0.7, 'low': 0.4}

# Faction allies (can have stations in each other's space)
ALLIES = {
    'terran_fed': ['science_collective'],
    'science_collective': ['terran_fed'],
    'merchants_guild': ['free_states'],
    'free_states': ['merchants_guild'],
    'iron_compact': [],
    'corsairs': [],
}

# Station naming patterns
NAMES = {
    'mining_colony': ['Mining Colony', 'Ore Extraction', 'Deep Mine', 'Belt Works'],
    'refinery': ['Refinery', 'Smelter', 'Processing Hub', 'Ore Works'],
    'factory': ['Factory', 'Industrial Hub', 'Forge', 'Manufacturing'],
    'component_works': ['Component Works', 'Assembly Plant', 'Tech Lab', 'Fabrication'],
    'shipyard': ['Shipyard', 'Drydock', 'Naval Yards', 'Dockyard'],
    'trade_hub': ['Trade Hub', 'Exchange', 'Market', 'Bazaar', 'Free Port'],
    'military_base': ['Military Base', 'Fleet Command', 'Naval Station', 'Garrison'],
}


def redistribute():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    
    # Clear existing stations
    conn.execute("DELETE FROM station_produces")
    conn.execute("DELETE FROM stations")
    
    # Get faction systems grouped by security
    factions = ['terran_fed', 'science_collective', 'merchants_guild', 'free_states', 'iron_compact', 'corsairs']
    
    station_id = 0
    total_stations = 0
    
    for fid in factions:
        if fid == 'corsairs':
            continue  # Corsairs don't have formal stations (yet)
        
        systems = conn.execute(
            "SELECT id, name, security FROM systems WHERE faction_id=? ORDER BY security DESC, name",
            (fid,)
        ).fetchall()
        
        # Determine how many of each station type this faction needs
        # Each faction gets: multiple refineries, factories, at least 1 of each type
        high_sys = [s for s in systems if s['security'] == 'high']
        med_sys = [s for s in systems if s['security'] == 'medium']
        low_sys = [s for s in systems if s['security'] == 'low']
        
        all_sys = high_sys + med_sys + low_sys
        if not all_sys:
            continue
        
        # Assign station types across systems ensuring full chain
        # Priority: shipyards in high-sec, mining in systems with belts, etc.
        chain_types = ['refinery', 'factory', 'component_works', 'shipyard', 
                       'trade_hub', 'military_base', 'mining_colony']
        
        faction_stations = []
        
        for sys in all_sys:
            sec = sys['security']
            num_stations = {'high': random.randint(3, 5), 'medium': random.randint(2, 3), 'low': random.randint(1, 2)}[sec]
            
            for i in range(num_stations):
                # First stations fill the chain, then repeat common types
                if i == 0 and sec == 'high':
                    stype = chain_types[len(faction_stations) % len(chain_types)]
                elif i == 0:
                    stype = random.choice(['refinery', 'factory', 'mining_colony', 'trade_hub'])
                else:
                    stype = random.choice(['refinery', 'factory', 'component_works', 'trade_hub', 'mining_colony'])
                
                station_id += 1
                sid = f"st_{station_id:05d}"
                name_options = NAMES[stype]
                sname = f"{sys['name']} {random.choice(name_options)}"
                rate = RATES[sec]
                services = json.dumps(STATION_SERVICES[stype])
                
                conn.execute(
                    "INSERT INTO stations (id, name, system_id, station_type, production_rate) VALUES (?,?,?,?,?)",
                    (sid, sname, sys['id'], stype, rate)
                )
                
                # Assign production (pick 2-4 items from the type's production list)
                produces = STATION_PRODUCTION[stype]
                if produces:
                    num_produce = min(random.randint(2, 4), len(produces))
                    selected = random.sample(produces, num_produce)
                    for prod_id in selected:
                        conn.execute(
                            "INSERT INTO station_produces (station_id, commodity_id) VALUES (?,?)",
                            (sid, prod_id)
                        )
                
                faction_stations.append((sid, stype))
                total_stations += 1
        
        # Ensure at least 1 of each critical type
        types_present = set(t for _, t in faction_stations)
        critical = ['refinery', 'factory', 'component_works', 'shipyard']
        for ctype in critical:
            if ctype not in types_present and all_sys:
                # Add one in a high-sec system
                target_sys = high_sys[0] if high_sys else all_sys[0]
                station_id += 1
                sid = f"st_{station_id:05d}"
                sname = f"{target_sys['name']} {random.choice(NAMES[ctype])}"
                conn.execute(
                    "INSERT INTO stations (id, name, system_id, station_type, production_rate) VALUES (?,?,?,?,?)",
                    (sid, sname, target_sys['id'], ctype, 1.0)
                )
                produces = STATION_PRODUCTION[ctype]
                if produces:
                    for prod_id in random.sample(produces, min(3, len(produces))):
                        conn.execute("INSERT INTO station_produces (station_id, commodity_id) VALUES (?,?)", (sid, prod_id))
                total_stations += 1
        
        print(f"  {fid}: {len(faction_stations)} stations across {len(all_sys)} systems")
    
    # Add some allied stations (Merchants Guild trade hubs in TF space, etc.)
    for fid, allies in ALLIES.items():
        for ally_fid in allies:
            # Find 2-3 high-sec systems of the ally to place a station
            ally_systems = conn.execute(
                "SELECT id, name FROM systems WHERE faction_id=? AND security='high' LIMIT 3",
                (ally_fid,)
            ).fetchall()
            for asys in ally_systems[:2]:
                station_id += 1
                sid = f"st_{station_id:05d}"
                stype = 'trade_hub' if fid == 'merchants_guild' else 'factory'
                sname = f"{asys['name']} {random.choice(NAMES[stype])} ({fid.replace('_',' ').title()})"
                conn.execute(
                    "INSERT INTO stations (id, name, system_id, station_type, production_rate) VALUES (?,?,?,?,?)",
                    (sid, sname, asys['id'], stype, 0.8)
                )
                total_stations += 1
    
    conn.commit()
    
    # Stats
    print(f"\nTotal stations: {total_stations}")
    rows = conn.execute("""
        SELECT s.faction_id, st.station_type, COUNT(*) as c 
        FROM stations st JOIN systems s ON st.system_id=s.id 
        GROUP BY s.faction_id, st.station_type ORDER BY s.faction_id
    """).fetchall()
    current_fac = ''
    for r in rows:
        f = r['faction_id'] or 'allied'
        if f != current_fac:
            print(f"  {f}:")
            current_fac = f
        print(f"    {r['station_type']}: {r['c']}")
    
    conn.close()


if __name__ == '__main__':
    print("Redistributing stations...")
    redistribute()
    print("\nDone!")
