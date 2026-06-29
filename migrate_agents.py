"""Expand agent system: add population agents, history tracking, structured events."""
import sqlite3
import os

DB = os.path.join(os.path.dirname(__file__), "data", "game_data.db")


def migrate():
    conn = sqlite3.connect(DB)

    # Add columns to faction_agents if missing
    existing = {r[1] for r in conn.execute("PRAGMA table_info(faction_agents)").fetchall()}
    new_cols = {
        'system_id': 'TEXT DEFAULT ""',
        'station_id': 'TEXT DEFAULT ""',
        'ship_id': 'TEXT DEFAULT ""',
        'rank': 'INTEGER DEFAULT 1',
        'wealth': 'REAL DEFAULT 100',
        'kills': 'INTEGER DEFAULT 0',
        'died_tick': 'INTEGER DEFAULT 0',
        'cause_of_death': 'TEXT DEFAULT ""',
        'patron_id': 'TEXT DEFAULT ""',
        'rival_id': 'TEXT DEFAULT ""',
    }
    for col, typedef in new_cols.items():
        if col not in existing:
            conn.execute(f"ALTER TABLE faction_agents ADD COLUMN {col} {typedef}")

    # Agent history log (accumulates over time, M&B style)
    conn.execute("""CREATE TABLE IF NOT EXISTS agent_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tick INTEGER NOT NULL,
        agent_id TEXT NOT NULL,
        event_type TEXT NOT NULL,
        detail TEXT DEFAULT '',
        related_agent_id TEXT DEFAULT '',
        system_id TEXT DEFAULT ''
    )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_hist_agent ON agent_history(agent_id)")

    # Structured events (replaces plain text EventLog for major events)
    conn.execute("""CREATE TABLE IF NOT EXISTS sim_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tick INTEGER NOT NULL,
        category TEXT NOT NULL,
        severity INTEGER DEFAULT 1,
        faction_id TEXT DEFAULT '',
        system_id TEXT DEFAULT '',
        agent_id TEXT DEFAULT '',
        title TEXT NOT NULL,
        detail TEXT DEFAULT '',
        effects TEXT DEFAULT '[]',
        chain_id TEXT DEFAULT '',
        chain_step INTEGER DEFAULT 0
    )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sim_events_tick ON sim_events(tick)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sim_events_faction ON sim_events(faction_id)")

    conn.commit()
    conn.close()
    print("Schema migration complete.")


if __name__ == "__main__":
    migrate()
