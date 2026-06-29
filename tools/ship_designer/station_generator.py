"""Station Generator: assembles station components into full stations by type and faction.

Station types match DB: mining_colony, refinery, component_works, factory, trade_hub, military_base, shipyard
Faction styles influence material choices, symmetry, and component selection.
"""
import random
import math
from station_components import (gen_hub, gen_ring, gen_arm, gen_dock, gen_solar,
                                 gen_antenna, gen_habitat, gen_industrial, gen_defense)


# ─── FACTION STYLES ────────────────────────────────────────────────────────

STATION_FACTION_STYLES = {
    'terran': {
        'description': 'Ordered, symmetrical, large hub cores with uniform arms',
        'hub_pref': ['cylinder', 'sphere'],
        'ring_pref': ['single', 'double'],
        'arm_pref': ['straight', 'truss'],
        'symmetry': 4,
        'scale_mult': 1.2,
    },
    'merchants': {
        'description': 'Sprawling, dock-heavy, modular and expandable',
        'hub_pref': ['modular', 'cylinder'],
        'ring_pref': ['wide'],
        'arm_pref': ['lattice', 'telescoping'],
        'symmetry': 3,
        'scale_mult': 1.0,
    },
    'science': {
        'description': 'Elegant, ring-focused, antenna arrays, minimal bulk',
        'hub_pref': ['sphere', 'octagonal'],
        'ring_pref': ['single', 'tilted'],
        'arm_pref': ['straight'],
        'symmetry': 6,
        'scale_mult': 0.9,
    },
    'iron_compact': {
        'description': 'Heavy, industrial, fortress-like with defense turrets',
        'hub_pref': ['octagonal', 'cylinder'],
        'ring_pref': ['double', 'wide'],
        'arm_pref': ['truss', 'lattice'],
        'symmetry': 4,
        'scale_mult': 1.3,
    },
    'frontier': {
        'description': 'Scrappy, asymmetric, practical, cobbled together',
        'hub_pref': ['modular', 'sphere'],
        'ring_pref': ['single'],
        'arm_pref': ['telescoping', 'straight'],
        'symmetry': 2,
        'scale_mult': 0.8,
    },
}

# ─── STATION TYPE RECIPES ──────────────────────────────────────────────────

# Each recipe defines what components a station type uses
STATION_RECIPES = {
    'mining_colony': {
        'hub': True, 'ring': False, 'arms': (2, 4), 'docks': (1, 2),
        'solar': True, 'industrial': True, 'defense': False,
        'industrial_style': 'refinery',
    },
    'refinery': {
        'hub': True, 'ring': False, 'arms': (2, 4), 'docks': (1, 2),
        'solar': True, 'industrial': True, 'defense': False,
        'industrial_style': 'refinery',
    },
    'component_works': {
        'hub': True, 'ring': False, 'arms': (2, 3), 'docks': (1, 2),
        'solar': True, 'industrial': True, 'defense': False,
        'industrial_style': 'factory',
    },
    'factory': {
        'hub': True, 'ring': False, 'arms': (3, 5), 'docks': (2, 3),
        'solar': True, 'industrial': True, 'defense': False,
        'industrial_style': 'factory',
    },
    'trade_hub': {
        'hub': True, 'ring': True, 'arms': (4, 6), 'docks': (3, 5),
        'solar': True, 'industrial': False, 'defense': True,
        'industrial_style': None,
    },
    'military_base': {
        'hub': True, 'ring': True, 'arms': (4, 6), 'docks': (2, 3),
        'solar': True, 'industrial': False, 'defense': True,
        'industrial_style': None,
    },
    'shipyard': {
        'hub': True, 'ring': True, 'arms': (4, 8), 'docks': (4, 6),
        'solar': True, 'industrial': True, 'defense': True,
        'industrial_style': 'factory',
    },
}


def generate_station(station_type='trade_hub', faction='terran', seed=None):
    """Generate a complete station from type + faction.
    
    Returns: {"components": [...], "meta": {...}}
    """
    if seed is not None:
        random.seed(seed)

    style = STATION_FACTION_STYLES.get(faction, STATION_FACTION_STYLES['terran'])
    recipe = STATION_RECIPES.get(station_type, STATION_RECIPES['trade_hub'])
    sm = style['scale_mult']
    sym = style['symmetry']
    components = []

    # Hub (center)
    hub_style = random.choice(style['hub_pref'])
    hub = gen_hub(style=hub_style, size=1.2 * sm)
    for p in hub['parts']:
        components.append(p)

    # Ring (if applicable)
    if recipe['ring']:
        ring_style = random.choice(style['ring_pref'])
        ring = gen_ring(style=ring_style, size=1.5 * sm)
        for p in ring['parts']:
            components.append(p)

    # Arms (radial, using symmetry)
    arm_count = random.randint(*recipe['arms'])
    arm_count = min(arm_count, sym * 2)  # cap by symmetry
    arm_style = random.choice(style['arm_pref'])
    for i in range(arm_count):
        angle = (2 * math.pi * i) / arm_count
        arm = gen_arm(style=arm_style, size=0.8 * sm)
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        for p in arm['parts']:
            ox, oy, oz = p['pos']
            # Rotate arm outward from center
            nx = cos_a * ox - sin_a * oz + cos_a * 0.4 * sm
            nz = sin_a * ox + cos_a * oz + sin_a * 0.4 * sm
            p['pos'] = [round(nx, 4), oy, round(nz, 4)]
            ry = p.get('rot', [0, 0, 0])[1] if p.get('rot') else 0
            p['rot'] = [p.get('rot', [0, 0, 0])[0], ry + angle, p.get('rot', [0, 0, 0])[2]]
            components.append(p)

    # Docks (at arm tips)
    dock_count = random.randint(*recipe['docks'])
    dock_style = random.choice(['bay', 'ring_port', 'hangar'])
    for i in range(min(dock_count, arm_count)):
        angle = (2 * math.pi * i) / arm_count
        dock = gen_dock(style=dock_style, size=0.6 * sm)
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        for p in dock['parts']:
            ox, oy, oz = p['pos']
            nx = cos_a * ox + cos_a * 0.85 * sm
            nz = sin_a * ox + sin_a * 0.85 * sm
            p['pos'] = [round(nx, 4), oy, round(nz, 4)]
            components.append(p)

    # Solar panels (top/bottom)
    if recipe['solar']:
        solar_style = random.choice(['panel', 'array', 'radiator'])
        for y_mult in [1, -1]:
            solar = gen_solar(style=solar_style, size=0.7 * sm)
            for p in solar['parts']:
                p['pos'][1] += 0.5 * sm * y_mult
                components.append(p)

    # Industrial modules
    if recipe['industrial']:
        ind_style = recipe['industrial_style'] or 'tank'
        ind = gen_industrial(style=ind_style, size=0.8 * sm)
        for p in ind['parts']:
            p['pos'][1] -= 0.35 * sm
            components.append(p)

    # Defense turrets
    if recipe['defense']:
        turret_count = random.randint(2, 4)
        for i in range(turret_count):
            angle = (2 * math.pi * i) / turret_count + 0.3
            d = gen_defense(style='turret', size=0.5 * sm)
            cos_a, sin_a = math.cos(angle), math.sin(angle)
            for p in d['parts']:
                ox, oy, oz = p['pos']
                p['pos'] = [round(cos_a * 0.35 * sm + ox, 4), oy + 0.3 * sm, round(sin_a * 0.35 * sm + oz, 4)]
                components.append(p)

    # Antenna (top)
    ant = gen_antenna(style=random.choice(['dish', 'mast']), size=0.5 * sm)
    for p in ant['parts']:
        p['pos'][1] += 0.6 * sm
        components.append(p)

    return {
        'components': components,
        'meta': {
            'station_type': station_type,
            'faction': faction,
            'seed': seed,
            'component_count': len(components),
        }
    }


# Station type list for UI
STATION_TYPES = list(STATION_RECIPES.keys())
