"""
Ship generator - Attachment Point system.

Each component defines attachment points (sockets). The generator starts with
a core hull, then recursively fills attachment points with appropriate components.
Nothing floats because everything grows from a connection.
"""
import math
import random
import copy

# ── Component templates with attachment points ───────────────────────────────
# Each template: {"parts": [...], "attachments": {"name": {"pos": [x,y,z], "accepts": [...]}}}
# "accepts" = list of component roles that can snap here

def _hull_angular(s):
    return {
        "parts": [
            {"type": "pod", "pos": [0,0,0], "rot": [0,0,0], "params": {"length": 0.4*s, "height": 0.14*s, "width": 0.22*s}, "material": "hull"},
            {"type": "pod", "pos": [0, 0.06*s, 0], "rot": [0,0,0], "params": {"length": 0.3*s, "height": 0.03*s, "width": 0.12*s}, "material": "hull"},
        ],
        "attachments": {
            "rear": {"pos": [-0.2*s, 0, 0], "accepts": ["engine", "hull"]},
            "front": {"pos": [0.2*s, 0, 0], "accepts": ["bridge", "hull"]},
            "top": {"pos": [0, 0.08*s, 0], "accepts": ["detail"]},
            "left": {"pos": [0, 0, 0.12*s], "accepts": ["wing"]},
            "right": {"pos": [0, 0, -0.12*s], "accepts": ["wing"]},
        }
    }

def _hull_flat(s):
    return {
        "parts": [
            {"type": "pod", "pos": [0,0,0], "rot": [0,0,0], "params": {"length": 0.4*s, "height": 0.08*s, "width": 0.3*s}, "material": "hull"},
            {"type": "box", "pos": [0, -0.035*s, 0], "rot": [0,0,0], "params": {"x": 0.3*s, "y": 0.005*s, "z": 0.22*s}, "material": "hull"},
        ],
        "attachments": {
            "rear": {"pos": [-0.2*s, 0, 0], "accepts": ["engine", "hull"]},
            "front": {"pos": [0.2*s, 0, 0], "accepts": ["bridge", "hull"]},
            "top": {"pos": [0, 0.05*s, 0], "accepts": ["detail"]},
            "left": {"pos": [0, 0, 0.16*s], "accepts": ["wing"]},
            "right": {"pos": [0, 0, -0.16*s], "accepts": ["wing"]},
        }
    }

def _hull_cylinder(s):
    return {
        "parts": [
            {"type": "cylinder", "pos": [0,0,0], "rot": [0,0,0], "params": {"r_top": 0.08*s, "r_bot": 0.1*s, "length": 0.4*s}, "material": "hull"},
            {"type": "torus", "pos": [0.1*s, 0, 0], "rot": [0,0,0], "params": {"radius": 0.1*s, "tube": 0.008*s}, "material": "hull"},
            {"type": "torus", "pos": [-0.1*s, 0, 0], "rot": [0,0,0], "params": {"radius": 0.1*s, "tube": 0.008*s}, "material": "hull"},
        ],
        "attachments": {
            "rear": {"pos": [-0.2*s, 0, 0], "accepts": ["engine", "hull"]},
            "front": {"pos": [0.2*s, 0, 0], "accepts": ["bridge", "hull"]},
            "top": {"pos": [0, 0.1*s, 0], "accepts": ["detail"]},
            "left": {"pos": [0, 0, 0.1*s], "accepts": ["wing"]},
            "right": {"pos": [0, 0, -0.1*s], "accepts": ["wing"]},
        }
    }

def _hull_blocky(s):
    return {
        "parts": [
            {"type": "pod", "pos": [0,0,0], "rot": [0,0,0], "params": {"length": 0.35*s, "height": 0.12*s, "width": 0.22*s}, "material": "hull"},
            {"type": "pod", "pos": [0, 0.05*s, 0], "rot": [0,0,0], "params": {"length": 0.25*s, "height": 0.03*s, "width": 0.18*s}, "material": "hull"},
            {"type": "pod", "pos": [0, -0.05*s, 0], "rot": [0,0,0], "params": {"length": 0.28*s, "height": 0.03*s, "width": 0.2*s}, "material": "hull"},
        ],
        "attachments": {
            "rear": {"pos": [-0.18*s, 0, 0], "accepts": ["engine", "hull"]},
            "front": {"pos": [0.18*s, 0, 0], "accepts": ["bridge", "hull"]},
            "top": {"pos": [0, 0.07*s, 0], "accepts": ["detail"]},
            "left": {"pos": [0, 0, 0.12*s], "accepts": ["wing"]},
            "right": {"pos": [0, 0, -0.12*s], "accepts": ["wing"]},
        }
    }

def _hull_sleek(s):
    """Low, wide, horizontal hull - good for fighters/destroyers"""
    return {
        "parts": [
            {"type": "pod", "pos": [0,0,0], "rot": [0,0,0], "params": {"length": 0.45*s, "height": 0.06*s, "width": 0.28*s}, "material": "hull"},
            {"type": "pod", "pos": [0.08*s, 0, 0], "rot": [0,0,0], "params": {"length": 0.2*s, "height": 0.04*s, "width": 0.18*s}, "material": "hull"},
        ],
        "attachments": {
            "rear": {"pos": [-0.22*s, 0, 0], "accepts": ["engine", "hull"]},
            "front": {"pos": [0.22*s, 0, 0], "accepts": ["bridge"]},
            "top": {"pos": [0, 0.04*s, 0], "accepts": ["detail"]},
            "left": {"pos": [0, 0, 0.15*s], "accepts": ["wing"]},
            "right": {"pos": [0, 0, -0.15*s], "accepts": ["wing"]},
        }
    }

def _hull_wedge(s):
    """Tapered wedge hull - aggressive, horizontal"""
    return {
        "parts": [
            {"type": "pod", "pos": [-0.05*s,0,0], "rot": [0,0,0], "params": {"length": 0.35*s, "height": 0.1*s, "width": 0.25*s}, "material": "hull"},
            {"type": "pod", "pos": [0.12*s,0,0], "rot": [0,0,0], "params": {"length": 0.18*s, "height": 0.06*s, "width": 0.15*s}, "material": "hull"},
            {"type": "pod", "pos": [-0.05*s, -0.04*s, 0], "rot": [0,0,0], "params": {"length": 0.25*s, "height": 0.03*s, "width": 0.2*s}, "material": "hull"},
        ],
        "attachments": {
            "rear": {"pos": [-0.22*s, 0, 0], "accepts": ["engine", "hull"]},
            "front": {"pos": [0.2*s, 0, 0], "accepts": ["bridge"]},
            "top": {"pos": [0, 0.06*s, 0], "accepts": ["detail"]},
            "left": {"pos": [-0.05*s, 0, 0.13*s], "accepts": ["wing"]},
            "right": {"pos": [-0.05*s, 0, -0.13*s], "accepts": ["wing"]},
        }
    }

def _hull_fighter_needle(s):
    """Long narrow needle - fast interceptor look"""
    return {
        "parts": [
            {"type": "pod", "pos": [0,0,0], "rot": [0,0,0], "params": {"length": 0.5*s, "height": 0.04*s, "width": 0.15*s}, "material": "hull"},
            {"type": "pod", "pos": [0.15*s,0,0], "rot": [0,0,0], "params": {"length": 0.2*s, "height": 0.03*s, "width": 0.08*s}, "material": "hull"},
        ],
        "attachments": {
            "rear": {"pos": [-0.25*s, 0, 0], "accepts": ["engine"]},
            "front": {"pos": [0.25*s, 0, 0], "accepts": ["bridge"]},
            "top": {"pos": [0, 0.03*s, 0], "accepts": ["detail"]},
            "left": {"pos": [0, 0, 0.07*s], "accepts": ["wing"]},
            "right": {"pos": [0, 0, -0.07*s], "accepts": ["wing"]},
        }
    }

def _hull_fighter_disc(s):
    """Wide flat disc - flying saucer / stealth bomber vibe"""
    return {
        "parts": [
            {"type": "pod", "pos": [0,0,0], "rot": [0,0,0], "params": {"length": 0.3*s, "height": 0.04*s, "width": 0.35*s}, "material": "hull"},
            {"type": "pod", "pos": [0,0.02*s,0], "rot": [0,0,0], "params": {"length": 0.18*s, "height": 0.03*s, "width": 0.2*s}, "material": "hull"},
        ],
        "attachments": {
            "rear": {"pos": [-0.15*s, 0, 0], "accepts": ["engine"]},
            "front": {"pos": [0.15*s, 0, 0], "accepts": ["bridge"]},
            "top": {"pos": [0, 0.04*s, 0], "accepts": ["detail"]},
            "left": {"pos": [0, 0, 0.18*s], "accepts": ["wing"]},
            "right": {"pos": [0, 0, -0.18*s], "accepts": ["wing"]},
        }
    }

def _hull_fighter_delta(s):
    """Delta/arrow shape - wide rear, narrow front"""
    return {
        "parts": [
            {"type": "pod", "pos": [-0.05*s,0,0], "rot": [0,0,0], "params": {"length": 0.25*s, "height": 0.06*s, "width": 0.3*s}, "material": "hull"},
            {"type": "pod", "pos": [0.1*s,0,0], "rot": [0,0,0], "params": {"length": 0.2*s, "height": 0.04*s, "width": 0.14*s}, "material": "hull"},
            {"type": "pod", "pos": [0.2*s,0,0], "rot": [0,0,0], "params": {"length": 0.1*s, "height": 0.03*s, "width": 0.06*s}, "material": "hull"},
        ],
        "attachments": {
            "rear": {"pos": [-0.18*s, 0, 0], "accepts": ["engine"]},
            "front": {"pos": [0.25*s, 0, 0], "accepts": ["bridge"]},
            "top": {"pos": [0, 0.04*s, 0], "accepts": ["detail"]},
            "left": {"pos": [-0.05*s, 0, 0.16*s], "accepts": ["wing"]},
            "right": {"pos": [-0.05*s, 0, -0.16*s], "accepts": ["wing"]},
        }
    }

def _hull_fighter_twin(s):
    """Twin-boom fuselage with center cockpit area"""
    return {
        "parts": [
            {"type": "pod", "pos": [0,0,0.08*s], "rot": [0,0,0], "params": {"length": 0.35*s, "height": 0.05*s, "width": 0.06*s}, "material": "hull"},
            {"type": "pod", "pos": [0,0,-0.08*s], "rot": [0,0,0], "params": {"length": 0.35*s, "height": 0.05*s, "width": 0.06*s}, "material": "hull"},
            {"type": "pod", "pos": [0.05*s,0,0], "rot": [0,0,0], "params": {"length": 0.15*s, "height": 0.05*s, "width": 0.14*s}, "material": "hull"},
        ],
        "attachments": {
            "rear": {"pos": [-0.18*s, 0, 0], "accepts": ["engine"]},
            "front": {"pos": [0.18*s, 0, 0], "accepts": ["bridge"]},
            "top": {"pos": [0.05*s, 0.03*s, 0], "accepts": ["detail"]},
            "left": {"pos": [0, 0, 0.12*s], "accepts": ["wing"]},
            "right": {"pos": [0, 0, -0.12*s], "accepts": ["wing"]},
        }
    }

def _hull_tapered(s):
    return {
        "parts": [
            {"type": "pod", "pos": [-0.05*s,0,0], "rot": [0,0,0], "params": {"length": 0.3*s, "height": 0.14*s, "width": 0.2*s}, "material": "hull"},
            {"type": "pod", "pos": [0.12*s,0,0], "rot": [0,0,0], "params": {"length": 0.15*s, "height": 0.09*s, "width": 0.13*s}, "material": "hull"},
        ],
        "attachments": {
            "rear": {"pos": [-0.2*s, 0, 0], "accepts": ["engine", "hull"]},
            "front": {"pos": [0.2*s, 0, 0], "accepts": ["bridge"]},
            "top": {"pos": [0, 0.08*s, 0], "accepts": ["detail"]},
            "left": {"pos": [-0.05*s, 0, 0.11*s], "accepts": ["wing"]},
            "right": {"pos": [-0.05*s, 0, -0.11*s], "accepts": ["wing"]},
        }
    }

# ── Engines (terminal - no outward attachments) ──────────────────────────────

def _engine_nacelle(s):
    return {
        "parts": [
            {"type": "cylinder", "pos": [0,0,0], "rot": [0,0,0], "params": {"r_top": 0.025*s, "r_bot": 0.045*s, "length": 0.2*s}, "material": "engine"},
            {"type": "cylinder", "pos": [-0.12*s,0,0], "rot": [0,0,0], "params": {"r_top": 0.045*s, "r_bot": 0.055*s, "length": 0.04*s}, "material": "engine"},
        ],
        "attachments": {}
    }

def _engine_twin(s):
    return {
        "parts": [
            {"type": "cylinder", "pos": [0,0,0.04*s], "rot": [0,0,0], "params": {"r_top": 0.02*s, "r_bot": 0.035*s, "length": 0.18*s}, "material": "engine"},
            {"type": "cylinder", "pos": [0,0,-0.04*s], "rot": [0,0,0], "params": {"r_top": 0.02*s, "r_bot": 0.035*s, "length": 0.18*s}, "material": "engine"},
            {"type": "box", "pos": [0.07*s,0,0], "rot": [0,0,0], "params": {"x": 0.03*s, "y": 0.04*s, "z": 0.1*s}, "material": "hull"},
        ],
        "attachments": {}
    }

def _engine_cluster(s):
    parts = []
    for i in range(3):
        a = (math.pi*2*i)/3
        y, z = math.sin(a)*0.035*s, math.cos(a)*0.035*s
        parts.append({"type": "cylinder", "pos": [0,y,z], "rot": [0,0,0], "params": {"r_top": 0.015*s, "r_bot": 0.028*s, "length": 0.12*s}, "material": "engine"})
    parts.append({"type": "cylinder", "pos": [0.05*s,0,0], "rot": [0,0,0], "params": {"r_top": 0.04*s, "r_bot": 0.04*s, "length": 0.04*s}, "material": "hull"})
    return {"parts": parts, "attachments": {}}

def _engine_big(s):
    return {
        "parts": [
            {"type": "cylinder", "pos": [0,0,0], "rot": [0,0,0], "params": {"r_top": 0.05*s, "r_bot": 0.08*s, "length": 0.22*s}, "material": "engine"},
            {"type": "cylinder", "pos": [-0.13*s,0,0], "rot": [0,0,0], "params": {"r_top": 0.08*s, "r_bot": 0.09*s, "length": 0.03*s}, "material": "hull"},
        ],
        "attachments": {}
    }

# ── Bridges (terminal forward) ───────────────────────────────────────────────

def _bridge_tower(s):
    return {
        "parts": [
            {"type": "pod", "pos": [0,0,0], "rot": [0,0,0], "params": {"length": 0.1*s, "height": 0.06*s, "width": 0.1*s}, "material": "hull"},
            {"type": "pod", "pos": [0,0.05*s,0], "rot": [0,0,0], "params": {"length": 0.07*s, "height": 0.06*s, "width": 0.07*s}, "material": "hull"},
            {"type": "box", "pos": [0.035*s,0.065*s,0], "rot": [0,0,0], "params": {"x": 0.004*s, "y": 0.015*s, "z": 0.06*s}, "material": "hull"},
        ],
        "attachments": {"top": {"pos": [0, 0.08*s, 0], "accepts": ["detail"]}}
    }

def _bridge_cockpit(s):
    return {
        "parts": [
            {"type": "pod", "pos": [0,0,0], "rot": [0,0,0], "params": {"length": 0.14*s, "height": 0.03*s, "width": 0.08*s}, "material": "hull"},
            {"type": "pod", "pos": [0.05*s,0,0], "rot": [0,0,0], "params": {"length": 0.06*s, "height": 0.02*s, "width": 0.05*s}, "material": "hull"},
            {"type": "box", "pos": [0.04*s,0.015*s,0], "rot": [0,0,0], "params": {"x": 0.05*s, "y": 0.005*s, "z": 0.05*s}, "material": "hull"},
        ],
        "attachments": {}
    }

def _bridge_flat(s):
    return {
        "parts": [
            {"type": "pod", "pos": [0,0,0], "rot": [0,0,0], "params": {"length": 0.12*s, "height": 0.025*s, "width": 0.14*s}, "material": "hull"},
            {"type": "box", "pos": [0.05*s,0.013*s,0], "rot": [0,0,0], "params": {"x": 0.004*s, "y": 0.008*s, "z": 0.1*s}, "material": "hull"},
        ],
        "attachments": {}
    }

# ── Wings (terminal lateral) ─────────────────────────────────────────────────

def _wing_radiator(s):
    return {
        "parts": [
            {"type": "box", "pos": [0,0,0.1*s], "rot": [0,0,0], "params": {"x": 0.15*s, "y": 0.003*s, "z": 0.18*s}, "material": "hull"},
            {"type": "box", "pos": [0,0,0.01*s], "rot": [0,0,0], "params": {"x": 0.02*s, "y": 0.02*s, "z": 0.02*s}, "material": "hull"},
        ],
        "attachments": {}
    }

def _wing_fin(s):
    return {
        "parts": [
            {"type": "pod", "pos": [0,0.07*s,0], "rot": [0,0,0], "params": {"length": 0.1*s, "height": 0.12*s, "width": 0.01*s}, "material": "hull"},
        ],
        "attachments": {}
    }

def _wing_stub(s):
    return {
        "parts": [
            {"type": "pod", "pos": [0,0,0.06*s], "rot": [0,0,0], "params": {"length": 0.1*s, "height": 0.02*s, "width": 0.1*s}, "material": "hull"},
        ],
        "attachments": {}
    }

def _wing_pylon(s):
    return {
        "parts": [
            {"type": "box", "pos": [0,0,0.04*s], "rot": [0,0,0], "params": {"x": 0.12*s, "y": 0.02*s, "z": 0.08*s}, "material": "hull"},
            {"type": "box", "pos": [0,-0.015*s,0.09*s], "rot": [0,0,0], "params": {"x": 0.04*s, "y": 0.02*s, "z": 0.02*s}, "material": "hull"},
        ],
        "attachments": {}
    }

# ── Details (terminal small components) ──────────────────────────────────────

def _detail_antenna(s):
    return {
        "parts": [
            {"type": "box", "pos": [0,0.03*s,0], "rot": [0,0,0], "params": {"x": 0.008*s, "y": 0.05*s, "z": 0.008*s}, "material": "hull"},
            {"type": "box", "pos": [0,0.05*s,0], "rot": [0,0,0], "params": {"x": 0.03*s, "y": 0.006*s, "z": 0.006*s}, "material": "hull"},
        ],
        "attachments": {}
    }

def _detail_sensor(s):
    return {
        "parts": [
            {"type": "box", "pos": [0,0.02*s,0], "rot": [0,0,0], "params": {"x": 0.04*s, "y": 0.025*s, "z": 0.03*s}, "material": "hull"},
        ],
        "attachments": {}
    }

def _detail_spine(s):
    return {
        "parts": [
            {"type": "spine", "pos": [0,0,0], "params": {"length": 0.08*s, "radius": 0.02*s, "flange_r": 0.03*s}, "material": "hull"},
        ],
        "attachments": {}
    }

# ── Connector (placed between hull sections automatically) ───────────────────

def _connector(s):
    return {
        "parts": [
            {"type": "spine", "pos": [0,0,0], "params": {"length": 0.06*s, "radius": 0.02*s, "flange_r": 0.035*s}, "material": "hull"},
        ],
    }


# ── Component pools by role ──────────────────────────────────────────────────

HULLS = [_hull_angular, _hull_flat, _hull_cylinder, _hull_blocky, _hull_tapered, _hull_sleek, _hull_wedge, _hull_fighter_needle, _hull_fighter_disc, _hull_fighter_delta, _hull_fighter_twin]
# Indices: 0=angular 1=flat 2=cyl 3=blocky 4=tapered 5=sleek 6=wedge 7=needle 8=disc 9=delta 10=twin
ENGINES = [_engine_nacelle, _engine_twin, _engine_cluster, _engine_big]
BRIDGES = [_bridge_tower, _bridge_cockpit, _bridge_flat]
WINGS = [_wing_radiator, _wing_fin, _wing_stub, _wing_pylon]
DETAILS = [_detail_antenna, _detail_sensor, _detail_spine]

ROLE_MAP = {
    "engine": ENGINES,
    "hull": HULLS,
    "bridge": BRIDGES,
    "wing": WINGS,
    "detail": DETAILS,
}

# ── Hull class configs ───────────────────────────────────────────────────────

HULL_CLASSES = {
    "fighter":       {"scale": 0.8, "hull_count": 1, "engine_count": 1, "wing_chance": 0.5, "detail_chance": 0.3, "hull_density": 1},
    "frigate":       {"scale": 1.2, "hull_count": 2, "engine_count": 1, "wing_chance": 0.6, "detail_chance": 0.5, "hull_density": 1},
    "destroyer":     {"scale": 1.6, "hull_count": 2, "engine_count": 2, "wing_chance": 0.7, "detail_chance": 0.6, "hull_density": 2},
    "cruiser":       {"scale": 2.0, "hull_count": 3, "engine_count": 2, "wing_chance": 0.7, "detail_chance": 0.7, "hull_density": 2},
    "battlecruiser": {"scale": 2.5, "hull_count": 3, "engine_count": 2, "wing_chance": 0.8, "detail_chance": 0.8, "hull_density": 3},
    "battleship":    {"scale": 3.0, "hull_count": 4, "engine_count": 3, "wing_chance": 0.9, "detail_chance": 0.9, "hull_density": 3},
    "carrier":       {"scale": 3.5, "hull_count": 4, "engine_count": 2, "wing_chance": 0.6, "detail_chance": 0.7, "hull_density": 4},
    "dreadnought":   {"scale": 4.0, "hull_count": 5, "engine_count": 3, "wing_chance": 0.8, "detail_chance": 0.9, "hull_density": 4},
    "industrial":    {"scale": 1.8, "hull_count": 3, "engine_count": 1, "wing_chance": 0.3, "detail_chance": 0.4, "hull_density": 2},
    "mining_barge":  {"scale": 1.5, "hull_count": 2, "engine_count": 1, "wing_chance": 0.4, "detail_chance": 0.5, "hull_density": 2},
}

FACTION_STYLES = {
    "terran":       {"description": "Military, angular, functional.", "prefer_hull": [0, 4, 6], "prefer_engine": [0, 1], "prefer_bridge": [0]},
    "merchants":    {"description": "Bulky, utilitarian, cargo-first.", "prefer_hull": [1, 3, 2], "prefer_engine": [1, 3], "prefer_bridge": [2]},
    "science":      {"description": "Sleek, rounded, sensor arrays.", "prefer_hull": [2, 5, 4], "prefer_engine": [2, 0], "prefer_bridge": [0, 1]},
    "iron_compact": {"description": "Heavy, armored, brutal.", "prefer_hull": [0, 3, 6], "prefer_engine": [3, 1], "prefer_bridge": [0]},
    "frontier":     {"description": "Kitbashed, mixed, improvised.", "prefer_hull": [1, 3, 5, 6], "prefer_engine": [0, 2], "prefer_bridge": [1, 2]},
}

# Override hull preferences for specific hull classes
HULL_CLASS_OVERRIDES = {
    "fighter": {
        "terran": [6, 7, 9],       # wedge, needle, delta
        "merchants": [5, 8, 10],    # sleek, disc, twin
        "science": [7, 8, 5],       # needle, disc, sleek
        "iron_compact": [6, 9, 7],  # wedge, delta, needle
        "frontier": [10, 9, 5, 7],  # twin, delta, sleek, needle
    },
}

# Bridge override for fighters (only flat/cockpit, no towers)
BRIDGE_CLASS_OVERRIDES = {
    "fighter": [1, 2],  # cockpit, flat only
}


def _offset_parts(parts, dx, dy, dz):
    out = []
    for p in parts:
        np = dict(p)
        np["pos"] = [p["pos"][0]+dx, p["pos"][1]+dy, p["pos"][2]+dz]
        out.append(np)
    return out


def _mirror_z(parts):
    out = []
    for p in parts:
        np = dict(p)
        np["pos"] = [p["pos"][0], p["pos"][1], -p["pos"][2]]
        out.append(np)
    return out


def generate_ship(faction="terran", hull_class="frigate", seed=None, **overrides):
    if seed is not None:
        random.seed(seed)
    else:
        seed = random.randint(0, 999999)
        random.seed(seed)

    cfg = HULL_CLASSES.get(hull_class, HULL_CLASSES["frigate"])
    style = FACTION_STYLES.get(faction, FACTION_STYLES["terran"])
    s = cfg["scale"]
    symmetric = random.random() < 0.6

    components = []

    # ── Build hull chain (connected via attachment points) ────────────────────
    # Use hull-class-specific overrides if available
    hull_override = HULL_CLASS_OVERRIDES.get(hull_class, {}).get(faction)
    hull_indices = hull_override if hull_override else style["prefer_hull"]
    hull_fns = [HULLS[i] for i in hull_indices]
    chain_x = 0.0
    density = cfg["hull_density"]

    for i in range(cfg["hull_count"]):
        hull_fn = random.choice(hull_fns)
        hull = hull_fn(s)

        # Place primary hull piece
        components.extend(_offset_parts(hull["parts"], chain_x, 0, 0))

        # Density pass: layer additional smaller hull pieces around the primary
        for d in range(density - 1):
            sub_fn = random.choice(hull_fns)
            sub_scale = s * random.uniform(0.5, 0.75)
            sub = sub_fn(sub_scale)
            # Stack vertically, or offset laterally
            placement = random.choice(["top", "bottom", "left", "right"])
            if placement == "top":
                dy = hull["attachments"]["top"]["pos"][1] * random.uniform(0.6, 1.0)
                components.extend(_offset_parts(sub["parts"], chain_x + random.uniform(-0.03*s, 0.03*s), dy, 0))
            elif placement == "bottom":
                dy = -abs(hull["attachments"]["top"]["pos"][1]) * random.uniform(0.6, 1.0)
                components.extend(_offset_parts(sub["parts"], chain_x + random.uniform(-0.03*s, 0.03*s), dy, 0))
            elif placement == "left":
                dz = hull["attachments"].get("left", {"pos":[0,0,0.1*s]})["pos"][2] * random.uniform(0.5, 0.9)
                placed = _offset_parts(sub["parts"], chain_x + random.uniform(-0.03*s, 0.03*s), 0, dz)
                components.extend(placed)
                if symmetric:
                    components.extend(_mirror_z(placed))
            else:
                dz = -hull["attachments"].get("right", {"pos":[0,0,-0.1*s]})["pos"][2] * random.uniform(0.5, 0.9)
                placed = _offset_parts(sub["parts"], chain_x + random.uniform(-0.03*s, 0.03*s), 0, dz)
                components.extend(placed)
                if symmetric:
                    components.extend(_mirror_z(placed))

        # Add connector between sections
        if i < cfg["hull_count"] - 1:
            front_pos = hull["attachments"]["front"]["pos"]
            conn_x = chain_x + front_pos[0]
            conn = _connector(s)
            components.extend(_offset_parts(conn["parts"], conn_x, 0, 0))
            chain_x = conn_x + 0.06*s  # advance past connector
        else:
            chain_x += hull["attachments"]["front"]["pos"][0]

        # Wings on this section
        if random.random() < cfg["wing_chance"]:
            wing_fn = random.choice(WINGS)
            if "left" in hull["attachments"]:
                lp = hull["attachments"]["left"]["pos"]
                wing = wing_fn(s)
                placed = _offset_parts(wing["parts"], chain_x - hull["attachments"]["front"]["pos"][0] + lp[0], lp[1], lp[2])
                components.extend(placed)
                if symmetric:
                    components.extend(_mirror_z(placed))
                elif random.random() < 0.5 and "right" in hull["attachments"]:
                    rp = hull["attachments"]["right"]["pos"]
                    wing2 = random.choice(WINGS)(s)
                    components.extend(_offset_parts(wing2["parts"], chain_x - hull["attachments"]["front"]["pos"][0] + rp[0], rp[1], rp[2]))

        # Detail on top
        if random.random() < cfg["detail_chance"] and "top" in hull["attachments"]:
            tp = hull["attachments"]["top"]["pos"]
            detail_fn = random.choice(DETAILS)
            detail = detail_fn(s)
            components.extend(_offset_parts(detail["parts"], chain_x - hull["attachments"]["front"]["pos"][0] + tp[0], tp[1], tp[2]))

    # ── Bridge at front ──────────────────────────────────────────────────────
    bridge_override = BRIDGE_CLASS_OVERRIDES.get(hull_class)
    bridge_indices = bridge_override if bridge_override else style["prefer_bridge"]
    bridge_fns = [BRIDGES[i] for i in bridge_indices]
    bridge_fn = random.choice(bridge_fns)
    bridge = bridge_fn(s)
    components.extend(_offset_parts(bridge["parts"], chain_x + 0.02*s, 0, 0))

    # ── Engines at rear ──────────────────────────────────────────────────────
    engine_fns = [ENGINES[i] for i in style["prefer_engine"]]
    first_hull = random.choice(hull_fns)(s)
    rear_x = first_hull["attachments"]["rear"]["pos"][0] - 0.02*s

    if cfg["engine_count"] == 1:
        eng = random.choice(engine_fns)(s)
        components.extend(_offset_parts(eng["parts"], rear_x, 0, 0))
    else:
        spacing = 0.08 * s
        for ei in range(cfg["engine_count"]):
            if symmetric:
                if cfg["engine_count"] % 2 == 1 and ei == 0:
                    eng = random.choice(engine_fns)(s)
                    components.extend(_offset_parts(eng["parts"], rear_x, 0, 0))
                else:
                    z = spacing * ((ei+1)//2)
                    eng = random.choice(engine_fns)(s)
                    placed = _offset_parts(eng["parts"], rear_x, 0, z)
                    components.extend(placed)
                    components.extend(_mirror_z(placed))
                    break
            else:
                z = random.uniform(-spacing*2, spacing*2)
                y = random.uniform(-0.03*s, 0.03*s)
                eng = random.choice(engine_fns)(s)
                components.extend(_offset_parts(eng["parts"], rear_x, y, z))

    meta = {
        "faction": faction, "hull_class": hull_class, "seed": seed,
        "scale": s, "symmetric": symmetric,
        "length": chain_x * 2, "beam": s * 0.5, "height": s * 0.3,
    }
    return {"components": components, "meta": meta}
