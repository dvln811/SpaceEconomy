"""Migrate ships table: add fitting columns, remap hardpoints to H/M/L + turret/launcher."""
import sqlite3, json, os

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'game_data.db')
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

# --- Add new columns ---
new_cols = [
    ('cpu', 'INTEGER', '0'),
    ('powergrid', 'INTEGER', '0'),
    ('cap_recharge', 'REAL', '0'),
    ('signature', 'INTEGER', '0'),
    ('scan_res', 'INTEGER', '0'),
    ('sensor_strength', 'INTEGER', '0'),
    ('target_range', 'INTEGER', '0'),
    ('max_targets', 'INTEGER', '0'),
    ('high_slots', 'INTEGER', '0'),
    ('mid_slots', 'INTEGER', '0'),
    ('low_slots', 'INTEGER', '0'),
    ('turret_hardpoints', 'INTEGER', '0'),
    ('launcher_hardpoints', 'INTEGER', '0'),
]

existing = [r[1] for r in conn.execute('PRAGMA table_info(ships)').fetchall()]
for col, typ, default in new_cols:
    if col not in existing:
        conn.execute(f'ALTER TABLE ships ADD COLUMN {col} {typ} DEFAULT {default}')
        print(f'  Added column: {col}')

# --- Base stats by hull class ---
CLASS_STATS = {
    'Fighter':       {'cpu':125, 'pg':40,  'cap':250,  'cap_r':5.0,  'sig':25,  'scan':900, 'sens':8,  'trange':30, 'maxt':2, 'h':2,'m':2,'l':2,'th':2,'lh':1},
    'Frigate':       {'cpu':200, 'pg':60,  'cap':400,  'cap_r':7.5,  'sig':40,  'scan':700, 'sens':12, 'trange':50, 'maxt':3, 'h':3,'m':3,'l':2,'th':2,'lh':2},
    'Destroyer':     {'cpu':275, 'pg':100, 'cap':550,  'cap_r':10.0, 'sig':65,  'scan':550, 'sens':16, 'trange':60, 'maxt':4, 'h':5,'m':3,'l':3,'th':4,'lh':3},
    'Cruiser':       {'cpu':350, 'pg':150, 'cap':800,  'cap_r':15.0, 'sig':120, 'scan':400, 'sens':20, 'trange':70, 'maxt':5, 'h':5,'m':4,'l':4,'th':4,'lh':3},
    'Battlecruiser': {'cpu':450, 'pg':250, 'cap':1200, 'cap_r':20.0, 'sig':250, 'scan':300, 'sens':24, 'trange':80, 'maxt':6, 'h':6,'m':5,'l':5,'th':5,'lh':4},
    'Battleship':    {'cpu':550, 'pg':400, 'cap':1800, 'cap_r':25.0, 'sig':400, 'scan':200, 'sens':28, 'trange':90, 'maxt':7, 'h':7,'m':5,'l':6,'th':6,'lh':5},
    'Carrier':       {'cpu':600, 'pg':350, 'cap':2500, 'cap_r':30.0, 'sig':450, 'scan':250, 'sens':32, 'trange':100,'maxt':8, 'h':4,'m':6,'l':5,'th':2,'lh':2},
    'Dreadnought':   {'cpu':700, 'pg':600, 'cap':3500, 'cap_r':35.0, 'sig':550, 'scan':150, 'sens':36, 'trange':100,'maxt':8, 'h':8,'m':6,'l':6,'th':6,'lh':4},
    'Industrial':    {'cpu':250, 'pg':80,  'cap':500,  'cap_r':8.0,  'sig':150, 'scan':350, 'sens':10, 'trange':50, 'maxt':3, 'h':2,'m':3,'l':4,'th':1,'lh':1},
    'Mining Barge':  {'cpu':225, 'pg':70,  'cap':450,  'cap_r':7.0,  'sig':100, 'scan':400, 'sens':10, 'trange':40, 'maxt':2, 'h':3,'m':2,'l':3,'th':1,'lh':0},
}

# --- Per-ship overrides for variants (adjust slots/stats based on role) ---
# Format: ship_id -> dict of overrides
OVERRIDES = {
    # === CIVILIAN - Industrials scale by tier ===
    'pinto_runner':    {'cpu':150, 'pg':45,  'cap':300, 'cap_r':5.5, 'sig':80,  'h':2,'m':2,'l':2,'th':1,'lh':0},
    'mule_freighter':  {'cpu':200, 'pg':65,  'cap':400, 'cap_r':6.5, 'sig':120, 'h':2,'m':3,'l':3,'th':1,'lh':0},
    'bison_mkiii':     {'cpu':250, 'pg':80,  'cap':500, 'cap_r':8.0, 'sig':150, 'h':2,'m':3,'l':4,'th':1,'lh':1},
    'mammoth':         {'cpu':300, 'pg':100, 'cap':600, 'cap_r':9.0, 'sig':180, 'h':3,'m':4,'l':5,'th':1,'lh':1},
    'ox_hauler':       {'cpu':280, 'pg':90,  'cap':550, 'cap_r':8.5, 'sig':200, 'h':2,'m':3,'l':5,'th':1,'lh':1},
    'clydesdale':      {'cpu':350, 'pg':120, 'cap':700, 'cap_r':10.0,'sig':300, 'h':2,'m':4,'l':6,'th':1,'lh':1},
    # === CIVILIAN - Mining Barges scale by tier ===
    'prospect_skiff':  {'cpu':175, 'pg':50,  'cap':350, 'cap_r':5.5, 'sig':60,  'h':2,'m':2,'l':2,'th':1,'lh':0},
    'rock_hopper':     {'cpu':200, 'pg':60,  'cap':400, 'cap_r':6.0, 'sig':75,  'h':3,'m':2,'l':2,'th':1,'lh':0},
    'strip_miner':     {'cpu':225, 'pg':70,  'cap':450, 'cap_r':7.0, 'sig':90,  'h':3,'m':2,'l':3,'th':1,'lh':0},
    'excavator':       {'cpu':250, 'pg':80,  'cap':500, 'cap_r':7.5, 'sig':100, 'h':3,'m':3,'l':3,'th':1,'lh':0},
    'deep_core_borer': {'cpu':300, 'pg':100, 'cap':600, 'cap_r':9.0, 'sig':130, 'h':4,'m':3,'l':4,'th':1,'lh':0},
    # === CIVILIAN combat hulls ===
    'viper_interceptor': {'cpu':180, 'pg':55, 'cap':350, 'cap_r':7.0, 'sig':35, 'h':3,'m':2,'l':2,'th':2,'lh':1},
    'warden_frigate':    {'cpu':220, 'pg':70, 'cap':450, 'cap_r':8.5, 'sig':45, 'h':3,'m':3,'l':3,'th':3,'lh':2},
    'sentinel_corvette': {'cpu':300, 'pg':110,'cap':600, 'cap_r':11.0,'sig':70, 'h':5,'m':3,'l':3,'th':4,'lh':2},
    # === TERRAN FED ===
    'tf_interceptor':  {'h':2,'m':3,'l':2,'th':2,'lh':1, 'sig':22, 'scan':950},  # fast locker
    'tf_frigate':      {'h':3,'m':3,'l':3,'th':2,'lh':2},
    'tf_destroyer':    {'h':5,'m':3,'l':3,'th':4,'lh':2},
    'tf_cruiser':      {'h':5,'m':4,'l':4,'th':4,'lh':3},
    'tf_battlecruiser':{'h':6,'m':5,'l':5,'th':5,'lh':3},
    'tf_assault_battlecruiser': {'h':7,'m':4,'l':5,'th':6,'lh':3, 'cpu':470, 'pg':280},  # more highs, fewer mids
    'tf_battleship':   {'h':7,'m':5,'l':6,'th':6,'lh':4},
    'tf_dreadnought':  {'h':8,'m':6,'l':6,'th':6,'lh':4},
    'tf_carrier':      {'h':4,'m':6,'l':5,'th':2,'lh':2, 'scan':280},
    # === FREE STATES (armor/projectile focus) ===
    'fa_interceptor':  {'h':2,'m':2,'l':3,'th':2,'lh':1, 'sig':28},  # armor tanky fighter
    'fa_frigate':      {'h':3,'m':2,'l':3,'th':2,'lh':2},
    'fa_destroyer':    {'h':5,'m':2,'l':4,'th':4,'lh':3},  # more lows
    'fa_cruiser':      {'h':5,'m':3,'l':5,'th':4,'lh':3},  # armor cruiser
    'fa_battlecruiser':{'h':6,'m':4,'l':6,'th':5,'lh':4},
    'fa_strike_battlecruiser': {'h':7,'m':4,'l':5,'th':5,'lh':4, 'cpu':470, 'pg':270},
    'fa_battleship':   {'h':7,'m':4,'l':7,'th':6,'lh':5},  # armor heavy
    'fa_dreadnought':  {'h':8,'m':5,'l':7,'th':6,'lh':5, 'pg':650},
    # === IRON COMPACT (heavy armor, railguns) ===
    'ic_interceptor':  {'h':2,'m':2,'l':3,'th':2,'lh':0, 'sig':28},
    'ic_frigate':      {'h':3,'m':2,'l':3,'th':3,'lh':1},
    'ic_heavy_frigate':{'h':4,'m':2,'l':3,'th':3,'lh':2, 'cpu':230, 'pg':75},
    'ic_destroyer':    {'h':5,'m':2,'l':4,'th':5,'lh':2},
    'ic_heavy_destroyer': {'h':6,'m':2,'l':4,'th':5,'lh':2, 'cpu':300, 'pg':120},
    'ic_cruiser':      {'h':5,'m':3,'l':5,'th':4,'lh':2},
    'ic_heavy_cruiser':{'h':6,'m':3,'l':5,'th':5,'lh':2, 'cpu':380, 'pg':180},
    'ic_battlecruiser':{'h':6,'m':4,'l':6,'th':5,'lh':3},
    'ic_heavy_battlecruiser': {'h':7,'m':4,'l':6,'th':6,'lh':3, 'cpu':480, 'pg':280},
    'ic_battleship':   {'h':7,'m':4,'l':7,'th':6,'lh':4},
    'ic_dreadnought':  {'h':8,'m':5,'l':7,'th':7,'lh':3, 'pg':650},
    # === SCIENCE COLLECTIVE (shield/energy focus) ===
    'nc_interceptor':  {'h':2,'m':3,'l':1,'th':1,'lh':1, 'sig':22, 'scan':950},
    'nc_frigate':      {'h':3,'m':4,'l':2,'th':2,'lh':1, 'cpu':220},  # extra mid
    'nc_destroyer':    {'h':5,'m':4,'l':2,'th':3,'lh':2, 'cpu':300},
    'nc_cruiser':      {'h':5,'m':5,'l':3,'th':3,'lh':2, 'cpu':380},  # ewar platform
    'nc_battlecruiser':{'h':6,'m':6,'l':4,'th':4,'lh':3, 'cpu':480},
    'nc_phase_battlecruiser': {'h':5,'m':7,'l':4,'th':3,'lh':3, 'cpu':500, 'pg':230},  # ewar monster
    'nc_battleship':   {'h':7,'m':6,'l':5,'th':5,'lh':4, 'cpu':580},
    'nc_dreadnought':  {'h':8,'m':7,'l':5,'th':5,'lh':4, 'cpu':750},
    'nc_carrier':      {'h':4,'m':7,'l':5,'th':2,'lh':2, 'cpu':650},
    # === MERCHANTS GUILD (balanced, missile/turret mix) ===
    'mg_interceptor':  {'h':2,'m':2,'l':2,'th':1,'lh':1},
    'mg_frigate':      {'h':3,'m':3,'l':3,'th':2,'lh':2},
    'mg_destroyer':    {'h':5,'m':3,'l':3,'th':3,'lh':3},  # balanced hardpoints
    'mg_cruiser':      {'h':5,'m':4,'l':4,'th':3,'lh':3},
    'mg_patrol_cruiser':{'h':5,'m':5,'l':3,'th':3,'lh':3, 'cpu':370, 'scan':450},
    'mg_battlecruiser':{'h':6,'m':5,'l':5,'th':4,'lh':4},
    'mg_patrol_battlecruiser': {'h':6,'m':6,'l':4,'th':4,'lh':4, 'cpu':470, 'scan':350},
    'mg_battleship':   {'h':7,'m':5,'l':6,'th':5,'lh':5},
    'mg_dreadnought':  {'h':8,'m':6,'l':6,'th':5,'lh':5},
    # === CORSAIRS (glass cannon, speed) ===
    'crs_interceptor': {'h':3,'m':2,'l':1,'th':2,'lh':1, 'cpu':135, 'pg':45, 'sig':22},  # extra high
    'crs_frigate':     {'h':4,'m':2,'l':2,'th':3,'lh':2, 'cpu':210, 'pg':65},
    'crs_destroyer':   {'h':6,'m':2,'l':2,'th':4,'lh':3, 'cpu':290, 'pg':110},  # glass cannon
    'crs_cruiser':     {'h':6,'m':3,'l':3,'th':5,'lh':3, 'cpu':360, 'pg':160},
    'crs_battlecruiser':{'h':7,'m':4,'l':4,'th':5,'lh':4, 'cpu':460, 'pg':260},
    'crs_ambush_battlecruiser': {'h':7,'m':5,'l':4,'th':6,'lh':4, 'cpu':470, 'pg':270},
    'crs_battleship':  {'h':8,'m':4,'l':5,'th':6,'lh':5, 'cpu':560, 'pg':420},
}

# --- Apply stats to all ships ---
ships = conn.execute('SELECT id, hull_class, tier FROM ships').fetchall()
print(f'\nUpdating {len(ships)} ships...')

for ship in ships:
    sid = ship['id']
    hc = ship['hull_class']
    tier = ship['tier']

    base = CLASS_STATS.get(hc)
    if not base:
        print(f'  WARNING: No class stats for {hc} (ship {sid})')
        continue

    # Start with class defaults
    cpu = base['cpu']
    pg = base['pg']
    cap = base['cap']
    cap_r = base['cap_r']
    sig = base['sig']
    scan = base['scan']
    sens = base['sens']
    trange = base['trange']
    maxt = base['maxt']
    h = base['h']
    m = base['m']
    l = base['l']
    th = base['th']
    lh = base['lh']

    # Apply per-ship overrides
    ov = OVERRIDES.get(sid, {})
    cpu = ov.get('cpu', cpu)
    pg = ov.get('pg', pg)
    cap = ov.get('cap', cap)
    cap_r = ov.get('cap_r', cap_r)
    sig = ov.get('sig', sig)
    scan = ov.get('scan', scan)
    sens = ov.get('sens', sens)
    trange = ov.get('trange', trange)
    maxt = ov.get('maxt', maxt)
    h = ov.get('h', h)
    m = ov.get('m', m)
    l = ov.get('l', l)
    th = ov.get('th', th)
    lh = ov.get('lh', lh)

    # Update ship
    conn.execute('''UPDATE ships SET
        cpu=?, powergrid=?, cap_recharge=?, signature=?,
        scan_res=?, sensor_strength=?, target_range=?, max_targets=?,
        high_slots=?, mid_slots=?, low_slots=?, turret_hardpoints=?, launcher_hardpoints=?
        WHERE id=?''',
        (cpu, pg, cap_r, sig, scan, sens, trange, maxt, h, m, l, th, lh, sid))

    # Also update capacitor in fuel_capacity (repurpose as cap pool)
    conn.execute('UPDATE ships SET fuel_capacity=? WHERE id=?', (cap, sid))

conn.commit()
print('Done. Verifying...')

# Verify
rows = conn.execute('SELECT id, name, hull_class, cpu, powergrid, high_slots, mid_slots, low_slots, turret_hardpoints, launcher_hardpoints FROM ships ORDER BY hull_class, id').fetchall()
for r in rows:
    print(f'  {r["hull_class"]:15s} {r["name"]:20s} CPU:{r["cpu"]:>3} PG:{r["powergrid"]:>3} H:{r["high_slots"]} M:{r["mid_slots"]} L:{r["low_slots"]} T:{r["turret_hardpoints"]} Lnch:{r["launcher_hardpoints"]}')

conn.close()
