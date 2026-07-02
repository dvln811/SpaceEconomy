"""Asteroid Generator v2: single-mesh randomized geometry.

Each asteroid is a single mesh built from an icosphere with randomly
displaced vertices. No overlapping primitives - just one irregular rock shape.

Output: dict with 'vertices' (flat float array) and 'faces' (flat int array)
that the client renders directly as a BufferGeometry.
"""
import random
import math
import json
import os


# Asteroid visual styles by ore type
ASTEROID_STYLES = {
    'iron': {'color_hint': 'dark_grey', 'roughness': 0.4, 'detail': 2},
    'copper': {'color_hint': 'reddish', 'roughness': 0.35, 'detail': 2},
    'titanium': {'color_hint': 'silver', 'roughness': 0.3, 'detail': 2},
    'gold': {'color_hint': 'gold', 'roughness': 0.25, 'detail': 2},
    'platinum': {'color_hint': 'white', 'roughness': 0.25, 'detail': 2},
    'palladium': {'color_hint': 'pale_blue', 'roughness': 0.3, 'detail': 3},
    'neutronium': {'color_hint': 'dark_purple', 'roughness': 0.5, 'detail': 3},
    'quartz_crystal': {'color_hint': 'clear', 'roughness': 0.6, 'detail': 2},
    'uranium': {'color_hint': 'green_glow', 'roughness': 0.35, 'detail': 2},
    'generic': {'color_hint': 'grey', 'roughness': 0.35, 'detail': 2},
}

SIZE_CLASSES = {
    'small': (20, 60),       # meters
    'medium': (80, 200),
    'large': (300, 800),
}


def _make_icosphere(subdivisions=2):
    """Generate an icosphere (subdivided icosahedron). Returns (vertices, faces)."""
    # Golden ratio
    t = (1 + math.sqrt(5)) / 2

    # Initial icosahedron vertices (normalized to unit sphere)
    verts = [
        [-1, t, 0], [1, t, 0], [-1, -t, 0], [1, -t, 0],
        [0, -1, t], [0, 1, t], [0, -1, -t], [0, 1, -t],
        [t, 0, -1], [t, 0, 1], [-t, 0, -1], [-t, 0, 1],
    ]
    # Normalize
    for i in range(len(verts)):
        l = math.sqrt(sum(v*v for v in verts[i]))
        verts[i] = [v/l for v in verts[i]]

    # Initial faces
    faces = [
        [0,11,5],[0,5,1],[0,1,7],[0,7,10],[0,10,11],
        [1,5,9],[5,11,4],[11,10,2],[10,7,6],[7,1,8],
        [3,9,4],[3,4,2],[3,2,6],[3,6,8],[3,8,9],
        [4,9,5],[2,4,11],[6,2,10],[8,6,7],[9,8,1],
    ]

    # Subdivide
    midpoint_cache = {}
    def get_midpoint(i1, i2):
        key = (min(i1,i2), max(i1,i2))
        if key in midpoint_cache:
            return midpoint_cache[key]
        v1, v2 = verts[i1], verts[i2]
        mid = [(v1[j]+v2[j])/2 for j in range(3)]
        l = math.sqrt(sum(v*v for v in mid))
        mid = [v/l for v in mid]  # project to unit sphere
        idx = len(verts)
        verts.append(mid)
        midpoint_cache[key] = idx
        return idx

    for _ in range(subdivisions):
        new_faces = []
        midpoint_cache = {}
        for tri in faces:
            a, b, c = tri
            ab = get_midpoint(a, b)
            bc = get_midpoint(b, c)
            ca = get_midpoint(c, a)
            new_faces.extend([
                [a, ab, ca],
                [b, bc, ab],
                [c, ca, bc],
                [ab, bc, ca],
            ])
        faces = new_faces

    return verts, faces


def generate_asteroid(ore_type='generic', size_class='medium', seed=None):
    """Generate a single asteroid as a displaced icosphere mesh.

    Returns dict with: vertices (flat [x,y,z,...]), faces (flat [i,j,k,...]),
    ore_type, size_class, radius (meters).
    """
    if seed is not None:
        random.seed(seed)

    style = ASTEROID_STYLES.get(ore_type, ASTEROID_STYLES['generic'])
    size_range = SIZE_CLASSES.get(size_class, SIZE_CLASSES['medium'])
    radius = random.uniform(*size_range)
    roughness = style['roughness']
    detail = style['detail']

    # Generate base icosphere
    verts, faces = _make_icosphere(subdivisions=detail)

    # Displace vertices randomly (multiply radius by 1 +/- roughness)
    displaced = []
    for v in verts:
        # Random displacement along the radial direction
        noise = 1.0 + random.uniform(-roughness, roughness)
        # Add some large-scale deformation (elongation along a random axis)
        displaced.append([v[0] * noise, v[1] * noise, v[2] * noise])

    # Apply large-scale deformation: stretch along a random axis
    stretch_axis = random.randint(0, 2)
    stretch_factor = random.uniform(1.0, 1.6)
    for v in displaced:
        v[stretch_axis] *= stretch_factor

    # Flatten vertices (pre-scaled by radius for the JSON, client just uses as-is)
    # Actually store as unit-scale, let client scale to size
    flat_verts = []
    for v in displaced:
        flat_verts.extend([round(v[0], 4), round(v[1], 4), round(v[2], 4)])

    flat_faces = []
    for f in faces:
        flat_faces.extend(f)

    return {
        'name': f'asteroid/{ore_type}/{size_class}',
        'ore_type': ore_type,
        'size_class': size_class,
        'radius': round(radius, 1),
        'vertices': flat_verts,
        'faces': flat_faces,
        'meta': {
            'ore_type': ore_type,
            'size_class': size_class,
            'radius': round(radius, 1),
            'vertex_count': len(displaced),
            'face_count': len(faces),
        }
    }


def generate_asteroid_field(ore_types=None, count=20, seed=None):
    """Generate a collection of asteroid meshes for a field."""
    if seed is not None:
        random.seed(seed)
    if ore_types is None:
        ore_types = ['iron', 'copper', 'titanium']

    asteroids = []
    for i in range(count):
        ore = random.choice(ore_types)
        roll = random.random()
        if roll < 0.6:
            size = 'small'
        elif roll < 0.9:
            size = 'medium'
        else:
            size = 'large'
        ast = generate_asteroid(ore_type=ore, size_class=size, seed=(seed * 1000 + i) if seed else None)
        asteroids.append(ast)

    return asteroids


def generate_all_asteroid_sets(output_dir=None):
    """Generate pre-built asteroid field sets."""
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), 'asteroid_designs')
    os.makedirs(output_dir, exist_ok=True)

    field_types = {
        'common_metals': ['iron', 'copper', 'titanium'],
        'precious_metals': ['gold', 'platinum', 'palladium'],
        'rare_ores': ['neutronium', 'quartz_crystal', 'uranium'],
        'mixed': ['iron', 'copper', 'gold', 'titanium', 'generic'],
    }

    for field_name, ores in field_types.items():
        asteroids = generate_asteroid_field(ore_types=ores, count=20, seed=hash(field_name) % 10000)
        path = os.path.join(output_dir, f'asteroids_{field_name}.json')
        with open(path, 'w') as f:
            json.dump(asteroids, f)
        print(f'  {field_name}: {len(asteroids)} asteroids (avg {sum(a["meta"]["vertex_count"] for a in asteroids)//len(asteroids)} verts)')


if __name__ == '__main__':
    print('Generating asteroid designs...')
    generate_all_asteroid_sets()
    print('Done.')
