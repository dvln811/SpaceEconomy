"""Game data database schema and management.

Two databases:
- game_data.db: Static game data (items, ships, systems, factions). Updatable without nuke.
- game.db: Runtime simulation state (inventories, positions, prices). Nuked on reset.
"""
import sqlite3
import os
import json

DATA_DIR = os.getenv("DATA_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"))

GAME_DATA_DB = os.path.join(DATA_DIR, "game_data.db")
GAME_STATE_DB = os.path.join(DATA_DIR, "game.db")


def get_data_db() -> sqlite3.Connection:
    """Get connection to the static game data database."""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(GAME_DATA_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_data_schema(conn: sqlite3.Connection):
    """Create all tables for game_data.db."""
    conn.executescript("""
    -- Factions
    CREATE TABLE IF NOT EXISTS factions (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        short TEXT NOT NULL,
        philosophy TEXT DEFAULT '',
        home_cluster TEXT DEFAULT '',
        allies TEXT DEFAULT '[]',      -- JSON array of faction IDs
        enemies TEXT DEFAULT '[]',     -- JSON array of faction IDs
        color TEXT DEFAULT '#ffffff'
    );

    -- Corporations (sub-factions)
    CREATE TABLE IF NOT EXISTS corporations (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        faction_id TEXT NOT NULL REFERENCES factions(id),
        focus TEXT DEFAULT '',
        description TEXT DEFAULT ''
    );

    -- Commodities (items)
    CREATE TABLE IF NOT EXISTS commodities (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        base_price REAL NOT NULL,
        tier INTEGER NOT NULL,
        volume REAL DEFAULT 1.0,
        elasticity REAL DEFAULT 1.0,
        description TEXT DEFAULT '',
        category TEXT DEFAULT '',
        subcategory TEXT DEFAULT '',
        stats TEXT DEFAULT '{}'        -- JSON dict of fitting stats
    );

    -- Recipes (what inputs a commodity needs)
    CREATE TABLE IF NOT EXISTS recipes (
        commodity_id TEXT NOT NULL REFERENCES commodities(id),
        input_id TEXT NOT NULL REFERENCES commodities(id),
        quantity REAL NOT NULL,
        PRIMARY KEY (commodity_id, input_id)
    );

    -- Star systems
    CREATE TABLE IF NOT EXISTS systems (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        system_type TEXT DEFAULT '',
        cluster TEXT DEFAULT '',
        security TEXT DEFAULT 'high',
        faction_id TEXT DEFAULT '' REFERENCES factions(id),
        x REAL DEFAULT 0,
        y REAL DEFAULT 0,
        z REAL DEFAULT 0
    );

    -- System connections (bidirectional, store both directions)
    CREATE TABLE IF NOT EXISTS system_connections (
        from_id TEXT NOT NULL REFERENCES systems(id),
        to_id TEXT NOT NULL REFERENCES systems(id),
        PRIMARY KEY (from_id, to_id)
    );

    -- Stations
    CREATE TABLE IF NOT EXISTS stations (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        system_id TEXT NOT NULL REFERENCES systems(id),
        station_type TEXT DEFAULT 'trade_hub',
        production_rate REAL DEFAULT 1.0
    );

    -- Station produces (what a station can manufacture)
    CREATE TABLE IF NOT EXISTS station_produces (
        station_id TEXT NOT NULL REFERENCES stations(id),
        commodity_id TEXT NOT NULL REFERENCES commodities(id),
        PRIMARY KEY (station_id, commodity_id)
    );

    -- Asteroid fields
    CREATE TABLE IF NOT EXISTS asteroid_fields (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        system_id TEXT NOT NULL REFERENCES systems(id),
        field_type TEXT DEFAULT '',
        density REAL DEFAULT 1.0,
        danger REAL DEFAULT 0.0
    );

    -- Asteroid field yields
    CREATE TABLE IF NOT EXISTS field_yields (
        field_id TEXT NOT NULL REFERENCES asteroid_fields(id),
        commodity_id TEXT NOT NULL REFERENCES commodities(id),
        PRIMARY KEY (field_id, commodity_id)
    );

    -- System objects (stars, planets, moons, gates, belts)
    CREATE TABLE IF NOT EXISTS system_objects (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        system_id TEXT NOT NULL REFERENCES systems(id),
        obj_type TEXT NOT NULL,
        distance REAL DEFAULT 0,
        angle REAL DEFAULT 0,
        parent TEXT DEFAULT '',
        connects_to TEXT DEFAULT ''
    );

    -- Civilian ship types
    CREATE TABLE IF NOT EXISTS ship_types (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        role TEXT DEFAULT 'hauler',
        tier INTEGER DEFAULT 1,
        cargo_capacity INTEGER DEFAULT 200,
        fuel_capacity INTEGER DEFAULT 100,
        speed REAL DEFAULT 1.0,
        intra_speed REAL DEFAULT 0.2,
        hull_hp INTEGER DEFAULT 100,
        align_time INTEGER DEFAULT 5,
        hardpoints TEXT DEFAULT '{}',   -- JSON dict
        build_cost TEXT DEFAULT '{}',   -- JSON dict
        description TEXT DEFAULT ''
    );

    -- Military ship classes
    CREATE TABLE IF NOT EXISTS military_ships (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        hull_class TEXT NOT NULL,
        faction_id TEXT NOT NULL REFERENCES factions(id),
        hull_hp INTEGER DEFAULT 0,
        armor_hp INTEGER DEFAULT 0,
        shield_hp INTEGER DEFAULT 0,
        crew INTEGER DEFAULT 0,
        weapons TEXT DEFAULT '[]',      -- JSON array
        modules TEXT DEFAULT '[]',      -- JSON array
        build_cost TEXT DEFAULT '{}',   -- JSON dict
        description TEXT DEFAULT ''
    );

    -- Fleet targets (how many of each ship each faction wants)
    CREATE TABLE IF NOT EXISTS fleet_targets (
        faction_id TEXT NOT NULL REFERENCES factions(id),
        ship_id TEXT NOT NULL REFERENCES military_ships(id),
        target_count INTEGER DEFAULT 1,
        PRIMARY KEY (faction_id, ship_id)
    );

    -- Station consumption (what each station type consumes as end-use)
    CREATE TABLE IF NOT EXISTS station_consumption (
        station_type TEXT NOT NULL,
        commodity_id TEXT NOT NULL REFERENCES commodities(id),
        PRIMARY KEY (station_type, commodity_id)
    );

    -- Schema version tracking
    CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER PRIMARY KEY,
        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()


if __name__ == "__main__":
    conn = get_data_db()
    init_data_schema(conn)
    print(f"Schema created at {GAME_DATA_DB}")
    conn.close()
