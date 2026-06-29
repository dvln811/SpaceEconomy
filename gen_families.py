"""Assign clans, ages, gender, and family relationships to existing agents."""
import sqlite3, random

conn = sqlite3.connect('data/game_data.db')
conn.row_factory = sqlite3.Row

# Female first names (union of all faction pools)
FEMALE_NAMES = {
    'Anastasia','Selene','Valentina','Octavia','Livia','Cassia','Aurelia','Petra','Irena','Natasha',
    'Katya','Galina','Tatiana','Marina','Daria','Helena','Diana','Julia','Cordelia','Minerva','Lucretia',
    'Camila','Ines','Ada','Marie','Rosalind','Emmy','Hypatia','Lise','Vera','Jocelyn','Maryam',
    'Cecilia','Chien','Nettie','Sofia','Elara','Nova','Stella','Lyra','Astrid','Celeste',
    'Linh','Zara','Priya','Mei','Noor','Aisha','Sakura','Fatima','Ananya','Suki','Jade','Pearl',
    'Amber','Ruby','Sapphire','Leila','Yasmin','Kamala','Indira','Padma','Lakshmi',
    'Maria','Mira','Freya','Ingrid','Sigrid','Ragna','Solveig','Hilda','Bryn','Wren','Fern',
    'Ivy','Sage','Dawn','Ember','Storm','Sky','River','Willow',
    'Brenna','Sigrun','Helga','Brunhild','Katarina','Olga','Natalia','Svetlana','Yelena',
    'Marta','Greta','Isolde','Dagny','Ragnhild','Thora',
    'Yuki','Yuna','Red','Scarlet','Tempest','Raven','Vex','Nyx','Luna','Onyx','Ash','Crimson',
    'Sable','Thorn','Echo','Fury','Havoc','Jinx','Riot','Blaze','Phantom',
    'Elena','Hana','Quinn','Nadia','Freya','Thea','Aria',
    'Fatima','Ines','Adisa',
}

# Clan name pools by faction
CLAN_NAMES = {
    'terran_fed': ['Eriksson', 'Volkov', 'Corvinus', 'Severus', 'Galkin', 'Orlov', 'Drathen', 'Marcellus'],
    'science_collective': ['Steele', 'Penrose', 'Curie', 'Kepler', 'Hopper', 'Dirac', 'Sagan', 'Maxwell'],
    'merchants_guild': ['Ivanov', 'Goldstein', 'Patel', 'Chen', 'Al-Rashid', 'Kapoor', 'Rothschild', 'Morgan'],
    'free_states': ['Stormborn', 'Ironside', 'Blackwood', 'Wolfram', 'Clearwater', 'Oakenshield', 'Frostborn', 'Hawksworth'],
    'iron_compact': ['Krov', 'Stahl', 'Eisenfaust', 'Hammerfell', 'Ironforge', 'Steelborn', 'Anvil', 'Crucible'],
    'corsairs': ['Black', 'Dread', 'Bloodaxe', 'Hellfire', 'Darkstar', 'Void', 'Graves', 'Razorblade'],
}

AGE_RANGES = {
    'leader': (45, 70), 'admiral': (40, 65), 'governor': (38, 60),
    'general': (35, 58), 'director': (32, 55), 'spymaster': (30, 50),
    'station_commander': (30, 55), 'fleet_captain': (25, 50),
    'merchant_lord': (28, 60), 'mining_foreman': (30, 55),
    'factory_overseer': (28, 50), 'mercenary_leader': (22, 45),
    'smuggler': (20, 40), 'diplomat': (30, 55),
    'bounty_hunter': (22, 40), 'spy': (22, 38),
}

def infer_gender(name):
    first = name.split()[0] if ' ' in name else name
    return 'female' if first in FEMALE_NAMES else 'male'

# Clear old family data
conn.execute("UPDATE faction_agents SET spouse_id='', parent_id='', clan='', age=35, gender=''")
conn.commit()

factions = [r['id'] for r in conn.execute("SELECT id FROM factions").fetchall()]

for fid in factions:
    agents = conn.execute("SELECT id, role, name FROM faction_agents WHERE faction_id=? AND alive=1", (fid,)).fetchall()
    clans = CLAN_NAMES.get(fid, ['Unknown'])

    for a in agents:
        last_name = a['name'].split()[-1] if ' ' in a['name'] else ''
        clan = last_name if last_name in clans else random.choice(clans)
        low, high = AGE_RANGES.get(a['role'], (25, 50))
        age = random.randint(low, high)
        gender = infer_gender(a['name'])
        conn.execute("UPDATE faction_agents SET clan=?, age=?, gender=? WHERE id=?", (clan, age, gender, a['id']))

    # Marriages: opposite-sex only, within same faction
    agent_list = [dict(a) for a in agents]
    for a in agent_list:
        a['gender'] = infer_gender(a['name'])
    males = [a for a in agent_list if a['gender'] == 'male']
    females = [a for a in agent_list if a['gender'] == 'female']
    random.shuffle(males)
    random.shuffle(females)
    married = set()
    pairs = min(len(males), len(females))
    for i in range(pairs):
        if random.random() < 0.35:
            m, f = males[i], females[i]
            if m['id'] not in married and f['id'] not in married:
                conn.execute("UPDATE faction_agents SET spouse_id=? WHERE id=?", (f['id'], m['id']))
                conn.execute("UPDATE faction_agents SET spouse_id=? WHERE id=?", (m['id'], f['id']))
                married.add(m['id'])
                married.add(f['id'])

    # Parent links within same clan (parent must be 16+ years older)
    by_clan = {}
    for a in agent_list:
        last_name = a['name'].split()[-1] if ' ' in a['name'] else ''
        c = last_name if last_name in clans else random.choice(clans)
        if c not in by_clan:
            by_clan[c] = []
        by_clan[c].append(a)
    for clan, members in by_clan.items():
        if len(members) < 2:
            continue
        for m in members[1:]:
            if random.random() < 0.25:
                # Find oldest member as potential parent
                parent = members[0]
                p_age = AGE_RANGES.get(parent['role'], (25,50))[1]
                c_age = AGE_RANGES.get(m['role'], (25,50))[0]
                if p_age - c_age >= 16:
                    conn.execute("UPDATE faction_agents SET parent_id=? WHERE id=?", (parent['id'], m['id']))

conn.commit()

total = conn.execute("SELECT count(*) FROM faction_agents WHERE clan != ''").fetchone()[0]
spouses = conn.execute("SELECT count(*) FROM faction_agents WHERE spouse_id != ''").fetchone()[0]
parents = conn.execute("SELECT count(*) FROM faction_agents WHERE parent_id != ''").fetchone()[0]
conn.close()
print(f"Assigned clans to {total} agents, {spouses} married (opposite-sex only), {parents} with parent links")

