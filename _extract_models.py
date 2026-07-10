import json

d = json.load(open('_model_data.json'))

# Just pinto_runner, station, gate
subset = {
    'pinto_runner': d['ships']['pinto_runner'],
    'station': d['station'],
    'gate': d['gate'],
}

# Write as compact JS
with open('_inline_models.js', 'w', encoding='utf-8') as f:
    f.write("// -- INLINE MODEL DATA (extracted from server, swap back to fetch when integrating) --\n")
    f.write("const INLINE_MODELS = ")
    f.write(json.dumps(subset, separators=(',', ':')))
    f.write(";\n")

print(f"Written _inline_models.js: {len(json.dumps(subset, separators=(',',':')))} chars")
print(f"  pinto_runner: {len(subset['pinto_runner']['components'])} components")
print(f"  station: {len(subset['station'].get('components', []))} components")
print(f"  gate: {len(subset['gate'].get('components', []))} components")
