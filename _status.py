content = open('warp_game_work.html', 'r', encoding='utf-8').read()
checks = [
    ('Hardcoded Rigel data', "system_id: 'rigel'" in content),
    ('SSE disabled', 'function connectStream(){ return; }' in content),
    ('STANDALONE_MODE flag', 'STANDALONE_MODE = true' in content),
    ('Fetch stub', '_realFetch' in content),
    ('INLINE_MODELS (pinto_runner)', '"pinto_runner"' in content),
    ('Real ship_renderer inlined', 'SHIP_MATERIALS' in content),
    ('Planet texture inline', 'function genPlanetTex' in content),
    ('Analytical warp (t^4)', 'Math.pow(at, 4)' in content),
    ('Analytical integral (t^5)', 'Math.pow(t, 5)' in content),
    ('WARP_TOP_SPEED', 'WARP_TOP_SPEED' in content),
    ('WARP_SCALE_FACTOR', 'WARP_SCALE_FACTOR' in content),
    ('SSG distKm/SCALE_FACTOR', 'distKm / SSG_SCALE_FACTOR' in content),
    ('_playerSS usage', '_playerSS' in content),
    ('Fade overlay opacity:0', 'opacity:0' in content),
    ('isDocked = false', 'isDocked = false' in content),
    ('Layout = flight', 'layout flight' in content),
    ('Hull class ship scaling', 'SHIP_LENGTHS_M' in content),
    ('Station km scaling', "'trade_hub':150" in content),
    ('Gate scaling (20/maxDim)', '20 / maxDim' in content),
    ('Orbit offset (radius*1.5)', 'radius_km * 1.5' in content or 'radius_km*1.5' in content),
]
print('=== warp_game_work.html STATUS ===')
for name, present in checks:
    print(f'  {"YES" if present else "NO ":3s}  {name}')
print(f'\nTotal lines: {content.count(chr(10))+1}')
