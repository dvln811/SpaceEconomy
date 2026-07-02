"""Jump Gate Generator v4: Multiple torus rings + outward greebles only.

Rules:
- NO geometry inside the gate hole (ships fly through)
- Multiple torus rings (3-5) parallel and aligned
- Greebles ONLY on the outside of the outermost ring, radiating outward
- Greeble orientation achieved by POSITION only (using spheres and boxes
  that don't need rotation, plus explicitly positioned spine segments)
"""
import random
import math
import json
import os


GATE_STYLES = {
    'terran': {
        'ring_count': (3, 5),
        'greeble_count': (10, 16),
        'greeble_length': (0.12, 0.30),
        'ring_tube': (0.04, 0.07),
        'scale_range': (0.9, 1.2),
        'greeble_style': 'angular',
    },
    'merchants': {
        'ring_count': (3, 4),
        'greeble_count': (8, 12),
        'greeble_length': (0.15, 0.40),
        'ring_tube': (0.05, 0.09),
        'scale_range': (1.0, 1.3),
        'greeble_style': 'chunky',
    },
    'science': {
        'ring_count': (4, 5),
        'greeble_count': (14, 22),
        'greeble_length': (0.08, 0.20),
        'ring_tube': (0.03, 0.05),
        'scale_range': (0.85, 1.1),
        'greeble_style': 'needle',
    },
    'iron_compact': {
        'ring_count': (3, 4),
        'greeble_count': (10, 14),
        'greeble_length': (0.18, 0.35),
        'ring_tube': (0.06, 0.10),
        'scale_range': (1.1, 1.4),
        'greeble_style': 'heavy',
    },
    'frontier': {
        'ring_count': (2, 3),
        'greeble_count': (6, 10),
        'greeble_length': (0.12, 0.25),
        'ring_tube': (0.04, 0.07),
        'scale_range': (0.75, 1.0),
        'greeble_style': 'mixed',
    },
}


def generate_gate(faction='terran', seed=None, connects_to=''):
    """Generate a jump gate. NO interior geometry. Rings + outward greebles only."""
    if seed is not None:
        random.seed(seed)

    style = GATE_STYLES.get(faction, GATE_STYLES['terran'])
    sc = random.uniform(*style['scale_range'])
    components = []

    ring_radius = 0.8 * sc
    ring_tube = random.uniform(*style['ring_tube']) * sc
    n_rings = random.randint(*style['ring_count'])
    n_greebles = random.randint(*style['greeble_count'])

    # ── 1. TORUS RINGS (parallel, spaced along X axis) ──
    # All rings aligned with hole along X. Spaced evenly.
    ring_spread = ring_tube * random.uniform(4, 8)
    total_width = ring_spread * (n_rings - 1)
    for i in range(n_rings):
        x_pos = -total_width / 2 + i * ring_spread
        # Vary radius slightly for visual interest
        r_var = ring_radius * random.uniform(0.95, 1.0) if i != n_rings // 2 else ring_radius
        t_var = ring_tube * (1.0 if i == n_rings // 2 else random.uniform(0.5, 0.8))
        components.append({
            'type': 'torus',
            'pos': [round(x_pos, 4), 0, 0],
            'rot': [0, math.pi / 2, 0],
            'params': {'radius': round(r_var, 4), 'tube': round(t_var, 4)},
            'material': 'hull'
        })

    # ── 2. GREEBLES ON THE OUTSIDE (radiate outward from ring surface) ──
    # Placed at positions around the ring, extending radially away from center.
    # Built from chains of spheres and boxes positioned along the radial line.
    for i in range(n_greebles):
        theta = (2 * math.pi * i) / n_greebles
        theta += random.uniform(-0.05, 0.05)

        # Radial direction outward in YZ plane
        out_y = math.cos(theta)
        out_z = math.sin(theta)

        # X position: on one of the rings (random)
        gx = -total_width / 2 + random.randint(0, n_rings - 1) * ring_spread

        # Greeble length
        g_len = random.uniform(*style['greeble_length']) * sc

        greeble_style = style['greeble_style']
        if greeble_style == 'mixed':
            greeble_style = random.choice(['angular', 'chunky', 'needle', 'heavy'])

        # Build greeble as a chain of positioned primitives along the radial line
        # Start at torus surface, extend outward
        start_dist = ring_radius + ring_tube
        end_dist = start_dist + g_len

        if greeble_style == 'angular':
            # Box at midpoint + sphere at tip
            mid_dist = (start_dist + end_dist) / 2
            my = out_y * mid_dist
            mz = out_z * mid_dist
            # Box width perpendicular to radial (along the ring tangent)
            bw = ring_tube * random.uniform(0.8, 1.5)
            bh = g_len * 0.9
            bd = ring_tube * random.uniform(0.5, 1.0)
            # Box aligned with Y being the radial direction - approximate with a tall box
            # Since we can't rotate boxes reliably, use a sphere-chain approach:
            # Place 2-3 spheres along the radial line
            n_segs = random.randint(2, 4)
            for s in range(n_segs):
                t = s / max(1, n_segs - 1)
                d = start_dist + t * g_len
                sy = out_y * d
                sz = out_z * d
                r = ring_tube * random.uniform(0.4, 0.8) * (1.0 - t * 0.3)
                components.append({
                    'type': 'sphere',
                    'pos': [round(gx, 4), round(sy, 4), round(sz, 4)],
                    'rot': [0, 0, 0],
                    'params': {'radius': round(r, 4), 'half': False},
                    'material': 'hull'
                })
            # Box at tip
            tip_y = out_y * end_dist
            tip_z = out_z * end_dist
            bs = ring_tube * random.uniform(0.8, 1.5)
            components.append({
                'type': 'box',
                'pos': [round(gx, 4), round(tip_y, 4), round(tip_z, 4)],
                'rot': [0, 0, 0],
                'params': {'x': bs, 'y': bs * 0.6, 'z': bs * 0.6},
                'material': 'hull'
            })

        elif greeble_style == 'chunky':
            # 2-3 decreasing spheres outward
            n_segs = random.randint(2, 3)
            for s in range(n_segs):
                t = s / max(1, n_segs - 1)
                d = start_dist + t * g_len
                sy = out_y * d
                sz = out_z * d
                r = ring_tube * random.uniform(0.8, 1.4) * (1.0 - t * 0.4)
                components.append({
                    'type': 'sphere',
                    'pos': [round(gx, 4), round(sy, 4), round(sz, 4)],
                    'rot': [0, 0, 0],
                    'params': {'radius': round(r, 4), 'half': False},
                    'material': 'hull'
                })

        elif greeble_style == 'needle':
            # Single thin spike: sphere at base, small sphere at tip
            base_y = out_y * start_dist
            base_z = out_z * start_dist
            components.append({
                'type': 'sphere',
                'pos': [round(gx, 4), round(base_y, 4), round(base_z, 4)],
                'rot': [0, 0, 0],
                'params': {'radius': round(ring_tube * 0.6, 4), 'half': False},
                'material': 'hull'
            })
            # Mid sphere (thinner)
            mid_y = out_y * (start_dist + g_len * 0.5)
            mid_z = out_z * (start_dist + g_len * 0.5)
            components.append({
                'type': 'sphere',
                'pos': [round(gx, 4), round(mid_y, 4), round(mid_z, 4)],
                'rot': [0, 0, 0],
                'params': {'radius': round(ring_tube * 0.3, 4), 'half': False},
                'material': 'hull'
            })
            # Tip
            tip_y = out_y * end_dist
            tip_z = out_z * end_dist
            components.append({
                'type': 'sphere',
                'pos': [round(gx, 4), round(tip_y, 4), round(tip_z, 4)],
                'rot': [0, 0, 0],
                'params': {'radius': round(ring_tube * 0.15, 4), 'half': False},
                'material': 'hull'
            })

        elif greeble_style == 'heavy':
            # Thick chain of spheres + box cap
            n_segs = random.randint(2, 4)
            for s in range(n_segs):
                t = s / max(1, n_segs - 1)
                d = start_dist + t * g_len * 0.7
                sy = out_y * d
                sz = out_z * d
                r = ring_tube * random.uniform(0.7, 1.2)
                components.append({
                    'type': 'sphere',
                    'pos': [round(gx, 4), round(sy, 4), round(sz, 4)],
                    'rot': [0, 0, 0],
                    'params': {'radius': round(r, 4), 'half': False},
                    'material': 'hull'
                })
            # Large box at end
            tip_y = out_y * end_dist
            tip_z = out_z * end_dist
            bs = ring_tube * random.uniform(1.5, 2.5)
            components.append({
                'type': 'box',
                'pos': [round(gx, 4), round(tip_y, 4), round(tip_z, 4)],
                'rot': [0, 0, 0],
                'params': {'x': bs, 'y': bs * 0.7, 'z': bs * 0.7},
                'material': 'hull'
            })

    return {
        'name': f'{faction}/gate',
        'faction': faction,
        'obj_type': 'gate',
        'connects_to': connects_to,
        'components': components,
        'meta': {
            'faction': faction,
            'component_count': len(components),
            'ring_count': n_rings,
            'ring_radius': ring_radius,
        }
    }


def generate_all_gates(output_dir=None):
    """Generate gate designs for all factions (6 variants each)."""
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), 'gate_designs')
    os.makedirs(output_dir, exist_ok=True)

    factions = ['terran', 'merchants', 'science', 'iron_compact', 'frontier']
    for faction in factions:
        designs = []
        for i in range(6):
            gate = generate_gate(faction=faction, seed=i * 7919 + hash(faction) % 1000)
            designs.append(gate)
        path = os.path.join(output_dir, f'gates_{faction}.json')
        with open(path, 'w') as f:
            json.dump(designs, f)
        print(f'  {faction}: {len(designs)} gates ({designs[0]["meta"]["ring_count"]}-{designs[-1]["meta"]["ring_count"]} rings, {designs[0]["meta"]["component_count"]}-{designs[-1]["meta"]["component_count"]} comps)')


if __name__ == '__main__':
    print('Generating gate designs...')
    generate_all_gates()
    print('Done.')
