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
        _wedge([1.45, 0, 0], [[0,-0.18],[0.4,-0.1],[0.5,0],[0.4,0.1],[0,-0.18]], 0.22, "hull", [-1.5708,0,0]),
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
        _wedge([2.3, 0, 0], [[0,-0.2],[0.45,-0.12],[0.55,0],[0.45,0.12],[0,-0.2]], 0.28, "hull", [-1.5708,0,0]),
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
    "bounds": {"length": 6.5, "height": 1.8, "width": 1.8},
    "components": [
        # Quad engines in frame
        _cyl([-3.0, 0.3, 0.3], 0.18, 0.22, 0.5, "engine"),
        _cyl([-3.0, 0.3, -0.3], 0.18, 0.22, 0.5, "engine"),
        _cyl([-3.0, -0.3, 0.3], 0.18, 0.22, 0.5, "engine"),
        _cyl([-3.0, -0.3, -0.3], 0.18, 0.22, 0.5, "engine"),
        _cone([-3.35, 0.3, 0.3], 0.14, 0.2, "engine"),
        _cone([-3.35, 0.3, -0.3], 0.14, 0.2, "engine"),
        _cone([-3.35, -0.3, 0.3], 0.14, 0.2, "engine"),
        _cone([-3.35, -0.3, -0.3], 0.14, 0.2, "engine"),
        # Engine frame cross-beams
        _box([-3.0, 0.35, 0], 0.08, 0.08, 0.8, "hull"),
        _box([-3.0, -0.35, 0], 0.08, 0.08, 0.8, "hull"),
        _box([-3.0, 0, 0], 0.08, 0.8, 0.08, "hull"),
        # Spine A
        _spine([-2.5, 0, 0], 0.35, 0.2, 0.25),
        # Cargo array (4 pods 2x2 + central spine + braces)
        _pod([-1.0, 0.32, -0.35], 1.5, 0.45, 0.55, "cargo"),
        _pod([-1.0, 0.32, 0.35], 1.5, 0.45, 0.55, "cargo"),
        _pod([-1.0, -0.32, -0.35], 1.5, 0.45, 0.55, "cargo"),
        _pod([-1.0, -0.32, 0.35], 1.5, 0.45, 0.55, "cargo"),
        _pod([-1.0, 0, 0], 1.8, 0.15, 0.15, "hull"),  # central spine
        _box([-1.4, 0, 0.35], 0.06, 0.5, 0.06, "hull"),
        _box([-1.4, 0, -0.35], 0.06, 0.5, 0.06, "hull"),
        _box([-0.6, 0, 0.35], 0.06, 0.5, 0.06, "hull"),
        _box([-0.6, 0, -0.35], 0.06, 0.5, 0.06, "hull"),
        # Spine B
        _spine([0.1, 0, 0], 0.3, 0.12, 0.16),
        # Bridge module
        _pod([0.45, 0.05, 0], 0.3, 0.28, 0.35, "hull"),
        _wedge([0.72, 0.05, 0], [[0,-0.14],[0.25,-0.08],[0.3,0],[0.25,0.08],[0,-0.14]], 0.22, "hull", [-1.5708,0,0]),
        _box([0.5, 0.22, 0], 0.12, 0.06, 0.1, "hull"),  # sensor housing
        # Hardpoints
        _hardpoint([-1.3, 0.58, 0], "defense", "turret_1"),
        _hardpoint([-0.7, 0.58, 0], "defense", "turret_2"),
        _hardpoint([-1.0, -0.58, -0.35], "utility", "util_1"),
        _hardpoint([-1.0, -0.58, 0.35], "utility", "util_2"),
        _hardpoint([-1.0, 0.58, -0.35], "utility", "util_3"),
        _hardpoint([-0.3, -0.58, 0], "industrial", "ind_1"),
        _hardpoint([0.0, -0.58, 0], "industrial", "ind_2"),
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
        # Narrow fuselage (2 small pods)
        _pod([-0.6, 0, 0], 0.45, 0.22, 0.35, "hull"),
        _spine([-0.3, 0, 0], 0.08, 0.08, 0.11),
        _pod([0.0, 0, 0], 0.4, 0.22, 0.35, "hull"),
        # Underslung cargo pod
        _pod([-0.3, -0.2, 0], 0.5, 0.15, 0.3, "cargo"),
        # Spine to cockpit
        _spine([0.28, 0, 0], 0.12, 0.08, 0.11),
        # Cockpit
        _wedge([0.55, 0, 0], [[0,-0.12],[0.3,-0.07],[0.38,0],[0.3,0.07],[0,-0.12]], 0.18, "hull", [-1.5708,0,0]),
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
        _wedge([1.65, 0.05, 0], [[0,-0.16],[0.35,-0.1],[0.42,0],[0.35,0.1],[0,-0.16]], 0.25, "hull", [-1.5708,0,0]),
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
        _wedge([0.55, 0, 0], [[0,-0.16],[0.3,-0.1],[0.38,0],[0.3,0.1],[0,-0.16]], 0.3, "hull", [-1.5708,0,0]),
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
        _spine([-1.4, 0, -0.1], 0.25, 0.16, 0.2),
        # Central core (processing)
        _pod([-0.9, 0, 0], 0.6, 0.45, 0.5, "hull"),
        # Ore bay (port side, lateral)
        _spine([-0.9, -0.05, -0.4], 0.15, 0.1, 0.14),  # lateral connector
        _pod([-0.9, -0.05, -0.75], 0.8, 0.3, 0.5, "cargo"),
        _pod([-0.9, -0.3, -0.65], 0.6, 0.25, 0.4, "cargo"),  # stacked second bay
        # Arm mount (forward)
        _spine([-0.45, 0, 0], 0.2, 0.14, 0.18),
        _pod([-0.1, 0, 0.15], 0.2, 0.5, 0.15, "hull"),  # arm plate
        # Mining arms (3)
        _cyl([-0.1, 0, 0.25], 0.04, 0.05, 0.7, "mining", [0, -0.1, 1.5708]),
        _sphere([0.25, 0, 0.3], 0.07, False, "mining"),
        _cyl([-0.1, 0.2, 0.25], 0.04, 0.05, 0.65, "mining", [0, -0.2, 1.5708]),
        _sphere([0.22, 0.2, 0.35], 0.07, False, "mining"),
        _cyl([-0.1, -0.2, 0.25], 0.04, 0.05, 0.65, "mining", [0, 0, 1.5708]),
        _sphere([0.22, -0.2, 0.28], 0.07, False, "mining"),
        # Hardpoints
        _hardpoint([-0.9, 0.24, 0.1], "utility", "scan_1"),
        _hardpoint([-0.9, 0.24, -0.1], "utility", "scan_2"),
        _hardpoint([-0.7, -0.24, 0.1], "defense", "def_1"),
        _hardpoint([-0.1, 0, 0.25], "mining", "mine_1"),
        _hardpoint([-0.1, 0.2, 0.25], "mining", "mine_2"),
        _hardpoint([-0.1, -0.2, 0.25], "mining", "mine_3"),
    ],
}



# ── PROSPECT SKIFF (T1 Miner) ─────────────────────────────────────────────────
SHIP_GEOMETRIES["prospect_skiff"] = {
    "name": "Prospect Skiff", "role": "miner", "tier": 1,
    "bounds": {"length": 3.0, "height": 0.6, "width": 0.8},
    "components": [
        _cyl([-1.1, 0, 0], 0.1, 0.13, 0.35, "engine"),
        _cone([-1.35, 0, 0], 0.08, 0.14, "engine"),
        _spine([-0.8, 0, 0], 0.15, 0.09, 0.12),
        _pod([-0.4, 0, 0], 0.5, 0.25, 0.35, "hull"),
        _pod([-0.4, -0.18, 0], 0.4, 0.14, 0.28, "cargo"),
        _cyl([0.1, 0, 0.1], 0.03, 0.04, 0.4, "mining", [0, -0.1, 1.5708]),
        _sphere([0.32, 0, 0.12], 0.05, False, "mining"),
        _hardpoint([0.1, 0, 0.1], "mining", "mine_1"),
        _hardpoint([-0.4, 0.14, 0], "utility", "util_1"),
    ],
}

# ── ROCK HOPPER (T1 Miner) ────────────────────────────────────────────────────
SHIP_GEOMETRIES["rock_hopper"] = {
    "name": "Rock Hopper", "role": "miner", "tier": 1,
    "bounds": {"length": 3.2, "height": 0.7, "width": 1.0},
    "components": [
        _cyl([-1.2, 0, 0], 0.12, 0.15, 0.4, "engine"),
        _cone([-1.48, 0, 0], 0.1, 0.16, "engine"),
        _spine([-0.85, 0, 0], 0.15, 0.1, 0.13),
        # Angular body
        _pod([-0.4, 0, 0], 0.6, 0.28, 0.45, "hull"),
        _pod([-0.4, -0.2, 0], 0.45, 0.14, 0.35, "cargo"),
        # Mining arm
        _cyl([0.15, 0, 0.12], 0.035, 0.04, 0.4, "mining", [0, -0.08, 1.5708]),
        _sphere([0.37, 0, 0.14], 0.055, False, "mining"),
        # Hardpoints
        _hardpoint([0.15, 0, 0.12], "mining", "mine_1"),
        _hardpoint([-0.4, 0.16, 0.23], "utility", "util_1"),
        _hardpoint([-0.1, 0.16, -0.23], "defense", "def_1"),
    ],
}

# ── STRIP MINER (T2 Miner) ────────────────────────────────────────────────────
SHIP_GEOMETRIES["strip_miner"] = {
    "name": "Strip Miner", "role": "miner", "tier": 2,
    "bounds": {"length": 4.0, "height": 1.0, "width": 1.2},
    "components": [
        # Dual engine
        _cyl([-1.7, 0.15, 0], 0.14, 0.17, 0.45, "engine"),
        _cyl([-1.7, -0.15, 0], 0.14, 0.17, 0.45, "engine"),
        _cone([-2.0, 0.15, 0], 0.1, 0.16, "engine"),
        _cone([-2.0, -0.15, 0], 0.1, 0.16, "engine"),
        _spine([-1.3, 0, 0], 0.2, 0.12, 0.16),
        # Central hull
        _pod([-0.8, 0, 0], 0.7, 0.38, 0.5, "hull"),
        # Ore bay (below)
        _pod([-0.8, -0.3, 0], 0.55, 0.2, 0.4, "cargo"),
        # Arm mount
        _pod([-0.25, 0, 0.1], 0.15, 0.35, 0.12, "hull"),
        # Dual mining arms
        _cyl([-0.1, 0.12, 0.15], 0.035, 0.04, 0.5, "mining", [0, -0.05, 1.5708]),
        _sphere([0.16, 0.12, 0.17], 0.06, False, "mining"),
        _cyl([-0.1, -0.12, 0.15], 0.035, 0.04, 0.5, "mining", [0, 0.05, 1.5708]),
        _sphere([0.16, -0.12, 0.13], 0.06, False, "mining"),
        # Hardpoints
        _hardpoint([-0.1, 0.12, 0.15], "mining", "mine_1"),
        _hardpoint([-0.1, -0.12, 0.15], "mining", "mine_2"),
        _hardpoint([-0.8, 0.2, 0.26], "utility", "util_1"),
        _hardpoint([-0.5, 0.2, -0.26], "defense", "def_1"),
    ],
}

# ── EXCAVATOR (T2 Miner) ──────────────────────────────────────────────────────
SHIP_GEOMETRIES["excavator"] = {
    "name": "Excavator", "role": "miner", "tier": 2,
    "bounds": {"length": 4.2, "height": 1.1, "width": 1.3},
    "components": [
        # Wide engine
        _cyl([-1.8, 0, 0], 0.2, 0.24, 0.5, "engine"),
        _cone([-2.12, 0, 0], 0.15, 0.2, "engine"),
        _spine([-1.35, 0, 0], 0.2, 0.14, 0.18),
        # Processing core
        _pod([-0.8, 0, 0], 0.7, 0.42, 0.5, "hull"),
        # Scanner array (top)
        _box([-0.8, 0.3, 0], 0.2, 0.12, 0.18, "hull"),
        _sphere([-0.8, 0.38, 0], 0.06, False, "hull"),
        # Ore bay (below)
        _pod([-0.8, -0.3, 0], 0.55, 0.2, 0.4, "cargo"),
        # Arm mount
        _pod([-0.25, 0, 0.1], 0.16, 0.4, 0.14, "hull"),
        # Dual arms
        _cyl([-0.05, 0.12, 0.18], 0.04, 0.045, 0.55, "mining", [0, -0.06, 1.5708]),
        _sphere([0.24, 0.12, 0.21], 0.065, False, "mining"),
        _cyl([-0.05, -0.12, 0.18], 0.04, 0.045, 0.55, "mining", [0, 0.06, 1.5708]),
        _sphere([0.24, -0.12, 0.15], 0.065, False, "mining"),
        # Hardpoints
        _hardpoint([-0.05, 0.12, 0.18], "mining", "mine_1"),
        _hardpoint([-0.05, -0.12, 0.18], "mining", "mine_2"),
        _hardpoint([-0.8, 0.3, 0.15], "utility", "util_1"),
        _hardpoint([-0.8, 0.3, -0.15], "utility", "util_2"),
        _hardpoint([-0.5, -0.22, -0.26], "defense", "def_1"),
    ],
}

# ── VIPER INTERCEPTOR (T2 Military) ───────────────────────────────────────────
SHIP_GEOMETRIES["viper_interceptor"] = {
    "name": "Viper Interceptor", "role": "military", "tier": 2,
    "bounds": {"length": 2.8, "height": 0.5, "width": 1.4},
    "components": [
        # Angular fuselage
        _wedge([0, 0, 0], [[0,-0.08],[0.16,-0.06],[0.12,0.08],[0,0.14],[-0.12,0.08],[-0.16,-0.06]], 1.1, "hull", [0, 1.5708, 0]),
        # Nose
        _wedge([0.75, 0.01, 0], [[0,-0.06],[0.12,-0.04],[0.08,0.06],[0,0.1],[-0.08,0.06],[-0.12,-0.04]], 0.4, "hull", [0, 1.5708, 0]),
        _cone([1.05, 0.01, 0], 0.03, 0.15, "hull", [0, 0, -1.5708]),
        # Engines (rectangular, integrated)
        _box([-0.6, -0.02, -0.18], 0.25, 0.1, 0.12, "engine"),
        _box([-0.6, -0.02, 0.18], 0.25, 0.1, 0.12, "engine"),
        _box([-0.75, -0.02, -0.18], 0.04, 0.12, 0.14, "engine"),
        _box([-0.75, -0.02, 0.18], 0.04, 0.12, 0.14, "engine"),
        # Wing pylons
        _box([-0.1, -0.04, -0.35], 0.5, 0.025, 0.04, "hull", [0, 0.3, 0]),
        _box([-0.1, -0.04, 0.35], 0.5, 0.025, 0.04, "hull", [0, -0.3, 0]),
        # Weapon pods (conformal under wings)
        _box([0.2, -0.09, -0.26], 0.18, 0.035, 0.06, "weapon"),
        _box([0.2, -0.09, 0.26], 0.18, 0.035, 0.06, "weapon"),
        # Hardpoints
        _hardpoint([0.2, -0.09, -0.26], "weapon", "wpn_1"),
        _hardpoint([0.2, -0.09, 0.26], "weapon", "wpn_2"),
        _hardpoint([0.0, -0.09, 0], "shield", "shield_1"),
    ],
}

# ── SENTINEL CORVETTE (T3 Military) ───────────────────────────────────────────
SHIP_GEOMETRIES["sentinel_corvette"] = {
    "name": "Sentinel Corvette", "role": "military", "tier": 3,
    "bounds": {"length": 4.5, "height": 1.0, "width": 1.2},
    "components": [
        # Twin engines
        _cyl([-1.8, 0, 0.25], 0.15, 0.18, 0.5, "engine"),
        _cyl([-1.8, 0, -0.25], 0.15, 0.18, 0.5, "engine"),
        _cone([-2.12, 0, 0.25], 0.12, 0.18, "engine"),
        _cone([-2.12, 0, -0.25], 0.12, 0.18, "engine"),
        # Armored hull
        _pod([-0.7, 0, 0], 1.6, 0.4, 0.6, "hull"),
        _spine([-1.4, 0, 0], 0.2, 0.14, 0.18),
        # Bridge
        _pod([0.3, 0, 0], 0.35, 0.3, 0.4, "hull"),
        _wedge([0.65, 0, 0], [[0,-0.14],[0.3,-0.08],[0.35,0],[0.3,0.08],[0,-0.14]], 0.25, "hull", [-1.5708,0,0]),
        # Hardpoints (3 weapon, 2 shield, 1 utility)
        _hardpoint([-1.0, 0.22, 0], "weapon", "wpn_1"),
        _hardpoint([-0.5, 0.22, 0], "weapon", "wpn_2"),
        _hardpoint([0.0, 0.22, 0], "weapon", "wpn_3"),
        _hardpoint([-0.8, -0.22, -0.3], "shield", "shield_1"),
        _hardpoint([-0.8, -0.22, 0.3], "shield", "shield_2"),
        _hardpoint([0.3, 0.18, 0.2], "utility", "util_1"),
    ],
}

# ── WARDEN FRIGATE (T3 Military) ──────────────────────────────────────────────
SHIP_GEOMETRIES["warden_frigate"] = {
    "name": "Warden Frigate", "role": "military", "tier": 3,
    "bounds": {"length": 5.5, "height": 1.5, "width": 1.4},
    "components": [
        # Quad engine in armored nacelle
        _pod([-2.5, 0, 0], 0.5, 0.9, 0.6, "hull"),  # nacelle frame
        _cyl([-2.5, 0.25, 0.15], 0.12, 0.15, 0.55, "engine"),
        _cyl([-2.5, 0.25, -0.15], 0.12, 0.15, 0.55, "engine"),
        _cyl([-2.5, -0.25, 0.15], 0.12, 0.15, 0.55, "engine"),
        _cyl([-2.5, -0.25, -0.15], 0.12, 0.15, 0.55, "engine"),
        _cone([-2.85, 0.25, 0.15], 0.1, 0.16, "engine"),
        _cone([-2.85, 0.25, -0.15], 0.1, 0.16, "engine"),
        _cone([-2.85, -0.25, 0.15], 0.1, 0.16, "engine"),
        _cone([-2.85, -0.25, -0.15], 0.1, 0.16, "engine"),
        # Heavy spine
        _spine([-2.0, 0, 0], 0.3, 0.2, 0.25),
        # Main hull (beveled, heavy)
        _pod([-1.0, 0, 0], 1.8, 0.6, 0.65, "hull"),
        # Spine to bridge
        _spine([0.05, 0, 0], 0.2, 0.14, 0.18),
        # Armored bridge
        _pod([0.4, 0, 0], 0.4, 0.4, 0.45, "hull"),
        _wedge([0.8, 0, 0], [[0,-0.18],[0.3,-0.1],[0.36,0],[0.3,0.1],[0,-0.18]], 0.3, "hull", [-1.5708,0,0]),
        # Weapon turrets on pylons (4)
        _hardpoint([-1.4, 0.35, 0], "weapon", "wpn_1"),
        _hardpoint([-0.7, 0.35, 0], "weapon", "wpn_2"),
        _hardpoint([-1.4, -0.35, 0], "weapon", "wpn_3"),
        _hardpoint([-0.7, -0.35, 0], "weapon", "wpn_4"),
        # Shield emitters (3)
        _hardpoint([-1.2, -0.32, -0.33], "shield", "shield_1"),
        _hardpoint([-0.5, -0.32, -0.33], "shield", "shield_2"),
        _hardpoint([-0.5, -0.32, 0.33], "shield", "shield_3"),
        # Utility
        _hardpoint([0.4, 0.22, 0.23], "utility", "util_1"),
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

def get_ship_geometry(class_id: str) -> dict | None:
    return SHIP_GEOMETRIES.get(class_id)

def get_all_ship_geometries() -> dict:
    return SHIP_GEOMETRIES
