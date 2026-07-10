"""Grab model data from running server and save as JSON for inline use."""
import requests, json

# Ship models (all classes)
print("Fetching ship models...")
r = requests.get('http://127.0.0.1:8000/api/ship_model/all', timeout=10)
ships = r.json()
print(f"  Got {len(ships)} ship classes: {list(ships.keys())}")

# Station model (just one - trade_hub)
print("Fetching station model...")
r = requests.get('http://127.0.0.1:8000/api/station_model/st_00028', timeout=10)
station = r.json()
print(f"  Got station: {station.get('station_type', '?')}, {len(station.get('components', []))} components")

# Gate model
print("Fetching gate model...")
r = requests.get('http://127.0.0.1:8000/api/gate_model/rigel/rigel_0021', timeout=10)
gate = r.json()
print(f"  Got gate: {len(gate.get('components', []))} components")

# Save all to one file
output = {
    'ships': ships,
    'station': station,
    'gate': gate,
}
with open('_model_data.json', 'w') as f:
    json.dump(output, f)
print(f"\nSaved to _model_data.json ({len(json.dumps(output))} bytes)")

# Also print Frigate model for quick reference
frigate = ships.get('Frigate', {})
print(f"\nFrigate components: {len(frigate.get('components', []))}")
