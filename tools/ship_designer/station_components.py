"""Station Component Library v2: all blue holographic material, more complex assemblies.

Every part uses material='hull' for uniform blue wireframe look.
Components are designed to be chained along spines, not just radial from center.
"""
import random
import math

MAT = 'hull'  # everything is blue holographic


def _seed(seed):
    if seed is not None:
        random.seed(seed)


# ─── HUB (central modules - varied shapes) ─────────────────────────────────

def gen_hub(style='sphere', size=1.0, seed=None):
    _seed(seed)
    s = size
    parts = []
    if style == 'sphere':
        parts.append({'type': 'sphere', 'pos': [0,0,0], 'rot': [0,0,0], 'params': {'radius': 0.3*s, 'half': False}, 'material': MAT})
        for y in [-0.32*s, 0.32*s]:
            parts.append({'type': 'cylinder', 'pos': [0,y,0], 'rot': [0,0,0], 'params': {'r_top': 0.15*s, 'r_bot': 0.15*s, 'length': 0.04*s}, 'material': MAT})
    elif style == 'cylinder':
        parts.append({'type': 'cylinder', 'pos': [0,0,0], 'rot': [0,0,0], 'params': {'r_top': 0.22*s, 'r_bot': 0.22*s, 'length': 0.7*s}, 'material': MAT})
        for y in [-0.37*s, 0.37*s]:
            parts.append({'type': 'cylinder', 'pos': [0,y,0], 'rot': [0,0,0], 'params': {'r_top': 0.28*s, 'r_bot': 0.28*s, 'length': 0.04*s}, 'material': MAT})
        # Internal ring detail
        parts.append({'type': 'torus', 'pos': [0,0,0], 'rot': [math.pi/2,0,0], 'params': {'radius': 0.22*s, 'tube': 0.02*s}, 'material': MAT})
    elif style == 'octagonal':
        parts.append({'type': 'cylinder', 'pos': [0,0,0], 'rot': [0,0,0], 'params': {'r_top': 0.28*s, 'r_bot': 0.28*s, 'length': 0.45*s}, 'material': MAT})
        parts.append({'type': 'cone', 'pos': [0,0.28*s,0], 'rot': [0,0,0], 'params': {'radius': 0.28*s, 'length': 0.15*s}, 'material': MAT})
        parts.append({'type': 'cone', 'pos': [0,-0.28*s,0], 'rot': [math.pi,0,0], 'params': {'radius': 0.28*s, 'length': 0.15*s}, 'material': MAT})
    elif style == 'modular':
        for i in range(4):
            y = (i - 1.5) * 0.2 * s
            r = 0.2*s if i in (1,2) else 0.14*s
            parts.append({'type': 'cylinder', 'pos': [0,y,0], 'rot': [0,0,0], 'params': {'r_top': r, 'r_bot': r, 'length': 0.17*s}, 'material': MAT})
        for y in [-0.2*s, 0, 0.2*s]:
            parts.append({'type': 'cylinder', 'pos': [0,y,0], 'rot': [0,0,0], 'params': {'r_top': 0.1*s, 'r_bot': 0.1*s, 'length': 0.03*s}, 'material': MAT})
    elif style == 'blocky':
        parts.append({'type': 'box', 'pos': [0,0,0], 'rot': [0,0,0], 'params': {'x': 0.4*s, 'y': 0.4*s, 'z': 0.4*s}, 'material': MAT})
        for face in [[0.22*s,0,0],[-0.22*s,0,0],[0,0.22*s,0],[0,-0.22*s,0],[0,0,0.22*s],[0,0,-0.22*s]]:
            parts.append({'type': 'cylinder', 'pos': face, 'rot': [0,0,0], 'params': {'r_top': 0.08*s, 'r_bot': 0.08*s, 'length': 0.03*s}, 'material': MAT})
    return {'parts': parts}


# ─── RING (habitat rings - more detailed) ──────────────────────────────────

def gen_ring(style='single', size=1.0, seed=None):
    _seed(seed)
    s = size
    parts = []
    if style == 'single':
        parts.append({'type': 'torus', 'pos': [0,0,0], 'rot': [math.pi/2,0,0], 'params': {'radius': 0.55*s, 'tube': 0.07*s}, 'material': MAT})
        for angle in range(0, 360, 60):
            rad = math.radians(angle)
            x, z = math.cos(rad)*0.27*s, math.sin(rad)*0.27*s
            parts.append({'type': 'box', 'pos': [x,0,z], 'rot': [0,rad,math.pi/2], 'params': {'x': 0.5*s, 'y': 0.015*s, 'z': 0.015*s}, 'material': MAT})
    elif style == 'double':
        for off in [-0.1*s, 0.1*s]:
            parts.append({'type': 'torus', 'pos': [0,off,0], 'rot': [math.pi/2,0,0], 'params': {'radius': 0.5*s, 'tube': 0.05*s}, 'material': MAT})
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            x, z = math.cos(rad)*0.25*s, math.sin(rad)*0.25*s
            parts.append({'type': 'box', 'pos': [x,0,z], 'rot': [0,rad,math.pi/2], 'params': {'x': 0.45*s, 'y': 0.012*s, 'z': 0.012*s}, 'material': MAT})
        # Connecting struts between rings
        for angle in range(0, 360, 90):
            rad = math.radians(angle)
            x, z = math.cos(rad)*0.5*s, math.sin(rad)*0.5*s
            parts.append({'type': 'box', 'pos': [x,0,z], 'rot': [0,0,0], 'params': {'x': 0.02*s, 'y': 0.2*s, 'z': 0.02*s}, 'material': MAT})
    elif style == 'wide':
        parts.append({'type': 'torus', 'pos': [0,0,0], 'rot': [math.pi/2,0,0], 'params': {'radius': 0.7*s, 'tube': 0.12*s}, 'material': MAT})
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            x, z = math.cos(rad)*0.35*s, math.sin(rad)*0.35*s
            parts.append({'type': 'box', 'pos': [x,0,z], 'rot': [0,rad,math.pi/2], 'params': {'x': 0.65*s, 'y': 0.018*s, 'z': 0.018*s}, 'material': MAT})
    elif style == 'incomplete':
        # Partial ring (under construction feel)
        parts.append({'type': 'torus', 'pos': [0,0,0], 'rot': [math.pi/2,0,0], 'params': {'radius': 0.5*s, 'tube': 0.06*s}, 'material': MAT})
        for angle in range(0, 270, 45):
            rad = math.radians(angle)
            x, z = math.cos(rad)*0.25*s, math.sin(rad)*0.25*s
            parts.append({'type': 'box', 'pos': [x,0,z], 'rot': [0,rad,math.pi/2], 'params': {'x': 0.45*s, 'y': 0.012*s, 'z': 0.012*s}, 'material': MAT})
    return {'parts': parts}


# ─── CORRIDOR (connecting spines between sections) ─────────────────────────

def gen_corridor(style='straight', size=1.0, seed=None):
    _seed(seed)
    s = size
    parts = []
    length = random.uniform(0.5, 1.0) * s
    if style == 'straight':
        parts.append({'type': 'cylinder', 'pos': [0,0,0], 'rot': [0,0,math.pi/2], 'params': {'r_top': 0.04*s, 'r_bot': 0.04*s, 'length': length}, 'material': MAT})
        for x in [-length/2, length/2]:
            parts.append({'type': 'cylinder', 'pos': [x,0,0], 'rot': [0,0,0], 'params': {'r_top': 0.07*s, 'r_bot': 0.07*s, 'length': 0.03*s}, 'material': MAT})
    elif style == 'truss':
        parts.append({'type': 'box', 'pos': [0,0,0], 'rot': [0,0,0], 'params': {'x': length, 'y': 0.05*s, 'z': 0.05*s}, 'material': MAT})
        num_braces = int(length / (0.12*s))
        for i in range(num_braces):
            x = -length/2 + (i+0.5) * length/num_braces
            parts.append({'type': 'box', 'pos': [x,0,0], 'rot': [0,0,math.pi/4], 'params': {'x': 0.01*s, 'y': 0.07*s, 'z': 0.01*s}, 'material': MAT})
    elif style == 'spine':
        parts.append({'type': 'spine', 'pos': [0,0,0], 'rot': [0,0,0], 'params': {'length': length, 'radius': 0.035*s, 'flange_r': 0.07*s}, 'material': MAT})
    elif style == 'tube_lattice':
        for z_off in [-0.04*s, 0.04*s]:
            parts.append({'type': 'cylinder', 'pos': [0,0,z_off], 'rot': [0,0,math.pi/2], 'params': {'r_top': 0.025*s, 'r_bot': 0.025*s, 'length': length}, 'material': MAT})
        for y_off in [-0.04*s, 0.04*s]:
            parts.append({'type': 'cylinder', 'pos': [0,y_off,0], 'rot': [0,0,math.pi/2], 'params': {'r_top': 0.025*s, 'r_bot': 0.025*s, 'length': length}, 'material': MAT})
        for i in range(4):
            x = -length/2 + (i+0.5)*length/4
            parts.append({'type': 'box', 'pos': [x,0,0], 'rot': [0,0,0], 'params': {'x': 0.015*s, 'y': 0.1*s, 'z': 0.1*s}, 'material': MAT})
    return {'parts': parts, '_length': length}



# ─── DOCK (docking bays - more complex) ────────────────────────────────────

def gen_dock(style='bay', size=1.0, seed=None):
    _seed(seed)
    s = size
    parts = []
    if style == 'bay':
        parts.append({'type': 'pod', 'pos': [0,0,0], 'rot': [0,0,0], 'params': {'length': 0.45*s, 'height': 0.18*s, 'width': 0.28*s}, 'material': MAT})
        for z in [-0.16*s, 0.16*s]:
            parts.append({'type': 'box', 'pos': [0.23*s,0,z], 'rot': [0,0,0], 'params': {'x': 0.03*s, 'y': 0.12*s, 'z': 0.02*s}, 'material': MAT})
        # Guide rails
        for y in [-0.06*s, 0.06*s]:
            parts.append({'type': 'box', 'pos': [0,y,0.15*s], 'rot': [0,0,0], 'params': {'x': 0.4*s, 'y': 0.01*s, 'z': 0.01*s}, 'material': MAT})
    elif style == 'ring_port':
        parts.append({'type': 'torus', 'pos': [0,0,0], 'rot': [0,0,0], 'params': {'radius': 0.18*s, 'tube': 0.035*s}, 'material': MAT})
        parts.append({'type': 'cylinder', 'pos': [0,0,0], 'rot': [0,0,0], 'params': {'r_top': 0.14*s, 'r_bot': 0.14*s, 'length': 0.08*s}, 'material': MAT})
        # Docking guides
        for angle in range(0, 360, 120):
            rad = math.radians(angle)
            parts.append({'type': 'box', 'pos': [math.cos(rad)*0.2*s, 0, math.sin(rad)*0.2*s], 'rot': [0,rad,0], 'params': {'x': 0.06*s, 'y': 0.03*s, 'z': 0.015*s}, 'material': MAT})
    elif style == 'hangar':
        parts.append({'type': 'pod', 'pos': [0,0,0], 'rot': [0,0,0], 'params': {'length': 0.7*s, 'height': 0.25*s, 'width': 0.4*s}, 'material': MAT})
        # Open front frame
        parts.append({'type': 'box', 'pos': [0.36*s,0.1*s,0], 'rot': [0,0,0], 'params': {'x': 0.02*s, 'y': 0.05*s, 'z': 0.38*s}, 'material': MAT})
        parts.append({'type': 'box', 'pos': [0.36*s,-0.1*s,0], 'rot': [0,0,0], 'params': {'x': 0.02*s, 'y': 0.05*s, 'z': 0.38*s}, 'material': MAT})
        # Internal gantry
        for z in [-0.12*s, 0.12*s]:
            parts.append({'type': 'box', 'pos': [0,0,z], 'rot': [0,0,0], 'params': {'x': 0.6*s, 'y': 0.01*s, 'z': 0.01*s}, 'material': MAT})
    elif style == 'multi_pad':
        # Multiple small docking pads
        for i in range(3):
            x = (i - 1) * 0.22*s
            parts.append({'type': 'box', 'pos': [x,0,0], 'rot': [0,0,0], 'params': {'x': 0.18*s, 'y': 0.03*s, 'z': 0.15*s}, 'material': MAT})
            parts.append({'type': 'cylinder', 'pos': [x,0.03*s,0], 'rot': [0,0,0], 'params': {'r_top': 0.02*s, 'r_bot': 0.03*s, 'length': 0.04*s}, 'material': MAT})
    return {'parts': parts}


# ─── SOLAR / RADIATOR ─────────────────────────────────────────────────────

def gen_solar(style='panel', size=1.0, seed=None):
    _seed(seed)
    s = size
    parts = []
    if style == 'panel':
        for z in [-0.22*s, 0.22*s]:
            parts.append({'type': 'box', 'pos': [0,0,z], 'rot': [0,0,0], 'params': {'x': 0.6*s, 'y': 0.004*s, 'z': 0.2*s}, 'material': MAT})
            # Panel subdivisions
            for i in range(4):
                x = (i - 1.5) * 0.14*s
                parts.append({'type': 'box', 'pos': [x,0.005*s,z], 'rot': [0,0,0], 'params': {'x': 0.005*s, 'y': 0.008*s, 'z': 0.19*s}, 'material': MAT})
        parts.append({'type': 'cylinder', 'pos': [0,0,0], 'rot': [math.pi/2,0,0], 'params': {'r_top': 0.02*s, 'r_bot': 0.02*s, 'length': 0.45*s}, 'material': MAT})
    elif style == 'array':
        for i in range(6):
            x = (i - 2.5) * 0.11*s
            parts.append({'type': 'box', 'pos': [x,0,0.12*s], 'rot': [0,0,0], 'params': {'x': 0.09*s, 'y': 0.003*s, 'z': 0.22*s}, 'material': MAT})
        parts.append({'type': 'box', 'pos': [0,0,0], 'rot': [0,0,0], 'params': {'x': 0.6*s, 'y': 0.02*s, 'z': 0.02*s}, 'material': MAT})
    elif style == 'radiator':
        for i in range(5):
            angle = (i - 2) * 0.25
            parts.append({'type': 'box', 'pos': [0,0,(i-2)*0.08*s], 'rot': [angle,0,0], 'params': {'x': 0.5*s, 'y': 0.003*s, 'z': 0.07*s}, 'material': MAT})
        parts.append({'type': 'cylinder', 'pos': [0,0,0], 'rot': [math.pi/2,0,0], 'params': {'r_top': 0.015*s, 'r_bot': 0.015*s, 'length': 0.4*s}, 'material': MAT})
    return {'parts': parts}


# ─── ANTENNA ───────────────────────────────────────────────────────────────

def gen_antenna(style='dish', size=1.0, seed=None):
    _seed(seed)
    s = size
    parts = []
    if style == 'dish':
        parts.append({'type': 'sphere', 'pos': [0,0.06*s,0], 'rot': [0,0,0], 'params': {'radius': 0.22*s, 'half': True}, 'material': MAT})
        parts.append({'type': 'cylinder', 'pos': [0,-0.12*s,0], 'rot': [0,0,0], 'params': {'r_top': 0.015*s, 'r_bot': 0.025*s, 'length': 0.25*s}, 'material': MAT})
        # Feed horn
        parts.append({'type': 'cone', 'pos': [0,0.18*s,0], 'rot': [math.pi,0,0], 'params': {'radius': 0.03*s, 'length': 0.08*s}, 'material': MAT})
    elif style == 'phased_array':
        parts.append({'type': 'box', 'pos': [0,0,0], 'rot': [0,0,0], 'params': {'x': 0.3*s, 'y': 0.02*s, 'z': 0.3*s}, 'material': MAT})
        for x in range(-2, 3):
            for z in range(-2, 3):
                parts.append({'type': 'cone', 'pos': [x*0.06*s, 0.02*s, z*0.06*s], 'rot': [0,0,0], 'params': {'radius': 0.015*s, 'length': 0.04*s}, 'material': MAT})
    elif style == 'mast':
        parts.append({'type': 'cylinder', 'pos': [0,0.25*s,0], 'rot': [0,0,0], 'params': {'r_top': 0.01*s, 'r_bot': 0.02*s, 'length': 0.6*s}, 'material': MAT})
        parts.append({'type': 'sphere', 'pos': [0,0.55*s,0], 'rot': [0,0,0], 'params': {'radius': 0.05*s, 'half': False}, 'material': MAT})
        # Cross-bars
        for y in [0.2*s, 0.35*s, 0.48*s]:
            parts.append({'type': 'box', 'pos': [0,y,0], 'rot': [0,0,0], 'params': {'x': 0.12*s, 'y': 0.008*s, 'z': 0.008*s}, 'material': MAT})
    return {'parts': parts}


# ─── HABITAT (pressurized modules) ────────────────────────────────────────

def gen_habitat(style='dome', size=1.0, seed=None):
    _seed(seed)
    s = size
    parts = []
    if style == 'dome':
        parts.append({'type': 'sphere', 'pos': [0,0.1*s,0], 'rot': [0,0,0], 'params': {'radius': 0.28*s, 'half': True}, 'material': MAT})
        parts.append({'type': 'cylinder', 'pos': [0,0,0], 'rot': [0,0,0], 'params': {'r_top': 0.28*s, 'r_bot': 0.3*s, 'length': 0.06*s}, 'material': MAT})
        # Viewport rings
        parts.append({'type': 'torus', 'pos': [0,0.15*s,0], 'rot': [math.pi/2,0,0], 'params': {'radius': 0.2*s, 'tube': 0.01*s}, 'material': MAT})
    elif style == 'cylinder':
        parts.append({'type': 'cylinder', 'pos': [0,0,0], 'rot': [0,0,math.pi/2], 'params': {'r_top': 0.16*s, 'r_bot': 0.16*s, 'length': 0.55*s}, 'material': MAT})
        for x in [-0.28*s, 0.28*s]:
            parts.append({'type': 'sphere', 'pos': [x,0,0], 'rot': [0,0,0], 'params': {'radius': 0.16*s, 'half': True}, 'material': MAT})
        # Window bands
        for x in [-0.12*s, 0, 0.12*s]:
            parts.append({'type': 'torus', 'pos': [x,0,0], 'rot': [0,0,math.pi/2], 'params': {'radius': 0.16*s, 'tube': 0.008*s}, 'material': MAT})
    elif style == 'pod_cluster':
        for i in range(5):
            angle = math.radians(i * 72)
            x, z = math.cos(angle)*0.15*s, math.sin(angle)*0.15*s
            parts.append({'type': 'pod', 'pos': [x,0,z], 'rot': [0,angle,0], 'params': {'length': 0.28*s, 'height': 0.12*s, 'width': 0.12*s}, 'material': MAT})
        # Central connector
        parts.append({'type': 'cylinder', 'pos': [0,0,0], 'rot': [0,0,0], 'params': {'r_top': 0.08*s, 'r_bot': 0.08*s, 'length': 0.15*s}, 'material': MAT})
    return {'parts': parts}


# ─── INDUSTRIAL (tanks, factories, ore processing) ─────────────────────────

def gen_industrial(style='tank', size=1.0, seed=None):
    _seed(seed)
    s = size
    parts = []
    if style == 'tank_farm':
        for i in range(4):
            angle = math.radians(i * 90 + 45)
            x, z = math.cos(angle)*0.15*s, math.sin(angle)*0.15*s
            h = random.uniform(0.25, 0.4)*s
            parts.append({'type': 'cylinder', 'pos': [x,0,z], 'rot': [0,0,0], 'params': {'r_top': 0.08*s, 'r_bot': 0.08*s, 'length': h}, 'material': MAT})
            parts.append({'type': 'sphere', 'pos': [x,h/2,z], 'rot': [0,0,0], 'params': {'radius': 0.08*s, 'half': True}, 'material': MAT})
        parts.append({'type': 'box', 'pos': [0,-0.15*s,0], 'rot': [0,0,0], 'params': {'x': 0.4*s, 'y': 0.03*s, 'z': 0.4*s}, 'material': MAT})
    elif style == 'refinery':
        for i in range(5):
            x = (i-2)*0.12*s
            h = random.uniform(0.3, 0.55)*s
            r = random.uniform(0.06, 0.1)*s
            parts.append({'type': 'cylinder', 'pos': [x,0,0], 'rot': [0,0,0], 'params': {'r_top': r*0.8, 'r_bot': r, 'length': h}, 'material': MAT})
        # Connecting pipes
        parts.append({'type': 'box', 'pos': [0,0.1*s,0.08*s], 'rot': [0,0,0], 'params': {'x': 0.5*s, 'y': 0.02*s, 'z': 0.02*s}, 'material': MAT})
        parts.append({'type': 'box', 'pos': [0,-0.1*s,0.08*s], 'rot': [0,0,0], 'params': {'x': 0.5*s, 'y': 0.02*s, 'z': 0.02*s}, 'material': MAT})
    elif style == 'factory':
        parts.append({'type': 'pod', 'pos': [0,0,0], 'rot': [0,0,0], 'params': {'length': 0.6*s, 'height': 0.25*s, 'width': 0.35*s}, 'material': MAT})
        # Exhaust stacks
        for x in [0.15*s, 0.25*s, -0.15*s]:
            parts.append({'type': 'cylinder', 'pos': [x,0.15*s,0], 'rot': [0,0,0], 'params': {'r_top': 0.02*s, 'r_bot': 0.03*s, 'length': 0.12*s}, 'material': MAT})
        # Conveyor rails
        parts.append({'type': 'box', 'pos': [0,-0.14*s,0.15*s], 'rot': [0,0,0], 'params': {'x': 0.55*s, 'y': 0.015*s, 'z': 0.015*s}, 'material': MAT})
    elif style == 'ore_processor':
        parts.append({'type': 'cylinder', 'pos': [0,0,0], 'rot': [0,0,math.pi/2], 'params': {'r_top': 0.18*s, 'r_bot': 0.22*s, 'length': 0.5*s}, 'material': MAT})
        # Intake funnels
        for x in [-0.28*s, 0.28*s]:
            parts.append({'type': 'cone', 'pos': [x,0,0], 'rot': [0,0,math.pi/2 if x>0 else -math.pi/2], 'params': {'radius': 0.15*s, 'length': 0.12*s}, 'material': MAT})
        # Output bins
        for z in [-0.12*s, 0.12*s]:
            parts.append({'type': 'box', 'pos': [0,-0.2*s,z], 'rot': [0,0,0], 'params': {'x': 0.15*s, 'y': 0.1*s, 'z': 0.08*s}, 'material': MAT})
    return {'parts': parts}


# ─── DEFENSE ───────────────────────────────────────────────────────────────

def gen_defense(style='turret', size=1.0, seed=None):
    _seed(seed)
    s = size
    parts = []
    if style == 'turret':
        parts.append({'type': 'cylinder', 'pos': [0,0,0], 'rot': [0,0,0], 'params': {'r_top': 0.06*s, 'r_bot': 0.09*s, 'length': 0.06*s}, 'material': MAT})
        parts.append({'type': 'sphere', 'pos': [0,0.04*s,0], 'rot': [0,0,0], 'params': {'radius': 0.055*s, 'half': True}, 'material': MAT})
        # Twin barrels
        for z in [-0.02*s, 0.02*s]:
            parts.append({'type': 'cylinder', 'pos': [0.08*s,0.04*s,z], 'rot': [0,0,math.pi/2], 'params': {'r_top': 0.01*s, 'r_bot': 0.012*s, 'length': 0.12*s}, 'material': MAT})
    elif style == 'missile_pod':
        parts.append({'type': 'box', 'pos': [0,0,0], 'rot': [0,0,0], 'params': {'x': 0.18*s, 'y': 0.12*s, 'z': 0.12*s}, 'material': MAT})
        for y in [-0.03*s, 0.03*s]:
            for z in [-0.03*s, 0.03*s]:
                parts.append({'type': 'cylinder', 'pos': [0.1*s,y,z], 'rot': [0,0,math.pi/2], 'params': {'r_top': 0.015*s, 'r_bot': 0.015*s, 'length': 0.08*s}, 'material': MAT})
    elif style == 'shield_gen':
        parts.append({'type': 'sphere', 'pos': [0,0,0], 'rot': [0,0,0], 'params': {'radius': 0.12*s, 'half': False}, 'material': MAT})
        parts.append({'type': 'torus', 'pos': [0,0,0], 'rot': [math.pi/2,0,0], 'params': {'radius': 0.16*s, 'tube': 0.018*s}, 'material': MAT})
        parts.append({'type': 'torus', 'pos': [0,0,0], 'rot': [0,0,0], 'params': {'radius': 0.16*s, 'tube': 0.018*s}, 'material': MAT})
    elif style == 'point_defense':
        parts.append({'type': 'cylinder', 'pos': [0,0,0], 'rot': [0,0,0], 'params': {'r_top': 0.04*s, 'r_bot': 0.05*s, 'length': 0.04*s}, 'material': MAT})
        parts.append({'type': 'cylinder', 'pos': [0.06*s,0.02*s,0], 'rot': [0,0,math.pi/2], 'params': {'r_top': 0.008*s, 'r_bot': 0.01*s, 'length': 0.08*s}, 'material': MAT})
    return {'parts': parts}


# ─── REGISTRY ──────────────────────────────────────────────────────────────

STATION_GENERATORS = {
    'hub': (gen_hub, ['sphere', 'cylinder', 'octagonal', 'modular', 'blocky']),
    'ring': (gen_ring, ['single', 'double', 'wide', 'incomplete']),
    'corridor': (gen_corridor, ['straight', 'truss', 'spine', 'tube_lattice']),
    'dock': (gen_dock, ['bay', 'ring_port', 'hangar', 'multi_pad']),
    'solar': (gen_solar, ['panel', 'array', 'radiator']),
    'antenna': (gen_antenna, ['dish', 'phased_array', 'mast']),
    'habitat': (gen_habitat, ['dome', 'cylinder', 'pod_cluster']),
    'industrial': (gen_industrial, ['tank_farm', 'refinery', 'factory', 'ore_processor']),
    'defense': (gen_defense, ['turret', 'missile_pod', 'shield_gen', 'point_defense']),
}

STATION_CATEGORIES = {k: f"{len(styles)} styles" for k, (_, styles) in STATION_GENERATORS.items()}
