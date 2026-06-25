"""
Component library - hand-crafted ship parts based on functional design principles.
Each component looks like it belongs on a real spacecraft because it's designed around PURPOSE.

Key principles (from naval architecture analysis):
- Propulsion dominates rear silhouette
- Weapons are prominent, forward-facing
- Hull connects engines to guns, crew crammed in between
- Shape communicates function at a glance
"""
import math
import random

COMPONENT_CATEGORIES = {
    "bridge": "Command structure, sensor tower, crew compartment",
    "hull_section": "Main body segment, spine, structural core",
    "engine": "Thruster nacelle, drive assembly, exhaust nozzle",
    "wing": "Radiator panel, weapon pylon, stabilizer fin",
    "weapon_mount": "Turret housing, spinal gun barrel, missile battery",
    "antenna": "Sensor array, comms dish, scanner boom",
    "connector": "Structural pylon, spine joint, docking collar",
}


# ── BRIDGES / COMMAND STRUCTURES ─────────────────────────────────────────────
# These sit atop or forward of the hull. They're where the crew SEES from.

def gen_bridge(style="tower", size=1.0, seed=None):
    if seed is not None: random.seed(seed)
    s = size
    parts = []

    if style == "tower":
        # Raised command tower (naval style)
        parts.append({"type": "pod", "pos": [0, 0, 0], "rot": [0, 0, 0],
                      "params": {"length": 0.12*s, "height": 0.06*s, "width": 0.14*s}, "material": "hull"})
        # Tower body
        parts.append({"type": "pod", "pos": [0, 0.06*s, 0], "rot": [0, 0, 0],
                      "params": {"length": 0.09*s, "height": 0.08*s, "width": 0.1*s}, "material": "hull"})
        # Viewport slit (flush, not tilted)
        parts.append({"type": "box", "pos": [0.045*s, 0.08*s, 0], "rot": [0, 0, 0],
                      "params": {"x": 0.005*s, "y": 0.02*s, "z": 0.08*s}, "material": "hull"})
        # Antenna mast
        parts.append({"type": "box", "pos": [0, 0.12*s, 0], "rot": [0, 0, 0],
                      "params": {"x": 0.008*s, "y": 0.05*s, "z": 0.008*s}, "material": "hull"})

    elif style == "hammerhead":
        # Wide forward bridge (wide sensor head)
        parts.append({"type": "pod", "pos": [0, 0, 0], "rot": [0, 0, 0],
                      "params": {"length": 0.15*s, "height": 0.05*s, "width": 0.22*s}, "material": "hull"})
        # Raised center section
        parts.append({"type": "pod", "pos": [0.02*s, 0.03*s, 0], "rot": [0, 0, 0],
                      "params": {"length": 0.08*s, "height": 0.04*s, "width": 0.1*s}, "material": "hull"})
        # Side sensor strips (integrated into hull edge, not floating)
        for side in [-1, 1]:
            parts.append({"type": "box", "pos": [0.04*s, 0, side*0.1*s], "rot": [0, 0, 0],
                          "params": {"x": 0.04*s, "y": 0.03*s, "z": 0.025*s}, "material": "hull"})

    elif style == "cockpit":
        # Fighter/frigate forward cockpit (tapered, no floating bits)
        parts.append({"type": "pod", "pos": [0, 0, 0], "rot": [0, 0, 0],
                      "params": {"length": 0.18*s, "height": 0.07*s, "width": 0.1*s}, "material": "hull"})
        # Narrow forward taper
        parts.append({"type": "pod", "pos": [0.1*s, 0, 0], "rot": [0, 0, 0],
                      "params": {"length": 0.08*s, "height": 0.04*s, "width": 0.05*s}, "material": "hull"})
        # Viewport band across front
        parts.append({"type": "box", "pos": [0.09*s, 0.025*s, 0], "rot": [0, 0, 0],
                      "params": {"x": 0.06*s, "y": 0.01*s, "z": 0.07*s}, "material": "hull"})

    elif style == "bunker":
        # Armored recessed bridge (military, protected)
        parts.append({"type": "pod", "pos": [0, 0, 0], "rot": [0, 0, 0],
                      "params": {"length": 0.14*s, "height": 0.08*s, "width": 0.12*s}, "material": "hull"})
        # Armored viewport (narrow slit)
        parts.append({"type": "box", "pos": [0.05*s, 0.02*s, 0], "rot": [0, 0, 0],
                      "params": {"x": 0.02*s, "y": 0.01*s, "z": 0.1*s}, "material": "hull"})
        # Top armor plate
        parts.append({"type": "box", "pos": [0, 0.045*s, 0], "rot": [0, 0, 0],
                      "params": {"x": 0.12*s, "y": 0.01*s, "z": 0.11*s}, "material": "hull"})

    elif style == "stepped":
        # Multi-level command structure with side wings
        for i in range(3):
            w = (0.16 - i*0.03) * s
            h = 0.035 * s
            parts.append({"type": "pod", "pos": [-i*0.02*s, i*0.035*s, 0], "rot": [0, 0, 0],
                          "params": {"length": 0.08*s, "height": h, "width": w}, "material": "hull"})
        # Side protruding sensor wings
        for side in [-1, 1]:
            parts.append({"type": "box", "pos": [0, 0.02*s, side*0.09*s], "rot": [0, 0, 0],
                          "params": {"x": 0.06*s, "y": 0.02*s, "z": 0.03*s}, "material": "hull"})
        # Top antenna array
        parts.append({"type": "box", "pos": [-0.04*s, 0.12*s, 0], "rot": [0, 0, 0],
                      "params": {"x": 0.04*s, "y": 0.02*s, "z": 0.06*s}, "material": "hull"})

    elif style == "wedge":
        # Low-profile wedge bridge (flat, aggressive)
        parts.append({"type": "pod", "pos": [0, 0, 0], "rot": [0, 0, 0],
                      "params": {"length": 0.2*s, "height": 0.04*s, "width": 0.16*s}, "material": "hull"})
        # Forward viewport strip
        parts.append({"type": "box", "pos": [0.08*s, 0.022*s, 0], "rot": [0, 0, 0],
                      "params": {"x": 0.005*s, "y": 0.015*s, "z": 0.12*s}, "material": "hull"})
        # Rear raised comms block
        parts.append({"type": "box", "pos": [-0.06*s, 0.03*s, 0], "rot": [0, 0, 0],
                      "params": {"x": 0.04*s, "y": 0.03*s, "z": 0.06*s}, "material": "hull"})

    elif style == "split":
        # Dual-pod bridge (redundant command, military)
        for side in [-1, 1]:
            parts.append({"type": "pod", "pos": [0, 0.02*s, side*0.05*s], "rot": [0, 0, 0],
                          "params": {"length": 0.1*s, "height": 0.05*s, "width": 0.06*s}, "material": "hull"})
            parts.append({"type": "box", "pos": [0.035*s, 0.04*s, side*0.05*s], "rot": [0, 0, 0],
                          "params": {"x": 0.04*s, "y": 0.008*s, "z": 0.04*s}, "material": "hull"})
        # Connecting walkway
        parts.append({"type": "box", "pos": [0, 0.02*s, 0], "rot": [0, 0, 0],
                      "params": {"x": 0.04*s, "y": 0.02*s, "z": 0.08*s}, "material": "hull"})

    elif style == "recessed":
        # Sunken bridge behind armor plate
        # Main armor housing
        parts.append({"type": "pod", "pos": [0, 0, 0], "rot": [0, 0, 0],
                      "params": {"length": 0.14*s, "height": 0.06*s, "width": 0.12*s}, "material": "hull"})
        # Recessed viewport slot cut into front
        parts.append({"type": "box", "pos": [0.06*s, 0.01*s, 0], "rot": [0, 0, 0],
                      "params": {"x": 0.02*s, "y": 0.015*s, "z": 0.08*s}, "material": "hull"})
        # Top armor overhang
        parts.append({"type": "pod", "pos": [0.02*s, 0.035*s, 0], "rot": [0, 0, 0],
                      "params": {"length": 0.1*s, "height": 0.02*s, "width": 0.13*s}, "material": "hull"})

    elif style == "antenna_tower":
        # Tall sensor mast with multiple arrays
        parts.append({"type": "pod", "pos": [0, 0, 0], "rot": [0, 0, 0],
                      "params": {"length": 0.08*s, "height": 0.04*s, "width": 0.08*s}, "material": "hull"})
        parts.append({"type": "box", "pos": [0, 0.06*s, 0], "rot": [0, 0, 0],
                      "params": {"x": 0.02*s, "y": 0.08*s, "z": 0.02*s}, "material": "hull"})
        # Cross arrays
        parts.append({"type": "box", "pos": [0, 0.08*s, 0], "rot": [0, 0, 0],
                      "params": {"x": 0.06*s, "y": 0.008*s, "z": 0.008*s}, "material": "hull"})
        parts.append({"type": "box", "pos": [0, 0.1*s, 0], "rot": [0, 0, 0],
                      "params": {"x": 0.008*s, "y": 0.008*s, "z": 0.05*s}, "material": "hull"})

    return {"category": "bridge", "style": style, "size": size, "parts": parts}


# ── HULL SECTIONS ────────────────────────────────────────────────────────────
# The body of the ship. Should communicate mass, armor, and purpose.

def gen_hull_section(style="angular", size=1.0, seed=None):
    if seed is not None: random.seed(seed)
    s = size
    parts = []

    if style == "angular":
        # Military angular hull (faceted armor plates)
        l = 0.4*s
        parts.append({"type": "pod", "pos": [0, 0, 0], "rot": [0, 0, 0],
                      "params": {"length": l, "height": 0.14*s, "width": 0.18*s}, "material": "hull"})
        # Dorsal ridge (armor spine)
        parts.append({"type": "pod", "pos": [0, 0.06*s, 0], "rot": [0, 0, 0],
                      "params": {"length": l*0.7, "height": 0.03*s, "width": 0.06*s}, "material": "hull"})
        # Ventral detail
        parts.append({"type": "box", "pos": [0, -0.06*s, 0], "rot": [0, 0, 0],
                      "params": {"x": l*0.5, "y": 0.02*s, "z": 0.12*s}, "material": "hull"})

    elif style == "cylindrical":
        # Science/exploration vessel (rounded, pressure hull look)
        l = 0.4*s
        r = 0.09*s
        parts.append({"type": "cylinder", "pos": [0, 0, 0], "rot": [0, 0, 0],
                      "params": {"r_top": r*0.9, "r_bot": r, "length": l}, "material": "hull"})
        # Ring details (bulkheads visible from outside)
        for i in range(3):
            x = (i-1) * l*0.3
            parts.append({"type": "torus", "pos": [x, 0, 0], "rot": [0, 0, 0],
                          "params": {"radius": r*1.05, "tube": 0.008*s}, "material": "hull"})

    elif style == "flat_wide":
        # Carrier/hauler (big flat slab, cargo doors implied)
        l = 0.45*s
        parts.append({"type": "pod", "pos": [0, 0, 0], "rot": [0, 0, 0],
                      "params": {"length": l, "height": 0.08*s, "width": 0.3*s}, "material": "hull"})
        # Cargo bay lines
        parts.append({"type": "box", "pos": [0, -0.035*s, 0], "rot": [0, 0, 0],
                      "params": {"x": l*0.6, "y": 0.005*s, "z": 0.25*s}, "material": "hull"})
        # Side rail
        for side in [-1, 1]:
            parts.append({"type": "box", "pos": [0, 0, side*0.14*s], "rot": [0, 0, 0],
                          "params": {"x": l*0.9, "y": 0.04*s, "z": 0.02*s}, "material": "hull"})

    elif style == "tapered":
        # Destroyer/cruiser (tapers toward bow, aggressive stance)
        parts.append({"type": "pod", "pos": [0, 0, 0], "rot": [0, 0, 0],
                      "params": {"length": 0.35*s, "height": 0.15*s, "width": 0.2*s}, "material": "hull"})
        parts.append({"type": "pod", "pos": [0.2*s, 0, 0], "rot": [0, 0, 0],
                      "params": {"length": 0.2*s, "height": 0.1*s, "width": 0.13*s}, "material": "hull"})
        # Ventral keel
        parts.append({"type": "box", "pos": [0.05*s, -0.07*s, 0], "rot": [0, 0, 0],
                      "params": {"x": 0.3*s, "y": 0.02*s, "z": 0.04*s}, "material": "hull"})

    elif style == "blocky":
        # Industrial/mining (layered panels, not plain box)
        parts.append({"type": "pod", "pos": [0, 0, 0], "rot": [0, 0, 0],
                      "params": {"length": 0.35*s, "height": 0.16*s, "width": 0.2*s}, "material": "hull"})
        # Inset panel top
        parts.append({"type": "pod", "pos": [0, 0.07*s, 0], "rot": [0, 0, 0],
                      "params": {"length": 0.25*s, "height": 0.03*s, "width": 0.16*s}, "material": "hull"})
        # Inset panel bottom
        parts.append({"type": "pod", "pos": [0, -0.07*s, 0], "rot": [0, 0, 0],
                      "params": {"length": 0.28*s, "height": 0.03*s, "width": 0.18*s}, "material": "hull"})
        # Side ridge left/right
        for side in [-1, 1]:
            parts.append({"type": "box", "pos": [0, 0, side*0.1*s], "rot": [0, 0, 0],
                          "params": {"x": 0.3*s, "y": 0.08*s, "z": 0.02*s}, "material": "hull"})

    elif style == "armored_wedge":
        # Tapered armored section with layered plates
        parts.append({"type": "pod", "pos": [0, 0, 0], "rot": [0, 0, 0],
                      "params": {"length": 0.4*s, "height": 0.12*s, "width": 0.16*s}, "material": "hull"})
        # Armor chevrons
        for i in range(3):
            parts.append({"type": "box", "pos": [(i-1)*0.1*s, 0.065*s, 0], "rot": [0, 0, 0],
                          "params": {"x": 0.06*s, "y": 0.01*s, "z": 0.14*s}, "material": "hull"})

    elif style == "spine_frame":
        # Open frame with central spine (destroyer style)
        parts.append({"type": "box", "pos": [0, 0, 0], "rot": [0, 0, 0],
                      "params": {"x": 0.45*s, "y": 0.04*s, "z": 0.04*s}, "material": "hull"})
        # Cross members
        for i in range(4):
            x = (i - 1.5) * 0.1*s
            parts.append({"type": "box", "pos": [x, 0, 0], "rot": [0, 0, 0],
                          "params": {"x": 0.015*s, "y": 0.03*s, "z": 0.16*s}, "material": "hull"})
        # Top rail
        parts.append({"type": "box", "pos": [0, 0.025*s, 0], "rot": [0, 0, 0],
                      "params": {"x": 0.35*s, "y": 0.01*s, "z": 0.02*s}, "material": "hull"})

    elif style == "double_hull":
        # Twin parallel hulls (catamaran style)
        for side in [-1, 1]:
            parts.append({"type": "pod", "pos": [0, 0, side*0.08*s], "rot": [0, 0, 0],
                          "params": {"length": 0.4*s, "height": 0.1*s, "width": 0.08*s}, "material": "hull"})
        # Cross beams
        for i in range(3):
            x = (i-1) * 0.12*s
            parts.append({"type": "box", "pos": [x, 0, 0], "rot": [0, 0, 0],
                          "params": {"x": 0.03*s, "y": 0.03*s, "z": 0.14*s}, "material": "hull"})

    elif style == "bulbous":
        # Wide midsection cargo/reactor hull
        parts.append({"type": "cylinder", "pos": [0, 0, 0], "rot": [0, 0, 0],
                      "params": {"r_top": 0.08*s, "r_bot": 0.12*s, "length": 0.2*s}, "material": "hull"})
        parts.append({"type": "cylinder", "pos": [0.15*s, 0, 0], "rot": [0, 0, 0],
                      "params": {"r_top": 0.12*s, "r_bot": 0.08*s, "length": 0.2*s}, "material": "hull"})
        # Equipment band
        parts.append({"type": "torus", "pos": [0.07*s, 0, 0], "rot": [0, 0, 0],
                      "params": {"radius": 0.12*s, "tube": 0.01*s}, "material": "hull"})

    return {"category": "hull_section", "style": style, "size": size, "parts": parts}


# ── ENGINES ──────────────────────────────────────────────────────────────────
# Should DOMINATE the rear. Engines are the biggest system on any ship.

def gen_engine(style="nacelle", size=1.0, seed=None):
    if seed is not None: random.seed(seed)
    s = size
    parts = []

    if style == "nacelle":
        # Classic paired nacelle (elongated, tapered intake, wide exhaust)
        l = 0.3*s
        parts.append({"type": "cylinder", "pos": [0, 0, 0], "rot": [0, 0, 0],
                      "params": {"r_top": 0.03*s, "r_bot": 0.055*s, "length": l}, "material": "engine"})
        # Exhaust bell
        parts.append({"type": "cylinder", "pos": [-l*0.45, 0, 0], "rot": [0, 0, 0],
                      "params": {"r_top": 0.055*s, "r_bot": 0.07*s, "length": 0.05*s}, "material": "engine"})
        # Intake cone
        parts.append({"type": "cone", "pos": [l*0.5, 0, 0], "rot": [0, 0, 0],
                      "params": {"radius": 0.03*s, "length": 0.06*s}, "material": "hull"})

    elif style == "bell_cluster":
        # Multiple exhaust bells (battleship/capital style)
        for i in range(4):
            angle = (math.pi*2*i)/4 + math.pi/4
            oy = math.sin(angle) * 0.05*s
            oz = math.cos(angle) * 0.05*s
            parts.append({"type": "cylinder", "pos": [0, oy, oz], "rot": [0, 0, 0],
                          "params": {"r_top": 0.02*s, "r_bot": 0.035*s, "length": 0.12*s}, "material": "engine"})
        # Center housing
        parts.append({"type": "cylinder", "pos": [0.04*s, 0, 0], "rot": [0, 0, 0],
                      "params": {"r_top": 0.04*s, "r_bot": 0.04*s, "length": 0.08*s}, "material": "hull"})

    elif style == "thruster_bank":
        # Flat array of rectangular thrusters (industrial/hauler)
        for row in range(2):
            for col in range(3):
                y = (row - 0.5) * 0.06*s
                z = (col - 1) * 0.06*s
                parts.append({"type": "box", "pos": [0, y, z], "rot": [0, 0, 0],
                              "params": {"x": 0.08*s, "y": 0.04*s, "z": 0.04*s}, "material": "engine"})
        # Mounting plate
        parts.append({"type": "box", "pos": [0.05*s, 0, 0], "rot": [0, 0, 0],
                      "params": {"x": 0.02*s, "y": 0.14*s, "z": 0.2*s}, "material": "hull"})

    elif style == "ring_drive":
        # Exotic toroidal drive (science faction)
        parts.append({"type": "torus", "pos": [0, 0, 0], "rot": [0, 0, 0],
                      "params": {"radius": 0.08*s, "tube": 0.02*s}, "material": "engine"})
        # Central emitter
        parts.append({"type": "sphere", "pos": [0, 0, 0], "rot": [0, 0, 0],
                      "params": {"radius": 0.03*s, "half": False}, "material": "hull"})
        # Support struts
        for i in range(4):
            angle = (math.pi*2*i)/4
            parts.append({"type": "box", "pos": [0, math.sin(angle)*0.05*s, math.cos(angle)*0.05*s], "rot": [angle, 0, 0],
                          "params": {"x": 0.01*s, "y": 0.04*s, "z": 0.01*s}, "material": "hull"})

    elif style == "massive":
        # Single huge engine (frigate/destroyer, engine IS the ship)
        parts.append({"type": "cylinder", "pos": [0, 0, 0], "rot": [0, 0, 0],
                      "params": {"r_top": 0.06*s, "r_bot": 0.1*s, "length": 0.25*s}, "material": "engine"})
        # Exhaust shroud
        parts.append({"type": "cylinder", "pos": [-0.14*s, 0, 0], "rot": [0, 0, 0],
                      "params": {"r_top": 0.1*s, "r_bot": 0.12*s, "length": 0.04*s}, "material": "hull"})
        # Heat vanes
        for i in range(6):
            angle = (math.pi*2*i)/6
            parts.append({"type": "box", "pos": [-0.05*s, math.sin(angle)*0.09*s, math.cos(angle)*0.09*s],
                          "rot": [angle, 0, 0],
                          "params": {"x": 0.1*s, "y": 0.015*s, "z": 0.01*s}, "material": "hull"})

    elif style == "asymmetric":
        # Offset twin engines (different sizes)
        parts.append({"type": "cylinder", "pos": [0, 0, 0.04*s], "rot": [0, 0, 0],
                      "params": {"r_top": 0.03*s, "r_bot": 0.05*s, "length": 0.25*s}, "material": "engine"})
        parts.append({"type": "cylinder", "pos": [0.03*s, 0, -0.03*s], "rot": [0, 0, 0],
                      "params": {"r_top": 0.02*s, "r_bot": 0.035*s, "length": 0.18*s}, "material": "engine"})
        # Connecting mount plate
        parts.append({"type": "box", "pos": [0.1*s, 0, 0], "rot": [0, 0, 0],
                      "params": {"x": 0.03*s, "y": 0.06*s, "z": 0.1*s}, "material": "hull"})

    elif style == "vectoring":
        # Gimbaled nozzle with visible actuators
        parts.append({"type": "cylinder", "pos": [0, 0, 0], "rot": [0, 0, 0],
                      "params": {"r_top": 0.04*s, "r_bot": 0.07*s, "length": 0.15*s}, "material": "engine"})
        # Gimbal ring
        parts.append({"type": "torus", "pos": [-0.05*s, 0, 0], "rot": [0, 0, 0],
                      "params": {"radius": 0.06*s, "tube": 0.008*s}, "material": "hull"})
        # Actuator struts
        for angle in [0.5, 2.1, 3.7, 5.3]:
            y = math.sin(angle) * 0.06*s
            z = math.cos(angle) * 0.06*s
            parts.append({"type": "box", "pos": [0.02*s, y, z], "rot": [angle, 0, 0],
                          "params": {"x": 0.06*s, "y": 0.008*s, "z": 0.008*s}, "material": "hull"})

    elif style == "twin_pod":
        # Two side-by-side engine pods on a mount
        for side in [-1, 1]:
            parts.append({"type": "cylinder", "pos": [0, 0, side*0.05*s], "rot": [0, 0, 0],
                          "params": {"r_top": 0.025*s, "r_bot": 0.04*s, "length": 0.2*s}, "material": "engine"})
        # Mount plate
        parts.append({"type": "box", "pos": [0.08*s, 0, 0], "rot": [0, 0, 0],
                      "params": {"x": 0.04*s, "y": 0.05*s, "z": 0.12*s}, "material": "hull"})

    return {"category": "engine", "style": style, "size": size, "parts": parts}


# ── WINGS / RADIATORS / PYLONS ───────────────────────────────────────────────
# In space these are radiator panels, weapon pylons, or structural fins.

def gen_wing(style="radiator", size=1.0, seed=None):
    if seed is not None: random.seed(seed)
    s = size
    parts = []

    if style == "radiator":
        # Large flat radiator panel (functional, glows with heat)
        span = 0.3*s
        parts.append({"type": "box", "pos": [0, 0, span*0.5], "rot": [0, 0, 0],
                      "params": {"x": 0.2*s, "y": 0.004*s, "z": span}, "material": "hull"})
        # Support strut
        parts.append({"type": "box", "pos": [0, -0.015*s, 0.06*s], "rot": [0, 0, 0.2],
                      "params": {"x": 0.015*s, "y": 0.03*s, "z": 0.015*s}, "material": "hull"})

    elif style == "swept_fin":
        # Aggressive swept stabilizer
        profile = [[0, 0], [0.15*s, 0.25*s], [0.1*s, 0.28*s], [-0.05*s, 0.08*s]]
        parts.append({"type": "wedge", "pos": [0, 0, 0], "rot": [math.pi/2, 0, 0],
                      "params": {"profile": profile, "depth": 0.015*s}, "material": "hull"})

    elif style == "weapon_pylon":
        # Hardpoint-carrying wing stub
        parts.append({"type": "pod", "pos": [0, 0, 0.08*s], "rot": [0, 0, 0],
                      "params": {"length": 0.12*s, "height": 0.025*s, "width": 0.15*s}, "material": "hull"})
        # Hardpoint at tip
        parts.append({"type": "box", "pos": [0, -0.015*s, 0.14*s], "rot": [0, 0, 0],
                      "params": {"x": 0.04*s, "y": 0.025*s, "z": 0.03*s}, "material": "weapon"})

    elif style == "solar_array":
        # Deployable solar panel
        parts.append({"type": "box", "pos": [0, 0, 0.15*s], "rot": [0, 0, 0],
                      "params": {"x": 0.18*s, "y": 0.003*s, "z": 0.25*s}, "material": "hull"})
        # Hinge mount
        parts.append({"type": "cylinder", "pos": [0, 0, 0.02*s], "rot": [math.pi/2, 0, 0],
                      "params": {"r_top": 0.01*s, "r_bot": 0.01*s, "length": 0.04*s}, "material": "hull"})

    else:  # "dorsal_fin"
        # Tall vertical stabilizer
        parts.append({"type": "pod", "pos": [0, 0.1*s, 0], "rot": [0, 0, 0],
                      "params": {"length": 0.12*s, "height": 0.18*s, "width": 0.012*s}, "material": "hull"})

    return {"category": "wing", "style": style, "size": size, "parts": parts}


# ── WEAPON MOUNTS ────────────────────────────────────────────────────────────

def gen_weapon_mount(style="turret", size=1.0, seed=None):
    if seed is not None: random.seed(seed)
    s = size
    parts = []

    if style == "turret":
        # Rotating turret with twin barrels
        parts.append({"type": "pod", "pos": [0, 0, 0], "rot": [0, 0, 0],
                      "params": {"length": 0.05*s, "height": 0.03*s, "width": 0.06*s}, "material": "weapon"})
        # Twin barrels
        for side in [-1, 1]:
            parts.append({"type": "cylinder", "pos": [0.07*s, 0.015*s, side*0.015*s], "rot": [0, 0, 0],
                          "params": {"r_top": 0.006*s, "r_bot": 0.008*s, "length": 0.1*s}, "material": "weapon"})

    elif style == "spinal":
        # Fixed forward gun (runs length of ship section)
        parts.append({"type": "cylinder", "pos": [0, 0, 0], "rot": [0, 0, 0],
                      "params": {"r_top": 0.015*s, "r_bot": 0.025*s, "length": 0.3*s}, "material": "weapon"})
        # Magnetic rings
        for i in range(4):
            x = (i-1.5) * 0.07*s
            parts.append({"type": "torus", "pos": [x, 0, 0], "rot": [0, 0, 0],
                          "params": {"radius": 0.03*s, "tube": 0.005*s}, "material": "hull"})

    elif style == "missile_rack":
        # Vertical launch cells
        parts.append({"type": "box", "pos": [0, 0, 0], "rot": [0, 0, 0],
                      "params": {"x": 0.08*s, "y": 0.06*s, "z": 0.1*s}, "material": "weapon"})
        # Cell hatches
        for row in range(2):
            for col in range(3):
                parts.append({"type": "box", "pos": [(row-0.5)*0.03*s, 0.032*s, (col-1)*0.03*s], "rot": [0, 0, 0],
                              "params": {"x": 0.02*s, "y": 0.003*s, "z": 0.02*s}, "material": "hull"})

    else:  # "broadside"
        # Side-mounted battery (capital ship)
        parts.append({"type": "box", "pos": [0, 0, 0], "rot": [0, 0, 0],
                      "params": {"x": 0.1*s, "y": 0.04*s, "z": 0.05*s}, "material": "weapon"})
        # Barrel protruding sideways
        parts.append({"type": "cylinder", "pos": [0, 0, 0.05*s], "rot": [math.pi/2, 0, 0],
                      "params": {"r_top": 0.008*s, "r_bot": 0.012*s, "length": 0.08*s}, "material": "weapon"})

    return {"category": "weapon_mount", "style": style, "size": size, "parts": parts}


# ── ANTENNAS / SENSORS ───────────────────────────────────────────────────────

def gen_antenna(style="dish", size=1.0, seed=None):
    if seed is not None: random.seed(seed)
    s = size
    parts = []

    if style == "dish":
        parts.append({"type": "sphere", "pos": [0, 0.03*s, 0], "rot": [math.pi, 0, 0],
                      "params": {"radius": 0.06*s, "half": True}, "material": "hull"})
        # Mounting stem
        parts.append({"type": "cylinder", "pos": [0, -0.02*s, 0], "rot": [0, 0, 0],
                      "params": {"r_top": 0.008*s, "r_bot": 0.012*s, "length": 0.05*s}, "material": "hull"})
        # Base plate
        parts.append({"type": "box", "pos": [0, -0.05*s, 0], "rot": [0, 0, 0],
                      "params": {"x": 0.03*s, "y": 0.01*s, "z": 0.03*s}, "material": "hull"})
    elif style == "phased_array":
        parts.append({"type": "box", "pos": [0, 0, 0], "rot": [0.3, 0, 0],
                      "params": {"x": 0.08*s, "y": 0.06*s, "z": 0.005*s}, "material": "hull"})
        parts.append({"type": "box", "pos": [0, -0.02*s, 0.01*s], "rot": [0, 0, 0],
                      "params": {"x": 0.02*s, "y": 0.03*s, "z": 0.02*s}, "material": "hull"})
    elif style == "boom":
        l = 0.2*s
        # Boom arm
        parts.append({"type": "box", "pos": [0, 0, 0], "rot": [0, 0, 0],
                      "params": {"x": l, "y": 0.012*s, "z": 0.012*s}, "material": "hull"})
        # Sensor tip (box, not sphere)
        parts.append({"type": "box", "pos": [l*0.5, 0, 0], "rot": [0, 0, 0],
                      "params": {"x": 0.03*s, "y": 0.02*s, "z": 0.02*s}, "material": "hull"})
        # Mount bracket
        parts.append({"type": "box", "pos": [-l*0.45, 0, 0], "rot": [0, 0, 0],
                      "params": {"x": 0.02*s, "y": 0.025*s, "z": 0.025*s}, "material": "hull"})
    else:  # "spine_array"
        for i in range(4):
            parts.append({"type": "box", "pos": [i*0.03*s, 0, 0], "rot": [0, 0, 0],
                          "params": {"x": 0.008*s, "y": 0.06*s, "z": 0.004*s}, "material": "hull"})
        parts.append({"type": "box", "pos": [0.045*s, 0, 0], "rot": [0, 0, 0],
                      "params": {"x": 0.12*s, "y": 0.008*s, "z": 0.008*s}, "material": "hull"})

    return {"category": "antenna", "style": style, "size": size, "parts": parts}


# ── CONNECTORS ───────────────────────────────────────────────────────────────

def gen_connector(style="spine", size=1.0, seed=None):
    if seed is not None: random.seed(seed)
    s = size
    parts = []

    if style == "spine":
        parts.append({"type": "spine", "pos": [0, 0, 0],
                      "params": {"length": 0.15*s, "radius": 0.025*s, "flange_r": 0.04*s}, "material": "hull"})
    elif style == "truss":
        l = 0.2*s
        for y in [-0.02*s, 0.02*s]:
            for z in [-0.02*s, 0.02*s]:
                parts.append({"type": "box", "pos": [0, y, z], "rot": [0, 0, 0],
                              "params": {"x": l, "y": 0.008*s, "z": 0.008*s}, "material": "hull"})
        # Cross braces
        parts.append({"type": "box", "pos": [0, 0, 0], "rot": [0, 0, math.pi/4],
                      "params": {"x": 0.01*s, "y": 0.055*s, "z": 0.01*s}, "material": "hull"})
    elif style == "collar":
        parts.append({"type": "torus", "pos": [0, 0, 0], "rot": [0, 0, 0],
                      "params": {"radius": 0.06*s, "tube": 0.015*s}, "material": "hull"})
    else:  # "pylon"
        parts.append({"type": "pod", "pos": [0, 0, 0], "rot": [0, 0, 0],
                      "params": {"length": 0.15*s, "height": 0.03*s, "width": 0.02*s}, "material": "hull"})

    return {"category": "connector", "style": style, "size": size, "parts": parts}


# ── DISPATCH ─────────────────────────────────────────────────────────────────

GENERATORS = {
    "bridge": (gen_bridge, ["tower", "hammerhead", "cockpit", "bunker", "stepped", "wedge", "split", "recessed", "antenna_tower"]),
    "hull_section": (gen_hull_section, ["angular", "cylindrical", "flat_wide", "tapered", "blocky", "armored_wedge", "spine_frame", "double_hull", "bulbous"]),
    "engine": (gen_engine, ["nacelle", "bell_cluster", "thruster_bank", "ring_drive", "massive", "asymmetric", "vectoring", "twin_pod"]),
    "wing": (gen_wing, ["radiator", "swept_fin", "weapon_pylon", "solar_array", "dorsal_fin"]),
    "weapon_mount": (gen_weapon_mount, ["turret", "spinal", "missile_rack", "broadside"]),
    "antenna": (gen_antenna, ["dish", "phased_array", "boom", "spine_array"]),
    "connector": (gen_connector, ["spine", "truss", "collar", "pylon"]),
}


def generate_component(category, style=None, size=1.0, seed=None):
    gen_fn, styles = GENERATORS.get(category, (None, []))
    if not gen_fn:
        return {"error": f"Unknown category: {category}"}
    if style is None or style == "":
        style = random.choice(styles)
    return gen_fn(style=style, size=size, seed=seed)
