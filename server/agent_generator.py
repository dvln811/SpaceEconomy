"""Randomized faction agent generator. Creates named agents with personality traits."""
import random
import sqlite3
import json
import os

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "game_data.db")

# Name pools
FIRST_NAMES = [
    'Wei', 'Elena', 'Dmitri', 'Lyra', 'Adisa', 'Hana', 'Victor', 'Camila', 'Marcus',
    'Fatima', 'Zara', 'Jack', 'Maria', 'Linh', 'Alexei', 'Irena', 'Conrad', 'Oleg',
    'Silas', 'Jax', 'Quinn', 'Mira', 'Yuki', 'Kai', 'Amir', 'Selene', 'Ravi',
    'Nadia', 'Tobias', 'Ingrid', 'Hassan', 'Yuna', 'Darius', 'Freya', 'Kofi',
    'Anastasia', 'Rafael', 'Petra', 'Idris', 'Soren', 'Celeste', 'Nikolai', 'Thea',
    'Emeka', 'Aria', 'Kenji', 'Astrid', 'Omar', 'Valentina', 'Ronan', 'Ines',
]
LAST_NAMES = [
    'Chen', 'Harris', 'Volkov', 'Voss', 'Okafor', 'Reis', 'Cross', 'Silva', 'Brennan',
    'Nouri', 'Okoro', 'Frost', 'Santos', 'Nguyen', 'Krov', 'Steele', 'Drake', 'Petrov',
    'Vex', 'Black', 'Tanaka', 'Park', 'Reeves', 'Andersson', 'Vasquez', 'Okonkwo',
    'Muller', 'Nakamura', 'Volkov', 'Sharma', 'Johansson', 'Al-Rashid', 'Moreau',
    'Kovacs', 'Nkosi', 'Eriksson', 'Torres', 'Ivanov', 'Kimura', 'Ferraro',
    'Larsson', 'Osman', 'Novak', 'Delacroix', 'Arias', 'Bergman', 'Kaur', 'Thorne',
]

# Title templates by role
TITLES = {
    'leader': {
        'republic': ['Supreme Commander', 'Chancellor', 'High Admiral', 'President'],
        'technocracy': ['Chief Researcher', 'Archon', 'Prime Director', 'First Scientist'],
        'oligarchy': ['Guild Master', 'Trade Magnate', 'Grand Merchant', 'First Broker'],
        'confederation': ['Elected President', 'Speaker', 'People\'s Marshal', 'Prime Minister'],
        'military_junta': ['Supreme Marshal', 'Grand Marshal', 'Warlord Supreme', 'Iron Fist'],
        'anarchy': ['Pirate King', 'Warlord', 'Blood Captain', 'Dread Lord'],
    },
    'admiral': ['Fleet Admiral', 'Vice Admiral', 'Rear Admiral', 'Commodore', 'Fleet Commander', 'War Captain'],
    'governor': ['System Governor', 'Colonial Director', 'Station Overseer', 'Sector Administrator', 'Prefect'],
    'general': ['General', 'War Strategist', 'Field Marshal', 'Militia Commander', 'Battle Master'],
    'director': ['Trade Director', 'Market Director', 'Operations Chief', 'Logistics Director', 'Supply Master'],
    'spymaster': ['Intelligence Director', 'Shadow Broker', 'Information Chief', 'Eyes of the Council', 'Ghost'],
}

# Faction personality bias (agents trend toward these)
FACTION_BIAS = {
    'terran_fed': {'aggression': -0.2, 'caution': 0.2, 'loyalty': 0.1, 'competence': 0.1},
    'science_collective': {'aggression': -0.3, 'competence': 0.2, 'ambition': 0.1},
    'merchants_guild': {'caution': 0.1, 'ambition': 0.2, 'corruption': 0.1},
    'free_states': {'loyalty': 0.2, 'aggression': 0.1, 'caution': -0.1},
    'iron_compact': {'aggression': 0.3, 'caution': -0.2, 'ambition': 0.2},
    'corsairs': {'aggression': 0.3, 'loyalty': -0.3, 'corruption': 0.2, 'caution': -0.2},
}

AGENT_SLOTS = [
    ('admiral', 1),
    ('governor', 1),
    ('general', 0.5),   # 50% chance
    ('director', 0.5),
    ('spymaster', 0.4),
]


def generate_name(used_names):
    """Generate a unique name."""
    for _ in range(100):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        name = f"{first} {last}"
        if name not in used_names:
            used_names.add(name)
            return name
    return f"Agent-{random.randint(1000,9999)}"


def generate_trait(base=0.5, bias=0.0):
    """Generate a trait value with noise and bias."""
    val = base + bias + random.gauss(0, 0.15)
    return round(max(0.05, min(0.95, val)), 2)


def generate_agents(faction_id, government, rng=None):
    """Generate a full set of agents for a faction."""
    if rng:
        random.seed(rng)

    bias = FACTION_BIAS.get(faction_id, {})
    used_names = set()
    agents = []

    # Leader
    name = generate_name(used_names)
    title_pool = TITLES['leader'].get(government, ['Leader'])
    title = random.choice(title_pool)
    agents.append({
        'id': f"{faction_id}_leader",
        'name': name,
        'title': title,
        'faction_id': faction_id,
        'role': 'leader',
        'aggression': generate_trait(0.5, bias.get('aggression', 0)),
        'caution': generate_trait(0.5, bias.get('caution', 0)),
        'competence': generate_trait(0.7, bias.get('competence', 0)),
        'loyalty': generate_trait(0.8, bias.get('loyalty', 0)),
        'ambition': generate_trait(0.6, bias.get('ambition', 0)),
        'corruption': generate_trait(0.1, bias.get('corruption', 0)),
    })

    # Other agents
    for role, chance in AGENT_SLOTS:
        if random.random() > chance:
            continue
        name = generate_name(used_names)
        title_pool = TITLES.get(role, ['Officer'])
        title = random.choice(title_pool)
        agents.append({
            'id': f"{faction_id}_{role}_{random.randint(100,999)}",
            'name': name,
            'title': title,
            'faction_id': faction_id,
            'role': role,
            'aggression': generate_trait(0.5, bias.get('aggression', 0)),
            'caution': generate_trait(0.5, bias.get('caution', 0)),
            'competence': generate_trait(0.5, bias.get('competence', 0)),
            'loyalty': generate_trait(0.7, bias.get('loyalty', 0)),
            'ambition': generate_trait(0.4, bias.get('ambition', 0)),
            'corruption': generate_trait(0.15, bias.get('corruption', 0)),
        })

    return agents


def regenerate_all():
    """Regenerate all faction agents in the database."""
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    # Get faction governments
    states = conn.execute("SELECT faction_id, government FROM faction_state").fetchall()

    conn.execute("DELETE FROM faction_agents")

    all_agents = []
    for state in states:
        agents = generate_agents(state['faction_id'], state['government'])
        all_agents.extend(agents)
        # Update leader reference
        leader = next(a for a in agents if a['role'] == 'leader')
        conn.execute("UPDATE faction_state SET leader_id=? WHERE faction_id=?",
                     (leader['id'], state['faction_id']))

    for a in all_agents:
        conn.execute("""INSERT INTO faction_agents
            (id, name, title, faction_id, role, aggression, caution, competence, loyalty, ambition, corruption)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (a['id'], a['name'], a['title'], a['faction_id'], a['role'],
             a['aggression'], a['caution'], a['competence'], a['loyalty'], a['ambition'], a['corruption']))

    conn.commit()
    conn.close()
    return all_agents


def regenerate_faction(faction_id):
    """Regenerate agents for a single faction."""
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    state = conn.execute("SELECT government FROM faction_state WHERE faction_id=?", (faction_id,)).fetchone()
    if not state:
        conn.close()
        return []

    conn.execute("DELETE FROM faction_agents WHERE faction_id=?", (faction_id,))
    agents = generate_agents(faction_id, state['government'])

    leader = next(a for a in agents if a['role'] == 'leader')
    conn.execute("UPDATE faction_state SET leader_id=? WHERE faction_id=?", (leader['id'], faction_id))

    for a in agents:
        conn.execute("""INSERT INTO faction_agents
            (id, name, title, faction_id, role, aggression, caution, competence, loyalty, ambition, corruption)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (a['id'], a['name'], a['title'], a['faction_id'], a['role'],
             a['aggression'], a['caution'], a['competence'], a['loyalty'], a['ambition'], a['corruption']))

    conn.commit()
    conn.close()
    return agents
