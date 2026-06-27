"""Update ship_geometry.py bounds to real-world scale and DB speed to m/s."""
import sqlite3, json, os, re, random

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB = os.path.join(BASE_DIR, 'data', 'game_data.db')
GEO_FILE = os.path.join(BASE_DIR, 'server', 'ship_geometry.py')

# --- Dimension ranges per hull class (meters) ---
# Based on Eve Online proportions
DIM_RANGES = {
    'Fighter':       {'length': (30, 50),    'width': (15, 30),   'height': (8, 18)},
    'Frigate':       {'length': (60, 110),   'width': (25, 55),   'height': (15, 35)},
    'Destroyer':     {'length': (120, 200),  'width': (40, 90),   'height': (25, 55)},
    'Cruiser':       {'length': (300, 500),  'width': (80, 180),  'height': (50, 120)},
    'Battlecruiser': {'length': (450, 700),  'width': (120, 250), 'height': (80, 170)},
    'Battleship':    {'length': (750, 1200), 'width': (200, 400), 'height': (120, 280)},
    'Carrier':       {'length': (1200, 2000),'width': (400, 800), 'height': (250, 500)},
    'Dreadnought':   {'length': (2200, 3800),'width': (500, 1000),'height': (350, 700)},
    'Industrial':    {'length': (200, 450),  'width': (60, 150),  'height': (50, 120)},
    'Mining Barge':  {'length': (150, 300),  'width': (60, 130),  'height': (40, 90)},
}

# --- Speed ranges per hull class (m/s) ---
SPEED_RANGES = {
    'Fighter':       (380, 450),
    'Frigate':       (300, 380),
    'Destroyer':     (220, 290),
    'Cruiser':       (160, 210),
    'Battlecruiser': (130, 160),
    'Battleship':    (95, 125),
    'Carrier':       (60, 80),
    'Dreadnought':   (50, 65),
    'Industrial':    (95, 130),
    'Mining Barge':  (85, 110),
}

# --- Update ship_geometry.py bounds ---
print("Updating ship_geometry.py bounds...")

with open(GEO_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# Get hull_class mapping from DB for each geometry ID
conn = sqlite3.connect(DB)
ship_classes = {}
rows = conn.execute('SELECT id, hull_class FROM ships').fetchall()
for r in rows:
    ship_classes[r[0]] = r[1]

# Find all bounds entries and replace with proper dimensions
# Pattern: "bounds": {"length": X, "height": Y, "width": Z}
def replace_bounds(match):
    # Find which ship this belongs to by searching backwards for the geometry ID
    start = match.start()
    # Look for the nearest SHIP_GEOMETRIES["xxx"] before this match
    preceding = content[:start]
    id_match = re.findall(r'SHIP_GEOMETRIES\["([^"]+)"\]', preceding)
    if not id_match:
        return match.group(0)
    ship_id = id_match[-1]
    hull_class = ship_classes.get(ship_id)
    if not hull_class:
        # Try to infer from the geometry data
        role_match = re.search(r'"role":\s*"([^"]+)"', content[start-200:start])
        if role_match:
            role = role_match.group(1)
            hull_class = role.replace('battlecruiser', 'Battlecruiser').replace('battleship', 'Battleship').replace('cruiser', 'Cruiser').replace('destroyer', 'Destroyer').replace('frigate', 'Frigate').replace('fighter', 'Fighter').replace('carrier', 'Carrier').replace('dreadnought', 'Dreadnought').replace('industrial', 'Industrial').replace('mining_barge', 'Mining Barge')
            # Capitalize first letter
            hull_class = hull_class[0].upper() + hull_class[1:]
    if not hull_class or hull_class not in DIM_RANGES:
        return match.group(0)

    dims = DIM_RANGES[hull_class]
    # Use a seeded random based on ship_id for consistency
    rng = random.Random(ship_id)
    length = round(rng.uniform(*dims['length']), 1)
    width = round(rng.uniform(*dims['width']), 1)
    height = round(rng.uniform(*dims['height']), 1)
    return f'"bounds": {{"length": {length}, "height": {height}, "width": {width}}}'

bounds_pattern = r'"bounds":\s*\{[^}]+\}'
new_content = re.sub(bounds_pattern, replace_bounds, content)

with open(GEO_FILE, 'w', encoding='utf-8') as f:
    f.write(new_content)

# Count changes
orig_count = len(re.findall(bounds_pattern, content))
print(f"  Updated {orig_count} bounds entries")

# --- Update DB speeds ---
print("Updating ship speeds to m/s...")

rows = conn.execute('SELECT id, hull_class, speed FROM ships').fetchall()
for r in rows:
    sid, hc, old_speed = r
    if hc not in SPEED_RANGES:
        continue
    lo, hi = SPEED_RANGES[hc]
    # Use the old speed multiplier to position within the range
    # old_speed was typically 0.7-1.8, normalize to 0-1
    norm = max(0, min(1, (old_speed - 0.7) / (1.8 - 0.7)))
    new_speed = round(lo + norm * (hi - lo))
    conn.execute('UPDATE ships SET speed=? WHERE id=?', (new_speed, sid))

conn.commit()

# Verify
print("\n--- Speed verification (sample) ---")
rows = conn.execute('SELECT name, hull_class, speed FROM ships ORDER BY hull_class, speed DESC LIMIT 20').fetchall()
for r in rows:
    print(f"  {r[1]:15s} {r[0]:20s} {int(r[2]):>4} m/s")

conn.close()
print("\nDone.")
