"""Set up faction AI tables: agents, state, history. Seed initial leadership."""
import sqlite3, json, os, random

random.seed(42)
DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "game_data.db")

FACTIONS = {
    'terran_fed': {
        'government': 'republic', 'aggression': 0.3, 'expansion': 0.4,
        'economic_focus': 0.6, 'diplomacy': 0.7, 'treasury': 50000,
        'leader': ('admiral_chen', 'Admiral Wei Chen', 'Supreme Commander', {'aggression': 0.3, 'caution': 0.7, 'competence': 0.8, 'loyalty': 0.9, 'ambition': 0.4}),
        'agents': [
            ('gov_harris', 'Governor Elena Harris', 'Senator', 'governor', {'aggression': 0.2, 'caution': 0.6, 'competence': 0.7, 'loyalty': 0.8, 'ambition': 0.5}),
            ('adm_volkov', 'Admiral Dmitri Volkov', 'Fleet Admiral', 'admiral', {'aggression': 0.5, 'caution': 0.5, 'competence': 0.9, 'loyalty': 0.7, 'ambition': 0.6}),
            ('dir_park', 'Director Min-Jun Park', 'Intelligence Director', 'spymaster', {'aggression': 0.4, 'caution': 0.8, 'competence': 0.75, 'loyalty': 0.85, 'ambition': 0.3}),
        ]
    },
    'science_collective': {
        'government': 'technocracy', 'aggression': 0.2, 'expansion': 0.6,
        'economic_focus': 0.7, 'diplomacy': 0.6, 'treasury': 35000,
        'leader': ('archon_voss', 'Archon Lyra Voss', 'Chief Researcher', {'aggression': 0.1, 'caution': 0.5, 'competence': 0.95, 'loyalty': 0.9, 'ambition': 0.7}),
        'agents': [
            ('prof_okafor', 'Professor Adisa Okafor', 'Lead Engineer', 'director', {'aggression': 0.1, 'caution': 0.7, 'competence': 0.85, 'loyalty': 0.9, 'ambition': 0.4}),
            ('cmdr_reis', 'Commander Hana Reis', 'Defense Coordinator', 'admiral', {'aggression': 0.4, 'caution': 0.6, 'competence': 0.7, 'loyalty': 0.8, 'ambition': 0.3}),
            ('gov_tanaka', 'Governor Yuki Tanaka', 'Colony Director', 'governor', {'aggression': 0.2, 'caution': 0.4, 'competence': 0.8, 'loyalty': 0.85, 'ambition': 0.5}),
        ]
    },
    'merchants_guild': {
        'government': 'oligarchy', 'aggression': 0.2, 'expansion': 0.5,
        'economic_focus': 0.9, 'diplomacy': 0.8, 'treasury': 100000,
        'leader': ('magnate_cross', 'Trade Magnate Victor Cross', 'Guild Master', {'aggression': 0.3, 'caution': 0.6, 'competence': 0.8, 'loyalty': 0.6, 'ambition': 0.9}),
        'agents': [
            ('broker_silva', 'Broker Camila Silva', 'Market Director', 'director', {'aggression': 0.1, 'caution': 0.7, 'competence': 0.9, 'loyalty': 0.7, 'ambition': 0.8}),
            ('capt_brennan', 'Captain Marcus Brennan', 'Convoy Marshal', 'admiral', {'aggression': 0.3, 'caution': 0.5, 'competence': 0.65, 'loyalty': 0.75, 'ambition': 0.4}),
            ('gov_nouri', 'Governor Fatima Nouri', 'Station Overseer', 'governor', {'aggression': 0.2, 'caution': 0.5, 'competence': 0.7, 'loyalty': 0.8, 'ambition': 0.5}),
        ]
    },
    'free_states': {
        'government': 'confederation', 'aggression': 0.4, 'expansion': 0.3,
        'economic_focus': 0.5, 'diplomacy': 0.4, 'treasury': 25000,
        'leader': ('pres_okoro', 'President Zara Okoro', 'Elected President', {'aggression': 0.5, 'caution': 0.4, 'competence': 0.7, 'loyalty': 0.95, 'ambition': 0.3}),
        'agents': [
            ('gen_frost', 'General Jack Frost', 'Militia Commander', 'general', {'aggression': 0.7, 'caution': 0.3, 'competence': 0.6, 'loyalty': 0.9, 'ambition': 0.4}),
            ('gov_santos', 'Governor Maria Santos', 'Frontier Governor', 'governor', {'aggression': 0.3, 'caution': 0.5, 'competence': 0.75, 'loyalty': 0.85, 'ambition': 0.6}),
            ('capt_nguyen', 'Captain Linh Nguyen', 'Patrol Leader', 'admiral', {'aggression': 0.6, 'caution': 0.4, 'competence': 0.7, 'loyalty': 0.8, 'ambition': 0.5}),
        ]
    },
    'iron_compact': {
        'government': 'military_junta', 'aggression': 0.8, 'expansion': 0.9,
        'economic_focus': 0.3, 'diplomacy': 0.2, 'treasury': 40000,
        'leader': ('marshal_krov', 'Grand Marshal Alexei Krov', 'Supreme Marshal', {'aggression': 0.9, 'caution': 0.2, 'competence': 0.85, 'loyalty': 0.5, 'ambition': 0.95}),
        'agents': [
            ('gen_steele', 'General Irena Steele', 'War Strategist', 'general', {'aggression': 0.8, 'caution': 0.4, 'competence': 0.9, 'loyalty': 0.7, 'ambition': 0.7}),
            ('adm_drake', 'Admiral Conrad Drake', 'Fleet Commander', 'admiral', {'aggression': 0.7, 'caution': 0.3, 'competence': 0.8, 'loyalty': 0.6, 'ambition': 0.8}),
            ('gov_petrov', 'Governor Oleg Petrov', 'Industrial Overseer', 'governor', {'aggression': 0.4, 'caution': 0.6, 'competence': 0.6, 'loyalty': 0.7, 'ambition': 0.5}),
        ]
    },
    'corsairs': {
        'government': 'anarchy', 'aggression': 0.9, 'expansion': 0.4,
        'economic_focus': 0.2, 'diplomacy': 0.1, 'treasury': 15000,
        'leader': ('warlord_vex', 'Warlord Silas Vex', 'Pirate King', {'aggression': 0.95, 'caution': 0.1, 'competence': 0.7, 'loyalty': 0.3, 'ambition': 1.0}),
        'agents': [
            ('raider_black', 'Raider Captain Jax Black', 'Raid Boss', 'admiral', {'aggression': 0.9, 'caution': 0.2, 'competence': 0.6, 'loyalty': 0.4, 'ambition': 0.7}),
            ('fence_quinn', 'The Fence Quinn', 'Smuggling Director', 'director', {'aggression': 0.3, 'caution': 0.7, 'competence': 0.8, 'loyalty': 0.5, 'ambition': 0.6}),
            ('ghost_mira', 'Ghost Mira', 'Intelligence Broker', 'spymaster', {'aggression': 0.4, 'caution': 0.6, 'competence': 0.85, 'loyalty': 0.3, 'ambition': 0.8}),
        ]
    },
}


def setup():
    conn = sqlite3.connect(DB)

    # Create tables
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS faction_agents (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            title TEXT DEFAULT '',
            faction_id TEXT NOT NULL,
            role TEXT NOT NULL,
            aggression REAL DEFAULT 0.5,
            caution REAL DEFAULT 0.5,
            competence REAL DEFAULT 0.5,
            loyalty REAL DEFAULT 0.8,
            ambition REAL DEFAULT 0.3,
            corruption REAL DEFAULT 0.1,
            assignment_type TEXT DEFAULT '',
            assignment_target TEXT DEFAULT '',
            battles_won INTEGER DEFAULT 0,
            battles_lost INTEGER DEFAULT 0,
            reputation REAL DEFAULT 0.5,
            alive INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS faction_state (
            faction_id TEXT PRIMARY KEY,
            leader_id TEXT,
            government TEXT DEFAULT '',
            aggression REAL DEFAULT 0.5,
            expansion_drive REAL DEFAULT 0.5,
            economic_focus REAL DEFAULT 0.5,
            diplomacy_openness REAL DEFAULT 0.5,
            treasury REAL DEFAULT 10000,
            priorities TEXT DEFAULT '[]',
            relationships TEXT DEFAULT '{}',
            last_decision_tick INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS faction_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tick INTEGER,
            faction_id TEXT,
            event_type TEXT,
            target TEXT DEFAULT '',
            details TEXT DEFAULT ''
        );
    """)

    # Seed agents and state
    for fid, fdata in FACTIONS.items():
        # Leader
        lid, lname, ltitle, ltraits = fdata['leader']
        conn.execute("""INSERT OR REPLACE INTO faction_agents 
            (id, name, title, faction_id, role, aggression, caution, competence, loyalty, ambition)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (lid, lname, ltitle, fid, 'leader',
             ltraits['aggression'], ltraits['caution'], ltraits['competence'], ltraits['loyalty'], ltraits['ambition']))

        # Other agents
        for aid, aname, atitle, arole, atraits in fdata['agents']:
            conn.execute("""INSERT OR REPLACE INTO faction_agents
                (id, name, title, faction_id, role, aggression, caution, competence, loyalty, ambition)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (aid, aname, atitle, fid, arole,
                 atraits['aggression'], atraits['caution'], atraits['competence'], atraits['loyalty'], atraits['ambition']))

        # Faction state
        conn.execute("""INSERT OR REPLACE INTO faction_state
            (faction_id, leader_id, government, aggression, expansion_drive, economic_focus, diplomacy_openness, treasury)
            VALUES (?,?,?,?,?,?,?,?)""",
            (fid, lid, fdata['government'], fdata['aggression'], fdata['expansion'],
             fdata['economic_focus'], fdata['diplomacy'], fdata['treasury']))

    conn.commit()

    # Report
    agents = conn.execute("SELECT COUNT(*) FROM faction_agents").fetchone()[0]
    states = conn.execute("SELECT COUNT(*) FROM faction_state").fetchone()[0]
    print(f"Created: {agents} agents, {states} faction states")
    print("\nLeadership:")
    for r in conn.execute("SELECT fa.name, fa.title, fs.government, fa.faction_id FROM faction_agents fa JOIN faction_state fs ON fa.faction_id=fs.faction_id WHERE fa.role='leader'"):
        print(f"  {r[0]} ({r[1]}) - {r[3]} [{r[2]}]")

    conn.close()


if __name__ == '__main__':
    setup()
