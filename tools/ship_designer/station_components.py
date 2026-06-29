"""Station Component Library: ring, arm, hub, dock, solar, antenna, habitat, industrial modules.

Each generator returns {"parts": [...]} where each part has:
  type, pos, rot, params, material
"""
import random
import math


STATION_CATEGORIES = {
    'hub': 'Central core modules - spherical or cylindrical command centers',
    'ring': 'Rotating habitat rings providing artificial gravity',
    'arm': 'Structural spines and connector arms',
    'dock': 'Docking bays and landing platforms',
    'solar': 'Solar panel arrays and radiators',
    'antenna': 'Communication dishes and sensor arrays',
    'habitat': 'Pressurized living quarters and biodomes',
    'industrial': 'Refinery tanks, factory bays, ore processing',
    'defense': 'Weapon platforms and shield generators',
}


def _seed(seed):
    if seed is not None:
        random.seed(seed)


# ─── HUB (central core) ────────────────────────────────────────────────────

def gen_hub(style='sphere', size=1.0, seed=None):
    _seed(seed)
    parts = []
    s = size
    if style == 'sphere':
        parts.append({'type': 'sphere', 'pos': [0, 0, 0], 'rot': [0, 0, 0],
                      'params': {'radius': 0.3 * s, 'half': False}, 'material': 'hull'})
        # Connector flanges at top/bottom
        for y in [-0.32 * s, 0.32 * s]:
            parts.append({'type': 'cylinder', 'pos': [0, y, 0], 'rot': [0, 0, 0],
                          'params': {'r_top': 0.12 * s, 'r_bot': 0.12 * s, 'length': 0.04 * s}, 'material': 'accent'})
    elif style == 'cylinder':
        parts.append({'type': 'cylinder', 'pos': [0, 0, 0], 'rot': [0, 0, 0],
                      'params': {'r_top': 0.2 * s, 'r_bot': 0.2 * s, 'length': 0.6 * s}, 'material': 'hull'})
        for y in [-0.32 * s, 0.32 * s]:
            parts.append({'type': 'cylinder', 'pos': [0, y, 0], 'rot': [0, 0, 0],
                          'params': {'r_top': 0.25 * s, 'r_bot': 0.25 * s, 'length': 0.03 * s}, 'material': 'accent'})
    elif style == 'octagonal':
        parts.append({'type': 'cylinder', 'pos': [0, 0, 0], 'rot': [0, 0, 0],
                      'params': {'r_top': 0.25 * s, 'r_bot': 0.25 * s, 'length': 0.4 * s}, 'material': 'hull'})
        parts.append({'type': 'sphere', 'pos': [0, 0.22 * s, 0], 'rot': [0, 0, 0],
                      'params': {'radius': 0.15 * s, 'half': True}, 'material': 'accent'})
    elif style == 'modular':
        for i in range(3):
            y = (i - 1) * 0.22 * s
            r = 0.18 * s if i == 1 else 0.14 * s
            parts.append({'type': 'cylinder', 'pos': [0, y, 0], 'rot': [0, 0, 0],
                          'params': {'r_top': r, 'r_bot': r, 'length': 0.18 * s}, 'material': 'hull'})
        # Connectors between segments
        for y in [-0.11 * s, 0.11 * s]:
            parts.append({'type': 'cylinder', 'pos': [0, y, 0], 'rot': [0, 0, 0],
                          'params': {'r_top': 0.08 * s, 'r_bot': 0.08 * s, 'length': 0.04 * s}, 'material': 'accent'})
    return {'parts': parts}


# ─── RING (habitat ring) ───────────────────────────────────────────────────

def gen_ring(style='single', size=1.0, seed=None):
    _seed(seed)
    parts = []
    s = size
    if style == 'single':
        parts.append({'type': 'torus', 'pos': [0, 0, 0], 'rot': [math.pi / 2, 0, 0],
                      'params': {'radius': 0.5 * s, 'tube': 0.06 * s}, 'material': 'hull'})
        # Spokes connecting to center
        for angle in range(0, 360, 90):
            rad = math.radians(angle)
            x = math.cos(rad) * 0.25 * s
            z = math.sin(rad) * 0.25 * s
            parts.append({'type': 'cylinder', 'pos': [x, 0, z], 'rot': [0, rad, math.pi / 2],
                          'params': {'r_top': 0.015 * s, 'r_bot': 0.015 * s, 'length': 0.45 * s}, 'material': 'accent'})
    elif style == 'double':
        for offset in [-0.08 * s, 0.08 * s]:
            parts.append({'type': 'torus', 'pos': [0, offset, 0], 'rot': [math.pi / 2, 0, 0],
                          'params': {'radius': 0.45 * s, 'tube': 0.05 * s}, 'material': 'hull'})
        for angle in range(0, 360, 60):
            rad = math.radians(angle)
            x = math.cos(rad) * 0.22 * s
            z = math.sin(rad) * 0.22 * s
            parts.append({'type': 'cylinder', 'pos': [x, 0, z], 'rot': [0, rad, math.pi / 2],
                          'params': {'r_top': 0.012 * s, 'r_bot': 0.012 * s, 'length': 0.4 * s}, 'material': 'accent'})
    elif style == 'wide':
        parts.append({'type': 'torus', 'pos': [0, 0, 0], 'rot': [math.pi / 2, 0, 0],
                      'params': {'radius': 0.6 * s, 'tube': 0.1 * s}, 'material': 'hull'})
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            x = math.cos(rad) * 0.3 * s
            z = math.sin(rad) * 0.3 * s
            parts.append({'type': 'cylinder', 'pos': [x, 0, z], 'rot': [0, rad, math.pi / 2],
                          'params': {'r_top': 0.02 * s, 'r_bot': 0.02 * s, 'length': 0.55 * s}, 'material': 'accent'})
    elif style == 'tilted':
        parts.append({'type': 'torus', 'pos': [0, 0, 0], 'rot': [math.pi / 2.5, 0.2, 0],
                      'params': {'radius': 0.5 * s, 'tube': 0.055 * s}, 'material': 'hull'})
    return {'parts': parts}


# ─── ARM (structural spine) ────────────────────────────────────────────────

def gen_arm(style='straight', size=1.0, seed=None):
    _seed(seed)
    parts = []
    s = size
    if style == 'straight':
        parts.append({'type': 'spine', 'pos': [0, 0, 0], 'rot': [0, 0, 0],
                      'params': {'length': 0.8 * s, 'radius': 0.03 * s, 'flange_r': 0.06 * s}, 'material': 'hull'})
    elif style == 'lattice':
        for z_off in [-0.03 * s, 0.03 * s]:
            parts.append({'type': 'spine', 'pos': [0, 0, z_off], 'rot': [0, 0, 0],
                          'params': {'length': 0.7 * s, 'radius': 0.02 * s, 'flange_r': 0.04 * s}, 'material': 'hull'})
        # Cross braces
        for x in [-0.2 * s, 0, 0.2 * s]:
            parts.append({'type': 'box', 'pos': [x, 0, 0], 'rot': [0, 0, 0],
                          'params': {'x': 0.01 * s, 'y': 0.01 * s, 'z': 0.08 * s}, 'material': 'accent'})
    elif style == 'truss':
        parts.append({'type': 'box', 'pos': [0, 0, 0], 'rot': [0, 0, 0],
                      'params': {'x': 0.9 * s, 'y': 0.04 * s, 'z': 0.04 * s}, 'material': 'hull'})
        for i in range(5):
            x = (i - 2) * 0.2 * s
            parts.append({'type': 'box', 'pos': [x, 0, 0], 'rot': [0, 0, math.pi / 4],
                          'params': {'x': 0.01 * s, 'y': 0.06 * s, 'z': 0.01 * s}, 'material': 'accent'})
    elif style == 'telescoping':
        for i in range(3):
            r = (0.04 - i * 0.01) * s
            x = (i - 1) * 0.25 * s
            parts.append({'type': 'cylinder', 'pos': [x, 0, 0], 'rot': [0, 0, math.pi / 2],
                          'params': {'r_top': r, 'r_bot': r, 'length': 0.28 * s}, 'material': 'hull'})
    return {'parts': parts}


# ─── DOCK (docking bay) ────────────────────────────────────────────────────

def gen_dock(style='bay', size=1.0, seed=None):
    _seed(seed)
    parts = []
    s = size
    if style == 'bay':
        parts.append({'type': 'pod', 'pos': [0, 0, 0], 'rot': [0, 0, 0],
                      'params': {'length': 0.4 * s, 'height': 0.15 * s, 'width': 0.25 * s}, 'material': 'hull'})
        # Docking clamps
        for z in [-0.14 * s, 0.14 * s]:
            parts.append({'type': 'box', 'pos': [0.2 * s, 0, z], 'rot': [0, 0, 0],
                          'params': {'x': 0.03 * s, 'y': 0.08 * s, 'z': 0.02 * s}, 'material': 'accent'})
    elif style == 'ring_port':
        parts.append({'type': 'torus', 'pos': [0, 0, 0], 'rot': [0, 0, 0],
                      'params': {'radius': 0.15 * s, 'tube': 0.03 * s}, 'material': 'hull'})
        parts.append({'type': 'cylinder', 'pos': [0, 0, 0], 'rot': [0, 0, 0],
                      'params': {'r_top': 0.12 * s, 'r_bot': 0.12 * s, 'length': 0.06 * s}, 'material': 'accent'})
    elif style == 'hangar':
        parts.append({'type': 'pod', 'pos': [0, 0, 0], 'rot': [0, 0, 0],
                      'params': {'length': 0.6 * s, 'height': 0.2 * s, 'width': 0.35 * s}, 'material': 'hull'})
        # Open front
        parts.append({'type': 'box', 'pos': [0.31 * s, 0, 0], 'rot': [0, 0, 0],
                      'params': {'x': 0.02 * s, 'y': 0.18 * s, 'z': 0.33 * s}, 'material': 'accent'})
    return {'parts': parts}


# ─── SOLAR (panel arrays) ─────────────────────────────────────────────────

def gen_solar(style='panel', size=1.0, seed=None):
    _seed(seed)
    parts = []
    s = size
    if style == 'panel':
        # Two large flat panels
        for z in [-0.2 * s, 0.2 * s]:
            parts.append({'type': 'box', 'pos': [0, 0, z], 'rot': [0, 0, 0],
                          'params': {'x': 0.5 * s, 'y': 0.005 * s, 'z': 0.18 * s}, 'material': 'shield'})
        # Connector arm
        parts.append({'type': 'cylinder', 'pos': [0, 0, 0], 'rot': [math.pi / 2, 0, 0],
                      'params': {'r_top': 0.015 * s, 'r_bot': 0.015 * s, 'length': 0.4 * s}, 'material': 'accent'})
    elif style == 'array':
        for i in range(4):
            x = (i - 1.5) * 0.15 * s
            parts.append({'type': 'box', 'pos': [x, 0, 0.15 * s], 'rot': [0, 0, 0],
                          'params': {'x': 0.12 * s, 'y': 0.003 * s, 'z': 0.25 * s}, 'material': 'shield'})
        parts.append({'type': 'box', 'pos': [0, 0, 0], 'rot': [0, 0, 0],
                      'params': {'x': 0.5 * s, 'y': 0.015 * s, 'z': 0.015 * s}, 'material': 'accent'})
    elif style == 'radiator':
        for i in range(3):
            angle = (i - 1) * 0.4
            parts.append({'type': 'box', 'pos': [0, 0, (i - 1) * 0.12 * s], 'rot': [angle, 0, 0],
                          'params': {'x': 0.4 * s, 'y': 0.003 * s, 'z': 0.1 * s}, 'material': 'engine'})
    return {'parts': parts}


# ─── ANTENNA (dishes and sensors) ──────────────────────────────────────────

def gen_antenna(style='dish', size=1.0, seed=None):
    _seed(seed)
    parts = []
    s = size
    if style == 'dish':
        parts.append({'type': 'sphere', 'pos': [0, 0.05 * s, 0], 'rot': [0, 0, 0],
                      'params': {'radius': 0.2 * s, 'half': True}, 'material': 'hull'})
        parts.append({'type': 'cylinder', 'pos': [0, -0.1 * s, 0], 'rot': [0, 0, 0],
                      'params': {'r_top': 0.015 * s, 'r_bot': 0.02 * s, 'length': 0.2 * s}, 'material': 'accent'})
    elif style == 'array':
        for x in [-0.1 * s, 0, 0.1 * s]:
            for z in [-0.1 * s, 0, 0.1 * s]:
                parts.append({'type': 'cone', 'pos': [x, 0.05 * s, z], 'rot': [0, 0, 0],
                              'params': {'radius': 0.03 * s, 'length': 0.08 * s}, 'material': 'hull'})
        parts.append({'type': 'box', 'pos': [0, 0, 0], 'rot': [0, 0, 0],
                      'params': {'x': 0.25 * s, 'y': 0.015 * s, 'z': 0.25 * s}, 'material': 'accent'})
    elif style == 'mast':
        parts.append({'type': 'cylinder', 'pos': [0, 0.2 * s, 0], 'rot': [0, 0, 0],
                      'params': {'r_top': 0.01 * s, 'r_bot': 0.015 * s, 'length': 0.5 * s}, 'material': 'accent'})
        parts.append({'type': 'sphere', 'pos': [0, 0.45 * s, 0], 'rot': [0, 0, 0],
                      'params': {'radius': 0.04 * s, 'half': False}, 'material': 'hull'})
    return {'parts': parts}


# ─── HABITAT (living quarters) ─────────────────────────────────────────────

def gen_habitat(style='dome', size=1.0, seed=None):
    _seed(seed)
    parts = []
    s = size
    if style == 'dome':
        parts.append({'type': 'sphere', 'pos': [0, 0.1 * s, 0], 'rot': [0, 0, 0],
                      'params': {'radius': 0.25 * s, 'half': True}, 'material': 'hull'})
        parts.append({'type': 'cylinder', 'pos': [0, 0, 0], 'rot': [0, 0, 0],
                      'params': {'r_top': 0.25 * s, 'r_bot': 0.25 * s, 'length': 0.05 * s}, 'material': 'accent'})
    elif style == 'cylinder':
        parts.append({'type': 'cylinder', 'pos': [0, 0, 0], 'rot': [0, 0, math.pi / 2],
                      'params': {'r_top': 0.15 * s, 'r_bot': 0.15 * s, 'length': 0.5 * s}, 'material': 'hull'})
        for x in [-0.26 * s, 0.26 * s]:
            parts.append({'type': 'sphere', 'pos': [x, 0, 0], 'rot': [0, 0, 0],
                          'params': {'radius': 0.15 * s, 'half': True}, 'material': 'accent'})
    elif style == 'pod_cluster':
        for i in range(4):
            angle = math.radians(i * 90)
            x = math.cos(angle) * 0.12 * s
            z = math.sin(angle) * 0.12 * s
            parts.append({'type': 'pod', 'pos': [x, 0, z], 'rot': [0, angle, 0],
                          'params': {'length': 0.25 * s, 'height': 0.1 * s, 'width': 0.1 * s}, 'material': 'hull'})
    return {'parts': parts}


# ─── INDUSTRIAL (refineries, factories) ────────────────────────────────────

def gen_industrial(style='tank', size=1.0, seed=None):
    _seed(seed)
    parts = []
    s = size
    if style == 'tank':
        parts.append({'type': 'cylinder', 'pos': [0, 0, 0], 'rot': [0, 0, 0],
                      'params': {'r_top': 0.12 * s, 'r_bot': 0.12 * s, 'length': 0.4 * s}, 'material': 'cargo'})
        parts.append({'type': 'sphere', 'pos': [0, 0.21 * s, 0], 'rot': [0, 0, 0],
                      'params': {'radius': 0.12 * s, 'half': True}, 'material': 'cargo'})
    elif style == 'refinery':
        for x in [-0.15 * s, 0, 0.15 * s]:
            h = random.uniform(0.3, 0.5) * s
            parts.append({'type': 'cylinder', 'pos': [x, 0, 0], 'rot': [0, 0, 0],
                          'params': {'r_top': 0.08 * s, 'r_bot': 0.1 * s, 'length': h}, 'material': 'cargo'})
        parts.append({'type': 'box', 'pos': [0, -0.2 * s, 0], 'rot': [0, 0, 0],
                      'params': {'x': 0.4 * s, 'y': 0.04 * s, 'z': 0.15 * s}, 'material': 'accent'})
    elif style == 'factory':
        parts.append({'type': 'pod', 'pos': [0, 0, 0], 'rot': [0, 0, 0],
                      'params': {'length': 0.5 * s, 'height': 0.2 * s, 'width': 0.3 * s}, 'material': 'cargo'})
        # Smoke stacks / vents
        for x in [0.15 * s, 0.25 * s]:
            parts.append({'type': 'cylinder', 'pos': [x, 0.12 * s, 0], 'rot': [0, 0, 0],
                          'params': {'r_top': 0.02 * s, 'r_bot': 0.025 * s, 'length': 0.1 * s}, 'material': 'accent'})
    return {'parts': parts}


# ─── DEFENSE (weapon platforms) ────────────────────────────────────────────

def gen_defense(style='turret', size=1.0, seed=None):
    _seed(seed)
    parts = []
    s = size
    if style == 'turret':
        parts.append({'type': 'cylinder', 'pos': [0, 0, 0], 'rot': [0, 0, 0],
                      'params': {'r_top': 0.06 * s, 'r_bot': 0.08 * s, 'length': 0.05 * s}, 'material': 'weapon'})
        parts.append({'type': 'cylinder', 'pos': [0.08 * s, 0.03 * s, 0], 'rot': [0, 0, math.pi / 2],
                      'params': {'r_top': 0.015 * s, 'r_bot': 0.02 * s, 'length': 0.12 * s}, 'material': 'weapon'})
    elif style == 'missile_pod':
        parts.append({'type': 'box', 'pos': [0, 0, 0], 'rot': [0, 0, 0],
                      'params': {'x': 0.15 * s, 'y': 0.1 * s, 'z': 0.1 * s}, 'material': 'weapon'})
        for y in [-0.03 * s, 0.03 * s]:
            for z in [-0.03 * s, 0.03 * s]:
                parts.append({'type': 'cylinder', 'pos': [0.08 * s, y, z], 'rot': [0, 0, math.pi / 2],
                              'params': {'r_top': 0.012 * s, 'r_bot': 0.012 * s, 'length': 0.06 * s}, 'material': 'accent'})
    elif style == 'shield_gen':
        parts.append({'type': 'sphere', 'pos': [0, 0, 0], 'rot': [0, 0, 0],
                      'params': {'radius': 0.1 * s, 'half': False}, 'material': 'shield'})
        parts.append({'type': 'torus', 'pos': [0, 0, 0], 'rot': [math.pi / 2, 0, 0],
                      'params': {'radius': 0.14 * s, 'tube': 0.015 * s}, 'material': 'accent'})
    return {'parts': parts}


# ─── REGISTRY ──────────────────────────────────────────────────────────────

STATION_GENERATORS = {
    'hub': (gen_hub, ['sphere', 'cylinder', 'octagonal', 'modular']),
    'ring': (gen_ring, ['single', 'double', 'wide', 'tilted']),
    'arm': (gen_arm, ['straight', 'lattice', 'truss', 'telescoping']),
    'dock': (gen_dock, ['bay', 'ring_port', 'hangar']),
    'solar': (gen_solar, ['panel', 'array', 'radiator']),
    'antenna': (gen_antenna, ['dish', 'array', 'mast']),
    'habitat': (gen_habitat, ['dome', 'cylinder', 'pod_cluster']),
    'industrial': (gen_industrial, ['tank', 'refinery', 'factory']),
    'defense': (gen_defense, ['turret', 'missile_pod', 'shield_gen']),
}
