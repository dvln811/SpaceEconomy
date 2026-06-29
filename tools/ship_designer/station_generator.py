"""Station Generator v2: spine-first architecture, higher component counts.

Builds stations as a backbone (main spine) with modules branching off,
secondary hubs, and layered construction. Much more complex output.

Component targets:
  mining_colony/refinery: 40-60
  component_works/factory: 50-70
  trade_hub/military_base: 80-120
  shipyard: 120-180
"""
import random
import math
from station_components import (gen_hub, gen_ring, gen_corridor, gen_dock, gen_solar,
                                 gen_antenna, gen_habitat, gen_industrial, gen_defense)


STATION_FACTION_STYLES = {
    'terran': {
        'description': 'Ordered, symmetrical, large hub cores with uniform arms',
        'hub_pref': ['cylinder', 'sphere', 'octagonal'],
        'corridor_pref': ['straight', 'spine'],
        'symmetry': 4,
        'scale': 1.2,
    },
    'merchants': {
        'description': 'Sprawling, dock-heavy, modular and expandable',
        'hub_pref': ['modular', 'cylinder', 'blocky'],
        'corridor_pref': ['truss', 'tube_lattice'],
        'symmetry': 3,
        'scale': 1.0,
    },
    'science': {
        'description': 'Elegant, ring-focused, antenna arrays, minimal bulk',
        'hub_pref': ['sphere', 'octagonal'],
        'corridor_pref': ['straight', 'spine'],
        'symmetry': 6,
        'scale': 0.9,
    },
    'iron_compact': {
        'description': 'Heavy, industrial, fortress-like with defense turrets',
        'hub_pref': ['octagonal', 'blocky', 'cylinder'],
        'corridor_pref': ['truss', 'tube_lattice'],
        'symmetry': 4,
        'scale': 1.3,
    },
    'frontier': {
        'description': 'Scrappy, asymmetric, practical, cobbled together',
        'hub_pref': ['modular', 'sphere', 'blocky'],
        'corridor_pref': ['truss', 'straight'],
        'symmetry': 2,
        'scale': 0.85,
    },
}

STATION_RECIPES = {
    'mining_colony': {'complexity': (40, 60), 'rings': 0, 'sections': 2, 'docks': 1, 'industrial': 2, 'defense': 0, 'ind_style': 'ore_processor'},
    'refinery': {'complexity': (45, 65), 'rings': 0, 'sections': 3, 'docks': 2, 'industrial': 3, 'defense': 0, 'ind_style': 'refinery'},
    'component_works': {'complexity': (50, 70), 'rings': 0, 'sections': 3, 'docks': 2, 'industrial': 2, 'defense': 1, 'ind_style': 'factory'},
    'factory': {'complexity': (55, 75), 'rings': 0, 'sections': 4, 'docks': 3, 'industrial': 3, 'defense': 1, 'ind_style': 'factory'},
    'trade_hub': {'complexity': (80, 120), 'rings': 1, 'sections': 4, 'docks': 4, 'industrial': 1, 'defense': 2, 'ind_style': 'tank_farm'},
    'military_base': {'complexity': (80, 120), 'rings': 1, 'sections': 4, 'docks': 3, 'industrial': 1, 'defense': 4, 'ind_style': 'tank_farm'},
    'shipyard': {'complexity': (120, 180), 'rings': 2, 'sections': 6, 'docks': 5, 'industrial': 3, 'defense': 3, 'ind_style': 'factory'},
}


def _offset_parts(parts, dx=0, dy=0, dz=0):
    """Offset all parts by dx/dy/dz."""
    for p in parts:
        p['pos'] = [p['pos'][0]+dx, p['pos'][1]+dy, p['pos'][2]+dz]
    return parts


def _rotate_parts_y(parts, angle):
    """Rotate all parts around Y axis by angle radians."""
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    for p in parts:
        x, y, z = p['pos']
        p['pos'] = [round(x*cos_a - z*sin_a, 4), y, round(x*sin_a + z*cos_a, 4)]
        if p.get('rot'):
            p['rot'] = [p['rot'][0], p['rot'][1] + angle, p['rot'][2]]
    return parts


def generate_station(station_type='trade_hub', faction='terran', seed=None):
    if seed is not None:
        random.seed(seed)

    style = STATION_FACTION_STYLES.get(faction, STATION_FACTION_STYLES['terran'])
    recipe = STATION_RECIPES.get(station_type, STATION_RECIPES['trade_hub'])
    sc = style['scale']
    sym = style['symmetry']
    components = []

    # ── 1. CENTRAL HUB ──
    hub_style = random.choice(style['hub_pref'])
    hub = gen_hub(style=hub_style, size=1.0*sc)
    components.extend(hub['parts'])

    # ── 2. MAIN SPINE (backbone corridor extending from hub) ──
    sections = recipe['sections']
    corridor_style = random.choice(style['corridor_pref'])
    section_positions = []  # track where each section ends up

    for section_idx in range(sections):
        angle = (2 * math.pi * section_idx) / min(sections, sym)
        dist = 0.5 * sc + section_idx * 0.1 * sc

        # Corridor
        corr = gen_corridor(style=corridor_style, size=0.8*sc)
        corr_length = corr.pop('_length', 0.6*sc)
        corr_parts = _rotate_parts_y(corr['parts'], angle)
        _offset_parts(corr_parts, math.cos(angle)*dist, 0, math.sin(angle)*dist)
        components.extend(corr_parts)

        # Secondary hub at end of corridor
        end_dist = dist + corr_length * 0.5
        end_x = math.cos(angle) * end_dist
        end_z = math.sin(angle) * end_dist
        section_positions.append((end_x, 0, end_z, angle))

        sec_hub_style = random.choice(style['hub_pref'])
        sec_hub = gen_hub(style=sec_hub_style, size=0.6*sc)
        _offset_parts(sec_hub['parts'], end_x, 0, end_z)
        components.extend(sec_hub['parts'])

    # ── 3. RINGS ──
    for r in range(recipe['rings']):
        ring_style = random.choice(['single', 'double', 'wide'])
        ring = gen_ring(style=ring_style, size=(1.2 + r*0.3)*sc)
        y_off = (r - recipe['rings']/2) * 0.15 * sc
        _offset_parts(ring['parts'], 0, y_off, 0)
        components.extend(ring['parts'])

    # ── 4. DOCKS (placed at section ends) ──
    dock_styles = ['bay', 'ring_port', 'hangar', 'multi_pad']
    for i in range(min(recipe['docks'], len(section_positions))):
        sx, sy, sz, sa = section_positions[i % len(section_positions)]
        dock = gen_dock(style=random.choice(dock_styles), size=0.7*sc)
        dock_parts = _rotate_parts_y(dock['parts'], sa)
        _offset_parts(dock_parts, sx + math.cos(sa)*0.4*sc, sy, sz + math.sin(sa)*0.4*sc)
        components.extend(dock_parts)

    # ── 5. INDUSTRIAL MODULES ──
    ind_styles = ['tank_farm', 'refinery', 'factory', 'ore_processor']
    main_ind = recipe['ind_style']
    for i in range(recipe['industrial']):
        ist = main_ind if i == 0 else random.choice(ind_styles)
        ind = gen_industrial(style=ist, size=0.7*sc)
        if i < len(section_positions):
            sx, sy, sz, sa = section_positions[i % len(section_positions)]
            _offset_parts(ind['parts'], sx, -0.3*sc, sz)
        else:
            angle = random.uniform(0, 2*math.pi)
            _offset_parts(ind['parts'], math.cos(angle)*0.6*sc, -0.25*sc, math.sin(angle)*0.6*sc)
        components.extend(ind['parts'])

    # ── 6. SOLAR / RADIATORS (top and bottom) ──
    solar_style = random.choice(['panel', 'array', 'radiator'])
    for y_mult in [1.0, -1.0]:
        for i in range(random.randint(1, 3)):
            solar = gen_solar(style=solar_style, size=0.6*sc)
            x_off = (i - 1) * 0.4 * sc
            _offset_parts(solar['parts'], x_off, 0.5*sc*y_mult, 0)
            components.extend(solar['parts'])

    # ── 7. DEFENSE ──
    defense_styles = ['turret', 'missile_pod', 'point_defense']
    for i in range(recipe['defense']):
        d = gen_defense(style=random.choice(defense_styles), size=0.5*sc)
        angle = (2*math.pi*i) / max(recipe['defense'], 1) + random.uniform(-0.3, 0.3)
        r_dist = random.uniform(0.3, 0.6) * sc
        _offset_parts(d['parts'], math.cos(angle)*r_dist, random.uniform(0.15, 0.4)*sc, math.sin(angle)*r_dist)
        components.extend(d['parts'])

    # ── 8. ANTENNA (top) ──
    ant_style = random.choice(['dish', 'mast', 'phased_array'])
    ant = gen_antenna(style=ant_style, size=0.5*sc)
    _offset_parts(ant['parts'], 0, 0.65*sc, 0)
    components.extend(ant['parts'])

    # ── 9. HABITATS (for large stations) ──
    if recipe['complexity'][0] >= 80:
        hab_styles = ['dome', 'cylinder', 'pod_cluster']
        for i in range(random.randint(1, 3)):
            hab = gen_habitat(style=random.choice(hab_styles), size=0.6*sc)
            if i < len(section_positions):
                sx, sy, sz, sa = section_positions[i]
                _offset_parts(hab['parts'], sx, 0.25*sc, sz)
            else:
                angle = random.uniform(0, 2*math.pi)
                _offset_parts(hab['parts'], math.cos(angle)*0.5*sc, 0.2*sc, math.sin(angle)*0.5*sc)
            components.extend(hab['parts'])

    return {
        'components': components,
        'meta': {
            'station_type': station_type,
            'faction': faction,
            'seed': seed,
            'component_count': len(components),
        }
    }


STATION_TYPES = list(STATION_RECIPES.keys())
