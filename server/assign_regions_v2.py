"""Reassign regions: 20 balanced regions (~125 systems each) for the multi-threaded architecture.
Regions are gameplay boundaries (market visibility, NPC search scope).
Clusters remain as spatial/generation grouping."""
import sqlite3
import math
import os

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "game_data.db")

REGION_NAMES = [
    'The Forge', 'Genesis', 'Domain', 'Citadel', 'Outer Ring',
    'Syndicate', 'Pure Blind', 'Detorid', 'Wicked Creek', 'Scalding Pass',
    'Great Wildlands', 'Stain', 'Molden Heath', 'Tribute', 'Vale of Silence',
    'Deklein', 'Fountain', 'Delve', 'Querious', 'Catch',
]

NUM_REGIONS = 20


def assign_regions():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    # Load all systems with positions
    rows = conn.execute('SELECT id, x, y, z FROM systems').fetchall()
    systems = [(r['id'], r['x'], r['y'], r['z']) for r in rows]
    total = len(systems)
    target_per_region = total / NUM_REGIONS
    print(f"{total} systems, target ~{target_per_region:.0f} per region")

    # Build adjacency from connections
    adjacency = {s[0]: set() for s in systems}
    conns = conn.execute('SELECT from_id, to_id FROM system_connections').fetchall()
    for c in conns:
        adjacency[c['from_id']].add(c['to_id'])
        adjacency[c['to_id']].add(c['from_id'])

    # Pick 20 seed systems maximally spread apart
    sys_map = {s[0]: (s[1], s[2], s[3]) for s in systems}
    seeds = [systems[0][0]]
    while len(seeds) < NUM_REGIONS:
        best_id = None
        best_dist = 0
        for sid, x, y, z in systems:
            if sid in seeds:
                continue
            min_d = min(
                math.sqrt((x - sys_map[s][0])**2 + (y - sys_map[s][1])**2 + (z - sys_map[s][2])**2)
                for s in seeds
            )
            if min_d > best_dist:
                best_dist = min_d
                best_id = sid
        seeds.append(best_id)

    # Balanced BFS: expand ONE system at a time, always from the smallest region
    assignment = {}  # system_id -> region_index
    region_sizes = [0] * NUM_REGIONS
    # Use lists as queues (deques would be better but fine for 2500)
    queues = [list() for _ in range(NUM_REGIONS)]
    for i, s in enumerate(seeds):
        assignment[s] = i
        region_sizes[i] = 1
        for nb in adjacency.get(s, set()):
            if nb not in assignment:
                queues[i].append(nb)

    import heapq
    # Priority queue: (size, region_index)
    heap = [(1, i) for i in range(NUM_REGIONS)]
    heapq.heapify(heap)

    while len(assignment) < total and heap:
        size, i = heapq.heappop(heap)
        # Skip stale entries
        if size != region_sizes[i]:
            if queues[i]:
                heapq.heappush(heap, (region_sizes[i], i))
            continue
        # Try to claim one unclaimed neighbor
        claimed = False
        while queues[i] and not claimed:
            candidate = queues[i].pop(0)
            if candidate in assignment:
                continue
            assignment[candidate] = i
            region_sizes[i] += 1
            claimed = True
            # Add candidate's unassigned neighbors to this region's queue
            for nb in adjacency.get(candidate, set()):
                if nb not in assignment:
                    queues[i].append(nb)
        if queues[i]:
            heapq.heappush(heap, (region_sizes[i], i))

    # Assign disconnected systems to nearest seed by Euclidean distance
    for sid, x, y, z in systems:
        if sid not in assignment:
            best_r = 0
            best_d = float('inf')
            for i, s in enumerate(seeds):
                sx, sy, sz = sys_map[s]
                d = math.sqrt((x - sx)**2 + (y - sy)**2 + (z - sz)**2)
                if d < best_d:
                    best_d = d
                    best_r = i
            assignment[sid] = best_r
            region_sizes[best_r] += 1

    # Write to DB
    for sid, region_idx in assignment.items():
        conn.execute('UPDATE systems SET region=? WHERE id=?', (REGION_NAMES[region_idx], sid))
    conn.commit()

    # Report
    print(f"\nAssigned {NUM_REGIONS} regions:")
    for i, name in enumerate(REGION_NAMES):
        print(f"  {name}: {region_sizes[i]} systems")
    print(f"\n  Min: {min(region_sizes)}, Max: {max(region_sizes)}, Avg: {sum(region_sizes)/len(region_sizes):.0f}")

    conn.close()


if __name__ == '__main__':
    assign_regions()
