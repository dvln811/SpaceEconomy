"""Generate M&B-style agent population: 50-100 per faction with station/system assignments."""
import sqlite3
import random
import json
import os

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "game_data.db")

# Extended name pools by faction culture
NAMES_BY_FACTION = {
    'terran_fed': {
        'first_m': ['Marcus', 'Victor', 'Adrian', 'Cassius', 'Julius', 'Gaius', 'Lucius', 'Tiberius',
                    'Maximus', 'Decimus', 'Corvus', 'Darius', 'Octavian', 'Aurelius', 'Konstantin',
                    'Dmitri', 'Nikolai', 'Alexei', 'Roman', 'Anton', 'Pavel', 'Sergei', 'Ivan'],
        'first_f': ['Anastasia', 'Selene', 'Valentina', 'Octavia', 'Livia', 'Cassia', 'Aurelia',
                    'Petra', 'Irena', 'Natasha', 'Katya', 'Galina', 'Tatiana', 'Marina', 'Daria',
                    'Helena', 'Diana', 'Julia', 'Cordelia', 'Minerva', 'Lucretia'],
        'last': ['Volkov', 'Eriksson', 'Petrova', 'Crassus', 'Corvinus', 'Marcellus', 'Severus',
                 'Cassius', 'Brennan', 'Voss', 'Novak', 'Kessler', 'Richter', 'Voronov',
                 'Galkin', 'Orlov', 'Kuznetsov', 'Morozov', 'Sokolov', 'Volkov', 'Drathen'],
    },
    'science_collective': {
        'first_m': ['Kai', 'Alexei', 'Felix', 'Theo', 'Jasper', 'Cedric', 'Raphael', 'Leon',
                    'Casper', 'Magnus', 'Quentin', 'Edgar', 'Newton', 'Pascal', 'Werner',
                    'Nikola', 'Erwin', 'Faraday', 'Kelvin', 'Planck', 'Darwin', 'Hawking'],
        'first_f': ['Camila', 'Ines', 'Ada', 'Marie', 'Rosalind', 'Emmy', 'Hypatia', 'Lise',
                    'Vera', 'Jocelyn', 'Maryam', 'Cecilia', 'Chien', 'Nettie', 'Sofia',
                    'Elara', 'Nova', 'Stella', 'Lyra', 'Astrid', 'Celeste'],
        'last': ['Steele', 'Okonkwo', 'Reeves', 'Voss', 'Curie', 'Feynman', 'Heisenberg',
                 'Penrose', 'Turing', 'Lovelace', 'Hopper', 'Dirac', 'Bohr', 'Kepler',
                 'Sagan', 'Hawkins', 'Thorne', 'Maxwell', 'Faraday', 'Wigner'],
    },
    'merchants_guild': {
        'first_m': ['Ravi', 'Silas', 'Quinn', 'Tariq', 'Hassan', 'Jin', 'Feng', 'Amir',
                    'Rohan', 'Vikram', 'Chen', 'Bao', 'Kamal', 'Navid', 'Sanjay',
                    'Yusuf', 'Ibrahim', 'Rajesh', 'Arjun', 'Malik', 'Zafar'],
        'first_f': ['Linh', 'Zara', 'Priya', 'Mei', 'Noor', 'Aisha', 'Sakura', 'Fatima',
                    'Ananya', 'Suki', 'Jade', 'Pearl', 'Amber', 'Ruby', 'Sapphire',
                    'Leila', 'Yasmin', 'Kamala', 'Indira', 'Padma', 'Lakshmi'],
        'last': ['Ivanov', 'Tanaka', 'Sharma', 'Chen', 'Goldstein', 'Rothschild', 'Morgan',
                 'Patel', 'Khan', 'Nakamura', 'Park', 'Osei', 'Al-Rashid', 'Gupta',
                 'Chandra', 'Mehta', 'Kapoor', 'Singh', 'Zhao', 'Wong'],
    },
    'free_states': {
        'first_m': ['Soren', 'Omar', 'Finn', 'Bjorn', 'Leif', 'Arlo', 'Colt', 'Ridge',
                    'Stone', 'Flint', 'Hawk', 'Wolf', 'Bear', 'Clay', 'Reed',
                    'Jasper', 'Rowan', 'Ash', 'Heath', 'Sage', 'Bram'],
        'first_f': ['Maria', 'Fatima', 'Mira', 'Freya', 'Ingrid', 'Sigrid', 'Astrid', 'Ragna',
                    'Solveig', 'Hilda', 'Bryn', 'Wren', 'Fern', 'Ivy', 'Sage',
                    'Dawn', 'Ember', 'Storm', 'Sky', 'River', 'Willow'],
        'last': ['Volkov', 'Nkosi', 'Osman', 'Muller', 'Johansson', 'Larsson', 'Stormborn',
                 'Ironside', 'Blackwood', 'Ashford', 'Thornton', 'Hawksworth', 'Clearwater',
                 'Ridgeborn', 'Stoneheart', 'Wolfram', 'Frostborn', 'Oakenshield', 'Windwalker'],
    },
    'iron_compact': {
        'first_m': ['Dmitri', 'Viktor', 'Gunnar', 'Bjorn', 'Ragnar', 'Hector', 'Ajax',
                    'Krov', 'Volkan', 'Krieg', 'Brutus', 'Magnus', 'Thor', 'Ares',
                    'Vulcan', 'Titan', 'Drago', 'Konrad', 'Helmut', 'Gerhard', 'Siegfried'],
        'first_f': ['Ines', 'Hana', 'Brenna', 'Sigrun', 'Helga', 'Brunhild', 'Freya',
                    'Katarina', 'Ingrid', 'Olga', 'Natalia', 'Svetlana', 'Yelena',
                    'Marta', 'Greta', 'Hilda', 'Isolde', 'Dagny', 'Ragnhild', 'Thora'],
        'last': ['Novak', 'Nakamura', 'Kimura', 'Okafor', 'Voss', 'Krov', 'Stahl',
                 'Eisenfaust', 'Hammerfell', 'Ironforge', 'Steelborn', 'Blackiron',
                 'Dreadnought', 'Warbringer', 'Skullcrusher', 'Anvil', 'Crucible', 'Bulwark'],
    },
    'corsairs': {
        'first_m': ['Rafael', 'Jax', 'Vex', 'Crow', 'Shade', 'Razor', 'Fang', 'Scar',
                    'Wraith', 'Ghost', 'Rook', 'Dagger', 'Viper', 'Jackal', 'Raven',
                    'Havoc', 'Jinx', 'Grim', 'Bane', 'Hex', 'Nox'],
        'first_f': ['Yuki', 'Yuna', 'Red', 'Scarlet', 'Tempest', 'Raven', 'Vex', 'Nyx',
                    'Luna', 'Onyx', 'Ash', 'Crimson', 'Sable', 'Thorn', 'Echo',
                    'Fury', 'Havoc', 'Jinx', 'Riot', 'Blaze', 'Phantom'],
        'last': ['Santos', 'Delacroix', 'Black', 'Cross', 'Graves', 'Holloway', 'Blackwood',
                 'Dread', 'Bloodaxe', 'Cutthroat', 'Hellfire', 'Razorblade', 'Deathstrike',
                 'Void', 'Darkstar', 'Bonesaw', 'Killjoy', 'Mayhem', 'Carnage'],
    },
}

# Roles for population agents (below leadership tier)
POPULATION_ROLES = {
    'station_commander': {'count': (3, 6), 'station_types': ['trade_hub', 'military_base', 'shipyard']},
    'fleet_captain': {'count': (5, 10), 'station_types': None},  # assigned to systems
    'merchant_lord': {'count': (4, 8), 'station_types': ['trade_hub']},
    'mining_foreman': {'count': (3, 6), 'station_types': ['mining_colony']},
    'factory_overseer': {'count': (2, 5), 'station_types': ['factory', 'component_works', 'refinery']},
    'mercenary_leader': {'count': (2, 5), 'station_types': None},
    'smuggler': {'count': (1, 3), 'station_types': None},
    'diplomat': {'count': (1, 3), 'station_types': None},
    'bounty_hunter': {'count': (1, 4), 'station_types': None},
    'spy': {'count': (1, 2), 'station_types': None},
}

# Title templates for population agents
POP_TITLES = {
    'station_commander': ['Station Commander', 'Port Authority', 'Dockmaster', 'Garrison Chief'],
    'fleet_captain': ['Captain', 'Wing Commander', 'Squadron Leader', 'Flotilla Chief', 'Patrol Leader'],
    'merchant_lord': ['Trade Baron', 'Merchant Prince', 'Exchange Master', 'Commodity King', 'Broker'],
    'mining_foreman': ['Mining Chief', 'Dig Boss', 'Ore Master', 'Extraction Lead', 'Site Foreman'],
    'factory_overseer': ['Production Chief', 'Assembly Master', 'Forge Director', 'Line Boss'],
    'mercenary_leader': ['Sellsword', 'Gun-for-Hire', 'Freelance Commander', 'Private Contractor'],
    'smuggler': ['Runner', 'Fixer', 'Shadow Broker', 'Contraband Specialist'],
    'diplomat': ['Envoy', 'Ambassador', 'Attaché', 'Negotiator', 'Liaison'],
    'bounty_hunter': ['Hunter', 'Tracker', 'Mark Collector', 'Licensed Pursuer'],
    'spy': ['Operative', 'Shadow Agent', 'Deep Cover', 'Information Broker'],
}

# Faction trait biases
FACTION_BIAS = {
    'terran_fed': {'aggression': -0.1, 'caution': 0.15, 'loyalty': 0.15, 'competence': 0.1},
    'science_collective': {'aggression': -0.2, 'competence': 0.2, 'caution': 0.1},
    'merchants_guild': {'caution': 0.1, 'ambition': 0.2, 'corruption': 0.1, 'competence': 0.05},
    'free_states': {'loyalty': 0.1, 'aggression': 0.05, 'caution': -0.1},
    'iron_compact': {'aggression': 0.25, 'caution': -0.15, 'loyalty': 0.1, 'ambition': 0.15},
    'corsairs': {'aggression': 0.25, 'loyalty': -0.2, 'corruption': 0.15, 'caution': -0.15},
}



def generate_name(faction_id, gender, used_names):
    """Generate a unique name from faction-appropriate pool."""
    pool = NAMES_BY_FACTION.get(faction_id, NAMES_BY_FACTION['terran_fed'])
    first_pool = pool['first_m'] if gender == 'male' else pool['first_f']
    for _ in range(200):
        name = f"{random.choice(first_pool)} {random.choice(pool['last'])}"
        if name not in used_names:
            used_names.add(name)
            return name
    return f"Agent-{random.randint(1000, 9999)}"


def generate_trait(base=0.5, bias=0.0):
    return round(max(0.05, min(0.95, base + bias + random.gauss(0, 0.15))), 2)


def generate_population(faction_id, systems, stations):
    """Generate 50-100 population agents for a faction.
    
    Args:
        faction_id: faction ID
        systems: list of (system_id, system_name) tuples for this faction
        stations: list of (station_id, station_name, station_type, system_id) tuples
    Returns:
        list of agent dicts ready for DB insertion
    """
    bias = FACTION_BIAS.get(faction_id, {})
    used_names = set()
    agents = []

    for role, config in POPULATION_ROLES.items():
        count = random.randint(*config['count'])
        valid_stations = [s for s in stations if config['station_types'] is None or s[2] in config['station_types']]

        for i in range(count):
            gender = random.choice(['male', 'female'])
            name = generate_name(faction_id, gender, used_names)
            title = random.choice(POP_TITLES[role])

            # Assign to station or system
            system_id = ''
            station_id = ''
            if valid_stations and config['station_types']:
                st = random.choice(valid_stations)
                station_id = st[0]
                system_id = st[3]
            elif systems:
                sys_pick = random.choice(systems)
                system_id = sys_pick[0]

            # Pick a patron (random existing agent or empty)
            patron_id = ''
            if agents and random.random() < 0.3:
                patron_id = random.choice(agents)['id']

            agent = {
                'id': f"{faction_id}_{role}_{random.randint(1000, 9999)}_{i}",
                'name': name,
                'title': title,
                'faction_id': faction_id,
                'role': role,
                'aggression': generate_trait(0.5, bias.get('aggression', 0)),
                'caution': generate_trait(0.5, bias.get('caution', 0)),
                'competence': generate_trait(0.5, bias.get('competence', 0)),
                'loyalty': generate_trait(0.6, bias.get('loyalty', 0)),
                'ambition': generate_trait(0.4, bias.get('ambition', 0)),
                'corruption': generate_trait(0.1, bias.get('corruption', 0)),
                'system_id': system_id,
                'station_id': station_id,
                'rank': random.randint(1, 5),
                'wealth': round(random.uniform(50, 500) * (2 if role in ('merchant_lord', 'smuggler') else 1), 1),
                'patron_id': patron_id,
                'rival_id': '',
                'bio': '',
            }
            agents.append(agent)

    # Assign some rivalries
    for agent in agents:
        if random.random() < 0.2 and len(agents) > 5:
            rival = random.choice([a for a in agents if a['id'] != agent['id'] and a['faction_id'] == faction_id])
            agent['rival_id'] = rival['id']

    return agents


def populate_all():
    """Generate population agents for all factions and insert into DB."""
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    # Clear old population agents (keep leadership tier)
    leadership_roles = ('leader', 'admiral', 'governor', 'general', 'director', 'spymaster')
    conn.execute(f"DELETE FROM faction_agents WHERE role NOT IN ({','.join('?' * len(leadership_roles))})",
                 leadership_roles)

    factions = [r['id'] for r in conn.execute("SELECT id FROM factions").fetchall()]
    total = 0

    for fid in factions:
        # Get faction's systems
        systems = [(r['id'], r['name']) for r in
                   conn.execute("SELECT id, name FROM systems WHERE faction_id=?", (fid,)).fetchall()]

        # Get faction's stations (join through systems)
        stations = [(r[0], r[1], r[2], r[3]) for r in
                    conn.execute("""SELECT s.id, s.name, s.station_type, s.system_id
                                    FROM stations s JOIN systems sys ON s.system_id = sys.id
                                    WHERE sys.faction_id = ?""", (fid,)).fetchall()]

        agents = generate_population(fid, systems, stations)

        for a in agents:
            conn.execute("""INSERT INTO faction_agents
                (id, name, title, faction_id, role, aggression, caution, competence,
                 loyalty, ambition, corruption, system_id, station_id, rank, wealth,
                 patron_id, rival_id, bio, alive)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)""",
                (a['id'], a['name'], a['title'], a['faction_id'], a['role'],
                 a['aggression'], a['caution'], a['competence'], a['loyalty'],
                 a['ambition'], a['corruption'], a['system_id'], a['station_id'],
                 a['rank'], a['wealth'], a['patron_id'], a['rival_id'], a['bio']))

        total += len(agents)
        print(f"  {fid}: {len(agents)} agents")

    conn.commit()
    conn.close()
    print(f"Total population agents: {total}")
    return total


if __name__ == "__main__":
    populate_all()
