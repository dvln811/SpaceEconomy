import sqlite3, math, random, json
random.seed(99)
conn = sqlite3.connect('data/game_data.db')
conn.row_factory = sqlite3.Row
conn.execute("DELETE FROM system_objects WHERE system_id='rigel'")

n = 0
def nid():
    global n; n += 1; return f'rigel_{n:04d}'

def ins(oid, name, otype, dist, angle, incl=0, parent='', ptype='', rkm=0, sid='', conn_to='', stats=None):
    conn.execute(
        "INSERT INTO system_objects (id,name,system_id,obj_type,distance,angle,inclination,parent,connects_to,planet_type,radius_km,station_id,stats) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (oid, name, 'rigel', otype, round(dist,4), round(angle,4), round(incl,4), parent, conn_to, ptype, rkm, sid, json.dumps(stats) if stats else ''))

ins(nid(), 'Rigel Star', 'star', 0, 0)

planets = [
    ('Rigel I',   1.8, 'rocky',       2800, 0,  0.08),
    ('Rigel II',  3.5, 'desert',      5200, 1, -0.12),
    ('Rigel III', 6.2, 'terrestrial', 6400, 1,  0.05),
    ('Rigel IV', 10.5, 'gas_giant',  52000, 3, -0.03),
    ('Rigel V',  16.0, 'ice_giant',  28000, 2,  0.10),
    ('Rigel VI', 22.0, 'ice',         3800, 0, -0.14),
]

pids = {}
for nm, dist, pt, rkm, nmoons, incl in planets:
    pid = nid()
    ang = random.uniform(0, 2*math.pi)
    pids[nm] = (pid, dist, ang)
    ins(pid, nm, 'planet', dist, ang, incl, ptype=pt, rkm=rkm, stats={'radius_km': rkm, 'planet_type': pt})
    for mi in range(nmoons):
        mid = nid()
        if pt in ('gas_giant', 'ice_giant'):
            md = (rkm * (5 + mi*4 + random.uniform(0,3))) / 150000000
        else:
            md = (rkm * (15 + mi*20 + random.uniform(0,10))) / 150000000
        mtype = random.choice(['rocky_moon', 'ice_moon', 'volcanic_moon'])
        mrkm = random.randint(300, 2500)
        ins(mid, f'{nm}-{chr(97+mi)}', 'moon', md, random.uniform(0, 2*math.pi),
            random.uniform(-0.3, 0.3), parent=pid, ptype=mtype, rkm=mrkm)

stations = conn.execute("SELECT id, name, station_type FROM stations WHERE system_id='rigel'").fetchall()
st_list = list(stations)

if len(st_list) > 0:
    pid, d, a = pids['Rigel III']
    od = (6400 * 2.0) / 150000000
    ins(nid(), st_list[0]['name'], 'station', od, a+0.3, 0.04, parent=pid, sid=st_list[0]['id'])
if len(st_list) > 1:
    pid, d, a = pids['Rigel IV']
    od = (52000 * 1.5) / 150000000
    ins(nid(), st_list[1]['name'], 'station', od, a-0.2, -0.02, parent=pid, sid=st_list[1]['id'])
for i, st in enumerate(st_list[2:], 2):
    sd = 4.0 + i*2.5 + random.uniform(0, 1.5)
    ins(nid(), st['name'], 'station', sd, random.uniform(0, 2*math.pi), random.uniform(-0.08, 0.08), sid=st['id'])

for gi, dest in enumerate(['NCD-286', 'Struve', 'Regulus', 'Canopus', 'Procyon']):
    gd = 25.0 + gi*2.0 + random.uniform(0, 1.0)
    ga = (2*math.pi/5)*gi + random.uniform(-0.2, 0.2)
    ins(nid(), f'Gate to {dest}', 'gate', gd, ga, random.uniform(-0.05, 0.05), conn_to=dest)

conn.commit()
print('Rigel rebuilt with inclinations')
