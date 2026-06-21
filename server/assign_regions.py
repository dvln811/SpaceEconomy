"""Assign 12 regions by grouping adjacent constellations."""
import sqlite3
import json
import os
import random

random.seed(42)

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "game_data.db")

REGION_NAMES = [
    'The Forge', 'Genesis', 'Domain', 'Citadel',
    'Outer Ring', 'Syndicate', 'Pure Blind', 'Detorid',
    'Wicked Creek', 'Scalding Pass', 'Great Wildlands', 'Stain',
]

def assign_regions():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    
    # Add region column if not exists
    cols = [r[1] for r in conn.execute('PRAGMA table_info(systems)')]
    if 'region' not in cols:
        conn.execute("ALTER TABLE systems ADD COLUMN region TEXT DEFAULT ''")
        conn.commit()
        print("Added region column")
    
    # Get all constellations and their centers
    constellations = {}
    rows = conn.execute('SELECT id, cluster, x, y, z FROM systems').fetchall()
    for r in rows:
        c = r['cluster']
        if not c:
            continue
        if c not in constellations:
            constellations[c] = {'x': 0, 'y': 0, 'z': 0, 'n': 0, 'systems': []}
        constellations[c]['x'] += r['x']
        constellations[c]['y'] += r['y']
        constellations[c]['z'] += r['z']
        constellations[c]['n'] += 1
        constellations[c]['systems'].append(r['id'])
    
    for c in constellations.values():
        c['x'] /= c['n']
        c['y'] /= c['n']
        c['z'] /= c['n']
    
    # Build constellation adjacency from system connections
    sys_to_const = {}
    for r in rows:
        sys_to_const[r['id']] = r['cluster']
    
    const_adj = {c: set() for c in constellations}
    conns = conn.execute('SELECT from_id, to_id FROM system_connections').fetchall()
    for r in conns:
        c1 = sys_to_const.get(r['from_id'], '')
        c2 = sys_to_const.get(r['to_id'], '')
        if c1 and c2 and c1 != c2:
            const_adj[c1].add(c2)
            const_adj[c2].add(c1)
    
    # Assign 12 regions via BFS from 12 seed constellations (spread out)
    const_names = list(constellations.keys())
    
    # Pick 12 seed constellations maximally spread apart
    import math
    seeds = [const_names[0]]
    while len(seeds) < 12:
        best_c = None
        best_dist = 0
        for c in const_names:
            if c in seeds:
                continue
            min_d = min(
                math.sqrt((constellations[c]['x'] - constellations[s]['x'])**2 +
                          (constellations[c]['y'] - constellations[s]['y'])**2 +
                          (constellations[c]['z'] - constellations[s]['z'])**2)
                for s in seeds
            )
            if min_d > best_dist:
                best_dist = min_d
                best_c = c
        seeds.append(best_c)
    
    # BFS from all seeds simultaneously (Voronoi-like expansion)
    region_assignment = {}  # constellation -> region index
    queues = [[s] for s in seeds]
    for i, s in enumerate(seeds):
        region_assignment[s] = i
    
    changed = True
    while changed:
        changed = False
        for i in range(12):
            next_queue = []
            for c in queues[i]:
                for nb in const_adj.get(c, set()):
                    if nb not in region_assignment:
                        region_assignment[nb] = i
                        next_queue.append(nb)
                        changed = True
            queues[i] = next_queue
    
    # Any unassigned (disconnected) get nearest region
    for c in const_names:
        if c not in region_assignment:
            best_r = 0
            best_d = float('inf')
            for i, s in enumerate(seeds):
                d = math.sqrt((constellations[c]['x'] - constellations[s]['x'])**2 +
                              (constellations[c]['y'] - constellations[s]['y'])**2 +
                              (constellations[c]['z'] - constellations[s]['z'])**2)
                if d < best_d:
                    best_d = d
                    best_r = i
            region_assignment[c] = best_r
    
    # Update DB
    for const_name, region_idx in region_assignment.items():
        region_name = REGION_NAMES[region_idx]
        for sid in constellations[const_name]['systems']:
            conn.execute('UPDATE systems SET region=? WHERE id=?', (region_name, sid))
    
    conn.commit()
    
    # Stats
    region_counts = {}
    for const_name, region_idx in region_assignment.items():
        rn = REGION_NAMES[region_idx]
        region_counts[rn] = region_counts.get(rn, 0) + constellations[const_name]['n']
    
    print(f"Assigned {len(REGION_NAMES)} regions:")
    for rn, count in sorted(region_counts.items(), key=lambda x: -x[1]):
        const_count = sum(1 for c, r in region_assignment.items() if REGION_NAMES[r] == rn)
        print(f"  {rn}: {count} systems, {const_count} constellations")
    
    conn.close()


if __name__ == '__main__':
    assign_regions()
