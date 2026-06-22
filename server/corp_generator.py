"""Corporation generator. Creates named corps with emblems, head agents, and specialties."""
import random
import sqlite3
import json
import os

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "game_data.db")
EMBLEM_TAGS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "emblem_tags.json")
PORTRAIT_TAGS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "portrait_tags.json")

# Faction -> archetype preference for emblem selection
FACTION_ARCHETYPE = {
    'corsairs': 'renegade',
    'free_states': 'military',
    'iron_compact': 'military',
    'merchants_guild': 'corporate',
    'science_collective': 'corporate',
    'terran_fed': 'military',
}

# How many corps per faction at start
FACTION_CORP_COUNT = {
    'terran_fed': 8,
    'iron_compact': 8,
    'free_states': 7,
    'merchants_guild': 9,
    'science_collective': 7,
    'corsairs': 6,  # renegade/independent
}

SPECIALTIES = [
    'mining', 'refining', 'weapons_manufacturing', 'ship_construction',
    'logistics', 'defense_contracting', 'electronics', 'pharmaceuticals',
    'energy_systems', 'trade_brokerage', 'salvage_operations', 'research',
]

# Corp name parts
PREFIXES = [
    'Apex', 'Nova', 'Stellar', 'Vanguard', 'Ares', 'Orion', 'Helios', 'Titan',
    'Obsidian', 'Crimson', 'Iron', 'Black', 'Deep', 'Void', 'Arc', 'Quantum',
    'Zenith', 'Cobalt', 'Nexus', 'Phoenix', 'Aegis', 'Talon', 'Raven', 'Forge',
    'Crescent', 'Meridian', 'Solaris', 'Tempest', 'Shadow', 'Citadel', 'Frontier',
    'Polar', 'Dusk', 'Vector', 'Prism', 'Core', 'Axiom', 'Atlas', 'Bastion',
]
SUFFIXES = [
    'Industries', 'Corp', 'Dynamics', 'Systems', 'Works', 'Holdings',
    'Collective', 'Foundries', 'Ventures', 'Logistics', 'Solutions',
    'Armaments', 'Syndicate', 'Consortium', 'Group', 'Technologies',
    'Enterprises', 'Fleet', 'Mining Co', 'Shipwrights', 'Arsenal',
]

# Head agent name pools
FIRST_NAMES_M = [
    'Viktor', 'Darius', 'Kofi', 'Soren', 'Alexei', 'Jin', 'Ronan', 'Idris',
    'Marcus', 'Tobias', 'Omar', 'Kenji', 'Rafael', 'Nikolai', 'Emeka', 'Ravi',
    'Conrad', 'Amir', 'Hassan', 'Silas',
]
FIRST_NAMES_F = [
    'Elena', 'Lyra', 'Hana', 'Camila', 'Fatima', 'Zara', 'Mira', 'Yuki',
    'Selene', 'Nadia', 'Ingrid', 'Yuna', 'Freya', 'Anastasia', 'Petra',
    'Aria', 'Astrid', 'Valentina', 'Ines', 'Celeste',
]
LAST_NAMES = [
    'Chen', 'Volkov', 'Okafor', 'Reis', 'Cross', 'Brennan', 'Nouri', 'Frost',
    'Tanaka', 'Reeves', 'Vasquez', 'Muller', 'Nakamura', 'Sharma', 'Moreau',
    'Kovacs', 'Eriksson', 'Torres', 'Kimura', 'Ferraro', 'Larsson', 'Novak',
    'Delacroix', 'Bergman', 'Thorne', 'Osman', 'Kaur', 'Steele', 'Drake', 'Voss',
]


def _load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


HISTORY_TEMPLATES = [
    "Founded {years} years ago in the {region} sector, {name} began as a small {specialty} outfit before expanding into a {faction}-aligned powerhouse.",
    "{name} rose to prominence after securing exclusive {specialty} contracts with the {faction}. Under {ceo}'s leadership, it has grown into one of the sector's most influential corporations.",
    "Originally a family-owned {specialty} venture, {name} was acquired and restructured {years} years ago. Now backed by {faction} capital, it operates across multiple systems.",
    "Born from the ashes of the Collapse, {name} carved out a niche in {specialty}. Its {members:,} employees are fiercely loyal to CEO {ceo}.",
    "{name} was established by ex-military officers seeking profit in the {specialty} trade. It maintains close ties to the {faction} and operates with military precision.",
    "What started as a cooperative of independent {specialty} operators became {name} after {ceo} unified them under a single banner {years} years ago.",
    "A controversial but profitable corporation, {name} dominates {specialty} in its home systems. Critics call it a monopoly; {ceo} calls it efficiency.",
    "{name} emerged from the frontier colonies, building its reputation on reliable {specialty} services. The {faction} granted it exclusive operating licenses {years} years ago.",
]


def generate_corp_history(name, specialty, faction_id, ceo_name, members):
    """Generate a short backstory for a corporation."""
    template = random.choice(HISTORY_TEMPLATES)
    faction_name = faction_id.replace('_', ' ').title()
    return template.format(
        name=name,
        specialty=specialty.replace('_', ' '),
        faction=faction_name,
        ceo=ceo_name,
        years=random.randint(8, 120),
        region=random.choice(['Outer Rim', 'Core', 'Mid-Belt', 'Frontier', 'Deep Space', 'Nexus']),
        members=members,
    )


def assign_stations(faction_id, conn):
    """Pick 1-3 stations in faction territory for a corp to control."""
    rows = conn.execute(
        "SELECT s.id, s.name, sys.id as sys_id, sys.name as sys_name FROM stations s "
        "JOIN systems sys ON s.system_id = sys.id WHERE sys.faction_id = ?",
        (faction_id,)
    ).fetchall()
    if not rows:
        rows = conn.execute(
            "SELECT s.id, s.name, sys.id as sys_id, sys.name as sys_name FROM stations s "
            "JOIN systems sys ON s.system_id = sys.id LIMIT 20"
        ).fetchall()
    count = random.choices([1, 2, 3], weights=[50, 35, 15])[0]
    picks = random.sample(rows, min(count, len(rows))) if rows else []
    return json.dumps([{"station": r[1], "system": r[3], "system_id": r[2]} for r in picks])


def generate_corp_name(used_names):
    for _ in range(200):
        name = f"{random.choice(PREFIXES)} {random.choice(SUFFIXES)}"
        if name not in used_names:
            used_names.add(name)
            return name
    return f"Corp-{random.randint(1000,9999)}"


def pick_emblem(archetype, used_emblems, emblem_tags):
    """Pick an emblem matching archetype, fallback to any unused."""
    candidates = [f for f, t in emblem_tags.items()
                  if t['archetype'] == archetype and f not in used_emblems]
    if not candidates:
        candidates = [f for f in emblem_tags if f not in used_emblems]
    if not candidates:
        return None
    pick = random.choice(candidates)
    used_emblems.add(pick)
    return pick


def pick_head_portrait(gender, archetype, used_portraits, portrait_tags):
    """Pick a portrait for the corp head agent."""
    candidates = [f for f, t in portrait_tags.items()
                  if t['archetype'] == archetype and t['gender'] == gender
                  and f not in used_portraits]
    if not candidates:
        candidates = [f for f, t in portrait_tags.items()
                      if t['archetype'] == archetype and f not in used_portraits]
    if not candidates:
        candidates = [f for f in portrait_tags if f not in used_portraits]
    if not candidates:
        return None
    pick = random.choice(candidates)
    used_portraits.add(pick)
    return pick


def seed_corporations():
    """Generate and insert the initial set of corporations."""
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("DELETE FROM corporations")
    conn.execute("DELETE FROM faction_agents WHERE id LIKE 'corp_%'")

    emblem_tags = _load_json(EMBLEM_TAGS_PATH)
    portrait_tags = _load_json(PORTRAIT_TAGS_PATH)

    used_names = set()
    used_emblems = set()
    used_portraits = set()

    # Reserve portraits already used by faction agents
    rows = conn.execute("SELECT portrait FROM faction_agents WHERE portrait IS NOT NULL").fetchall()
    used_portraits.update(r[0] for r in rows)

    corps = []
    for faction_id, count in FACTION_CORP_COUNT.items():
        archetype = FACTION_ARCHETYPE[faction_id]
        for _ in range(count):
            name = generate_corp_name(used_names)
            emblem = pick_emblem(archetype, used_emblems, emblem_tags)
            specialty = random.choice(SPECIALTIES)
            corp_id = name.lower().replace(' ', '_').replace("'", '')

            # Head agent
            gender = random.choice(['male', 'female'])
            first = random.choice(FIRST_NAMES_M if gender == 'male' else FIRST_NAMES_F)
            last = random.choice(LAST_NAMES)
            head_name = f"{first} {last}"
            portrait = pick_head_portrait(gender, archetype, used_portraits, portrait_tags)
            head_id = f"corp_{corp_id}_ceo"

            # Corp details
            members = random.randint(800, 45000)
            stations_json = assign_stations(faction_id, conn)
            history = generate_corp_history(name, specialty, faction_id, head_name, members)

            # Insert head agent into faction_agents
            conn.execute("""INSERT INTO faction_agents
                (id, name, title, faction_id, role, aggression, caution, competence,
                 loyalty, ambition, corruption, bio, portrait)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (head_id, head_name, 'CEO', faction_id, 'director',
                 round(random.gauss(0.5, 0.15), 2),
                 round(random.gauss(0.5, 0.15), 2),
                 round(random.gauss(0.6, 0.15), 2),
                 round(random.gauss(0.6, 0.15), 2),
                 round(random.gauss(0.7, 0.12), 2),
                 round(random.gauss(0.2, 0.1), 2),
                 history, portrait))

            corps.append((corp_id, name, emblem, faction_id, specialty, head_id, 0, 'active', history, members, stations_json))

    conn.executemany("""INSERT INTO corporations
        (id, name, emblem, faction_id, specialty, head_agent_id, founded_tick, status, history, members, stations)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)""", corps)

    conn.commit()
    conn.close()
    print(f"Seeded {len(corps)} corporations")
    return corps


if __name__ == '__main__':
    seed_corporations()
