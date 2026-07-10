import requests
r = requests.get('http://127.0.0.1:8000/api/player/local_space/stream', stream=True, timeout=10, headers={'Accept':'text/event-stream'})
for i, line in enumerate(r.iter_lines(decode_unicode=True)):
    if line.startswith('data:'):
        import json
        data = json.loads(line[5:])
        planets = [o for o in data.get('objects',[]) if o['type'] in ('planet','moon')]
        print(f"Objects: {len(data.get('objects',[]))}, Planets/moons: {len(planets)}")
        for p in planets[:3]:
            print(f"  {p['name']:20s} ss_x={p.get('ss_x','MISS'):>10} ss_y={p.get('ss_y','MISS'):>10} ss_z={p.get('ss_z','MISS'):>10} radius_km={p.get('radius_km',0)}")
        break
    if i > 20:
        print("No data received")
        break
