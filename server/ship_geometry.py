"""
Ship geometry definitions. Each ship is described as a hierarchy of components
that can be serialized to JSON and rendered client-side in Three.js.

Component types:
- pod: beveled box (length, height, width)
- cylinder: engine nacelle (radius_top, radius_bottom, length)
- cone: nozzle/cockpit tip (radius, length)
- spine: hexagonal connector with flanges (length, radius, flange_radius)
- wedge: tapered shape (profile points extruded to height)
- box: simple box (x, y, z dimensions)
- sphere: dome/turret head (radius, half=True for hemisphere)
- torus: ring (radius, tube_radius)
- wing: flat panel (profile points, thickness)

Each component has:
- type: component type string
- pos: [x, y, z] position
- rot: [x, y, z] rotation in radians (optional)
- scale: [x, y, z] scale (optional)
- params: type-specific parameters
- material: "hull", "engine", "weapon", "mining", "cargo", "shield", "accent"
- hardpoint: optional hardpoint ID if this is a mountable slot
"""


def _pod(pos, length, height, width, material="hull", rot=None, hardpoint=None):
    return {"type": "pod", "pos": pos, "rot": rot or [0,0,0], "params": {"length": length, "height": height, "width": width}, "material": material, "hardpoint": hardpoint}

def _cyl(pos, r_top, r_bot, length, material="hull", rot=None):
    return {"type": "cylinder", "pos": pos, "rot": rot or [0,0,0], "params": {"r_top": r_top, "r_bot": r_bot, "length": length}, "material": material}

def _cone(pos, radius, length, material="engine", rot=None):
    return {"type": "cone", "pos": pos, "rot": rot or [0,0,0], "params": {"radius": radius, "length": length}, "material": material}

def _spine(pos, length, radius, flange_r, material="hull"):
    return {"type": "spine", "pos": pos, "params": {"length": length, "radius": radius, "flange_r": flange_r}, "material": material}

def _box(pos, x, y, z, material="hull", rot=None, hardpoint=None):
    return {"type": "box", "pos": pos, "rot": rot or [0,0,0], "params": {"x": x, "y": y, "z": z}, "material": material, "hardpoint": hardpoint}

def _sphere(pos, radius, half=False, material="accent", rot=None):
    return {"type": "sphere", "pos": pos, "rot": rot or [0,0,0], "params": {"radius": radius, "half": half}, "material": material}

def _torus(pos, radius, tube, material="hull", rot=None):
    return {"type": "torus", "pos": pos, "rot": rot or [0,0,0], "params": {"radius": radius, "tube": tube}, "material": material}

def _wedge(pos, profile, depth, material="hull", rot=None):
    """profile: list of [x,y] points defining the cross-section"""
    return {"type": "wedge", "pos": pos, "rot": rot or [0,0,0], "params": {"profile": profile, "depth": depth}, "material": material}

def _hardpoint(pos, slot_type, slot_id):
    """Visible hardpoint marker"""
    return {"type": "hardpoint", "pos": pos, "params": {"slot_type": slot_type, "slot_id": slot_id}, "material": slot_type}


# ═══════════════════════════════════════════════════════════════════════════════
# COMPONENT LIBRARY - Standard parts used across all ships
# ═══════════════════════════════════════════════════════════════════════════════

# ── BRIDGE VARIANTS ───────────────────────────────────────────────────────────
_BRIDGE_TAPERED_PROFILE = [[0,-0.2],[0.6,-0.12],[0.75,0],[0.6,0.12],[0,0.2]]
_BRIDGE_DOME_PROFILE = [[0,-0.2],[0.3,-0.19],[0.55,-0.14],[0.7,-0.05],[0.72,0],[0.7,0.05],[0.55,0.14],[0.3,0.19],[0,0.2]]
_BRIDGE_ANGULAR_PROFILE = [[0,-0.18],[0.5,-0.18],[0.65,-0.08],[0.7,0],[0.65,0.08],[0.5,0.18],[0,0.18]]

def _bridge(pos, scale=1.0, material="hull", variant="tapered"):
    """Standard bridge module. Variants: tapered, dome, angular"""
    profiles = {"tapered": _BRIDGE_TAPERED_PROFILE, "dome": _BRIDGE_DOME_PROFILE, "angular": _BRIDGE_ANGULAR_PROFILE}
    profile = [[p[0]*scale, p[1]*scale] for p in profiles.get(variant, _BRIDGE_TAPERED_PROFILE)]
    return {"type": "wedge", "pos": pos, "rot": [0,0,0], "params": {"profile": profile, "depth": 0.35*scale}, "material": material}

# ── POD VARIANTS ──────────────────────────────────────────────────────────────
# Standard beveled pod uses _pod() directly
# Spherical pod segment
_POD_SPHERE_PROFILE = [[0,-0.2],[0.15,-0.19],[0.28,-0.14],[0.35,-0.05],[0.36,0],[0.35,0.05],[0.28,0.14],[0.15,0.19],[0,0.2],[-0.15,0.19],[-0.28,0.14],[-0.35,0.05],[-0.36,0],[-0.35,-0.05],[-0.28,-0.14],[-0.15,-0.19]]
# Cylindrical rounded pod
_POD_ROUND_PROFILE = [[0,-0.2],[0.3,-0.2],[0.35,-0.18],[0.35,0.18],[0.3,0.2],[0,0.2],[-0.3,0.2],[-0.35,0.18],[-0.35,-0.18],[-0.3,-0.2]]

def _pod_sphere(pos, length, radius, material="cargo"):
    """Spherical/rounded pod segment."""
    profile = [[p[0]*radius/0.36, p[1]*radius/0.2] for p in _POD_SPHERE_PROFILE]
    return {"type": "wedge", "pos": pos, "rot": [0,0,0], "params": {"profile": profile, "depth": length}, "material": material}

def _pod_round(pos, length, height, width, material="cargo"):
    """Cylindrical rounded pod."""
    profile = [[p[0]*height/0.7, p[1]*width/0.4] for p in _POD_ROUND_PROFILE]
    return {"type": "wedge", "pos": pos, "rot": [0,0,0], "params": {"profile": profile, "depth": length}, "material": material}

# ── CONNECTOR VARIANTS ────────────────────────────────────────────────────────
# Hex spine uses _spine() directly
def _collar(pos, length, radius, material="hull"):
    """Cylindrical collar connector."""
    return {"type": "cylinder", "pos": pos, "rot": [0,0,0], "params": {"r_top": radius, "r_bot": radius*1.1, "length": length}, "material": material}

def _bracket(pos, x, y, z, material="hull"):
    """Angular bracket connector (flat structural plate)."""
    return {"type": "box", "pos": pos, "rot": [0,0,0], "params": {"x": x, "y": y, "z": z}, "material": material}


def _bridge_dome(pos, scale=1.0, material="hull"):
    """Dome bridge - two-layer axe-head shape for large ships."""
    s = scale
    return [
        {"type": "wedge", "pos": pos, "rot": [1.5708, 0, 0], "params": {"profile": [[0,-0.25*s],[0,0.25*s],[0.22*s,0.24*s],[0.38*s,0.2*s],[0.48*s,0.12*s],[0.52*s,0],[0.48*s,-0.12*s],[0.38*s,-0.2*s],[0.22*s,-0.24*s]], "depth": 0.05*s}, "material": material},
        {"type": "wedge", "pos": [pos[0], pos[1]+0.06*s, pos[2]], "rot": [1.5708, 0, 0], "params": {"profile": [[0,-0.18*s],[0,0.18*s],[0.16*s,0.17*s],[0.28*s,0.14*s],[0.35*s,0.08*s],[0.38*s,0],[0.35*s,-0.08*s],[0.28*s,-0.14*s],[0.16*s,-0.17*s]], "depth": 0.05*s}, "material": material},
    ]

# ── TURRET ────────────────────────────────────────────────────────────────────
def _turret(pos, material="accent"):
    """Standard weapon turret (base + dome + barrel). Returns list of components."""
    return [
        {"type": "cylinder", "pos": [pos[0], pos[1]-0.02, pos[2]], "rot": [0,0,0], "params": {"r_top": 0.07, "r_bot": 0.09, "length": 0.04, "vertical": True}, "material": material},
        {"type": "sphere", "pos": [pos[0], pos[1]+0.02, pos[2]], "rot": [0,0,0], "params": {"radius": 0.06, "half": True}, "material": material},
        {"type": "cylinder", "pos": [pos[0]+0.08, pos[1]+0.02, pos[2]], "rot": [0,0,-1.5708], "params": {"r_top": 0.012, "r_bot": 0.012, "length": 0.12}, "material": material},
    ]

# ── MINING ARM ────────────────────────────────────────────────────────────────
def _mining_arm(pos, length=0.5, angle_y=0, material="mining"):
    """Mining arm: joint + boom + emitter. angle_y rotates the arm direction."""
    return [
        {"type": "sphere", "pos": pos, "rot": [0,0,0], "params": {"radius": 0.05, "half": False}, "material": material},
        {"type": "cylinder", "pos": [pos[0], pos[1], pos[2]+length*0.5], "rot": [1.5708, angle_y, 0], "params": {"r_top": 0.03, "r_bot": 0.04, "length": length}, "material": material},
        {"type": "sphere", "pos": [pos[0], pos[1], pos[2]+length], "rot": [0,0,0], "params": {"radius": 0.06, "half": False}, "material": material},
    ]



# ═══════════════════════════════════════════════════════════════════════════════
# SHIP DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

SHIP_GEOMETRIES = {}

# ── MULE FREIGHTER (T1 Hauler) ────────────────────────────────────────────────
SHIP_GEOMETRIES["mule_freighter"] = {
    "name": "Mule Freighter", "role": "hauler", "tier": 1,
    "bounds": {"length": 4.5, "height": 1.0, "width": 1.5},
    "components": [
        # Engine assembly
        _cyl([-2.6, 0, 0.3], 0.16, 0.2, 0.5, "engine"),
        _cyl([-2.6, 0, -0.3], 0.16, 0.2, 0.5, "engine"),
        _cone([-2.94, 0, 0.3], 0.12, 0.18, "engine"),
        _cone([-2.94, 0, -0.3], 0.12, 0.18, "engine"),
        _box([-2.25, 0, 0], 0.12, 0.4, 0.8, "hull"),  # mount plate
        # Spine A
        _spine([-1.93, 0, 0], 0.35, 0.15, 0.19),
        # Cargo bay (3 pods + internal spines)
        _pod([-1.4, 0, 0], 0.55, 0.38, 0.7, "cargo"),
        _spine([-1.0, 0, 0], 0.1, 0.12, 0.16),
        _pod([-0.55, 0, 0], 0.65, 0.42, 0.75, "cargo"),
        _spine([-0.1, 0, 0], 0.1, 0.12, 0.16),
        _pod([0.3, 0, 0], 0.55, 0.38, 0.7, "cargo"),
        # Spine B
        _spine([0.75, 0, 0], 0.2, 0.15, 0.19),
        # Bridge
        _pod([1.05, 0, 0], 0.35, 0.3, 0.45, "hull"),
        _bridge([1.45, 0, 0], scale=0.7),
        # Hardpoints
        _hardpoint([-0.55, 0.22, 0], "defense", "turret_1"),
        _hardpoint([0.3, 0.2, 0.36], "utility", "util_1"),
    ],
}

# ── BISON MK.III (T2 Hauler) ──────────────────────────────────────────────────
SHIP_GEOMETRIES["bison_mk3"] = {
    "name": "Bison Mk.III", "role": "hauler", "tier": 2,
    "bounds": {"length": 5.5, "height": 1.2, "width": 1.8},
    "components": [
        # Triple engine
        _cyl([-2.8, 0, 0.35], 0.18, 0.22, 0.5, "engine"),
        _cyl([-2.8, 0, 0], 0.2, 0.24, 0.55, "engine"),
        _cyl([-2.8, 0, -0.35], 0.18, 0.22, 0.5, "engine"),
        _cone([-3.15, 0, 0.35], 0.13, 0.2, "engine"),
        _cone([-3.15, 0, 0], 0.15, 0.22, "engine"),
        _cone([-3.15, 0, -0.35], 0.13, 0.2, "engine"),
        _box([-2.45, 0, 0], 0.14, 0.55, 1.0, "hull"),
        # Spine A
        _spine([-2.1, 0, 0], 0.35, 0.18, 0.22),
        # Cargo (4 pods)
        _pod([-1.5, 0, 0], 0.6, 0.42, 0.8, "cargo"),
        _spine([-1.1, 0, 0], 0.12, 0.14, 0.18),
        _pod([-0.65, 0, 0], 0.7, 0.48, 0.85, "cargo"),
        _spine([-0.2, 0, 0], 0.12, 0.14, 0.18),
        _pod([0.25, 0, 0], 0.7, 0.48, 0.85, "cargo"),
        _spine([0.7, 0, 0], 0.12, 0.14, 0.18),
        _pod([1.1, 0, 0], 0.6, 0.42, 0.8, "cargo"),
        # Spine B
        _spine([1.55, 0, 0], 0.25, 0.16, 0.2),
        # Bridge
        _pod([1.9, 0, 0], 0.4, 0.35, 0.5, "hull"),
        _bridge([2.3, 0, 0], scale=0.85),
        # Hardpoints
        _hardpoint([-0.65, 0.26, 0], "utility", "util_1"),
        _hardpoint([0.25, 0.26, 0], "utility", "util_2"),
        _hardpoint([1.1, 0.22, 0.42], "defense", "turret_1"),
        _hardpoint([-1.5, -0.22, 0], "industrial", "ind_1"),
    ],
}

# ── CLYDESDALE (T4 Hauler) ────────────────────────────────────────────────────
SHIP_GEOMETRIES["clydesdale"] = {
    "name": "Clydesdale", "role": "hauler", "tier": 4,
    "bounds": {"length": 7.0, "height": 1.8, "width": 1.8},
    "components": [
        # Quad engines in frame
        _cyl([-3.2, 0.3, 0.3], 0.18, 0.22, 0.5, "engine"),
        _cyl([-3.2, 0.3, -0.3], 0.18, 0.22, 0.5, "engine"),
        _cyl([-3.2, -0.3, 0.3], 0.18, 0.22, 0.5, "engine"),
        _cyl([-3.2, -0.3, -0.3], 0.18, 0.22, 0.5, "engine"),
        _cone([-3.55, 0.3, 0.3], 0.14, 0.2, "engine"),
        _cone([-3.55, 0.3, -0.3], 0.14, 0.2, "engine"),
        _cone([-3.55, -0.3, 0.3], 0.14, 0.2, "engine"),
        _cone([-3.55, -0.3, -0.3], 0.14, 0.2, "engine"),
        # Engine frame cross-beams
        _box([-3.2, 0.35, 0], 0.08, 0.08, 0.8, "hull"),
        _box([-3.2, -0.35, 0], 0.08, 0.08, 0.8, "hull"),
        _box([-3.2, 0, 0], 0.08, 0.8, 0.08, "hull"),
        # Spine A (long, connects engine to cargo)
        _spine([-2.7, 0, 0], 0.4, 0.2, 0.25),
        # Central spine (runs through entire cargo section)
        _pod([-1.2, 0, 0], 2.6, 0.12, 0.12, "hull"),
        # 8 spherical cargo pods (2x2x2 grid)
        _sphere([-2.0, 0.35, 0.4], 0.32, False, "cargo"),
        _sphere([-2.0, 0.35, -0.4], 0.32, False, "cargo"),
        _sphere([-2.0, -0.35, 0.4], 0.32, False, "cargo"),
        _sphere([-2.0, -0.35, -0.4], 0.32, False, "cargo"),
        _sphere([-0.8, 0.35, 0.4], 0.32, False, "cargo"),
        _sphere([-0.8, 0.35, -0.4], 0.32, False, "cargo"),
        _sphere([-0.8, -0.35, 0.4], 0.32, False, "cargo"),
        _sphere([-0.8, -0.35, -0.4], 0.32, False, "cargo"),
        # Spine B
        _spine([0.2, 0, 0], 0.3, 0.12, 0.16),
        # Bridge module
        _pod([0.55, 0.05, 0], 0.3, 0.28, 0.35, "hull"),
        *_bridge_dome([0.82, 0.05, 0], scale=0.55),
        # Hardpoints
        _hardpoint([-2.0, 0.7, 0], "defense", "turret_1"),
        _hardpoint([-0.8, 0.7, 0], "defense", "turret_2"),
        _hardpoint([-2.0, -0.7, 0], "utility", "util_1"),
        _hardpoint([-0.8, -0.7, 0], "utility", "util_2"),
        _hardpoint([-1.4, 0.7, 0], "utility", "util_3"),
        _hardpoint([-1.4, -0.7, 0], "industrial", "ind_1"),
        _hardpoint([0.0, -0.5, 0], "industrial", "ind_2"),
    ],
}



# ── PINTO RUNNER (T1 Hauler - light courier) ───────────────────────────────────
SHIP_GEOMETRIES["pinto_runner"] = {
    "name": "Pinto Runner", "role": "hauler", "tier": 1,
    "bounds": {"length": 3.5, "height": 0.6, "width": 0.8},
    "components": [
        # Single engine
        _cyl([-1.4, 0, 0], 0.12, 0.15, 0.4, "engine"),
        _cone([-1.68, 0, 0], 0.1, 0.16, "engine"),
        # Spine
        _spine([-1.05, 0, 0], 0.2, 0.1, 0.13),
        # Cargo pods (2, connected)
        _pod([-0.6, 0, 0], 0.45, 0.22, 0.35, "cargo"),
        _spine([-0.3, 0, 0], 0.08, 0.08, 0.11),
        _pod([0.0, 0, 0], 0.4, 0.22, 0.35, "cargo"),
        # Spine to bridge
        _spine([0.28, 0, 0], 0.12, 0.08, 0.11),
        # Bridge
        _bridge([0.55, 0, 0], scale=0.5),
        # Hardpoints
        _hardpoint([0.0, 0.12, 0.18], "utility", "util_1"),
        _hardpoint([-0.6, 0.12, -0.18], "defense", "def_1"),
    ],
}

# ── OX HAULER (T3 Hauler - heavy) ─────────────────────────────────────────────
SHIP_GEOMETRIES["ox_hauler"] = {
    "name": "Ox Hauler", "role": "hauler", "tier": 3,
    "bounds": {"length": 5.8, "height": 1.4, "width": 1.6},
    "components": [
        # Triple engine block
        _cyl([-2.7, 0.25, 0], 0.18, 0.22, 0.5, "engine"),
        _cyl([-2.7, -0.25, 0.2], 0.16, 0.2, 0.45, "engine"),
        _cyl([-2.7, -0.25, -0.2], 0.16, 0.2, 0.45, "engine"),
        _cone([-3.05, 0.25, 0], 0.14, 0.2, "engine"),
        _cone([-3.0, -0.25, 0.2], 0.12, 0.18, "engine"),
        _cone([-3.0, -0.25, -0.2], 0.12, 0.18, "engine"),
        _box([-2.35, 0, 0], 0.14, 0.6, 0.6, "hull"),  # mount frame
        # Spine A
        _spine([-2.05, 0, 0], 0.3, 0.18, 0.22),
        # Main cargo hull (3 large pods)
        _pod([-1.4, 0, 0], 0.7, 0.5, 0.75, "cargo"),
        _spine([-0.95, 0, 0], 0.12, 0.15, 0.19),
        _pod([-0.5, 0, 0], 0.8, 0.55, 0.8, "cargo"),
        _spine([-0.0, 0, 0], 0.12, 0.15, 0.19),
        _pod([0.45, 0, 0], 0.7, 0.5, 0.75, "cargo"),
        # Spine B
        _spine([0.95, 0, 0], 0.25, 0.15, 0.19),
        # Bridge
        _pod([1.3, 0.05, 0], 0.35, 0.32, 0.4, "hull"),
        _bridge([1.65, 0.05, 0], scale=0.7),
        # Hardpoints
        _hardpoint([-1.4, 0.27, 0], "defense", "turret_1"),
        _hardpoint([0.45, 0.27, 0], "defense", "turret_2"),
        _hardpoint([-0.5, -0.28, 0], "industrial", "ind_1"),
        _hardpoint([-1.4, 0.27, 0.4], "utility", "util_1"),
        _hardpoint([0.45, 0.27, 0.4], "utility", "util_2"),
    ],
}

# ── MAMMOTH (T3 Hauler - heavy transport) ──────────────────────────────────────
SHIP_GEOMETRIES["mammoth"] = {
    "name": "Mammoth", "role": "hauler", "tier": 3,
    "bounds": {"length": 6.0, "height": 1.5, "width": 1.6},
    "components": [
        # Triple engine in armored housing
        _pod([-2.8, 0, 0], 0.5, 0.7, 0.6, "hull"),  # engine housing
        _cyl([-2.8, 0.2, 0], 0.14, 0.18, 0.55, "engine"),
        _cyl([-2.8, -0.15, 0.15], 0.12, 0.16, 0.5, "engine"),
        _cyl([-2.8, -0.15, -0.15], 0.12, 0.16, 0.5, "engine"),
        _cone([-3.15, 0.2, 0], 0.12, 0.18, "engine"),
        _cone([-3.1, -0.15, 0.15], 0.1, 0.16, "engine"),
        _cone([-3.1, -0.15, -0.15], 0.1, 0.16, "engine"),
        # Armored spine
        _pod([-2.3, 0, 0], 0.25, 0.2, 0.2, "hull"),
        _spine([-2.0, 0, 0], 0.3, 0.16, 0.2),
        # Cargo module A (top)
        _pod([-1.2, 0.3, 0], 1.5, 0.45, 0.7, "cargo"),
        # Cargo module B (bottom)
        _pod([-1.2, -0.3, 0], 1.5, 0.45, 0.7, "cargo"),
        # Internal cross-braces
        _box([-1.6, 0, 0], 0.06, 0.4, 0.06, "hull"),
        _box([-0.8, 0, 0], 0.06, 0.4, 0.06, "hull"),
        # Spine B
        _spine([-0.2, 0, 0], 0.25, 0.14, 0.18),
        # Armored bridge
        _pod([0.15, 0, 0], 0.4, 0.35, 0.45, "hull"),
        _bridge([0.55, 0, 0], scale=0.65),
        # Hardpoints
        _hardpoint([-1.5, 0.55, 0], "defense", "turret_1"),
        _hardpoint([-0.9, 0.55, 0], "defense", "turret_2"),
        _hardpoint([-1.2, -0.55, -0.36], "industrial", "ind_1"),
        _hardpoint([-1.2, -0.55, 0.36], "industrial", "ind_2"),
        _hardpoint([-1.5, 0.55, 0.36], "utility", "util_1"),
        _hardpoint([-0.9, 0.55, 0.36], "utility", "util_2"),
    ],
}

# ── DEEP CORE BORER (T3 Miner) ────────────────────────────────────────────────
SHIP_GEOMETRIES["deep_core_borer"] = {
    "name": "Deep Core Borer", "role": "miner", "tier": 3,
    "bounds": {"length": 4.5, "height": 1.2, "width": 2.0},
    "components": [
        # Single large engine (offset port)
        _cyl([-2.0, 0, -0.1], 0.28, 0.32, 0.6, "engine"),
        _cone([-2.45, 0, -0.1], 0.22, 0.25, "engine"),
        _torus([-1.65, 0, -0.1], 0.3, 0.03),
        # Spine to core
        _spine([-1.4, 0, 0], 0.25, 0.16, 0.2),
        # Central core (processing)
        _pod([-0.9, 0, 0], 0.6, 0.45, 0.5, "hull"),
        # Ore bay (port side, lateral)
        _spine([-0.9, 0, -0.35], 0.15, 0.1, 0.14),
        _pod([-0.9, 0, -0.7], 0.8, 0.3, 0.5, "cargo"),
        _pod([-0.9, -0.25, -0.6], 0.6, 0.25, 0.4, "cargo"),
        # Spine to bridge
        _spine([-0.4, 0, 0], 0.15, 0.12, 0.15),
        # Bridge (dome style for large miner)
        _bridge([-0.1, 0, 0], scale=0.55),
        # Mining arms (3, out starboard side of core)
        _sphere([-1.1, 0, 0.28], 0.05, False, "mining"),
        _cyl([-1.1, 0, 0.52], 0.04, 0.05, 0.4, "mining", [1.5708, 0, 0]),
        _sphere([-1.1, 0, 0.7], 0.07, False, "mining"),
        _sphere([-0.8, 0.15, 0.28], 0.05, False, "mining"),
        _cyl([-0.8, 0.15, 0.5], 0.04, 0.05, 0.38, "mining", [1.5708, 0, 0]),
        _sphere([-0.8, 0.15, 0.66], 0.07, False, "mining"),
        _sphere([-0.8, -0.15, 0.28], 0.05, False, "mining"),
        _cyl([-0.8, -0.15, 0.5], 0.04, 0.05, 0.38, "mining", [1.5708, 0, 0]),
        _sphere([-0.8, -0.15, 0.66], 0.07, False, "mining"),
        # Hardpoints
        _hardpoint([-0.9, 0.24, 0], "utility", "scan_1"),
        _hardpoint([-0.9, 0.24, -0.2], "utility", "scan_2"),
        _hardpoint([-0.7, -0.24, 0.1], "defense", "def_1"),
        _hardpoint([-1.1, 0, 0.28], "mining", "mine_1"),
        _hardpoint([-0.8, 0.15, 0.28], "mining", "mine_2"),
        _hardpoint([-0.8, -0.15, 0.28], "mining", "mine_3"),
    ],
}



# ── PROSPECT SKIFF (T1 Miner) ─────────────────────────────────────────────────
SHIP_GEOMETRIES["prospect_skiff"] = {
    "name": "Prospect Skiff", "role": "miner", "tier": 1,
    "bounds": {"length": 3.0, "height": 0.6, "width": 1.0},
    "components": [
        # Engine
        _cyl([-1.1, 0, 0], 0.1, 0.13, 0.35, "engine"),
        _cone([-1.35, 0, 0], 0.08, 0.14, "engine"),
        # Spine
        _spine([-0.8, 0, 0], 0.15, 0.09, 0.12),
        # Main hull (serves as cargo)
        _pod([-0.3, 0, 0], 0.6, 0.25, 0.4, "cargo"),
        # Spine to bridge
        _spine([0.08, 0, 0], 0.1, 0.08, 0.1),
        # Bridge
        _bridge([0.3, 0, 0], scale=0.4),
        # Mining arm (out starboard side)
        _sphere([-0.3, 0, 0.22], 0.04, False, "mining"),
        _cyl([-0.3, 0, 0.45], 0.03, 0.035, 0.4, "mining", [1.5708, 0, 0]),
        _sphere([-0.3, 0, 0.62], 0.05, False, "mining"),
        # Hardpoints
        _hardpoint([-0.3, 0, 0.22], "mining", "mine_1"),
        _hardpoint([-0.3, 0.14, 0], "utility", "util_1"),
    ],
}

# ── ROCK HOPPER (T1 Miner) ────────────────────────────────────────────────────
# ── STRIP MINER (T2 Miner) ────────────────────────────────────────────────────
SHIP_GEOMETRIES["strip_miner"] = {
    "name": "Strip Miner", "role": "miner", "tier": 2,
    "bounds": {"length": 4.0, "height": 1.0, "width": 1.2},
    "components": [
        # Dual engine
        _cyl([-1.7, 0.15, 0], 0.12, 0.15, 0.45, "engine"),
        _cyl([-1.7, -0.15, 0], 0.12, 0.15, 0.45, "engine"),
        _cone([-2.0, 0.15, 0], 0.09, 0.14, "engine"),
        _cone([-2.0, -0.15, 0], 0.09, 0.14, "engine"),
        # Spine to hull
        _spine([-1.3, 0, 0], 0.2, 0.12, 0.16),
        # Double hull (2 pods joined by connector)
        _pod([-0.85, 0, 0], 0.5, 0.32, 0.45, "hull"),
        _spine([-0.5, 0, 0], 0.12, 0.1, 0.14),
        _pod([-0.15, 0, 0], 0.5, 0.32, 0.45, "cargo"),
        # Spine to bridge
        _spine([0.2, 0, 0], 0.12, 0.09, 0.12),
        # Bridge
        _bridge([0.45, 0, 0], scale=0.5),
        # Mining arms (out both sides)
        _sphere([-0.5, 0, 0.25], 0.04, False, "mining"),
        _cyl([-0.5, 0, 0.48], 0.03, 0.035, 0.4, "mining", [1.5708, 0, 0]),
        _sphere([-0.5, 0, 0.65], 0.055, False, "mining"),
        _sphere([-0.5, 0, -0.25], 0.04, False, "mining"),
        _cyl([-0.5, 0, -0.48], 0.03, 0.035, 0.4, "mining", [1.5708, 0, 0]),
        _sphere([-0.5, 0, -0.65], 0.055, False, "mining"),
        # Hardpoints
        _hardpoint([-0.5, 0, 0.25], "mining", "mine_1"),
        _hardpoint([-0.5, 0, -0.25], "mining", "mine_2"),
        _hardpoint([-0.85, 0.18, 0], "utility", "util_1"),
        _hardpoint([-0.15, 0.18, 0], "defense", "def_1"),
    ],
}

# ── EXCAVATOR (T2 Miner) ──────────────────────────────────────────────────────
SHIP_GEOMETRIES["excavator"] = {
    "name": "Excavator", "role": "miner", "tier": 2,
    "bounds": {"length": 4.2, "height": 1.1, "width": 1.3},
    "components": [
        # Engine
        _cyl([-1.6, 0, 0], 0.18, 0.22, 0.5, "engine"),
        _cone([-1.92, 0, 0], 0.14, 0.18, "engine"),
        _spine([-1.2, 0, 0], 0.2, 0.13, 0.17),
        # Double hull (processing + ore)
        _pod([-0.7, 0, 0], 0.55, 0.35, 0.45, "hull"),
        _spine([-0.35, 0, 0], 0.1, 0.1, 0.13),
        _pod([0.0, 0, 0], 0.5, 0.35, 0.45, "cargo"),
        # Scanner array (top of first hull)
        _box([-0.7, 0.22, 0], 0.15, 0.06, 0.12, "hull"),
        _sphere([-0.7, 0.28, 0], 0.05, False, "hull"),
        # Spine to bridge
        _spine([0.35, 0, 0], 0.12, 0.09, 0.12),
        # Bridge
        _bridge([0.6, 0, 0], scale=0.5),
        # Mining arms (out starboard side)
        _sphere([-0.5, 0, 0.25], 0.04, False, "mining"),
        _cyl([-0.5, 0, 0.48], 0.035, 0.04, 0.4, "mining", [1.5708, 0, 0]),
        _sphere([-0.5, 0, 0.65], 0.06, False, "mining"),
        _sphere([0.0, 0, 0.25], 0.04, False, "mining"),
        _cyl([0.0, 0, 0.48], 0.035, 0.04, 0.4, "mining", [1.5708, 0, 0]),
        _sphere([0.0, 0, 0.65], 0.06, False, "mining"),
        # Hardpoints
        _hardpoint([-0.5, 0, 0.25], "mining", "mine_1"),
        _hardpoint([0.0, 0, 0.25], "mining", "mine_2"),
        _hardpoint([-0.7, 0.22, 0.1], "utility", "util_1"),
        _hardpoint([-0.7, 0.22, -0.1], "utility", "util_2"),
        _hardpoint([0.0, 0.2, -0.23], "defense", "def_1"),
    ],
}

# ── VIPER INTERCEPTOR (T2 Military) ───────────────────────────────────────────
SHIP_GEOMETRIES["viper_interceptor"] = {
    "name": "Viper Interceptor", "role": "military", "tier": 2,
    "bounds": {"length": 2.2, "height": 0.5, "width": 1.2},
    "components": [
        # Angular fuselage (shorter)
        _wedge([0, 0, 0], [[0,-0.08],[0.16,-0.06],[0.12,0.08],[0,0.14],[-0.12,0.08],[-0.16,-0.06]], 0.8, "hull", [0, 1.5708, 0]),
        # Nose
        _wedge([0.55, 0.01, 0], [[0,-0.05],[0.1,-0.03],[0.06,0.05],[0,0.08],[-0.06,0.05],[-0.1,-0.03]], 0.3, "hull", [0, 1.5708, 0]),
        _cone([0.8, 0.01, 0], 0.025, 0.12, "hull", [0, 0, -1.5708]),
        # Engines (rectangular, integrated)
        _box([-0.45, -0.02, -0.16], 0.22, 0.09, 0.1, "engine"),
        _box([-0.45, -0.02, 0.16], 0.22, 0.09, 0.1, "engine"),
        _box([-0.58, -0.02, -0.16], 0.04, 0.1, 0.12, "engine"),
        _box([-0.58, -0.02, 0.16], 0.04, 0.1, 0.12, "engine"),
        # Wing pylons
        _box([-0.05, -0.04, -0.3], 0.4, 0.02, 0.035, "hull", [0, 0.25, 0]),
        _box([-0.05, -0.04, 0.3], 0.4, 0.02, 0.035, "hull", [0, -0.25, 0]),
        # Weapon pods
        _box([0.15, -0.08, -0.22], 0.15, 0.03, 0.05, "weapon"),
        _box([0.15, -0.08, 0.22], 0.15, 0.03, 0.05, "weapon"),
        # Hardpoints
        _hardpoint([0.15, -0.08, -0.22], "weapon", "wpn_1"),
        _hardpoint([0.15, -0.08, 0.22], "weapon", "wpn_2"),
        _hardpoint([0.0, -0.08, 0], "shield", "shield_1"),
    ],
}

# ── SENTINEL CORVETTE (T3 Military) ───────────────────────────────────────────
SHIP_GEOMETRIES["sentinel_corvette"] = {
    "name": "Sentinel Corvette", "role": "military", "tier": 3,
    "bounds": {"length": 4.5, "height": 1.0, "width": 1.2},
    "components": [
        # Twin engines
        _cyl([-1.8, 0, 0.22], 0.13, 0.16, 0.45, "engine"),
        _cyl([-1.8, 0, -0.22], 0.13, 0.16, 0.45, "engine"),
        _cone([-2.1, 0, 0.22], 0.1, 0.15, "engine"),
        _cone([-2.1, 0, -0.22], 0.1, 0.15, "engine"),
        # Spine
        _spine([-1.4, 0, 0], 0.2, 0.13, 0.17),
        # Modular hull (3 sections)
        _pod([-1.0, 0, 0], 0.5, 0.32, 0.5, "hull"),
        _spine([-0.65, 0, 0], 0.1, 0.1, 0.14),
        _pod([-0.3, 0, 0], 0.55, 0.35, 0.5, "hull"),
        _spine([0.05, 0, 0], 0.1, 0.1, 0.14),
        _pod([0.35, 0, 0], 0.45, 0.3, 0.45, "hull"),
        # Spine to bridge
        _spine([0.68, 0, 0], 0.12, 0.1, 0.13),
        # Bridge (angular for military)
        _bridge([0.9, 0, 0], scale=0.55),
        # Hardpoints
        _hardpoint([-1.0, 0.18, 0], "weapon", "wpn_1"),
        _hardpoint([-0.3, 0.18, 0], "weapon", "wpn_2"),
        _hardpoint([0.35, 0.16, 0], "weapon", "wpn_3"),
        _hardpoint([-0.65, -0.18, -0.26], "shield", "shield_1"),
        _hardpoint([-0.65, -0.18, 0.26], "shield", "shield_2"),
        _hardpoint([0.35, 0.16, 0.23], "utility", "util_1"),
    ],
}

# ── WARDEN FRIGATE (T3 Military) ──────────────────────────────────────────────
SHIP_GEOMETRIES["warden_frigate"] = {
    "name": "Warden Frigate", "role": "military", "tier": 3,
    "bounds": {"length": 5.5, "height": 1.5, "width": 1.4},
    "components": [
        # Quad engines
        _cyl([-2.5, 0.2, 0.15], 0.12, 0.15, 0.5, "engine"),
        _cyl([-2.5, 0.2, -0.15], 0.12, 0.15, 0.5, "engine"),
        _cyl([-2.5, -0.2, 0.15], 0.12, 0.15, 0.5, "engine"),
        _cyl([-2.5, -0.2, -0.15], 0.12, 0.15, 0.5, "engine"),
        _cone([-2.82, 0.2, 0.15], 0.09, 0.14, "engine"),
        _cone([-2.82, 0.2, -0.15], 0.09, 0.14, "engine"),
        _cone([-2.82, -0.2, 0.15], 0.09, 0.14, "engine"),
        _cone([-2.82, -0.2, -0.15], 0.09, 0.14, "engine"),
        # Engine frame
        _box([-2.5, 0, 0], 0.1, 0.55, 0.08, "hull"),
        _box([-2.5, 0.2, 0], 0.1, 0.08, 0.45, "hull"),
        _box([-2.5, -0.2, 0], 0.1, 0.08, 0.45, "hull"),
        # Heavy spine
        _spine([-2.0, 0, 0], 0.3, 0.18, 0.22),
        # Modular armored hull (3 sections)
        _pod([-1.4, 0, 0], 0.6, 0.45, 0.55, "hull"),
        _spine([-1.0, 0, 0], 0.12, 0.14, 0.18),
        _pod([-0.6, 0, 0], 0.7, 0.5, 0.6, "hull"),
        _spine([-0.15, 0, 0], 0.12, 0.14, 0.18),
        _pod([0.25, 0, 0], 0.55, 0.42, 0.5, "hull"),
        # Spine to bridge
        _spine([0.65, 0, 0], 0.15, 0.12, 0.16),
        # Bridge (dome for large warship)
        *_bridge_dome([0.95, 0, 0], scale=0.6),
        # Weapon turrets (4)
        _hardpoint([-1.4, 0.25, 0], "weapon", "wpn_1"),
        _hardpoint([-0.6, 0.28, 0], "weapon", "wpn_2"),
        _hardpoint([-1.4, -0.25, 0], "weapon", "wpn_3"),
        _hardpoint([-0.6, -0.28, 0], "weapon", "wpn_4"),
        # Shield emitters (3)
        _hardpoint([-1.1, -0.24, -0.28], "shield", "shield_1"),
        _hardpoint([-0.3, -0.22, -0.26], "shield", "shield_2"),
        _hardpoint([-0.3, -0.22, 0.26], "shield", "shield_3"),
        # Utility
        _hardpoint([0.25, 0.22, 0.26], "utility", "util_1"),
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

def get_ship_geometry(class_id: str) -> dict | None:
    return SHIP_GEOMETRIES.get(class_id)

def get_all_ship_geometries() -> dict:
    return SHIP_GEOMETRIES
