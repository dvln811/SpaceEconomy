import requests, json
r = requests.get('http://127.0.0.1:8000/api/system/rigel', timeout=5)
data = r.json()
planets = [o for o in data['objects'] if o['type'] in ('planet', 'moon')]
print(f"Planets/moons in Rigel: {len(planets)}")
for p in planets[:5]:
    print(f"  {p['name']:20s} type={p['type']:10s} radius_km={p.get('radius_km',0):>8} ss_x={p.get('ss_x','MISS'):>10} ss_y={p.get('ss_y','MISS'):>10}")
