import json
d = json.load(open('_model_data.json'))
p = d['ships']['pinto_runner']
print(f"Pinto Runner: {len(p.get('components', []))} components")
print(json.dumps(p['components'][0], indent=2) if p.get('components') else "NO COMPONENTS")
