"""
Ship Designer Tool - Local standalone Flask app for generating and previewing 3D ship designs.
Run: python tools/ship_designer/app.py
Opens browser at http://localhost:5050
"""
import json
import os
import random
import webbrowser
from flask import Flask, jsonify, request, send_from_directory
from ship_generator import generate_ship, FACTION_STYLES, HULL_CLASSES
from component_library import generate_component, GENERATORS, COMPONENT_CATEGORIES

app = Flask(__name__, static_folder=None)
TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(TOOL_DIR))
SAVE_DIR = os.path.join(TOOL_DIR, "saved_designs")
COMP_DIR = os.path.join(TOOL_DIR, "saved_components")
os.makedirs(SAVE_DIR, exist_ok=True)
os.makedirs(COMP_DIR, exist_ok=True)


@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory(os.path.join(PROJECT_ROOT, "static"), filename)


@app.route("/")
def index():
    return send_from_directory(TOOL_DIR, "index.html")


@app.route("/api/generate", methods=["POST"])
def api_generate():
    params = request.get_json() or {}
    faction = params.get("faction", "terran")
    hull_class = params.get("hull_class", "frigate")
    seed = params.get("seed")
    if seed == "":
        seed = None
    elif seed is not None:
        seed = int(seed)
    result = generate_ship(faction=faction, hull_class=hull_class, seed=seed)
    return jsonify(result)


@app.route("/api/batch_generate", methods=["POST"])
def api_batch_generate():
    """Generate multiple ships per faction/class for review."""
    params = request.get_json() or {}
    hull_class = params.get("hull_class", "fighter")
    count = int(params.get("count", 4))
    factions = ["terran", "merchants", "science", "iron_compact", "frontier"]
    results = []
    for faction in factions:
        for i in range(count):
            seed = random.randint(0, 999999)
            ship = generate_ship(faction=faction, hull_class=hull_class, seed=seed)
            results.append({
                "name": f"{faction}/{hull_class}/{seed}",
                "faction": faction,
                "hull_class": hull_class,
                "seed": seed,
                "components": ship["components"],
                "meta": ship["meta"],
            })
    return jsonify(results)


@app.route("/review")
def review_page():
    return send_from_directory(TOOL_DIR, "review.html")


@app.route("/lod")
def lod_page():
    return send_from_directory(TOOL_DIR, "lod_viewer.html")


@app.route("/api/factions")
def api_factions():
    return jsonify({k: v["description"] for k, v in FACTION_STYLES.items()})


@app.route("/api/hull_classes")
def api_hull_classes():
    return jsonify(list(HULL_CLASSES.keys()))


@app.route("/api/save", methods=["POST"])
def api_save():
    data = request.get_json()
    name = data.get("name", "unnamed")
    safe_name = "".join(c for c in name if c.isalnum() or c in "_-").lower()
    path = os.path.join(SAVE_DIR, f"{safe_name}.json")
    with open(path, "w") as f:
        json.dump(data["design"], f, indent=2)
    return jsonify({"status": "saved", "path": path})


@app.route("/api/saved")
def api_saved():
    files = [f[:-5] for f in os.listdir(SAVE_DIR) if f.endswith(".json")]
    return jsonify(files)


@app.route("/api/load/<name>")
def api_load(name):
    path = os.path.join(SAVE_DIR, f"{name}.json")
    if not os.path.exists(path):
        return jsonify({"error": "not found"}), 404
    with open(path) as f:
        return jsonify(json.load(f))


# ── Component Library ────────────────────────────────────────────────────────

@app.route("/components")
def components_page():
    return send_from_directory(TOOL_DIR, "components.html")


@app.route("/gallery")
def gallery_page():
    return send_from_directory(TOOL_DIR, "gallery.html")


@app.route("/api/component_categories")
def api_comp_categories():
    return jsonify({k: {"description": COMPONENT_CATEGORIES[k], "styles": styles}
                    for k, (_, styles) in GENERATORS.items()})


@app.route("/api/generate_component", methods=["POST"])
def api_gen_component():
    params = request.get_json() or {}
    category = params.get("category", "cockpit")
    style = params.get("style")
    size = float(params.get("size", 1.0))
    seed = params.get("seed")
    if seed == "" or seed is None:
        seed = None
    else:
        seed = int(seed)
    result = generate_component(category=category, style=style, size=size, seed=seed)
    return jsonify(result)


@app.route("/api/save_component", methods=["POST"])
def api_save_component():
    data = request.get_json()
    name = data.get("name", "unnamed")
    safe_name = "".join(c for c in name if c.isalnum() or c in "_-").lower()
    path = os.path.join(COMP_DIR, f"{safe_name}.json")
    with open(path, "w") as f:
        json.dump(data["component"], f, indent=2)
    return jsonify({"status": "saved", "path": path})


@app.route("/api/saved_components")
def api_saved_components():
    files = [f[:-5] for f in os.listdir(COMP_DIR) if f.endswith(".json")]
    return jsonify(files)


@app.route("/api/load_component/<name>")
def api_load_component(name):
    path = os.path.join(COMP_DIR, f"{name}.json")
    if not os.path.exists(path):
        return jsonify({"error": "not found"}), 404
    with open(path) as f:
        return jsonify(json.load(f))


@app.route("/api/export_tagged", methods=["POST"])
def api_export_tagged():
    data = request.get_json()
    path = os.path.join(TOOL_DIR, "tagged_feedback.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return jsonify({"status": "saved", "path": path, "count": len(data)})


@app.route("/api/all_components")
def api_all_components():
    """Return every component: generated styles + saved custom ones."""
    items = []
    # Generated styles
    for cat, (fn, styles) in GENERATORS.items():
        for style in styles:
            result = fn(style=style, size=1.0, seed=42)
            items.append({"name": f"{cat}/{style}", "category": cat, "parts": result["parts"]})
    # Saved custom components
    for fname in sorted(os.listdir(COMP_DIR)):
        if not fname.endswith(".json"):
            continue
        with open(os.path.join(COMP_DIR, fname)) as f:
            data = json.load(f)
        name = fname[:-5]
        items.append({"name": name, "category": data.get("category", "other"), "parts": data["parts"]})
    return jsonify(items)


if __name__ == "__main__":
    port = 5050
    print(f"Ship Designer running at http://localhost:{port}")
    webbrowser.open(f"http://localhost:{port}")
    app.run(port=port, debug=True)
